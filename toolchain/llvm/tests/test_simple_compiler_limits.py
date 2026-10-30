"""Oversized simple sources have compiler diagnostics instead of Python crashes."""
import contextlib
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / 'software'))
from opencpu.cli import main
from opencpu.core.compiler import CompileError, Compiler
from opencpu.core.toolchain import Toolchain
from cases import SIMPLE_BINARY_SHA256


class SimpleCompilerLimitTests(unittest.TestCase):
    def test_deep_expression_and_statement_nesting_are_controlled(self):
        sources = ['result=' + '+'.join(['1'] * size) + ';' for size in (1000, 2000)]
        sources.append('if(1){' * 1100 + 'result=1;' + '}' * 1100)
        compiler = Compiler()
        for source in sources:
            with self.subTest(length=len(source)):
                with self.assertRaisesRegex(CompileError, 'nesting.*limit'):
                    compiler.compile(source)
        # A failed compile must not prevent reusing the service.
        self.assertIn('halt', compiler.compile('result=42;'))

    def test_cli_limit_diagnostic_has_no_traceback_or_partial_output(self):
        with tempfile.TemporaryDirectory(prefix='opencpu-simple-limit-') as temporary:
            source = Path(temporary) / 'deep.oc'
            output = Path(temporary) / 'result.bin'
            source.write_text('result=' + '+'.join(['1'] * 2000) + ';')
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(['compile', str(source), '-o', str(output)])
            self.assertEqual(code, 2)
            self.assertIn('nesting', stderr.getvalue())
            self.assertNotIn('Traceback', stderr.getvalue())
            self.assertNotIn('RecursionError', stderr.getvalue())
            self.assertFalse(output.exists())

    def test_normal_examples_keep_their_exact_binary(self):
        for name, expected in SIMPLE_BINARY_SHA256.items():
            with self.subTest(example=name):
                path = REPOSITORY / 'software/examples/simple' / name
                source = path.read_text()
                build = Toolchain().assemble(source) if name.endswith('.asm') else Toolchain().compile(source)
                self.assertEqual(hashlib.sha256(build.binary.encode()).hexdigest(), expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
