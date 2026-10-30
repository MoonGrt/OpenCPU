"""Build services shared by the IDE, standalone downloader and command line."""
from dataclasses import dataclass, field
from pathlib import Path
import re

from .assembler import Assembler
from .compiler import Compiler
from .image import ROM_WORDS, parse_binary


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
    language: str = "simple"
    abi_version: str = "simple-v1"
    dependencies: tuple[Path, ...] = ()
    dependency_hashes: dict[str, str] = field(default_factory=dict)
    data_size_bytes: int = 0


class Toolchain:
    @staticmethod
    def _assemble(source: str, variable_offsets: dict[str, int], *, backend="simple") -> BuildResult:
        assembler = Assembler(max_words=ROM_WORDS)
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

    def _llvm_result(self, assembly, compiler):
        from .compiler.llvm import LLVMCompilerError, STARTUP_ASSEMBLY
        if re.search(r"^\s*__opencpu_init_data\s*:", assembly, re.MULTILINE) is None:
            raise LLVMCompilerError("Selected OpenCPU LLVM backend does not provide ABI v2 startup initialization")
        result = self._assemble(STARTUP_ASSEMBLY + assembly, {}, backend="llvm")
        if "main" not in result.labels:
            raise LLVMCompilerError("LLVM module must define a no-argument main function")
        result.language = compiler.language
        result.abi_version = "llvm-v2"
        result.dependencies = compiler.dependencies
        result.dependency_hashes = dict(compiler.dependency_hashes)
        metadata = re.search(r"^\s*#\s*opencpu-data-size:\s*(\d+)\s*$", assembly, re.MULTILINE)
        result.data_size_bytes = int(metadata.group(1)) if metadata else 2
        if result.data_size_bytes > 2044:
            raise LLVMCompilerError("Static data exceeds the 2048-byte RAM and minimum entry stack capacity")
        return result

    def compile(self, source: str, *, backend="simple", source_name=None,
                language="auto", include_dirs=(), defines=(),
                llvm_bin_dir=None, cancel_event=None, timeout=60) -> BuildResult:
        if backend == "llvm":
            from .compiler.llvm import LLVMCompiler
            compiler = LLVMCompiler(llvm_bin_dir)
            assembly = compiler.compile(
                source, source_name=source_name, language=language,
                include_dirs=include_dirs, defines=defines, cancel_event=cancel_event, timeout=timeout,
            )
            return self._llvm_result(assembly, compiler)
        if backend != "simple":
            raise ValueError(f"Unknown compiler backend: {backend!r}; choose simple or llvm")
        if language != "auto" or include_dirs or defines:
            raise ValueError("C/LLVM language options, header paths and definitions require the LLVM backend")
        compiler = Compiler()
        assembly = compiler.compile(source)
        return self._assemble(assembly, compiler.variable_offsets)

    def compile_project(self, project, *, buffers=None, llvm_bin_dir=None,
                        cancel_event=None, timeout=60) -> BuildResult:
        from .compiler.llvm import LLVMCompiler
        compiler = LLVMCompiler(llvm_bin_dir)
        assembly = compiler.compile_project(project, buffers=buffers, cancel_event=cancel_event, timeout=timeout)
        return self._llvm_result(assembly, compiler)
