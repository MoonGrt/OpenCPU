"""Explicit Qt acceptance using the built OpenCPU Clang and LLVM backend.

The serial boundary is controlled so no hardware port is opened. Compilation,
image construction, and instruction execution use the real implementations.
Missing native tools fail this suite rather than being skipped.
"""
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / 'software'))

from PyQt5.QtCore import QObject, QTimer, pyqtSignal  # noqa: E402
from PyQt5.QtTest import QTest  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402
from opencpu.core.toolchain import Toolchain  # noqa: E402
from opencpu.gui.ide import IDEWindow  # noqa: E402


class _SerialBoundary(QObject):
    received = pyqtSignal(bytes)
    connection_changed = pyqtSignal(bool)
    error = pyqtSignal(str)
    download_finished = pyqtSignal(int)
    progress = pyqtSignal(int, int)
    is_open = True
    busy = False

    def __init__(self):
        super().__init__()
        self.downloads = []

    def download(self, binary):
        self.downloads.append(binary)

    def close(self):
        self.is_open = False


class NativeGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])
        Toolchain().compile('int main(void) { return 0; }', backend='llvm', language='c')

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='opencpu native GUI ')
        self.directory = Path(self.temporary.name)
        self.transport = _SerialBoundary()
        self.window = IDEWindow(transport=self.transport)
        self.window._confirm_all_documents = lambda: True
        self.window._confirm_close = lambda _editor: True

    def tearDown(self):
        self.window.stop()
        self.wait_until(lambda: not self.window._compile_threads)
        self.window.close()
        self.application.processEvents()
        self.temporary.cleanup()

    def wait_until(self, predicate, timeout=65):
        deadline = time.monotonic() + timeout
        while not predicate() and time.monotonic() < deadline:
            QTest.qWait(5)
        self.assertTrue(predicate(), self.window.message_tab.toPlainText())

    def build_and_run(self, expected):
        ticks = []
        timer = QTimer(self.window)
        timer.setInterval(1)
        timer.timeout.connect(lambda: ticks.append(1))
        timer.start()
        self.assertTrue(self.window.assemble(), self.window.message_tab.toPlainText())
        self.assertTrue(self.window.compiling)
        self.assertFalse(self.window.run_action.isEnabled())
        self.assertFalse(self.window.download_action.isEnabled())
        self.wait_until(lambda: not self.window._compile_threads)
        timer.stop()
        self.assertGreaterEqual(len(ticks), 2, 'the Qt event loop must advance while native tools run')
        build = self.window.build_result
        self.assertIsNotNone(build, self.window.message_tab.toPlainText())
        self.assertEqual(build.language, 'c')
        self.assertEqual(build.labels['_start'], 0)
        self.assertEqual(self.window.simulator.pc, 0)
        self.window.run()
        self.wait_until(lambda: not self.window.running)
        model = self.window.simulator
        self.assertIsNotNone(model, self.window.message_tab.toPlainText())
        self.assertFalse(model.faulted, model.fault_reason)
        self.assertTrue(model.halted, self.window.message_tab.toPlainText())
        self.assertEqual(model.registers[1], expected)
        self.assertEqual(model.registers[5], 0)
        self.assertEqual(model.registers[7], 1024)

    def test_factorial_uses_real_native_tools_and_startup(self):
        self.window.open_files(paths=[REPOSITORY / 'software/examples/c/factorial.c'])
        self.build_and_run(120)

    def test_project_uses_unsaved_buffers_and_rejects_changed_disk_dependencies(self):
        project = self.directory / 'project'
        shutil.copytree(REPOSITORY / 'software/examples/c/multifile', project)
        self.assertTrue(self.window.open_project(path=project / 'demo.opencpu.json'))
        header_path = project / 'include/math.h'
        main_path = project / 'main.c'
        original_header, original_main = header_path.read_text(), main_path.read_text()
        header = self.window.open_files(paths=[header_path])[0]
        header.setPlainText(original_header + '\n#undef EXAMPLE_BIAS\n#define EXAMPLE_BIAS 11\n')
        main = self.window.open_files(paths=[main_path])[0]
        main.setPlainText(original_main.replace('triangle(6)', 'triangle(4)'))
        # triangle(4)=2+(1+2+3+4); shared_counter=3; unsaved header bias=11.
        self.build_and_run(26)
        self.assertEqual(main_path.read_text(), original_main)
        self.assertEqual(header_path.read_text(), original_header)
        header_path.write_text(original_header + '\n#define EXTERNAL_CHANGE 1\n')
        # Deliberately do not process watcher events before attempting download.
        self.window.download()
        self.assertEqual(self.transport.downloads, [])
        self.assertIsNone(self.window.build_result)
        self.assertFalse(self.window.run_action.isEnabled())
        self.assertFalse(self.window.download_action.isEnabled())
        self.window.run()
        self.assertFalse(self.window.running)

    def test_explicit_c_menu_supports_a_text_named_source(self):
        path = self.directory / 'program.txt'
        path.write_text('int main(void) { return 42; }\n')
        self.window.open_files(paths=[path])
        self.assertTrue(self.window.set_compiler_language('c'))
        self.build_and_run(42)


if __name__ == '__main__':
    unittest.main(verbosity=2)
