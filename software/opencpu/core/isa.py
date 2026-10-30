"""Shared definitions for OpenCPU ISA v2 (16-bit word-addressed machine)."""

OPCODES = {
    "add": 0, "sub": 1, "mul": 2, "and": 3,
    "or": 4, "xor": 5, "sll": 6, "srl": 7,
    "beq": 8, "blt": 9, "halt": 10, "mret": 11,
    "lui": 12, "j": 13,
    "addi": 16, "subi": 17, "muli": 18, "andi": 19,
    "ori": 20, "xori": 21, "slli": 22, "srli": 23,
    "lw": 24, "sw": 25, "csrr": 26, "csrw": 27,
    "jal": 28, "jr": 29, "li": 30, "rc": 31,
}
R_OPS = frozenset(("add", "sub", "mul", "and", "or", "xor", "sll", "srl"))
I_SIGNED_OPS = frozenset(("addi", "subi", "muli"))
I_UNSIGNED_OPS = frozenset(("andi", "ori", "xori"))
SHIFT_OPS = frozenset(("slli", "srli"))
BRANCH_OPS = frozenset(("beq", "blt"))
MEM_OPS = frozenset(("lw", "sw"))
CSR_OPS = frozenset(("csrr", "csrw"))
REGISTER_NAMES = ("zero", "a1", "a2", "a3", "a4", "fp", "ra", "sp")
REGISTERS = {f"r{index}": index for index in range(8)}
REGISTERS.update({f"a{index}": index for index in range(1, 6)})
REGISTERS.update({"zero": 0, "zr": 0, "s0": 0, "fp": 5, "ra": 6, "sp": 7})


def sign_extend(value, bits):
    """Interpret the low *bits* of value as a two's-complement integer."""
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def word(value):
    """Return the 16-bit machine representation of an integer."""
    return value & 0xFFFF


def format_instruction(value, pc=0):
    """Format one word without losing reserved encodings or instruction slots."""
    value = word(value)
    opcode = value & 31
    mnemonic = next((name for name, code in OPCODES.items() if code == opcode), None)
    rd = REGISTER_NAMES[(value >> 5) & 7]
    rs = REGISTER_NAMES[(value >> 8) & 7]
    imm8 = value >> 8
    imm5 = value >> 11
    raw = f".word 0x{value:04x}"
    if value == 0:
        return "nop"
    if mnemonic in R_OPS:
        return raw if imm5 else f"{mnemonic} {rd}, {rs}"
    if mnemonic in I_SIGNED_OPS:
        return f"{mnemonic} {rd}, {sign_extend(imm8, 8)}"
    if mnemonic in I_UNSIGNED_OPS:
        return f"{mnemonic} {rd}, {imm8}"
    if mnemonic in SHIFT_OPS:
        return raw if imm8 > 15 else f"{mnemonic} {rd}, {imm8}"
    if mnemonic in MEM_OPS:
        return f"{mnemonic} {rd}, {sign_extend(imm5, 5)}({rs})"
    if mnemonic in CSR_OPS:
        return raw if (value >> 8) & 7 else f"{mnemonic} {rd}, {imm5}"
    if mnemonic in BRANCH_OPS:
        target = word(pc + 1 + sign_extend(imm5, 5))
        return f"{mnemonic} {rd}, {rs}, {target}"
    if mnemonic == "jal":
        return f"jal {rd}, {word(pc + 1 + sign_extend(imm8, 8))}"
    if mnemonic == "jr":
        return f"jr {rd}, {sign_extend(imm8, 8)}"
    if mnemonic == "j":
        return f"j {word(pc + 1 + sign_extend(value >> 5, 11))}"
    if mnemonic in ("li", "lui"):
        return f"{mnemonic} {rd}, {imm8}"
    if mnemonic in ("halt", "mret", "rc"):
        return raw if value >> 5 else mnemonic
    return raw
