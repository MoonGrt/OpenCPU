"""Instruction-level reference model for the word-addressed OpenCPU ISA v2.

The cycle counter counts reference-model steps, not FPGA pipeline clocks. IRQs
are sampled after retirement, so MEPC names the next real instruction.
"""

from collections import deque
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
    peripheral_state: object = None


class Simulator:
    """Instruction-level CPU with memory-efficient reversible execution."""

    DEFAULT_MAX_STEPS = 10000

    def __init__(self, start_pc=0, ram_depth=1024, rom_depth=1024, *,
                 history_limit=10000, peripherals=None):
        if type(start_pc) is not int or not 0 <= start_pc <= 65535:
            raise ValueError("start_pc must be a word address in 0..65535")
        if any(type(depth) is not int or not 1 <= depth <= 65536 for depth in (ram_depth, rom_depth)):
            raise ValueError("memory depths must be integers in 1..65536")
        if history_limit is not None and (type(history_limit) is not int or history_limit < 0):
            raise ValueError("history_limit must be a nonnegative integer or None")
        if peripherals is None:
            from .peripherals import PeripheralModel
            peripherals = PeripheralModel()
        self.peripherals = peripherals
        self.history_limit = history_limit
        self.breakpoints = set()
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
        self.fault_pc = None
        self.fault_inst = None
        self.fault_code = 0
        self.stop_reason = None
        self.breakpoint_hit = None
        self.last_retire = None
        self.stopped = False
        self.limit_reached = False
        self.in_interrupt = False
        self.irq_taken = False
        self.pending_interrupts = 0
        self.peripherals.reset()
        self._history = deque(maxlen=self.history_limit)

    def _capture_control(self):
        return {
            "registers": self.registers.copy(),
            "csr": self.csr.copy(), "cycle": self.cycle,
            "instructions_retired": self.instructions_retired,
            "pc": self.pc, "next_pc": self.next_pc, "last_pc": self.last_pc,
            "halted": self.halted, "faulted": self.faulted,
            "fault_reason": self.fault_reason, "fault_pc": self.fault_pc,
            "fault_inst": self.fault_inst, "fault_code": self.fault_code,
            "stop_reason": self.stop_reason, "breakpoint_hit": self.breakpoint_hit,
            "last_retire": self._copy_retire(self.last_retire), "stopped": self.stopped,
            "limit_reached": self.limit_reached, "in_interrupt": self.in_interrupt,
            "irq_taken": self.irq_taken, "pending_interrupts": self.pending_interrupts,
        }

    @staticmethod
    def _copy_retire(record):
        if record is None:
            return None
        return dict(record, registers=list(record["registers"]), csrs=list(record["csrs"]))

    def _begin_undo(self):
        if self.history_limit == 0:
            return None
        return _Undo(self._capture_control(), peripheral_state=self.peripherals.checkpoint())

    def _remember(self, undo):
        if undo is not None:
            self._history.append(undo)

    @property
    def history_size(self):
        return len(self._history)

    def clear_history(self):
        self._history.clear()

    @property
    def can_undo(self):
        return bool(self._history)

    def snapshot(self, *, include_output=True):
        """Copy the full machine state on explicit request, never on each step."""
        return dict(self._capture_control(), data_mem=self.data_mem.copy(),
                    peripherals=self.peripherals.snapshot(include_output=include_output))

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

    @staticmethod
    def _mask(value):
        if type(value) is not int or not 0 <= value <= 255:
            raise ValueError("IRQ mask must be an integer in 0..255")
        return value

    def request_interrupt(self, mask=1):
        """Latch external events until a retirement acknowledges their source."""
        mask = self._mask(mask)
        if mask:
            undo = self._begin_undo()
            self.pending_interrupts |= mask
            self._remember(undo)

    def set_inputs(self, *, buttons=None, switches=None):
        """Change GPIO inputs as an independently reversible debugger event."""
        undo = self._begin_undo()
        self.peripherals.set_inputs(buttons=buttons, switches=switches)
        self._remember(undo)

    def inject_uart(self, data, *, framing_error=False):
        """Queue received bytes; the device raises an event on its next tick."""
        undo = self._begin_undo()
        self.peripherals.inject_uart(data, framing_error=framing_error)
        self._remember(undo)

    def advance_ticks(self, ticks=1):
        """Advance devices while the CPU is idle, including after HALT/fault.

        One logical tick is also one reference-model cycle. These ticks do not
        model the RTL pipeline's physical clocks and do not retire instructions.
        """
        if type(ticks) is not int or ticks < 0:
            raise ValueError("ticks must be a nonnegative integer")
        if not ticks:
            return 0
        undo = self._begin_undo()
        events = self.peripherals.tick(ticks)
        self.pending_interrupts |= events & 255
        self.cycle = (self.cycle + ticks) & 0xFFFFFFFF
        self._remember(undo)
        return events

    @staticmethod
    def _address(address):
        if type(address) is not int or not 0 <= address <= 65535:
            raise ValueError("memory address must be an integer in 0..65535")
        return address

    def _mapped_data_address(self, address):
        return 0 <= address < min(self.ram_depth, 0xFF00) or 0xFF00 <= address <= 0xFFFF

    def peek_data(self, address):
        """Inspect a word without consuming FIFOs or changing device state."""
        return self._read_data(self._address(address), side_effects=False)

    def read_data(self, address, *, side_effects=False):
        """Read RAM/MMIO; debugger reads are non-destructive by default.

        Explicit side-effectful reads are reversible events. Instruction LW
        uses the internal bus read and joins its side effects to that step.
        """
        address = self._address(address)
        if not side_effects:
            return self._read_data(address, side_effects=False)
        undo = self._begin_undo()
        result = self._read_data(address)
        self._remember(undo)
        return result

    def _read_data(self, address, *, side_effects=True):
        if 0xFF00 <= address <= 0xFFFF:
            return word(self.peripherals.read(address, side_effects=side_effects))
        if 0 <= address < self.ram_depth:
            return word(self.data_mem.get(address, 0))
        return 0

    def _write_data(self, address, value):
        if 0xFF00 <= address <= 0xFFFF:
            self.peripherals.write(address, word(value))
        elif 0 <= address < self.ram_depth:
            change = (address, address in self.data_mem, self.data_mem.get(address, 0))
            self.data_mem[address] = word(value)
            return change
        return None

    def _fault(self, code, reason, instruction, undo):
        self.faulted = True
        self.fault_reason = reason
        self.fault_pc = self.pc
        self.fault_inst = instruction
        self.fault_code = code
        self.stop_reason = "fault"
        self._remember(undo)
        return False

    def _fetch(self, address):
        if not 0 <= address < self.rom_depth:
            raise ValueError("instruction address %d is outside ROM" % address)
        if isinstance(self.inst_mem, dict):
            instruction = self.inst_mem.get(address, OPCODES["halt"])
        else:
            instruction = self.inst_mem[address] if address < len(self.inst_mem) else OPCODES["halt"]
        if type(instruction) is not int or not 0 <= instruction <= 0xFFFF:
            raise ValueError("instruction at word address %d is not a 16-bit word" % address)
        return instruction

    def step(self, irq=0):
        """Retire one instruction; return False when halted or stopped.

        IRQ is an external level sampled for this instruction only. Device
        events raised after retirement latch for the following instruction.
        Unmapped reads return zero and writes are ignored. Unloaded ROM words
        are HALTs; an explicit zero word is a NOP. Step ignores breakpoints.
        """
        if self.halted or self.faulted or (self.stopped and self.stop_reason != "breakpoint"):
            return False
        irq = self._mask(irq)
        undo = self._begin_undo()
        self.stopped = False
        self.stop_reason = None
        self.breakpoint_hit = None
        self.limit_reached = False
        self.irq_taken = False
        try:
            instruction = self._fetch(self.pc)
        except ValueError as error:
            return self._fault(2, str(error), None, undo)
        opcode = instruction & 0x1F
        invalid = (
            opcode in (14, 15)
            or (opcode <= 7 and instruction >> 11 != 0)
            or (opcode in (10, 11, 31) and instruction >> 5 != 0)
            or (opcode in (26, 27) and (instruction >> 8) & 7 != 0)
        )
        if invalid:
            return self._fault(1, "illegal instruction 0x%04x at word address %d" % (instruction, self.pc),
                               instruction, undo)
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
            change = self._write_data(word(b + offset), a)
            if undo is not None:
                undo.memory_change = change
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
        selected = 0
        eligible = (self.pending_interrupts | irq) & self.csr[CSR_MIE] & 0xFF
        if (eligible and self.csr[CSR_MSTATUS] & MIE and not self.in_interrupt
                and not self.halted and opcode != OPCODES["mret"]):
            selected = eligible & -eligible
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
        events = self.peripherals.tick()
        self.pending_interrupts = ((self.pending_interrupts & ~selected) | events) & 255
        if self.halted:
            self.stop_reason = "halt"
        self.last_retire = {
            "pc": self.last_pc, "instruction": instruction, "next_pc": destination,
            "registers": self.registers.copy(),
            "csrs": [self.read_csr(address) for address in range(2, 8)],
            "irq_ack": selected, "irq": self.irq_taken,
        }
        self._remember(undo)
        return True

    def run_step(self):
        return self.step()

    @staticmethod
    def _breakpoint_set(values):
        try:
            values = set(values)
        except TypeError as error:
            raise ValueError("breakpoints must contain word addresses") from error
        if any(type(value) is not int or not 0 <= value <= 65535 for value in values):
            raise ValueError("breakpoints must contain word addresses in 0..65535")
        return values

    def run(self, max_steps=DEFAULT_MAX_STEPS, *, breakpoints=None, trace=None):
        """Run bounded instructions; breakpoints stop before an instruction.

        Calling Run again at the breakpoint that just stopped execution skips
        that initial check once. A loop returning to it stops normally. Single
        Step always executes the instruction. Trace receives retired records.
        """
        if type(max_steps) is not int or max_steps < 0:
            raise ValueError("max_steps must be a nonnegative integer")
        points = self._breakpoint_set(self.breakpoints if breakpoints is None else breakpoints)
        if trace is not None and not callable(trace):
            raise ValueError("trace must be a callable accepting a retirement record")
        resume = self.stop_reason == "breakpoint" and self.breakpoint_hit == self.pc
        self.stopped = False
        self.limit_reached = False
        self.stop_reason = "halt" if self.halted else "fault" if self.faulted else None
        self.breakpoint_hit = None
        count = 0
        while count < max_steps and not self.halted and not self.faulted and not self.stopped:
            if self.pc in points and not (resume and count == 0):
                self.stopped = True
                self.stop_reason = "breakpoint"
                self.breakpoint_hit = self.pc
                break
            if not self.step():
                break
            count += 1
            if trace is not None:
                trace(self._copy_retire(self.last_retire))
        if count == max_steps and not self.halted and not self.faulted and not self.stopped:
            self.limit_reached = True
            self.stop_reason = "limit"
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
        self.peripherals.restore(undo.peripheral_state)
        self._restore(undo.state)
        return True

    def stop(self):
        self.stopped = True
        self.stop_reason = "stopped"
        self.breakpoint_hit = None
