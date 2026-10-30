"""Instruction-level reference model for the word-addressed OpenCPU ISA v2.

The cycle counter counts reference-model steps, not FPGA pipeline clocks. IRQs
are sampled after retirement, so MEPC names the next real instruction.
"""

from dataclasses import dataclass

from .isa import OPCODES, sign_extend, word


CSR_CYCLE, CSR_CYCLEH, CSR_MTVEC, CSR_MCAUSE = range(4)
CSR_MEPC, CSR_MIE, CSR_MSTATUS, CSR_MSCRATCH = range(4, 8)
MIE = 1 << 3
MPIE = 1 << 7


@dataclass(slots=True)
class _Undo:
    state: dict
    memory_change: tuple[int, bool, int] | None = None


class Simulator:
    """Instruction-level CPU with memory-efficient reversible execution."""

    DEFAULT_MAX_STEPS = 10000

    def __init__(self, start_pc=0, ram_depth=1024, rom_depth=1024):
        if type(start_pc) is not int or not 0 <= start_pc <= 65535:
            raise ValueError("start_pc must be a word address in 0..65535")
        if any(type(depth) is not int or not 1 <= depth <= 65536 for depth in (ram_depth, rom_depth)):
            raise ValueError("memory depths must be integers in 1..65536")
        self.start_pc = start_pc
        self.ram_depth = ram_depth
        self.rom_depth = rom_depth
        self.inst_mem = {}
        self.reset()

    def reset(self):
        """Reset execution and RAM, retaining the loaded instruction image."""
        self.registers = [0] * 8
        self.data_mem = {}
        self.csr = {index: 0 for index in range(8)}
        self.cycle = 0
        self.instructions_retired = 0
        self.pc = self.start_pc
        self.next_pc = self.start_pc
        self.last_pc = self.start_pc
        self.halted = False
        self.faulted = False
        self.fault_reason = None
        self.stopped = False
        self.limit_reached = False
        self.in_interrupt = False
        self.irq_taken = False
        self.pending_interrupts = 0
        self._history = []

    def _capture_control(self):
        return {
            "registers": self.registers.copy(),
            "csr": self.csr.copy(), "cycle": self.cycle,
            "instructions_retired": self.instructions_retired,
            "pc": self.pc, "next_pc": self.next_pc, "last_pc": self.last_pc,
            "halted": self.halted, "faulted": self.faulted,
            "fault_reason": self.fault_reason, "stopped": self.stopped,
            "limit_reached": self.limit_reached, "in_interrupt": self.in_interrupt,
            "irq_taken": self.irq_taken, "pending_interrupts": self.pending_interrupts,
        }

    @property
    def can_undo(self):
        return bool(self._history)

    def snapshot(self):
        """Copy the full machine state on explicit request, never on each step."""
        return dict(self._capture_control(), data_mem=self.data_mem.copy())

    def _restore(self, snapshot):
        for name, value in snapshot.items():
            setattr(self, name, value)

    def read_csr(self, address):
        if address == CSR_CYCLE:
            return self.cycle & 0xFFFF
        if address == CSR_CYCLEH:
            return (self.cycle >> 16) & 0xFFFF
        return self.csr.get(address, 0)

    def write_csr(self, address, value):
        if CSR_MTVEC <= address <= CSR_MSCRATCH:
            self.csr[address] = word(value)

    def request_interrupt(self, mask=1):
        """Latch IRQ bits until accepted; bit 0 has the highest priority."""
        self.pending_interrupts |= int(mask) & 0xFF

    def _mapped_data_address(self, address):
        return 0 <= address < self.ram_depth or 0xFF00 <= address <= 0xFF5F

    def _read_data(self, address):
        return word(self.data_mem.get(address, 0)) if self._mapped_data_address(address) else 0

    def _write_data(self, address, value):
        if self._mapped_data_address(address):
            change = (address, address in self.data_mem, self.data_mem.get(address, 0))
            self.data_mem[address] = word(value)
            return change
        return None

    def _fetch(self, address):
        if not 0 <= address < self.rom_depth:
            raise ValueError("instruction address %d is outside ROM" % address)
        if isinstance(self.inst_mem, dict):
            instruction = self.inst_mem.get(address, OPCODES["halt"])
        else:
            instruction = self.inst_mem[address] if address < len(self.inst_mem) else OPCODES["halt"]
        if not isinstance(instruction, int) or not 0 <= instruction <= 0xFFFF:
            raise ValueError("instruction at word address %d is not a 16-bit word" % address)
        return instruction

    def step(self, irq=0):
        """Retire one instruction; return False when halted or stopped.

        IRQ is the external level sampled for this instruction only. RAM and
        MMIO store 16-bit words. Unmapped reads return zero, unmapped writes are
        ignored. Unloaded ROM words are HALTs; an explicit zero word is a NOP.
        """
        if self.halted or self.faulted or self.stopped:
            return False
        undo = _Undo(self._capture_control())
        try:
            instruction = self._fetch(self.pc)
        except ValueError as error:
            self.faulted = True
            self.fault_reason = str(error)
            return False
        opcode = instruction & 0x1F
        invalid = (
            opcode in (14, 15)
            or (opcode <= 7 and instruction >> 11 != 0)
            or (opcode in (10, 11, 31) and instruction >> 5 != 0)
            or (opcode in (26, 27) and (instruction >> 8) & 7 != 0)
        )
        if invalid:
            self.faulted = True
            self.fault_reason = "illegal instruction 0x%04x at word address %d" % (instruction, self.pc)
            return False
        rd = (instruction >> 5) & 7
        rs = (instruction >> 8) & 7
        immediate = instruction >> 8
        offset = sign_extend(instruction >> 11, 5)
        self.registers[0] = 0
        a, b = self.registers[rd], self.registers[rs]
        destination = word(self.pc + 1)
        result = None
        self.irq_taken = False

        if opcode <= OPCODES["srl"]:
            operations = (
                lambda: a + b, lambda: a - b, lambda: a * b,
                lambda: a & b, lambda: a | b, lambda: a ^ b,
                lambda: a << b if b < 16 else 0,
                lambda: a >> b if b < 16 else 0,
            )
            result = operations[opcode]()
        elif opcode == OPCODES["beq"]:
            if a == b:
                destination = word(destination + offset)
        elif opcode == OPCODES["blt"]:
            if sign_extend(a, 16) < sign_extend(b, 16):
                destination = word(destination + offset)
        elif opcode == OPCODES["halt"]:
            self.halted = True
        elif opcode == OPCODES["mret"]:
            status = self.csr[CSR_MSTATUS]
            self.csr[CSR_MSTATUS] = (status & ~MIE) | (MIE if status & MPIE else 0) | MPIE
            destination = self.csr[CSR_MEPC]
            self.in_interrupt = False
        elif opcode == OPCODES["lui"]:
            result = immediate << 8
        elif opcode == OPCODES["j"]:
            destination = word(destination + sign_extend(instruction >> 5, 11))
        elif opcode == OPCODES["addi"]:
            result = a + sign_extend(immediate, 8)
        elif opcode == OPCODES["subi"]:
            result = a - sign_extend(immediate, 8)
        elif opcode == OPCODES["muli"]:
            result = a * sign_extend(immediate, 8)
        elif opcode == OPCODES["andi"]:
            result = a & immediate
        elif opcode == OPCODES["ori"]:
            result = a | immediate
        elif opcode == OPCODES["xori"]:
            result = a ^ immediate
        elif opcode == OPCODES["slli"]:
            result = a << immediate if immediate < 16 else 0
        elif opcode == OPCODES["srli"]:
            result = a >> immediate if immediate < 16 else 0
        elif opcode == OPCODES["lw"]:
            result = self._read_data(word(b + offset))
        elif opcode == OPCODES["sw"]:
            undo.memory_change = self._write_data(word(b + offset), a)
        elif opcode == OPCODES["csrr"]:
            result = self.read_csr(instruction >> 11)
        elif opcode == OPCODES["csrw"]:
            self.write_csr(instruction >> 11, a)
        elif opcode == OPCODES["jal"]:
            result = destination
            destination = word(destination + sign_extend(immediate, 8))
        elif opcode == OPCODES["jr"]:
            destination = word(a + sign_extend(immediate, 8))
        elif opcode == OPCODES["li"]:
            result = immediate
        elif opcode == OPCODES["rc"]:
            self.registers = [0] * 8

        if result is not None and rd:
            self.registers[rd] = word(result)
        self.registers[0] = 0
        # A CSRW has already committed, so interrupt enables take effect now.
        eligible = (self.pending_interrupts | int(irq)) & self.csr[CSR_MIE] & 0xFF
        if (eligible and self.csr[CSR_MSTATUS] & MIE and not self.in_interrupt
                and not self.halted and opcode != OPCODES["mret"]):
            selected = eligible & -eligible
            self.pending_interrupts &= ~selected
            self.csr[CSR_MEPC] = destination
            self.csr[CSR_MCAUSE] = selected.bit_length() - 1
            status = self.csr[CSR_MSTATUS]
            self.csr[CSR_MSTATUS] = (status & ~(MIE | MPIE)) | (MPIE if status & MIE else 0)
            destination = self.csr[CSR_MTVEC]
            self.in_interrupt = True
            self.irq_taken = True
        self.last_pc = self.pc
        self.pc = self.next_pc = destination
        self.cycle = (self.cycle + 1) & 0xFFFFFFFF
        self.instructions_retired += 1
        self._history.append(undo)
        return True

    def run_step(self):
        return self.step()

    def run(self, max_steps=DEFAULT_MAX_STEPS):
        """Run a bounded number of steps, including programs with infinite loops."""
        if not isinstance(max_steps, int) or max_steps < 0:
            raise ValueError("max_steps must be a nonnegative integer")
        self.stopped = False
        self.limit_reached = False
        count = 0
        while count < max_steps and self.step():
            count += 1
        self.limit_reached = count == max_steps and not self.halted and not self.faulted and not self.stopped
        return count

    def run_undo(self):
        """Restore registers, memory, CSRs, control state and PC from a snapshot."""
        if not self._history:
            return False
        undo = self._history.pop()
        if undo.memory_change is not None:
            address, was_present, old_value = undo.memory_change
            if was_present:
                self.data_mem[address] = old_value
            else:
                self.data_mem.pop(address, None)
        self._restore(undo.state)
        return True

    def stop(self):
        self.stopped = True
