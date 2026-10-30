"""Lossless word-for-word disassembly for OpenCPU ISA v2."""
from .image import parse_binary
from .isa import format_instruction


class Disassembler:
    def disassemble(self, binary: str) -> str:
        # The library also handles ROMs larger than the default board image.
        words = parse_binary(binary, max_words=None)
        return "\n".join(format_instruction(value, pc) for pc, value in enumerate(words))
