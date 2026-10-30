#!/usr/bin/env python3
"""Explicit native LLVM -> UART -> real RTL retirement acceptance.

This suite requires the actual OpenCPU LLVM and Verilator executables. Neither
missing tool is treated as a successful skipped test.
"""
import sys
import unittest

from soc_support import REPOSITORY, SocDriverMixin

sys.path.insert(0, str(REPOSITORY / "software/tests/native"))
from llvm_cases import EXPECTED_RETURNS, build_fixture  # noqa: E402
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
