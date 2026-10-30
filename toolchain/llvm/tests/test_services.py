"""Compiler process and project tests; native acceptance uses the real tools.

The controlled executables exercise transport, arguments and failures only.
They neither parse C nor replace the native Clang / RTL acceptance tests.
"""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / "software"))

from opencpu.cli import main  # noqa: E402
from opencpu.core.assembler import Assembler  # noqa: E402
from opencpu.core.compiler import Compiler  # noqa: E402
from opencpu.core.compiler.llvm import (  # noqa: E402
    CProject, CompilationCancelled, LLVMCompiler, LLVMCompilerError, LLVMTimeoutError,
)
from opencpu.core.compiler.simple import Compiler as SimpleCompiler  # noqa: E402
from opencpu.core.simulator import Simulator  # noqa: E402
from opencpu.core.toolchain import BuildResult, Toolchain  # noqa: E402

ASSEMBLY = "# opencpu-data-size: 2\nmain:\n    li a1, 42\n    ret\n__opencpu_init_data:\n    ret\n"


class CompilerServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="opencpu C service ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bin = self.root / "tools/bin"
        self.bin.mkdir(parents=True)
        self.sdk = self.root / "tools/lib/opencpu"
        (self.sdk / "include").mkdir(parents=True)
        (self.sdk / "runtime.bc").write_bytes(b"controlled SDK transport fixture")
        self.resource = self.root / "tools/lib/clang/23"
        (self.resource / "include").mkdir(parents=True)
        self.config = self.root / "config.json"
        self.log = self.root / "commands.jsonl"
        self.source = self.root / "main.c"
        self.source.write_text("int main(void) { return 42; }\n")
        self.header = self.root / "header with space.h"
        self.header.write_text("#define ANSWER 42\n")
        script = f'''#!{sys.executable}
import json,pathlib,sys,time
config=json.loads(pathlib.Path({str(self.config)!r}).read_text())
name=pathlib.Path(sys.argv[0]).name
args=sys.argv[1:]
with pathlib.Path({str(self.log)!r}).open('a') as log:
    log.write(json.dumps([name,args])+'\\n')
if '--version' in args:
    time.sleep(config.get('version_delay',0))
    print(('clang' if name=='clang' else 'LLVM')+' version '+config.get('version','23.1.4'))
    if name=='llc' and config.get('target',True):
        print('  Registered Targets:\\n    opencpu - OpenCPU ISA v2')
    raise SystemExit(0)
if '-print-resource-dir' in args:
    print({str(self.resource)!r})
    raise SystemExit(0)
behavior=config.get(name,'success')
if behavior=='sleep':
    time.sleep(30)
if behavior=='failure':
    print('original.c:4: error: controlled compiler failure',file=sys.stderr)
    raise SystemExit(2)
if behavior=='missing':
    raise SystemExit(0)
if name=='clang':
    overlay=json.loads(pathlib.Path(args[args.index('-ivfsoverlay')+1]).read_text())
    overlays={{item['name']:item['external-contents'] for item in overlay['roots']}}
    for path,expected in config.get('expect_buffers',{{}}).items():
        if pathlib.Path(overlays.get(path,path)).read_text()!=expected:
            print('overlay did not contain expected snapshot',file=sys.stderr)
            raise SystemExit(5)
    dependencies=config.get('dependencies',[{str(self.source)!r}])
    def escape(path):
        return path.replace('\\\\','\\\\\\\\').replace(' ','\\\\ ').replace('#','\\\\#').replace('$','$$')
    pathlib.Path(args[args.index('-MF')+1]).write_text('output.bc: '+' '.join(escape(p) for p in dependencies)+'\\n')
    pathlib.Path(args[args.index('-o')+1]).write_text('controlled bitcode transport')
elif name=='llvm-link':
    pathlib.Path(args[args.index('-o')+1]).write_text('controlled linked bitcode transport')
else:
    if config.get('mutate'):
        pathlib.Path(config['mutate']).write_text('changed during compilation')
    pathlib.Path(args[args.index('-o')+1]).write_text(config.get('assembly',{ASSEMBLY!r}))
'''
        for name in ("llc", "clang", "llvm-link"):
            path = self.bin / name
            path.write_text(script)
            path.chmod(0o755)
        self.configure()

    def configure(self, **values):
        self.config.write_text(json.dumps(values))

    def project(self, **values):
        return CProject(sources=(self.source,), **values)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_simple_remains_the_independent_default(self):
        self.assertIs(Compiler, SimpleCompiler)
        with mock.patch("subprocess.Popen", side_effect=AssertionError("simple must not invoke LLVM")):
            first = Toolchain().compile("answer = 6 * 7;")
            second = Toolchain().compile("answer = 6 * 7;", backend="simple")
        self.assertEqual(first, second)
        self.assertEqual(first.language, "simple")
        simulator = Simulator(first.entry_pc)
        simulator.inst_mem = first.words
        simulator.run()
        self.assertTrue(simulator.halted)
        self.assertEqual(simulator.data_mem[1021], 42)

    def test_build_result_old_constructor_has_compatible_defaults(self):
        build = BuildResult("halt", "0000000000001010", [10], ["halt"], {}, [1])
        self.assertEqual(build.dependencies, ())
        self.assertEqual(build.dependency_hashes, {})
        self.assertEqual(build.backend, "simple")

    def test_rom_limit_is_reported_before_out_of_range_jump_encoding(self):
        # The unrelaxed program fits exactly; expanding its far branch needs
        # two additional words and would otherwise fail during J encoding.
        source = "beq a1, zero, done\n" + "nop\n" * 1022 + "done: halt\n"
        with self.assertRaisesRegex(ValueError, "1024-word ROM.*1026 words required"):
            Toolchain().assemble(source)
        exact = Toolchain().assemble("nop\n" * 1023 + "halt\n")
        self.assertEqual(len(exact.words), 1024)
        self.assertEqual(len(Assembler().assemble("nop\n" * 1025).splitlines()), 1025)

    def test_manifest_resolves_relative_paths_in_order(self):
        manifest = self.root / ".opencpu.json"
        manifest.write_text(json.dumps({"version": 1, "sources": ["main.c", "second.c"],
                                       "include_dirs": ["headers"], "defines": ["COUNT=3", "FEATURE"]}))
        project = CProject.load(manifest)
        self.assertEqual(project.sources, (self.source, self.root / "second.c"))
        self.assertEqual(project.include_dirs, (self.root / "headers",))
        self.assertEqual(project.defines, ("COUNT=3", "FEATURE"))
        self.assertEqual(project.path, manifest)

    def test_invalid_manifests_have_actionable_errors(self):
        invalid = [[], {}, {"version": 2, "sources": ["main.c"]},
                   {"version": True, "sources": ["main.c"]},
                   {"version": 1, "sources": []}, {"version": 1, "sources": ["x.ll"]},
                   {"version": 1, "sources": ["main.c", "main.c"]},
                   {"version": 1, "sources": ["main.c"], "defines": "COUNT=1"},
                   {"version": 1, "sources": ["main.c"], "unsupported": True}]
        path = self.root / ".opencpu.json"
        for value in invalid:
            with self.subTest(value=value):
                path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    CProject.load(path)

    def test_c_pipeline_arguments_and_sdk_location(self):
        build = Toolchain().compile(self.source.read_text(), backend="llvm", source_name=str(self.source),
                                    llvm_bin_dir=self.bin, include_dirs=(self.root,), defines=("COUNT=3",))
        self.assertEqual(build.language, "c")
        self.assertEqual(build.abi_version, "llvm-v2")
        self.assertEqual(build.data_size_bytes, 2)
        self.assertEqual(build.entry_pc, 0)
        self.assertEqual(build.labels["_start"], 0)
        self.assertGreater(build.labels["main"], 0)
        self.assertEqual(build.variable_offsets, {})
        self.assertEqual(len(build.source_map), len(build.words))
        calls = self.calls()
        clang = next(arguments for name, arguments in calls if name == "clang" and "-emit-llvm" in arguments)
        for argument in ("--target=opencpu-unknown-none", "-ffreestanding", "-nostdlibinc", "-disable-O0-optnone", "COUNT=3"):
            self.assertIn(argument, clang)
        llc = next(arguments for name, arguments in calls if name == "llc" and "-march=opencpu" in arguments)
        self.assertIn(f"-opencpu-runtime={self.sdk / 'runtime.bc'}", llc)

    def test_unsaved_source_and_header_buffers_are_snapshotted(self):
        source = '#include "header with space.h"\nint main(void) { return ANSWER; }\n'
        header = "#define ANSWER 43\n"
        self.configure(expect_buffers={str(self.source): source, str(self.header): header},
                       dependencies=[str(self.source), str(self.header)])
        build = Toolchain().compile_project(self.project(), buffers={self.source: source, self.header: header},
                                            llvm_bin_dir=self.bin)
        self.assertEqual(build.dependency_hashes[str(self.header)], hashlib.sha256(header.encode()).hexdigest())
        self.assertEqual(self.header.read_text(), "#define ANSWER 42\n")
        self.assertIn(self.header, build.dependencies)

    def test_disk_dependency_change_rejects_stale_output(self):
        self.configure(dependencies=[str(self.source), str(self.header)], mutate=str(self.header))
        with self.assertRaisesRegex(LLVMCompilerError, "changed during compilation"):
            Toolchain().compile_project(self.project(), llvm_bin_dir=self.bin)

    def test_manifest_change_after_load_requires_reload(self):
        manifest = self.root / "demo.opencpu.json"
        manifest.write_text(json.dumps({"version": 1, "sources": ["main.c"]}))
        project = CProject.load(manifest)
        manifest.write_text(json.dumps({"version": 1, "sources": ["main.c"], "defines": ["NEW_VALUE=7"]}))
        with self.assertRaisesRegex(LLVMCompilerError, "changed after loading"):
            Toolchain().compile_project(project, llvm_bin_dir=self.bin)

    def test_relative_project_buffers_use_the_manifest_directory(self):
        manifest = self.root / "demo.opencpu.json"
        manifest.write_text(json.dumps({"version": 1, "sources": ["main.c"]}))
        text = "int main(void){return 43;}"
        self.configure(expect_buffers={str(self.source): text})
        build = Toolchain().compile_project(CProject.load(manifest), buffers={Path("main.c"): text},
                                            llvm_bin_dir=self.bin)
        self.assertEqual(build.dependency_hashes[str(self.source)], hashlib.sha256(text.encode()).hexdigest())

    def test_explicit_c_mode_accepts_non_c_document_name(self):
        path = self.root / "draft.txt"
        self.configure(dependencies=[str(path)], expect_buffers={str(path): "int main(void){return 42;}"})
        build = Toolchain().compile("int main(void){return 42;}", backend="llvm", language="c",
                                    source_name=str(path), llvm_bin_dir=self.bin)
        self.assertEqual(build.language, "c")

    def test_llvm_ir_never_requires_clang(self):
        (self.bin / "clang").unlink()
        (self.bin / "llvm-link").unlink()
        (self.sdk / "runtime.bc").unlink()
        build = Toolchain().compile("define i16 @main(){ret i16 42}", backend="llvm", llvm_bin_dir=self.bin)
        self.assertEqual(build.language, "llvm-ir")
        self.assertTrue(all(name == "llc" for name, _ in self.calls()))

    def test_missing_c_tool_has_clear_diagnostic(self):
        (self.bin / "clang").unlink()
        with self.assertRaisesRegex(LLVMCompilerError, "tool not found.*clang"):
            Toolchain().compile_project(self.project(), llvm_bin_dir=self.bin)

    def test_missing_sdk_has_clear_diagnostic(self):
        (self.sdk / "runtime.bc").unlink()
        with self.assertRaisesRegex(LLVMCompilerError, "SDK is missing"):
            Toolchain().compile_project(self.project(), llvm_bin_dir=self.bin)

    def test_wrong_version_and_missing_target_are_rejected(self):
        for values in ({"version": "22.1.0"}, {"target": False}):
            self.configure(**values)
            with self.assertRaises(LLVMCompilerError):
                Toolchain().compile_project(self.project(), llvm_bin_dir=self.bin)

    def test_each_c_pipeline_failure_preserves_diagnostic(self):
        for stage in ("clang", "llvm-link", "llc"):
            with self.subTest(stage=stage):
                self.configure(**{stage: "failure"})
                with self.assertRaisesRegex(LLVMCompilerError, "original.c:4: error: controlled"):
                    Toolchain().compile_project(self.project(), llvm_bin_dir=self.bin)

    def test_success_without_required_stage_output_is_an_error(self):
        for stage in ("clang", "llvm-link", "llc"):
            with self.subTest(stage=stage):
                self.configure(**{stage: "missing"})
                with self.assertRaisesRegex(LLVMCompilerError, "did not produce"):
                    Toolchain().compile_project(self.project(), llvm_bin_dir=self.bin)

    def test_timeout_applies_to_the_entire_pipeline(self):
        self.configure(version_delay=0.08)
        started = time.monotonic()
        with self.assertRaises(LLVMTimeoutError):
            Toolchain().compile_project(self.project(), llvm_bin_dir=self.bin, timeout=0.14)
        self.assertLess(time.monotonic() - started, 2)

    def test_cancellation_stops_a_running_stage(self):
        self.configure(clang="sleep")
        event = threading.Event()
        timer = threading.Timer(0.3, event.set)
        self.addCleanup(timer.cancel)
        timer.start()
        started = time.monotonic()
        with self.assertRaises(CompilationCancelled):
            Toolchain().compile_project(self.project(), llvm_bin_dir=self.bin, cancel_event=event)
        self.assertLess(time.monotonic() - started, 2)

    def test_pre_cancelled_build_does_not_launch_tools(self):
        event = threading.Event()
        event.set()
        with mock.patch("subprocess.Popen", side_effect=AssertionError("must not spawn")):
            with self.assertRaises(CompilationCancelled):
                Toolchain().compile_project(self.project(), llvm_bin_dir=self.bin, cancel_event=event)

    def test_invalid_timeout_and_language_do_not_launch_tools(self):
        with mock.patch("subprocess.Popen", side_effect=AssertionError("must not spawn")):
            for timeout in (0, -1, float("inf"), float("nan"), None):
                with self.assertRaises(ValueError):
                    Toolchain().compile_project(self.project(), llvm_bin_dir=self.bin, timeout=timeout)
            with self.assertRaises(ValueError):
                Toolchain().compile("", backend="llvm", language="c++", llvm_bin_dir=self.bin)

    def test_image_and_static_data_capacity_are_checked(self):
        for assembly in (ASSEMBLY.replace("2\n", "2048\n", 1), ASSEMBLY + "halt\n" * 1024):
            self.configure(assembly=assembly)
            with self.assertRaises(ValueError):
                Toolchain().compile_project(self.project(), llvm_bin_dir=self.bin)

    def test_cli_selects_c_and_builds_multiple_files(self):
        second = self.root / "second.c"
        second.write_text("int helper(void){return 42;}\n")
        output = self.root / "app.bin"
        self.assertEqual(main(["compile", str(self.source), str(second), "-I", str(self.root), "-D", "COUNT=1",
                               "--llvm-bin-dir", str(self.bin), "-o", str(output)]), 0)
        calls = self.calls()
        self.assertEqual(sum(name == "clang" and "-emit-llvm" in args for name, args in calls), 2)
        self.assertTrue(output.is_file())

    def test_cli_project_build_and_failure_leave_no_image(self):
        manifest = self.root / ".opencpu.json"
        manifest.write_text(json.dumps({"version": 1, "sources": ["main.c"]}))
        output = self.root / "app.bin"
        self.configure(clang="failure")
        with contextlib.redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(["compile", "--project", str(manifest), "--llvm-bin-dir", str(self.bin),
                                   "-o", str(output)]), 2)
        self.assertIn("controlled compiler failure", errors.getvalue())
        self.assertFalse(output.exists())

    def test_explicit_tool_directory_overrides_environment(self):
        with mock.patch.dict(os.environ, {"OPENCPU_LLVM_BIN_DIR": "/not/installed"}):
            self.assertEqual(LLVMCompiler(self.bin).bin_dir, self.bin)
            Toolchain().compile_project(self.project(), llvm_bin_dir=self.bin)


if __name__ == "__main__":
    unittest.main(verbosity=2)
