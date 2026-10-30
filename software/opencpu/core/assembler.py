"""Assembler and relaxing layout for the shared OpenCPU ISA v2."""

from dataclasses import dataclass
import re

from .isa import (
    BRANCH_OPS, CSR_OPS, I_SIGNED_OPS, I_UNSIGNED_OPS, MEM_OPS,
    OPCODES, REGISTERS, R_OPS, SHIFT_OPS, format_instruction, word,
)


class AssemblerError(ValueError):
    """An assembly error with a source line number."""


@dataclass
class _Instruction:
    line: int
    labels: tuple
    mnemonic: str
    operands: tuple
    source: str
    size: int = 0
    pc: int = 0


class Assembler:
    """Assemble ISA v2 source with deterministic, relaxing word layout."""

    def __init__(self):
        self.opcode_dict = {name: f"{opcode:05b}" for name, opcode in OPCODES.items()}
        self.opcode_dict["nop"] = "00000"
        self.reg_dict = dict(REGISTERS)
        self.clear()

    def clear(self):
        self.binary = ""
        self.basic_code = ""
        self.source_map = []
        self.labels = {}
        self.address = 0

    @staticmethod
    def _fail(instruction, message):
        raise AssemblerError(f"line {instruction.line}: {message} [{instruction.source}]")

    def _count(self, instruction, *counts):
        if len(instruction.operands) not in counts:
            expected = "/".join(map(str, counts))
            self._fail(instruction, f"{instruction.mnemonic} expects {expected} operands")

    def _register(self, token, instruction):
        value = self.reg_dict.get(token.lower())
        if value is None:
            self._fail(instruction, f"unknown register {token!r}")
        return value

    def _number(self, token, instruction):
        try:
            try:
                return int(token, 0)
            except ValueError:
                if re.fullmatch(r"[+-]?[0-9]+", token):
                    return int(token, 10)
                raise
        except (TypeError, ValueError):
            self._fail(instruction, f"expected integer or defined label, got {token!r}")

    def _range(self, value, low, high, instruction, description="immediate"):
        if not low <= value <= high:
            self._fail(instruction, f"{description} {value} is outside {low}..{high}")
        return value

    def _target(self, token, instruction):
        value = self.labels[token] if token in self.labels else self._number(token, instruction)
        return self._range(value, 0, 65535, instruction, "target word address")

    @staticmethod
    def _relative(target, pc):
        return ((target - (pc + 1) + 32768) & 65535) - 32768

    def _parse(self, source):
        instructions = []
        seen_labels = set()
        for line_number, raw in enumerate(source.splitlines(), 1):
            text = re.split(r"//|#|;", raw, maxsplit=1)[0].strip()
            if not text:
                continue
            labels = []
            while True:
                match = re.match(r"^([A-Za-z_.$][\w.$]*)\s*:\s*", text)
                if not match:
                    break
                name = match.group(1)
                if name in seen_labels:
                    raise AssemblerError(f"line {line_number}: duplicate label {name!r}")
                seen_labels.add(name)
                labels.append(name)
                text = text[match.end():]
            parts = text.split(None, 1)
            mnemonic = parts[0].lower() if parts else ""
            operands = ()
            if len(parts) == 2:
                operand_text = re.sub(r"\s*([()])\s*", r"\1", parts[1])
                operands = tuple(operand_text.replace(",", " ").split())
            instruction = _Instruction(line_number, tuple(labels), mnemonic, operands, raw.strip())
            instruction.size = self._initial_size(instruction)
            instructions.append(instruction)
        return instructions

    def _initial_size(self, instruction):
        name = instruction.mnemonic
        if not name:
            return 0
        if name == "ble":
            self._fail(instruction, "BLE is not an ISA v2 instruction; use BLT for signed <")
        if name == ".word":
            if not instruction.operands:
                self._fail(instruction, ".word expects at least one integer")
            return len(instruction.operands)
        if name == "li":
            self._count(instruction, 2)
            value = self._number(instruction.operands[1], instruction)
            self._range(value, -32768, 65535, instruction, "constant")
            return 1 if 0 <= value <= 255 else 2
        if name == "la":
            self._count(instruction, 2)
            return 2
        if name == "mov":
            self._count(instruction, 2)
            rd, rs = (self._register(token, instruction) for token in instruction.operands)
            return 1 if rd == rs else 2
        if name not in OPCODES and name not in ("nop", "call", "ret"):
            self._fail(instruction, f"unknown instruction {name!r}")
        return 1

    def _jal_operands(self, instruction):
        if instruction.mnemonic == "call":
            self._count(instruction, 1)
            return REGISTERS["ra"], instruction.operands[0]
        self._count(instruction, 2)
        return self._register(instruction.operands[0], instruction), instruction.operands[1]

    def _layout(self, instructions):
        # Expansions only grow, so forward references reach a fixed point.
        for _ in range(len(instructions) + 2):
            pc = 0
            self.labels = {}
            for instruction in instructions:
                instruction.pc = pc
                self.labels.update((label, pc) for label in instruction.labels)
                pc += instruction.size
            if pc > 65536:
                self._fail(instructions[-1], "program exceeds the 16-bit word address space")
            changed = False
            for instruction in instructions:
                if instruction.mnemonic in BRANCH_OPS:
                    self._count(instruction, 3)
                    target = self._target(instruction.operands[2], instruction)
                    delta = self._relative(target, instruction.pc)
                    if not -16 <= delta <= 15 and instruction.size < 3:
                        instruction.size = 3
                        changed = True
                elif instruction.mnemonic in ("jal", "call"):
                    rd, operand = self._jal_operands(instruction)
                    delta = self._relative(self._target(operand, instruction), instruction.pc)
                    if rd and not -128 <= delta <= 127 and instruction.size < 3:
                        instruction.size = 3
                        changed = True
            if not changed:
                return
        raise AssemblerError("instruction layout did not converge")

    def _r_operands(self, instruction):
        self._count(instruction, 2, 3)
        args = instruction.operands
        rd = self._register(args[0], instruction)
        rs = self._register(args[1], instruction)
        if len(args) == 3:
            if args[2].lower() in self.reg_dict:
                if rs != rd:
                    self._fail(instruction, "three-register form requires destination = first source")
                rs = self._register(args[2], instruction)
            elif self._number(args[2], instruction) != 0:
                self._fail(instruction, "register instruction's legacy placeholder must be zero")
        return rd, rs

    def _i_operands(self, instruction):
        self._count(instruction, 2, 3)
        args = instruction.operands
        rd = self._register(args[0], instruction)
        if len(args) == 3 and self._register(args[1], instruction) not in (rd, 0):
            self._fail(instruction, "immediate instruction updates rd; source must be rd or zero placeholder")
        return rd, self._number(args[-1], instruction)

    def _mem_operands(self, instruction):
        self._count(instruction, 2, 3)
        args = instruction.operands
        rd = self._register(args[0], instruction)
        if len(args) == 3:
            rs = self._register(args[1], instruction)
            offset = self._number(args[2], instruction)
        else:
            match = re.fullmatch(r"([^()]*)\(([^()]+)\)", args[1])
            if not match:
                self._fail(instruction, "memory operand must be offset(base)")
            offset = self._number(match.group(1) or "0", instruction)
            rs = self._register(match.group(2), instruction)
        return rd, rs, self._range(offset, -16, 15, instruction, "memory offset")

    def _jump_word(self, target, pc, instruction):
        delta = self._relative(target, pc)
        self._range(delta, -1024, 1023, instruction, "J displacement")
        return ((delta & 2047) << 5) | OPCODES["j"]

    def _encode(self, instruction):
        name, args, pc = instruction.mnemonic, instruction.operands, instruction.pc
        if not name:
            return []
        if name == ".word":
            return [word(self._range(self._number(arg, instruction), -32768, 65535,
                                     instruction, "raw word")) for arg in args]
        if name in ("nop", "halt", "mret", "rc"):
            self._count(instruction, 0)
            return [0 if name == "nop" else OPCODES[name]]
        if name in R_OPS:
            rd, rs = self._r_operands(instruction)
            return [(rs << 8) | (rd << 5) | OPCODES[name]]
        if name in I_SIGNED_OPS | I_UNSIGNED_OPS | SHIFT_OPS:
            rd, imm = self._i_operands(instruction)
            low, high = (-128, 127) if name in I_SIGNED_OPS else (0, 15 if name in SHIFT_OPS else 255)
            self._range(imm, low, high, instruction)
            return [((imm & 255) << 8) | (rd << 5) | OPCODES[name]]
        if name in MEM_OPS:
            rd, rs, offset = self._mem_operands(instruction)
            return [((offset & 31) << 11) | (rs << 8) | (rd << 5) | OPCODES[name]]
        if name in CSR_OPS:
            self._count(instruction, 2, 3)
            rd = self._register(args[0], instruction)
            if len(args) == 3 and self._register(args[1], instruction) != 0:
                self._fail(instruction, "CSR instruction's reserved register field must be zero")
            address = self._range(self._number(args[-1], instruction), 0, 31, instruction, "CSR address")
            return [(address << 11) | (rd << 5) | OPCODES[name]]
        if name in BRANCH_OPS:
            self._count(instruction, 3)
            rd, rs = (self._register(arg, instruction) for arg in args[:2])
            target = self._target(args[2], instruction)
            prefix = (rs << 8) | (rd << 5) | OPCODES[name]
            if instruction.size == 3:
                return [(1 << 11) | prefix,
                        (1 << 5) | OPCODES["j"],
                        self._jump_word(target, pc + 2, instruction)]
            return [((self._relative(target, pc) & 31) << 11) | prefix]
        if name in ("jal", "call"):
            rd, operand = self._jal_operands(instruction)
            target = self._target(operand, instruction)
            delta = self._relative(target, pc)
            if instruction.size == 3:
                link = word(pc + 3)
                return [(link & 0xFF00) | (rd << 5) | OPCODES["lui"],
                        ((link & 255) << 8) | (rd << 5) | OPCODES["ori"],
                        self._jump_word(target, pc + 2, instruction)]
            if rd == 0 and not -128 <= delta <= 127:
                return [self._jump_word(target, pc, instruction)]
            return [((delta & 255) << 8) | (rd << 5) | OPCODES["jal"]]
        if name in ("jr", "ret"):
            if name == "ret":
                self._count(instruction, 0)
                rd, delta = REGISTERS["ra"], 0
            else:
                self._count(instruction, 1, 2)
                rd = self._register(args[0], instruction)
                delta = self._number(args[1], instruction) if len(args) == 2 else 0
            self._range(delta, -128, 127, instruction)
            return [((delta & 255) << 8) | (rd << 5) | OPCODES["jr"]]
        if name == "j":
            self._count(instruction, 1)
            return [self._jump_word(self._target(args[0], instruction), pc, instruction)]
        if name in ("li", "lui", "la"):
            self._count(instruction, 2)
            rd = self._register(args[0], instruction)
            value = self._target(args[1], instruction) if name == "la" else self._number(args[1], instruction)
            if name == "lui":
                self._range(value, 0, 255, instruction)
            else:
                self._range(value, -32768, 65535, instruction, "constant")
            value = word(value)
            if instruction.size == 2:
                return [(value & 0xFF00) | (rd << 5) | OPCODES["lui"],
                        ((value & 255) << 8) | (rd << 5) | OPCODES["ori"]]
            return [(value << 8) | (rd << 5) | OPCODES[name]]
        if name == "mov":
            rd, rs = (self._register(arg, instruction) for arg in args)
            if rd == rs:
                return [(rd << 5) | OPCODES["add"]]
            return [(rd << 5) | OPCODES["li"],
                    (rs << 8) | (rd << 5) | OPCODES["add"]]
        self._fail(instruction, f"unknown instruction {name!r}")

    def assemble(self, instruction):
        self.clear()
        try:
            instructions = self._parse(instruction)
            self._layout(instructions)
            words = []
            for entry in instructions:
                emitted = self._encode(entry)
                if len(emitted) != entry.size:
                    self._fail(entry, "internal instruction layout mismatch")
                words.extend(emitted)
                self.source_map.extend([entry.line] * len(emitted))
            self.address = len(words)
            self.binary = "".join(f"{value:016b}\n" for value in words)
            self.basic_code = "".join(
                format_instruction(value, pc) + "\n" for pc, value in enumerate(words)
            )
            return self.binary
        except Exception:
            self.clear()
            raise
