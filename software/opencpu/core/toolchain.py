"""Build services shared by the IDE, standalone downloader and command line."""
from dataclasses import dataclass, field

from .assembler import Assembler
from .compiler import Compiler
from .image import parse_binary


@dataclass(slots=True)
class BuildResult:
    assembly: str
    binary: str
    words: list[int]
    instructions: list[str]
    labels: dict[str, int]
    source_map: list[int]
    variable_offsets: dict[str, int] = field(default_factory=dict)


class Toolchain:
    @staticmethod
    def _assemble(source: str, variable_offsets: dict[str, int]) -> BuildResult:
        assembler = Assembler()
        binary = assembler.assemble(source)
        words = parse_binary(binary)
        return BuildResult(
            assembly=source, binary=binary, words=words,
            instructions=assembler.basic_code.splitlines(),
            labels=dict(assembler.labels), source_map=list(assembler.source_map),
            variable_offsets=dict(variable_offsets),
        )

    def assemble(self, source: str) -> BuildResult:
        return self._assemble(source, {})

    def compile(self, source: str) -> BuildResult:
        compiler = Compiler()
        assembly = compiler.compile(source)
        return self._assemble(assembly, compiler.variable_offsets)
