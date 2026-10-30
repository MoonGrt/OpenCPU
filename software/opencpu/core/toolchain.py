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
    backend: str = "simple"
    isa_version: str = "v2"
    entry_pc: int = 0


class Toolchain:
    @staticmethod
    def _assemble(source: str, variable_offsets: dict[str, int], *, backend="simple") -> BuildResult:
        assembler = Assembler()
        binary = assembler.assemble(source)
        words = parse_binary(binary)
        return BuildResult(
            assembly=source, binary=binary, words=words,
            instructions=assembler.basic_code.splitlines(),
            labels=dict(assembler.labels), source_map=list(assembler.source_map),
            variable_offsets=dict(variable_offsets),
            backend=backend,
        )

    def assemble(self, source: str) -> BuildResult:
        return self._assemble(source, {})

    def compile(self, source: str, *, backend="simple", source_name=None,
                llvm_bin_dir=None, cancel_event=None, timeout=60) -> BuildResult:
        if backend == "llvm":
            from .compiler.llvm import LLVMCompiler, LLVMCompilerError, STARTUP_ASSEMBLY
            compiler = LLVMCompiler(llvm_bin_dir)
            assembly = compiler.compile(
                source, source_name=source_name, cancel_event=cancel_event, timeout=timeout,
            )
            result = self._assemble(STARTUP_ASSEMBLY + assembly, {}, backend="llvm")
            if "main" not in result.labels:
                raise LLVMCompilerError("LLVM module must define a no-argument main function")
            return result
        if backend != "simple":
            raise ValueError(f"Unknown compiler backend: {backend!r}; choose simple or llvm")
        compiler = Compiler()
        assembly = compiler.compile(source)
        return self._assemble(assembly, compiler.variable_offsets)
