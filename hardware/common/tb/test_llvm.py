#!/usr/bin/env python3
"""Explicit native LLVM -> UART -> real RTL retirement acceptance.

This suite requires the actual OpenCPU LLVM and Verilator executables. Neither
missing tool is treated as a successful skipped test.
"""
import sys
import unittest

from soc_support import REPOSITORY, SocDriverMixin

sys.path.insert(0, str(REPOSITORY / "toolchain/llvm/tests"))
from cases import (  # noqa: E402
    C_EXPECTED_RETURNS, EXPECTED_RETURNS, STACK_EXHAUSTION_C, Toolchain,
    abi_cases, build_c_fixture, build_fixture, integer_cases,
)
from opencpu.core.compiler.llvm import LLVMCompiler  # noqa: E402


class SocLLVMTests(SocDriverMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        LLVMCompiler().compile("define i16 @main() { ret i16 0 }", source_name="rtl-toolchain-check.ll")

    def test_native_examples_match_reference_at_every_retirement(self):
        for name, expected in EXPECTED_RETURNS.items():
            with self.subTest(example=name):
                build = build_fixture(name)
                self.assertEqual(build.entry_pc, 0)
                self.assertEqual(build.labels["_start"], 0)
                self.assertGreater(build.labels["main"], 0)
                state = self.assert_matches_reference(build)
                self.assertEqual(state["registers"][1], expected)
                self.assertEqual(state["registers"][5], 0)
                self.assertEqual(state["registers"][7], 1024)

    def test_c_examples_match_reference_at_every_retirement(self):
        for name, expected in C_EXPECTED_RETURNS.items():
            with self.subTest(example=name):
                build = build_c_fixture(name)
                state = self.assert_matches_reference(build, max_cycles=250000)
                self.assertEqual(state["registers"][1], expected)
                self.assertEqual(state["registers"][5], 0)
                self.assertEqual(state["registers"][7], 1024)
                if name == "mmio":
                    self.assertEqual(state["led"], 10)
                    self.assertEqual(state["display_value"], 0x1234)

    def test_c_integer_operations_match_reference_at_every_retirement(self):
        for case in integer_cases():
            with self.subTest(operation=case.name):
                build = Toolchain().compile(case.source, backend="llvm", language="c")
                state = self.assert_matches_reference(build, max_cycles=250000)
                self.assertEqual(state["registers"][1], case.expected)
                self.assertEqual(state["registers"][5], 0)
                self.assertEqual(state["registers"][7], 1024)

    def test_wide_argument_split_and_live_values_match_reference(self):
        for case in abi_cases():
            with self.subTest(abi=case.name):
                build = Toolchain().compile(case.source, backend="llvm", language="c")
                state = self.assert_matches_reference(build, max_cycles=250000)
                self.assertEqual(state["registers"][1], case.expected)
                self.assertEqual(state["registers"][5], 0)
                self.assertEqual(state["registers"][7], 1024)

    def test_c_stack_exhaustion_fault(self):
        build = Toolchain().compile(STACK_EXHAUSTION_C, backend="llvm", language="c")
        state, _ = self.run_image(build.words, expected_code=2, max_cycles=250000)
        self.assertTrue(state["faulted"])
        self.assertFalse(state["halted"])
        self.assertEqual(self.memory(state, 1), 0x5AA5, "stack overflow overwrote static data")


if __name__ == "__main__":
    unittest.main(verbosity=2)
