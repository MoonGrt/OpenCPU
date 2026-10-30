"""Native acceptance: a real OpenCPU Clang/llc is required; never skipped."""
from pathlib import Path
import hashlib
import tempfile
import unittest

from cases import (  # noqa: E402
    C_EXPECTED_RETURNS, EXPECTED_RETURNS, REJECTED_C, SIMPLE_BINARY_SHA256, STACK_EXHAUSTION_C,
    CProject, EXAMPLES, Toolchain, abi_cases, build_c_fixture, build_fixture, integer_cases,
)
from opencpu.core.simulator import Simulator  # noqa: E402


class NativeCCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Toolchain().compile("int main(void){return 0;}", backend="llvm", language="c")

    def execute(self, build, expected):
        self.assertEqual(build.backend, "llvm")
        self.assertEqual(build.abi_version, "llvm-v2")
        self.assertEqual(build.entry_pc, 0)
        self.assertEqual(build.labels["_start"], 0)
        self.assertLessEqual(len(build.words), 1024)
        self.assertEqual(len(build.source_map), len(build.words))
        model = Simulator(build.entry_pc)
        model.inst_mem = build.words
        model.run(max_steps=200000)
        self.assertFalse(model.faulted, model.fault_reason)
        self.assertTrue(model.halted, "native program did not reach HALT")
        self.assertEqual(model.registers[1], expected)
        self.assertEqual(model.registers[0], 0)
        self.assertEqual(model.registers[5], 0, "FP must be restored")
        self.assertEqual(model.registers[7], 1024, "SP must be restored")
        return model

    def test_c_examples_match_independent_results(self):
        for name, expected in C_EXPECTED_RETURNS.items():
            with self.subTest(example=name):
                build = build_c_fixture(name)
                self.assertEqual(build.language, "c")
                self.execute(build, expected)

    def test_each_integer_width_and_operation(self):
        for case in integer_cases():
            with self.subTest(operation=case.name):
                build = Toolchain().compile(case.source, backend="llvm", language="c",
                                            source_name=f"integer-{case.name}.c")
                self.execute(build, case.expected)

    def test_wide_argument_split_and_values_live_across_calls(self):
        for case in abi_cases():
            with self.subTest(abi=case.name):
                build = Toolchain().compile(case.source, backend="llvm", language="c")
                self.execute(build, case.expected)

    def test_existing_llvm_ir_examples_keep_their_results(self):
        for name, expected in EXPECTED_RETURNS.items():
            with self.subTest(example=name):
                self.execute(build_fixture(name), expected)

    def test_existing_simple_examples_keep_their_results(self):
        for name, expected in (("loops.oc", {"X": 15, "Y": 11, "i": 3}),
                               ("functions.oc", {"result": 120})):
            with self.subTest(example=name):
                path = EXAMPLES / "simple" / name
                build = Toolchain().compile(path.read_text())
                self.assertEqual(hashlib.sha256(build.binary.encode()).hexdigest(), SIMPLE_BINARY_SHA256[name])
                model = Simulator(build.entry_pc)
                model.inst_mem = build.words
                model.run()
                self.assertTrue(model.halted)
                self.assertFalse(model.faulted)
                for variable, value in expected.items():
                    self.assertEqual(model.data_mem[1022 + build.variable_offsets[variable]], value)
        build = Toolchain().assemble((EXAMPLES / "simple/isa.asm").read_text())
        self.assertEqual(hashlib.sha256(build.binary.encode()).hexdigest(), SIMPLE_BINARY_SHA256["isa.asm"])
        model = Simulator(build.entry_pc)
        model.inst_mem = build.words
        model.run()
        self.assertTrue(model.halted)
        self.assertEqual(model.data_mem[0], 43980)

    def test_unsaved_new_source_and_virtual_header_keep_original_names(self):
        with tempfile.TemporaryDirectory(prefix="opencpu unsaved C ") as temporary:
            directory = Path(temporary)
            source = directory / "new file.c"
            header = directory / "new header.h"
            text = '#include "new header.h"\nint main(void){return ANSWER;}'
            project = CProject(sources=(source,))
            build = Toolchain().compile_project(project, buffers={source: text, header: "#define ANSWER 42\n"})
            self.execute(build, 42)
            self.assertFalse(source.exists())
            self.assertFalse(header.exists())
            with self.assertRaises(ValueError) as rejected:
                Toolchain().compile("int main(void){\nreturn unknown_name;\n}", backend="llvm", language="c",
                                    source_name=str(source))
            self.assertIn(str(source) + ":2:", str(rejected.exception))
            self.assertFalse(source.exists())

    def test_type_model_headers_and_promotions(self):
        source = """
        #include <stdint.h>
        #include <stddef.h>
        #include <limits.h>
        #include <stdbool.h>
        _Static_assert(CHAR_BIT == 8, "byte");
        _Static_assert(sizeof(short) == 2 && sizeof(int) == 2, "int16");
        _Static_assert(sizeof(long) == 4 && sizeof(long long) == 8, "wide");
        _Static_assert(sizeof(void *) == 2 && sizeof(size_t) == 2, "pointer16");
        _Static_assert(_Alignof(long long) == 2 && _Alignof(void *) == 2, "alignment");
        _Static_assert(CHAR_MIN == -128, "plain char signedness");
        int main(void){ int8_t value=-100; uint8_t bias=20; bool yes=true; return yes ? value+bias+130 : 0; }
        """
        self.execute(Toolchain().compile(source, backend="llvm", language="c"), 50)

    def test_startup_reinitializes_globals_in_dirty_ram(self):
        build = build_c_fixture("globals")
        model = Simulator(build.entry_pc)
        model.inst_mem = build.words
        model.data_mem = {address: 0xA55A for address in range(1024)}
        model.run(max_steps=200000)
        self.assertTrue(model.halted)
        self.assertFalse(model.faulted, model.fault_reason)
        self.assertEqual(model.registers[1], C_EXPECTED_RETURNS["globals"])
        self.assertEqual(model.registers[5], 0)
        self.assertEqual(model.registers[7], 1024)

    def test_unsupported_c_reports_controlled_diagnostics(self):
        for name, source in REJECTED_C.items():
            with self.subTest(feature=name):
                with self.assertRaises(ValueError) as rejected:
                    Toolchain().compile(source, backend="llvm", language="c", source_name=f"rejected-{name}.c")
                diagnostic = str(rejected.exception)
                self.assertTrue(diagnostic)
                for unexpected in ("Stack dump:", "PLEASE submit a bug report", "Assertion failed", "Cannot select"):
                    self.assertNotIn(unexpected, diagnostic)

    def test_duplicate_definitions_and_missing_headers(self):
        with tempfile.TemporaryDirectory(prefix="opencpu-native-project-") as temporary:
            directory = Path(temporary)
            first, second = directory / "main.c", directory / "duplicate.c"
            first.write_text("int duplicated=1; int main(void){return duplicated;}")
            second.write_text("int duplicated=2;")
            with self.assertRaisesRegex(ValueError, "[Mm]ultiply|[Dd]uplicate|multiple definition"):
                Toolchain().compile_project(CProject(sources=(first, second)))
            first.write_text('#include "missing-header.h"\nint main(void){return 0;}')
            with self.assertRaises(ValueError) as rejected:
                Toolchain().compile_project(CProject(sources=(first,)))
            self.assertIn("missing-header.h", str(rejected.exception))
            self.assertIn(str(first), str(rejected.exception))

    def test_rom_and_static_ram_capacity(self):
        huge_data = "volatile unsigned char blob[2048]; int main(void){return blob[0];}"
        huge_code = "int main(void){volatile unsigned value=0;" + "value += 1;" * 1000 + "return value;}"
        for name, source in (("RAM", huge_data), ("ROM", huge_code)):
            with self.subTest(capacity=name):
                with self.assertRaises(ValueError):
                    Toolchain().compile(source, backend="llvm", language="c")

    def test_stack_exhaustion_faults_instead_of_overwriting_data(self):
        build = Toolchain().compile(STACK_EXHAUSTION_C, backend="llvm", language="c")
        model = Simulator(build.entry_pc)
        model.inst_mem = build.words
        model.run(max_steps=100000)
        self.assertTrue(model.faulted)
        self.assertFalse(model.limit_reached)
        self.assertFalse(model.halted)
        self.assertEqual(model.data_mem[1], 0x5AA5, "stack overflow overwrote the static-data sentinel")


if __name__ == "__main__":
    unittest.main(verbosity=2)
