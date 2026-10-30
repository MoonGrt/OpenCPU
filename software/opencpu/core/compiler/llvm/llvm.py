"""Process adapter for the native OpenCPU LLVM backend.

LLVM owns IR parsing, verification and code generation. This module only locates
the selected toolchain, manages its lifetime and returns its assembly output.
"""
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time

from ..simple import CompileError


LLVM_VERSION = "23.1.4"
REPOSITORY = Path(__file__).resolve().parents[5]
STARTUP_ASSEMBLY = """# OpenCPU LLVM ABI v1; all addresses below are hardware word addresses.
_start:
    li sp, 1024
    li fp, 0
    call main
    halt
"""


class LLVMCompilerError(CompileError):
    """A missing/incompatible LLVM tool or a native LLVM compilation error."""


class CompilationCancelled(CompileError):
    """The caller cancelled the current build."""


class LLVMTimeoutError(LLVMCompilerError):
    """The external compiler exceeded its configured wall-clock budget."""


def _cancelled(cancel_event):
    if cancel_event is not None and cancel_event.is_set():
        raise CompilationCancelled("Compilation cancelled")


def _stop(process):
    """Reap the compiler and any children without blocking the GUI thread."""
    if os.name != "posix" and process.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
    except ProcessLookupError:
        pass
    try:
        process.communicate(timeout=0.5)
    except subprocess.TimeoutExpired:
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
        except ProcessLookupError:
            pass
        process.communicate()


def _run(command, *, deadline, cancel_event, source_path=None, source_name=None):
    _cancelled(cancel_event)
    if time.monotonic() >= deadline:
        raise LLVMTimeoutError("LLVM compilation timed out")
    try:
        process = subprocess.Popen(
            [str(argument) for argument in command],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
            start_new_session=os.name == "posix",
        )
    except OSError as error:
        raise LLVMCompilerError(f"Unable to start LLVM compiler: {error}") from error
    try:
        while True:
            _cancelled(cancel_event)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise LLVMTimeoutError("LLVM compilation timed out")
            try:
                stdout, stderr = process.communicate(timeout=min(0.05, remaining))
                break
            except subprocess.TimeoutExpired:
                continue
        _cancelled(cancel_event)
    except BaseException:
        _stop(process)
        raise
    if process.returncode:
        diagnostic = stderr.strip() or stdout.strip() or f"exit status {process.returncode}"
        if source_path is not None and source_name:
            diagnostic = diagnostic.replace(str(source_path), str(source_name))
        raise LLVMCompilerError(f"LLVM compilation failed: {diagnostic}")
    return stdout


class LLVMCompiler:
    """Compile textual LLVM IR with the fixed native OpenCPU LLVM target."""

    def __init__(self, llvm_bin_dir=None):
        selected = llvm_bin_dir if llvm_bin_dir is not None else os.environ.get("OPENCPU_LLVM_BIN_DIR")
        self.bin_dir = Path(selected).expanduser().resolve() if selected else REPOSITORY / "build/llvm/bin"
        self.executable = self.bin_dir / ("llc.exe" if os.name == "nt" else "llc")

    def compile(self, source, *, source_name=None, cancel_event=None, timeout=60):
        if not isinstance(source, str):
            raise TypeError("LLVM source must be text")
        if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("LLVM timeout must be a positive finite number of seconds")
        _cancelled(cancel_event)
        if not self.executable.is_file():
            raise LLVMCompilerError(
                f"OpenCPU LLVM compiler not found: {self.executable}. "
                "Build it with toolchain/llvm/build.py or set --llvm-bin-dir / OPENCPU_LLVM_BIN_DIR."
            )
        deadline = time.monotonic() + timeout
        banner = _run([self.executable, "--version"], deadline=deadline, cancel_event=cancel_event)
        version = re.search(r"\bLLVM version\s+(\d+\.\d+\.\d+)(?!\d)", banner, re.IGNORECASE)
        if version is None or version.group(1) != LLVM_VERSION:
            raise LLVMCompilerError(f"OpenCPU LLVM {LLVM_VERSION} is required; selected tool: {self.executable}")
        if re.search(r"^\s*opencpu\s+-", banner, re.MULTILINE) is None:
            raise LLVMCompilerError(f"Selected LLVM has no registered OpenCPU target: {self.executable}")
        with tempfile.TemporaryDirectory(prefix="opencpu-llvm-") as temporary:
            directory = Path(temporary)
            source_path = directory / "input.ll"
            output_path = directory / "output.asm"
            source_path.write_text(source, encoding="utf-8")
            _run(
                [self.executable, "-march=opencpu", "-O0", "-filetype=asm", "-o", output_path, source_path],
                deadline=deadline, cancel_event=cancel_event,
                source_path=source_path, source_name=source_name,
            )
            _cancelled(cancel_event)
            try:
                assembly = output_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                raise LLVMCompilerError(f"LLVM did not produce a readable assembly file: {error}") from error
            if not assembly.strip():
                raise LLVMCompilerError("LLVM produced empty assembly")
            return assembly.rstrip() + "\n"
