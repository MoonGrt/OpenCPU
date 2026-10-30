"""Independent native expected results shared by software and UART acceptance."""
from dataclasses import dataclass
from pathlib import Path
import sys

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / "software"))

from opencpu.core.compiler.llvm import CProject  # noqa: E402
from opencpu.core.toolchain import Toolchain  # noqa: E402

EXAMPLES = REPOSITORY / "software/examples"
EXPECTED_RETURNS = {
    "constant": 43981, "arithmetic": 836, "comparisons": 3099,
    "booleans": 23, "bool_branch": 13, "bool_phi": 17, "phi_loop": 45,
    "select": 65521, "minmax_abs": 126, "calls": 133, "factorial": 120,
    "call_live_values": 117, "stack_array": 666, "memory_word_ops": 52651,
    "far_branch": 32771, "shift_boundaries": 32769,
}
C_EXPECTED_RETURNS = {
    "constant": 43981, "integers": 65502, "control": 125,
    "pointers": 65005, "globals": 289, "strings": 527, "calls": 4670,
    "factorial": 120, "narrow": 50, "wide32": 47119, "wide64": 57344,
    "mmio": 4665, "large_frame": 3432, "multifile": 33,
}
SIMPLE_BINARY_SHA256 = {
    # Captured from the pre-C toolchain in commit d3df811.
    "isa.asm": "1dfea68cf23c81589ce8c45edc7378f5770ef3d2cd6d210f49c12e45dc753209",
    "loops.oc": "cfb164ea18d301d53d639fbd428cfbd3e88af383655b6a3f0564665b25549f8e",
    "functions.oc": "977873422980b363f0be885f601255d6cfcb7ea607c329d2f2b86370e62f8ab1",
}


def build_fixture(name):
    path = EXAMPLES / "llvm" / (name + ".ll")
    return Toolchain().compile(path.read_text(), backend="llvm", source_name=str(path))


def build_c_fixture(name):
    if name == "multifile":
        project = CProject.load(EXAMPLES / "c/multifile/demo.opencpu.json")
        return Toolchain().compile_project(project)
    path = EXAMPLES / "c" / (name + ".c")
    return Toolchain().compile(path.read_text(), backend="llvm", source_name=str(path))


def _fold(value, bits):
    value &= (1 << bits) - 1
    result = value & 65535
    for shift in range(16, bits, 16):
        result = ((result * 33) ^ ((value >> shift) & 65535)) & 65535
    return result


@dataclass(frozen=True)
class IntegerCase:
    name: str
    source: str
    expected: int


def _integer_source(ctype, unsigned, bits, a, b, suffix, expression):
    def literal(value):
        # Keep MIN signed instead of spelling a positive literal that does not
        # fit long long before unary minus is applied.
        if value == -(1 << (bits - 1)):
            return f"(-{(1 << (bits - 1)) - 1}{suffix} - 1{suffix})"
        return f"{value}{suffix}"

    folded = "".join(f"checksum = (checksum * 33u) ^ (unsigned int)(word >> {shift}); "
                      for shift in range(16, bits, 16))
    return (
        f"volatile {ctype} left = {literal(a)};\n"
        f"volatile {ctype} right = {literal(b)};\n"
        f"int main(void) {{ {ctype} value = ({ctype})({expression}); "
        f"{unsigned} word = ({unsigned})value; unsigned int checksum = (unsigned int)word; "
        f"{folded}return (int)checksum; }}\n"
    )


def integer_cases():
    """Use volatile operands so Clang must execute every operation on target.

    Signed arithmetic stays representable; signed shifts use the documented
    arithmetic-right-shift policy. Division never uses zero or MIN / -1.
    Python computes the expected result without invoking another C compiler.
    """
    types = (
        ("u8", "unsigned char", "unsigned char", 8, False, ""),
        ("s8", "signed char", "unsigned char", 8, True, ""),
        ("u16", "unsigned int", "unsigned int", 16, False, "u"),
        ("s16", "int", "unsigned int", 16, True, ""),
        ("u32", "unsigned long", "unsigned long", 32, False, "UL"),
        ("s32", "long", "unsigned long", 32, True, "L"),
        ("u64", "unsigned long long", "unsigned long long", 64, False, "ULL"),
        ("s64", "long long", "unsigned long long", 64, True, "LL"),
    )
    signed_inputs = {8: -11, 16: -1234, 32: -1234567, 64: -0x123456789AB}
    for label, ctype, unsigned, bits, signed, suffix in types:
        for operation in ("add", "sub", "mul", "div", "rem", "and", "or", "xor", "shl", "shr", "cmp"):
            a = signed_inputs[bits] if signed else (1 << bits) - 17
            b = 7 if bits == 8 else 17
            if operation in ("shl", "shr"):
                b = 3
                if signed and operation == "shl":
                    a = 11
            symbols = {"add": "+", "sub": "-", "mul": "*", "div": "/", "rem": "%",
                       "and": "&", "or": "|", "xor": "^", "shl": "<<", "shr": ">>"}
            if operation == "cmp":
                expression = "(left < right) | ((left <= right) << 1) | ((left == right) << 2) | ((left != right) << 3) | ((left > right) << 4) | ((left >= right) << 5)"
                value = ((a < b) | ((a <= b) << 1) | ((a == b) << 2)
                         | ((a != b) << 3) | ((a > b) << 4) | ((a >= b) << 5))
            else:
                expression = f"left {symbols[operation]} right"
                quotient = (abs(a) // abs(b)) * (-1 if (a < 0) != (b < 0) else 1)
                operations = {
                    "add": lambda: a + b, "sub": lambda: a - b, "mul": lambda: a * b,
                    "div": lambda: quotient, "rem": lambda: a - quotient * b,
                    "and": lambda: a & b, "or": lambda: a | b, "xor": lambda: a ^ b,
                    "shl": lambda: a << b, "shr": lambda: a >> b,
                }
                value = operations[operation]()
            source = _integer_source(ctype, unsigned, bits, a, b, suffix, expression)
            yield IntegerCase(f"{label}-{operation}", source, _fold(value, bits))
        if signed and bits >= 16:
            edges = (
                ("negative-divisor", -signed_inputs[bits], -17),
                ("both-negative", signed_inputs[bits], -17),
                ("minimum", -(1 << (bits - 1)), -2),
                ("maximum", (1 << (bits - 1)) - 1, -17),
            )
            for edge, a, b in edges:
                quotient = (abs(a) // abs(b)) * (-1 if (a < 0) != (b < 0) else 1)
                for operation, expression, value in (
                    ("div", "left / right", quotient),
                    ("rem", "left % right", a - quotient * b),
                ):
                    source = _integer_source(ctype, unsigned, bits, a, b, suffix, expression)
                    yield IntegerCase(f"{label}-{operation}-{edge}", source, _fold(value, bits))
        if bits >= 16:
            for count in (0, 15, 16, 17, 31, 32, 33, 47, 48, 63):
                if count >= bits:
                    continue
                a = signed_inputs[bits] if signed else (1 << bits) - 17
                source = _integer_source(ctype, unsigned, bits, a, count, suffix, "left >> right")
                yield IntegerCase(f"{label}-shr-boundary-{count}", source, _fold(a >> count, bits))
                if not signed:
                    source = _integer_source(ctype, unsigned, bits, a, count, suffix, "left << right")
                    yield IntegerCase(f"{label}-shl-boundary-{count}", source, _fold(a << count, bits))
        a = signed_inputs[bits] if signed else (1 << bits) - 17
        for destination_bits, destination_type in ((8, "unsigned char"), (16, "unsigned int"),
                                                   (32, "unsigned long"), (64, "unsigned long long")):
            folded = "".join(f"checksum = (checksum * 33u) ^ (unsigned int)(word >> {shift}); "
                             for shift in range(16, destination_bits, 16))
            source = (
                f"volatile {ctype} input = {a}{suffix};\n"
                f"int main(void) {{ {destination_type} word = ({destination_type})input; "
                f"unsigned int checksum = (unsigned int)word; {folded}return (int)checksum; }}\n"
            )
            yield IntegerCase(f"{label}-cast-u{destination_bits}", source, _fold(a, destination_bits))


def abi_cases():
    source = """
    #include <stdint.h>
    volatile uint64_t input = 0x123456789ABCDEF0ULL;
    static uint64_t join(unsigned leading, uint64_t value, unsigned trailing) {
        return value + leading + trailing;
    }
    static unsigned clobber(unsigned value) { return value * 7u + 3u; }
    int main(void) {
        uint64_t saved = input;
        uint64_t result = join(5, saved, 9);
        unsigned side = clobber(11);
        uint64_t word = result + saved;
        unsigned checksum = (unsigned)word;
        checksum = checksum * 33u ^ (unsigned)(word >> 16);
        checksum = checksum * 33u ^ (unsigned)(word >> 32);
        checksum = checksum * 33u ^ (unsigned)(word >> 48);
        return (int)(checksum ^ side);
    }
    """
    value = 0x123456789ABCDEF0
    yield IntegerCase("split64-and-live-across-calls", source, _fold(value * 2 + 14, 64) ^ 80)


REJECTED_C = {
    "structure": "struct S {int x;}; volatile struct S value; int main(void){return value.x;}",
    "union": "union U {int x;long y;}; volatile union U value; int main(void){return value.x;}",
    "bit field": "struct S {unsigned x:3;}; volatile struct S value; int main(void){return (int)value.x;}",
    "floating point": "volatile float value=1.5f; int main(void){return (int)(value+2.5f);}",
    "VLA": "volatile int length=3; int main(void){int values[length];values[0]=7;return values[0];}",
    "varargs": "int first(int value,...){return value;} int main(void){return first(7,8);}",
    "function pointers": "int helper(void){return 7;} int (*volatile function)(void)=helper; int main(void){return function();}",
    "structure values": "struct Pair{int a,b;}; struct Pair make(int x){struct Pair p={x,2};return p;} int main(void){struct Pair p=make(7);return p.a+p.b;}",
    "union objects": "union Value{unsigned word;unsigned char bytes[2];}; volatile union Value value; int main(void){value.word=0x1234u;return value.bytes[0];}",
    "atomics": "_Atomic unsigned value; int main(void){return (int)__c11_atomic_fetch_add(&value,1,5);}",
    "inline assembly": 'int main(void){__asm__ volatile("nop");return 0;}',
    "thread local": "_Thread_local int value; int main(void){return value;}",
    "unresolved function": "extern int missing(int value); int main(void){return missing(7);}",
    "unresolved global": "extern int missing; int main(void){return missing;}",
    "main arguments": "int main(int argc,char **argv){return argc+(argv!=0);}",
    "missing return": "int main(void){int value=3;}",
}

STACK_EXHAUSTION_C = """
volatile unsigned sentinel = 0x5AA5u;
__attribute__((noinline)) int descend(int value) {
    volatile unsigned payload[64];
    payload[0] = (unsigned)value;
    return descend(value + 1) + (int)payload[0];
}
int main(void) { if(sentinel != 0x5AA5u) return 1; return descend(0); }
"""
