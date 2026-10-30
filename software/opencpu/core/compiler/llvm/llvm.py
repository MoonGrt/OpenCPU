"""Process adapter for the native OpenCPU LLVM backend.

LLVM owns IR parsing, verification and code generation. This module only locates
the selected toolchain, manages its lifetime and returns its assembly output.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time

from ..simple import CompileError
from .project import CProject


LLVM_VERSION = "23.1.4"
REPOSITORY = Path(__file__).resolve().parents[5]
STARTUP_ASSEMBLY = """# OpenCPU LLVM ABI v2; all addresses below are hardware word addresses.
_start:
    li sp, 1024
    li fp, 0
    call __opencpu_init_data
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


def _digest(content):
    return hashlib.sha256(content).hexdigest()


def _dependencies(path):
    """Read Clang's make dependency format without shell interpretation."""
    text = re.sub(r"\\\r?\n", " ", path.read_text(encoding="utf-8"))
    separator = re.search(r":(?:\s|$)", text)
    if separator is None:
        raise LLVMCompilerError("Clang did not produce a valid dependency file")
    text = text[separator.start() + 1:]
    words, word, index = [], [], 0
    while index < len(text):
        character = text[index]
        if character == "\\" and index + 1 < len(text):
            index += 1
            word.append(text[index])
        elif character == "$" and index + 1 < len(text) and text[index + 1] == "$":
            word.append("$")
            index += 1
        elif character.isspace():
            if word:
                words.append("".join(word))
                word = []
        else:
            word.append(character)
        index += 1
    if word:
        words.append("".join(word))
    return tuple(Path(value).resolve() for value in words)


def _check_budget(deadline, cancel_event):
    _cancelled(cancel_event)
    if time.monotonic() >= deadline:
        raise LLVMTimeoutError("LLVM compilation timed out")


def _snapshot(roots, files, buffers, deadline, cancel_event):
    """Capture known input versions before launching any compiler process."""
    captured = {path: _digest(text.encode("utf-8")) for path, text in buffers.items()}
    candidates = set(files)
    ignored = {".git", ".venv", "build", "obj_dir", "thirdpartys", "__pycache__", "node_modules"}
    for root in set(roots):
        _check_budget(deadline, cancel_event)
        if not root.is_dir():
            continue
        for directory, children, names in os.walk(root):
            _check_budget(deadline, cancel_event)
            children[:] = [child for child in children if child not in ignored and not child.startswith(".")]
            for name in names:
                if Path(name).suffix.lower() in (".c", ".h", ".inc", ".def"):
                    candidates.add(Path(directory) / name)
    for path in candidates:
        _check_budget(deadline, cancel_event)
        path = path.resolve()
        if path in captured:
            continue
        try:
            captured[path] = _digest(path.read_bytes())
        except OSError:
            # An unrelated unreadable file need not prevent compiling a project.
            # Actual dependencies are required and checked after preprocessing.
            pass
    return captured


class LLVMCompiler:
    """Manage the real Clang / llvm-link / OpenCPU llc toolchain."""

    def __init__(self, llvm_bin_dir=None):
        selected = llvm_bin_dir if llvm_bin_dir is not None else os.environ.get("OPENCPU_LLVM_BIN_DIR")
        self.bin_dir = Path(selected).expanduser().resolve() if selected else REPOSITORY / "build/llvm/bin"
        self.executable = self.bin_dir / ("llc.exe" if os.name == "nt" else "llc")
        self.sdk_dir = self.bin_dir.parent / "lib/opencpu"
        self.runtime = self.sdk_dir / "runtime.bc"
        self.language = "llvm-ir"
        self.dependencies = ()
        self.dependency_hashes = {}

    @staticmethod
    def _deadline(timeout, cancel_event):
        if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("LLVM timeout must be a positive finite number of seconds")
        _cancelled(cancel_event)
        return time.monotonic() + timeout

    def _tool(self, name, deadline, cancel_event):
        executable = self.bin_dir / (name + (".exe" if os.name == "nt" else ""))
        if not executable.is_file():
            raise LLVMCompilerError(
                f"OpenCPU LLVM tool not found: {executable}. "
                "Build it with toolchain/llvm/build.py or set --llvm-bin-dir / OPENCPU_LLVM_BIN_DIR."
            )
        banner = _run([executable, "--version"], deadline=deadline, cancel_event=cancel_event)
        version = re.search(r"\b(?:LLVM|clang) version\s+(\d+\.\d+\.\d+)(?!\d)", banner, re.IGNORECASE)
        if version is None or version.group(1) != LLVM_VERSION:
            raise LLVMCompilerError(f"OpenCPU LLVM {LLVM_VERSION} is required; selected tool: {executable}")
        if name == "llc" and re.search(r"^\s*opencpu\s+-", banner, re.MULTILINE) is None:
            raise LLVMCompilerError(f"Selected LLVM has no registered OpenCPU target: {executable}")
        return executable

    def _assembly(self, source_path, output_path, llc, deadline, cancel_event, source_name=None):
        command = [llc, "-march=opencpu", "-O0", "-filetype=asm"]
        if self.runtime.is_file():
            command.append(f"-opencpu-runtime={self.runtime}")
        command += ["-o", output_path, source_path]
        _run(command, deadline=deadline, cancel_event=cancel_event,
             source_path=source_path, source_name=source_name)
        _cancelled(cancel_event)
        try:
            assembly = output_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise LLVMCompilerError(f"LLVM did not produce a readable assembly file: {error}") from error
        if not assembly.strip():
            raise LLVMCompilerError("LLVM produced empty assembly")
        return assembly.rstrip() + "\n"

    def compile(self, source, *, source_name=None, language="auto", include_dirs=(), defines=(),
                cancel_event=None, timeout=60):
        if not isinstance(source, str):
            raise TypeError("LLVM source must be text")
        if language not in ("auto", "c", "llvm-ir"):
            raise ValueError("LLVM language must be auto, c, or llvm-ir")
        if language == "auto":
            language = "c" if source_name and Path(source_name).suffix.lower() == ".c" else "llvm-ir"
        if language == "c":
            source_path = Path(source_name or "untitled.c").expanduser().resolve()
            # Explicit C mode also accepts non-.c editor filenames.
            if source_path.suffix.lower() != ".c":
                return self._compile_c_text(source, source_path, include_dirs, defines, cancel_event, timeout)
            project = CProject(sources=(source_path,), include_dirs=tuple(include_dirs), defines=tuple(defines))
            return self.compile_project(project, buffers={source_path: source},
                                        cancel_event=cancel_event, timeout=timeout)
        if include_dirs or defines:
            raise ValueError("Header paths and definitions apply only to C input")
        deadline = self._deadline(timeout, cancel_event)
        self.language = language
        self.dependencies = ()
        self.dependency_hashes = {}
        llc = self._tool("llc", deadline, cancel_event)
        with tempfile.TemporaryDirectory(prefix="opencpu-llvm-") as temporary:
            directory = Path(temporary)
            source_path = directory / "input.ll"
            output_path = directory / "output.asm"
            source_path.write_text(source, encoding="utf-8")
            return self._assembly(source_path, output_path, llc, deadline, cancel_event, source_name)

    def _compile_c_text(self, source, source_path, include_dirs, defines, cancel_event, timeout):
        # CProject deliberately validates manifest source suffixes; a standalone
        # editor document can still explicitly select C for .txt or untitled input.
        project = CProject(sources=(source_path.with_suffix(".c"),),
                           include_dirs=tuple(include_dirs), defines=tuple(defines))
        return self._compile_project(project, {source_path: source}, cancel_event, timeout,
                                     sources=(source_path,))

    def compile_project(self, project, *, buffers=None, cancel_event=None, timeout=60):
        if not isinstance(project, CProject):
            project = CProject.load(project)
        return self._compile_project(project, buffers or {}, cancel_event, timeout)

    def _compile_project(self, project, buffers, cancel_event, timeout, *, sources=None):
        deadline = self._deadline(timeout, cancel_event)
        self.language = "c"
        self.dependencies = ()
        self.dependency_hashes = {}
        normalized = {}
        for path, text in buffers.items():
            if not isinstance(text, str):
                raise TypeError("C source buffers must contain text")
            candidate = Path(path).expanduser()
            if not candidate.is_absolute() and project.path is not None:
                candidate = project.path.parent / candidate
            normalized[candidate.resolve()] = text
        sources = sources or project.sources
        llc = self._tool("llc", deadline, cancel_event)
        clang = self._tool("clang", deadline, cancel_event)
        llvm_link = self._tool("llvm-link", deadline, cancel_event)
        if not self.runtime.is_file() or not (self.sdk_dir / "include").is_dir():
            raise LLVMCompilerError(
                f"OpenCPU C SDK is missing: {self.sdk_dir}; rebuild with toolchain/llvm/build.py"
            )
        resource = Path(_run([clang, "-print-resource-dir"], deadline=deadline,
                             cancel_event=cancel_event).strip())
        files = tuple(sources) + (self.runtime,) + ((project.path,) if project.path else ())
        roots = tuple(source.parent for source in sources) + project.include_dirs + (
            self.sdk_dir / "include", resource / "include",
        )
        initial = _snapshot(roots, files, normalized, deadline, cancel_event)
        if project.path and project._manifest_hash and initial.get(project.path) != project._manifest_hash:
            raise LLVMCompilerError(f"C project changed after loading; reload: {project.path}")
        started_ns = time.time_ns()
        dependencies = set(sources)
        dependencies.add(self.runtime)
        if project.path:
            dependencies.add(project.path)
        with tempfile.TemporaryDirectory(prefix="opencpu-c-") as temporary:
            directory = Path(temporary)
            overlay_roots = []
            for index, (path, text) in enumerate(normalized.items()):
                external = directory / f"buffer-{index}.txt"
                external.write_text(text, encoding="utf-8")
                overlay_roots.append({"type": "file", "name": str(path), "external-contents": str(external)})
            overlay = directory / "overlay.json"
            overlay.write_text(json.dumps({"version": 0, "use-external-names": False,
                                            "roots": overlay_roots}), encoding="utf-8")
            modules = []
            for index, source_path in enumerate(sources):
                _cancelled(cancel_event)
                module = directory / f"source-{index}.bc"
                depfile = directory / f"source-{index}.d"
                compiler_input = source_path
                if not source_path.is_file() and source_path in normalized:
                    # The Clang driver checks physical input existence before
                    # cc1 loads -ivfsoverlay. Never create editor files merely
                    # to satisfy that check; keep the snapshot in our temp dir.
                    compiler_input = directory / f"source-{index}.c"
                    line = f"#line 1 {json.dumps(str(source_path), ensure_ascii=False)}\n"
                    compiler_input.write_text(line + normalized[source_path].removeprefix("\ufeff"), encoding="utf-8")
                command = [
                    clang, "--target=opencpu-unknown-none", "-std=c17", "-ffreestanding", "-nostdlibinc",
                    "-O0", "-Xclang", "-disable-O0-optnone", "-fno-jump-tables", "-Werror=return-type",
                    "-fno-pic", "-fno-pie", "-fno-stack-protector",
                    "-x", "c", "-emit-llvm", "-c", "-ivfsoverlay", overlay,
                    "-iquote", source_path.parent, "-isystem", self.sdk_dir / "include",
                    "-MD", "-MF", depfile,
                ]
                for include in project.include_dirs:
                    command.extend(("-I", include))
                for define in project.defines:
                    command.extend(("-D", define))
                command.extend((compiler_input, "-o", module))
                _run(command, deadline=deadline, cancel_event=cancel_event)
                if not depfile.is_file():
                    raise LLVMCompilerError("Clang did not produce the requested dependency file")
                if not module.is_file() or module.stat().st_size == 0:
                    raise LLVMCompilerError("Clang did not produce a bitcode module")
                dependencies.update(path for path in _dependencies(depfile)
                                    if compiler_input == source_path or path != compiler_input)
                modules.append(module)
            linked = directory / "program.bc"
            _run([llvm_link, *modules, "-o", linked], deadline=deadline, cancel_event=cancel_event)
            if not linked.is_file() or linked.stat().st_size == 0:
                raise LLVMCompilerError("llvm-link did not produce a linked bitcode module")
            assembly = self._assembly(linked, directory / "output.asm", llc, deadline, cancel_event)
            hashes = {}
            for path in sorted(dependencies):
                _check_budget(deadline, cancel_event)
                if path in normalized:
                    hashes[str(path)] = initial[path]
                    continue
                try:
                    current = _digest(path.read_bytes())
                    changed = (path in initial and initial[path] != current) or (
                        path not in initial and path.stat().st_mtime_ns >= started_ns)
                except OSError as error:
                    raise LLVMCompilerError(f"C dependency disappeared during compilation: {path}") from error
                if changed:
                    raise LLVMCompilerError(f"C dependency changed during compilation; rebuild: {path}")
                hashes[str(path)] = initial.get(path, current)
            self.dependencies = tuple(sorted(dependencies))
            self.dependency_hashes = hashes
            _check_budget(deadline, cancel_event)
            return assembly
