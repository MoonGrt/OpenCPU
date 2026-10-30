"""Qt lifecycle regression with controlled services; native tests use real LLVM."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / 'software'))

from PyQt5.QtCore import QObject, QTimer, pyqtSignal  # noqa: E402
from PyQt5.QtTest import QTest  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402
from opencpu.core.toolchain import Toolchain  # noqa: E402
from opencpu.gui.documents import Document  # noqa: E402
from opencpu.gui.ide import IDEWindow  # noqa: E402


class _Transport(QObject):
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


class _Services:
    def __init__(self):
        self.jobs = []
        self.dependencies = ()

    def assemble(self, source):
        return Toolchain().assemble(source)

    def compile(self, source, **options):
        if options.get('backend', 'simple') == 'simple':
            return Toolchain().compile(source)
        return self._build(source=source, **options)

    def compile_project(self, project, **options):
        return self._build(project=project, **options)

    def _build(self, **options):
        release = threading.Event()
        buffers = dict(options.get('buffers', {}))
        paths = self.dependencies or getattr(options.get('project'), 'sources', ())
        hashes = {str(path): hashlib.sha256(buffers[path].encode() if path in buffers else path.read_bytes()).hexdigest()
                  for path in paths}
        job = dict(options, release=release)
        self.jobs.append(job)
        if not release.wait(5):
            raise RuntimeError('test service was not released')
        result = self.assemble('li sp, 1024\nli fp, 0\nli a1, 42\nhalt\n')
        result.backend = 'llvm'
        result.language = 'c' if options.get('project') else options.get('language', 'llvm-ir')
        result.dependencies = tuple(paths)
        result.dependency_hashes = hashes
        return result

    def release_all(self):
        for job in self.jobs:
            job['release'].set()


class _CountingSimulator:
    """Controlled execution service that needs more than the legacy run budget."""
    def __init__(self, halt_after):
        self.halt_after = halt_after
        self.instructions_retired = 0
        self.halted = self.faulted = self.stopped = self.limit_reached = False
        self.can_undo = False
        self.stop_reason = None
        self.breakpoints = set()

    def run(self, max_steps):
        self.stopped = self.limit_reached = False
        count = 0
        while count < max_steps and not self.halted:
            self.step()
            count += 1
        self.limit_reached = not self.halted
        self.stop_reason = 'halt' if self.halted else 'limit'
        return count

    def step(self):
        self.instructions_retired += 1
        self.halted = self.instructions_retired >= self.halt_after
        return True


class GuiCTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='opencpu-c-gui-')
        self.directory = Path(self.temporary.name)
        self.main = self.directory / 'main.c'
        self.utility = self.directory / 'utility.c'
        self.header = self.directory / 'config.h'
        self.manifest = self.directory / 'example.opencpu.json'
        self.main.write_text('#include "config.h"\nint main(void) { return VALUE; }\n')
        self.utility.write_text('int utility(int x) { return x + 1; }\n')
        self.header.write_text('#define VALUE 42\n')
        self.write_manifest()
        self.tools = _Services()
        self.transport = _Transport()
        self.window = IDEWindow(toolchain=self.tools, transport=self.transport)
        self.window._confirm_all_documents = lambda: True
        self.window._confirm_close = lambda _editor: True

    def tearDown(self):
        self.tools.release_all()
        self.wait_until(lambda: not self.window._compile_threads)
        self.window.close()
        self.application.processEvents()
        self.temporary.cleanup()

    def write_manifest(self, defines=()):
        self.manifest.write_text(json.dumps({
            'version': 1, 'sources': ['main.c', 'utility.c'],
            'include_dirs': ['.'], 'defines': list(defines),
        }))

    def wait_until(self, predicate, timeout=2):
        deadline = time.monotonic() + timeout
        while not predicate() and time.monotonic() < deadline:
            QTest.qWait(5)
        self.assertTrue(predicate(), 'Qt operation did not finish')

    def open_main(self):
        return self.window.open_files(paths=[self.main])[0]

    def start_project(self):
        self.assertTrue(self.window.open_project(path=self.manifest))
        editor = next(editor for editor, item in self.window._documents.items() if item.path == self.main)
        self.window.edit_area.setCurrentWidget(editor)
        self.assertTrue(self.window.assemble())
        self.wait_until(lambda: bool(self.tools.jobs))
        return editor

    def finish_build(self):
        self.tools.release_all()
        self.wait_until(lambda: not self.window._compile_threads)
        self.assertIsNotNone(self.window.build_result)

    def test_c_and_ir_auto_selection_and_per_document_language(self):
        self.assertEqual((Document(path=self.main).backend, Document(path=self.main).language), ('llvm', 'c'))
        self.assertEqual(Document(path=self.main.with_suffix('.ll')).language, 'llvm-ir')
        first = self.open_main()
        self.window.set_compiler_language('llvm-ir')
        second = self.window.new_file(text='result = 1;')
        self.assertEqual(self.window.current_document.backend, 'simple')
        self.window.edit_area.setCurrentWidget(first)
        self.assertEqual(self.window.current_document.language, 'llvm-ir')
        self.assertTrue(self.window._language_actions['llvm-ir'].isChecked())

    def test_c_compilation_keeps_event_loop_responsive_and_runs_startup(self):
        self.open_main()
        ticks = []
        timer = QTimer(self.window)
        timer.setInterval(1)
        timer.timeout.connect(lambda: ticks.append(1))
        timer.start()
        self.assertTrue(self.window.assemble())
        self.wait_until(lambda: bool(self.tools.jobs) and len(ticks) >= 3)
        self.assertFalse(self.window.run_action.isEnabled())
        self.finish_build()
        self.window.run()
        self.wait_until(lambda: self.window.simulator.halted)
        self.assertEqual(self.window.simulator.registers[1], 42)
        self.assertEqual(self.window.simulator.registers[7], 1024)

    def test_explicit_c_language_keeps_non_c_source_filename(self):
        path = self.directory / 'program.txt'
        path.write_text('int main(void) { return 42; }\n')
        self.window.open_files(paths=[path])
        self.window.set_compiler_language('c')
        self.assertTrue(self.window.assemble())
        self.wait_until(lambda: bool(self.tools.jobs))
        self.assertEqual(self.tools.jobs[-1]['source_name'], str(path))
        self.assertEqual(self.tools.jobs[-1]['language'], 'c')
        self.assertNotIn('project', self.tools.jobs[-1])
        self.finish_build()

    def test_c_run_can_complete_beyond_legacy_instruction_limit(self):
        self.open_main()
        self.assertTrue(self.window.assemble())
        self.wait_until(lambda: bool(self.tools.jobs))
        self.finish_build()
        model = _CountingSimulator(10050)
        self.window.simulator = model
        self.window._refresh_execution = lambda: None
        self.window.run()
        self.wait_until(lambda: model.halted)
        self.assertEqual(model.instructions_retired, 10050)
        self.assertFalse(model.limit_reached)

        # Other inputs keep the established budget and explain how to continue.
        self.window.build_result.language = 'llvm-ir'
        model = _CountingSimulator(20000)
        self.window.simulator = model
        self.window.run()
        self.wait_until(lambda: model.limit_reached)
        self.assertFalse(model.halted)
        self.assertEqual(model.instructions_retired, 10000)
        self.assertIn('10000 instructions', self.window.message_tab.toPlainText())

    def test_project_captures_all_unsaved_source_and_header_buffers(self):
        self.assertTrue(self.window.open_project(path=self.manifest))
        header = self.window.open_files(paths=[self.header])[0]
        header.setPlainText('#define VALUE 43\n')
        main = self.window.open_files(paths=[self.main])[0]
        main.setPlainText('int main(void) { return 44; }\n')
        self.assertTrue(self.window.assemble())
        self.wait_until(lambda: bool(self.tools.jobs))
        job = self.tools.jobs[-1]
        self.assertEqual(job['project'].sources, (self.main, self.utility))
        self.assertEqual(job['buffers'][self.header], '#define VALUE 43\n')
        self.assertEqual(job['buffers'][self.main], 'int main(void) { return 44; }\n')
        self.finish_build()
        self.assertTrue(self.window.run_action.isEnabled())
        self.assertEqual(self.header.read_text(), '#define VALUE 42\n')

    def test_edit_in_background_project_tab_cancels_and_discards_late_result(self):
        self.start_project()
        utility = next(editor for editor, item in self.window._documents.items() if item.path == self.utility)
        utility.setPlainText('int utility(int x) { return x + 2; }\n')
        self.assertTrue(self.tools.jobs[-1]['cancel_event'].is_set())
        self.tools.release_all()
        self.wait_until(lambda: not self.window._compile_threads)
        self.assertIsNone(self.window.build_result)

    def test_unopened_header_change_invalidates_completed_project(self):
        self.tools.dependencies = (self.main, self.utility, self.header)
        self.start_project()
        self.finish_build()
        self.header.write_text('#define VALUE 99\n')
        # Check synchronously, before QFileSystemWatcher has delivered its event.
        self.window.run()
        self.assertIsNone(self.window.build_result)
        self.assertFalse(self.window.running)
        self.assertFalse(self.window.download_action.isEnabled())

    def test_changed_dependency_cannot_be_downloaded_before_watch_event(self):
        self.tools.dependencies = (self.main, self.header)
        self.start_project()
        self.finish_build()
        self.header.unlink()
        self.window.download()
        self.assertEqual(self.transport.downloads, [])
        self.assertIsNone(self.window.build_result)

    def test_disk_change_of_open_buffer_is_checked_before_watch_event(self):
        self.start_project()
        self.finish_build()
        self.main.write_text('int main(void) { return 99; }\n')
        self.window.download()
        self.assertEqual(self.transport.downloads, [])
        self.assertIsNone(self.window.build_result)

    def test_manifest_change_cancels_and_next_build_reloads_configuration(self):
        self.start_project()
        self.write_manifest(['VALUE=7'])
        self.wait_until(lambda: self.tools.jobs[0]['cancel_event'].is_set())
        self.tools.release_all()
        self.wait_until(lambda: not self.window._compile_threads)
        self.assertIsNone(self.window.build_result)
        self.assertTrue(self.window.assemble())
        self.wait_until(lambda: len(self.tools.jobs) == 2)
        self.assertEqual(self.tools.jobs[-1]['project'].defines, ('VALUE=7',))

    def test_language_and_tool_changes_discard_results(self):
        self.start_project()
        self.window.set_compiler_language('llvm-ir')
        self.assertTrue(self.tools.jobs[0]['cancel_event'].is_set())
        self.window.set_llvm_bin_dir(self.directory / 'other-tools')
        self.tools.release_all()
        self.wait_until(lambda: not self.window._compile_threads)
        self.assertIsNone(self.window.build_result)

    def test_stop_then_late_completion_never_enables_execution(self):
        self.start_project()
        self.window.stop()
        self.assertTrue(self.tools.jobs[0]['cancel_event'].is_set())
        self.tools.release_all()
        self.wait_until(lambda: not self.window._compile_threads)
        self.assertFalse(self.window.run_action.isEnabled())
        self.assertIsNone(self.window.build_result)

    def test_closing_project_cancels_request_and_keeps_documents(self):
        self.start_project()
        count = len(self.window._documents)
        self.window.close_project()
        self.assertIsNone(self.window._project)
        self.assertEqual(len(self.window._documents), count)
        self.assertTrue(self.tools.jobs[0]['cancel_event'].is_set())
        self.tools.release_all()
        self.wait_until(lambda: not self.window._compile_threads)
        self.assertIsNone(self.window.build_result)

    def test_closing_window_waits_for_worker_without_applying_result(self):
        self.start_project()
        self.window.show()
        self.assertFalse(self.window.close())
        self.assertTrue(self.window._closing)
        self.assertFalse(self.window.assemble())
        self.tools.release_all()
        self.wait_until(lambda: not self.window._compile_threads and not self.window._closing)
        self.assertIsNone(self.window.build_result)
        self.assertFalse(self.window.isVisible())

    def test_simple_compiler_remains_synchronous_without_project(self):
        self.window.new_file(text='result = 6 * 7;')
        self.assertTrue(self.window.assemble())
        self.assertEqual(self.tools.jobs, [])
        self.assertEqual(self.window.build_result.backend, 'simple')


if __name__ == '__main__':
    unittest.main(verbosity=2)
