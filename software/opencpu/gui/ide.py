"""IDE document, build and execution controller for the retained window layout."""
from pathlib import Path
import threading

from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtGui import QColor, QTextCursor
from PyQt5.QtWidgets import QAction, QActionGroup, QApplication, QDialog, QFileDialog, QMainWindow, QMessageBox, QTableWidgetItem, QTextEdit, QToolBar

from ..core.disassembler import Disassembler
from ..core.simulator import Simulator
from ..core.toolchain import Toolchain
from .documents import Document
from .ide_ui import IDELayout
from .serial_dialog import SerialDialog
from ..transport.serial import SerialTransport


class _CompileWorker(QThread):
    """Only the toolchain runs here; widgets are updated by the owner thread."""

    def __init__(self, parent, toolchain, document, request_id):
        super().__init__(parent)
        self.toolchain = toolchain
        self.document = document
        self.request_id = request_id
        self.revision = document.revision
        self.source = document.text
        self.backend = document.backend
        self.source_name = str(document.path or "untitled.ll")
        self.cancel_event = threading.Event()
        self.result = None
        self.error = None

    def run(self):
        try:
            self.result = self.toolchain.compile(
                self.source, backend=self.backend, source_name=self.source_name,
                cancel_event=self.cancel_event,
            )
        except Exception as error:
            # An uncaught exception in a Qt worker would terminate the GUI.
            self.error = str(error)


class IDEWindow(QMainWindow, IDELayout):
    """One current document owns a build; edits and tab changes invalidate it."""

    RUN_BATCH_SIZE = 64
    RUN_STEP_LIMIT = 10000

    def __init__(self, parent=None, *, transport=None, toolchain=None):
        super().__init__(parent)
        self.toolchain = toolchain or Toolchain()
        self.serial_transport = transport or SerialTransport(self)
        self.serial_dialog = SerialDialog(self)
        self.serial_settings = self.serial_dialog.settings()
        self.downloader_window = None
        self.build_result = None
        self.simulator = None
        self._documents = {}
        self._focused_editor = None
        self._build_document = None
        self._compile_document = None
        self._compile_worker = None
        self._compile_threads = set()
        self._compile_request_id = 0
        self._closing = False
        self._steps_remaining = 0
        self._run_timer = QTimer(self)
        self._run_timer.setInterval(0)
        self._run_timer.timeout.connect(self._run_batch)
        self.setup_ui()
        self._setup_compiler_menu()
        self.edit_area.currentChanged.connect(self._active_document_changed)
        QApplication.instance().focusChanged.connect(self._focus_changed)
        self.serial_transport.received.connect(self._serial_received)
        self.serial_transport.connection_changed.connect(self._connection_changed)
        self.serial_transport.error.connect(self._serial_error)
        self.serial_transport.download_finished.connect(self._download_finished)
        self.serial_transport.progress.connect(lambda _sent, _total: self._sync_actions())
        self._sync_actions()

    @property
    def current_editor(self):
        return self.edit_area.currentWidget()

    @property
    def current_document(self):
        return self._documents.get(self.current_editor)

    @property
    def running(self):
        return self._run_timer.isActive()

    @property
    def compiling(self):
        return self._compile_worker is not None

    def _setup_compiler_menu(self):
        tools = next(action.menu() for action in self.menuBar().actions() if action.text() == 'Tools')
        self.compiler_menu = tools.addMenu('Compiler backend')
        self._backend_group = QActionGroup(self)
        self._backend_group.setExclusive(True)
        self._backend_actions = {}
        for backend, label in (('simple', 'Simple (.oc)'), ('llvm', 'LLVM IR (.ll)')):
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda _checked, name=backend: self.set_compiler_backend(name))
            self._backend_group.addAction(action)
            self.compiler_menu.addAction(action)
            self._backend_actions[backend] = action

    def set_compiler_backend(self, backend):
        document = self.current_document
        if document is None or document.kind != 'source':
            return False
        if backend != document.backend:
            document.set_backend(backend)
            self._invalidate_build()
            self.message_showmessage(f'Compiler backend: {backend}.\n')
        self._sync_actions()
        return True

    def _add_document(self, document):
        editor = QTextEdit(self)
        editor.setPlainText(document.text)
        self._documents[editor] = document
        editor.textChanged.connect(lambda: self._document_changed(editor))
        index = self.edit_area.addTab(editor, document.title)
        self.edit_area.setTabToolTip(index, str(document.path or 'Untitled'))
        self.edit_area.setCurrentIndex(index)
        return editor

    def new_file(self, _checked=False, *, text='', kind='source', backend=None):
        document = Document(kind=kind, backend=backend)
        document.set_text(text)
        return self._add_document(document)

    def open_files(self, _checked=False, *, paths=None):
        if paths is None:
            paths, _ = QFileDialog.getOpenFileNames(
                self, 'Open Files', '', 'OpenCPU files (*.oc *.ll *.asm *.s *.bin *.txt);;All Files (*)', options=QFileDialog.Options())
        opened = []
        for path in paths:
            try:
                suffix = Path(path).suffix.lower()
                kind = 'assembly' if suffix in ('.asm', '.s') else 'binary' if suffix == '.bin' else 'source'
                document = Document.open(path, kind)
            except (OSError, UnicodeError, ValueError) as error:
                self.message_showmessage(f'Open error: {error}\n')
                continue
            opened.append(self._add_document(document))
        return opened

    def _document_changed(self, editor):
        document = self._documents[editor]
        document.set_text(editor.toPlainText())
        self._update_title(editor)
        if document is self._build_document or document is self._compile_document:
            self._invalidate_build()

    def _update_title(self, editor):
        document = self._documents[editor]
        index = self.edit_area.indexOf(editor)
        if index >= 0:
            self.edit_area.setTabText(index, document.title)
            self.edit_area.setTabToolTip(index, str(document.path or 'Untitled'))

    def _active_document_changed(self, _index):
        self._focused_editor = self.current_editor
        if self.current_document is not self._build_document:
            self._invalidate_build()
        self._sync_actions()

    def _choose_save_path(self, document):
        path, _ = QFileDialog.getSaveFileName(
            self, 'Save As', str(document.path or ''), 'Text Files (*.txt);;All Files (*)',
            options=QFileDialog.Options())
        return path or None

    def _save_editor(self, editor, path=None, *, choose=False):
        if editor is None:
            return False
        document = self._documents[editor]
        if choose or (path is None and document.path is None):
            path = self._choose_save_path(document)
            if path is None:
                return False
        try:
            previous_revision = document.revision
            document.save(editor.toPlainText(), path)
        except (OSError, UnicodeError, ValueError) as error:
            self.message_showmessage(f'Save error: {error}\n')
            return False
        if document.revision != previous_revision and document in (self._build_document, self._compile_document):
            self._invalidate_build()
        self._update_title(editor)
        return True

    def save_file(self, _checked=False):
        return self._save_editor(self.current_editor)

    def save_as(self, _checked=False, *, path=None):
        return self._save_editor(self.current_editor, path, choose=path is None)

    def save_all_files(self, _checked=False):
        for editor in list(self._documents):
            if not self._save_editor(editor):
                return False
        return True

    def _confirm_close(self, editor):
        document = self._documents[editor]
        if not document.dirty:
            return True
        answer = QMessageBox.question(
            self, 'Save changes', f'Save changes to {document.title.rstrip("*")}?',
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
        return self._save_editor(editor) if answer == QMessageBox.Save else answer == QMessageBox.Discard

    def _confirm_all_documents(self):
        return all(self._confirm_close(editor) for editor in list(self._documents))

    def _remove_document(self, editor):
        if self._documents.get(editor) in (self._build_document, self._compile_document):
            self._invalidate_build()
        if self._focused_editor is editor:
            self._focused_editor = None
        self.edit_area.removeTab(self.edit_area.indexOf(editor))
        self._documents.pop(editor, None)
        editor.deleteLater()

    def close_file(self, _checked=False):
        editor = self.current_editor
        if editor is None or not self._confirm_close(editor):
            return False
        self._remove_document(editor)
        return True

    def close_all_files(self, _checked=False):
        if not self._confirm_all_documents():
            return False
        for editor in list(self._documents):
            self._remove_document(editor)
        return True

    def _focus_changed(self, _previous, current):
        if isinstance(current, QTextEdit) and current.window() is self:
            self._focused_editor = current

    def _edit(self, operation):
        editor = self._focused_editor or self.current_editor
        if editor is None or (operation != 'copy' and editor.isReadOnly()):
            return
        getattr(editor, operation)()

    def undo(self):
        self._edit('undo')

    def redo(self):
        self._edit('redo')

    def cut(self):
        self._edit('cut')

    def copy(self):
        self._edit('copy')

    def paste(self):
        self._edit('paste')

    def _cancel_compilation(self):
        self._compile_request_id += 1
        if self._compile_worker is not None:
            self._compile_worker.cancel_event.set()
        self._compile_worker = None
        self._compile_document = None

    def _invalidate_build(self):
        self._run_timer.stop()
        self._cancel_compilation()
        had_build = self.build_result is not None
        self.build_result = None
        self._build_document = None
        self.simulator = None
        if had_build:
            self.assemble_code_area.clear()
            self.machine_code_area.clear()
            self.code_table.setRowCount(32)
            self.label_table.setRowCount(8)
            self.data_table.setRowCount(32)
            self.initialize_tables()
        self._sync_actions()

    def assemble(self, _checked=False):
        if self._closing:
            return False
        self._invalidate_build()
        document = self.current_document
        if document is None or not document.text.strip():
            self.message_showmessage('Please input source code.\n')
            return False
        if document.kind == 'source' and document.backend == 'llvm':
            worker = _CompileWorker(self, self.toolchain, document, self._compile_request_id)
            self._compile_worker = worker
            self._compile_document = document
            self._compile_threads.add(worker)
            worker.finished.connect(self._compile_finished)
            self.message_showmessage('LLVM IR: compiling...\n')
            self._sync_actions()
            worker.start()
            return True
        try:
            if document.kind == 'assembly':
                result = self.toolchain.assemble(document.text)
            elif document.kind == 'binary':
                result = self.toolchain.assemble(Disassembler().disassemble(document.text))
            else:
                result = self.toolchain.compile(document.text)
        except (OSError, ValueError, TypeError) as error:
            self.message_showmessage(f'Compile error: {error}\n')
            return False
        self._apply_build(document, result)
        return True

    def _compile_finished(self):
        worker = self.sender()
        current = (
            worker is self._compile_worker
            and worker.request_id == self._compile_request_id
            and worker.document is self.current_document
            and worker.document in self._documents.values()
            and worker.revision == worker.document.revision
            and worker.source == worker.document.text
            and worker.backend == worker.document.backend
            and not worker.cancel_event.is_set()
            and not self._closing
        )
        self._compile_threads.discard(worker)
        if worker is self._compile_worker:
            self._compile_worker = None
            self._compile_document = None
        if current:
            if worker.error is not None:
                self.message_showmessage(f'Compile error: {worker.error}\n')
            else:
                self._apply_build(worker.document, worker.result)
        worker.deleteLater()
        self._sync_actions()
        if self._closing and not self._compile_threads:
            QTimer.singleShot(0, self.close)

    def _apply_build(self, document, result):
        self.build_result = result
        self._build_document = document
        self.simulator = Simulator(getattr(result, 'entry_pc', 0))
        self.simulator.inst_mem = list(result.words)
        self.assemble_code_area.setPlainText(result.assembly)
        self.machine_code_area.setPlainText(result.binary)
        self.fill_code(result)
        self.fill_labels(result.labels)
        self._refresh_execution()
        self._sync_actions()
        self.message_showmessage(f'ISA v2 ({getattr(result, "backend", "simple")}): compiled {len(result.words)} words.\n')

    def _sync_actions(self):
        built = not self._closing and self.build_result is not None and self.current_document is self._build_document
        active = self.running and not self._closing
        compiling = self.compiling and not self._closing
        resumable = built and not self.simulator.halted and not self.simulator.faulted
        self.run_action.setEnabled(resumable and not active and not compiling)
        self.run_step_action.setEnabled(resumable and not active and not compiling)
        self.run_undo_action.setEnabled(built and self.simulator.can_undo and not active and not compiling)
        self.reset_action.setEnabled(built and not active and not compiling)
        self.stop_action.setEnabled(active or compiling)
        self.download_action.setEnabled(built and not compiling and self.serial_transport.is_open and not self.serial_transport.busy)
        self.connect_button.setEnabled(not self._closing and not self.serial_transport.is_open)
        self.disconnect_button.setEnabled(not self._closing and self.serial_transport.is_open)
        document = self.current_document
        self.compiler_menu.setEnabled(document is not None and document.kind == 'source' and not self._closing)
        for backend, action in self._backend_actions.items():
            action.setChecked(document is not None and document.backend == backend)

    def run(self, _checked=False):
        if self._closing or self.simulator is None or self.simulator.halted or self.simulator.faulted or self.running:
            return
        self.simulator.stopped = False
        self.simulator.limit_reached = False
        self._steps_remaining = self.RUN_STEP_LIMIT
        self._run_timer.start()
        self._sync_actions()

    def _run_batch(self):
        model = self.simulator
        if model is None:
            self._run_timer.stop()
            self._sync_actions()
            return
        for _ in range(min(self.RUN_BATCH_SIZE, self._steps_remaining)):
            if not model.step():
                break
            self._steps_remaining -= 1
            if model.halted or model.faulted or model.stopped:
                break
        finished = model.halted or model.faulted or model.stopped or self._steps_remaining == 0
        if finished:
            self._run_timer.stop()
            model.limit_reached = self._steps_remaining == 0 and not model.halted and not model.faulted
            if model.faulted:
                self.message_showmessage(f'Execution fault: {model.fault_reason}\n')
            elif model.limit_reached:
                self.message_showmessage('Step limit reached; Run continues from the current instruction.\n')
            elif model.halted:
                self.message_showmessage('HALT\n')
        self._refresh_execution()
        self._sync_actions()

    def run_step(self, _checked=False):
        if self._closing or self.simulator is None or self.running:
            return
        self.simulator.stopped = False
        self.simulator.step()
        self._refresh_execution()
        self._sync_actions()
        if self.simulator.faulted:
            self.message_showmessage(f'Execution fault: {self.simulator.fault_reason}\n')

    def run_undo(self, _checked=False):
        if self._closing or self.simulator is None or self.running:
            return
        self.simulator.run_undo()
        self._refresh_execution()
        self._sync_actions()

    def reset(self, _checked=False):
        if self._closing or self.simulator is None:
            return
        self._run_timer.stop()
        self.simulator.reset()
        self._refresh_execution()
        self._sync_actions()

    def stop(self, _checked=False):
        if self.compiling:
            self._invalidate_build()
            self.message_showmessage('Compilation cancelled.\n')
            return
        self._run_timer.stop()
        if self.simulator is not None:
            self.simulator.stop()
            self._refresh_execution()
        self._sync_actions()
        self.message_showmessage('Execution paused.\n')

    def _refresh_execution(self):
        if self.simulator is None:
            return
        self.fill_registers(self.simulator.registers)
        self.fill_data(self.simulator.data_mem)
        for row in range(self.code_table.rowCount()):
            self.set_row_background(self.code_table, row, None)
        row = self.find_code_row(self.simulator.next_pc)
        if row >= 0 and not self.simulator.halted and not self.simulator.faulted:
            self.set_row_background(self.code_table, row, QColor(255, 0, 0))

    def fill_code(self, result):
        source = result.assembly.splitlines()
        self.code_table.setRowCount(len(result.words))
        for row, bits in enumerate(result.binary.splitlines()):
            line = source[result.source_map[row] - 1] if row < len(result.source_map) else ''
            for column, text in enumerate((str(row), bits, result.instructions[row], line)):
                self.code_table.setItem(row, column, QTableWidgetItem(text))

    def fill_labels(self, labels):
        self.label_table.clearContents()
        self.label_table.setRowCount(len(labels))
        for row, (name, address) in enumerate(labels.items()):
            self.label_table.setItem(row, 0, QTableWidgetItem(name))
            self.label_table.setItem(row, 1, QTableWidgetItem(str(address)))

    def fill_data(self, data):
        bases = list(range(0, 1024, 8)) + sorted({address & ~7 for address in data if address >= 1024})
        self.data_table.setRowCount(len(bases))
        for row, base in enumerate(bases):
            for column in range(9):
                text = f'0x{base:04X}' if column == 0 else f'0x{data.get(base + column - 1, 0):04X}'
                item = self.data_table.item(row, column)
                if item is None:
                    self.data_table.setItem(row, column, QTableWidgetItem(text))
                else:
                    item.setText(text)

    def fill_registers(self, registers):
        for row, value in enumerate(registers):
            self.register_table.item(row, 2).setText(f'0x{value:04X}')

    @staticmethod
    def _append(editor, text):
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        editor.setTextCursor(cursor)
        editor.ensureCursorVisible()

    def message_showmessage(self, message):
        self._append(self.message_tab, message)

    def message_clear(self):
        self.message_tab.clear()

    def serial_showmessage(self, message):
        self._append(self.serial_tab, message)

    def serial_clear(self):
        self.serial_tab.clear()

    def _serial_received(self, data):
        self.serial_showmessage(bytes(data).hex())

    def _serial_error(self, message):
        self.message_showmessage(f'Serial error: {message}\n')
        self._sync_actions()

    def _connection_changed(self, opened):
        self.message_showmessage('Port open successful\n' if opened else 'Port closed\n')
        self._sync_actions()

    def serial_setting(self):
        self.serial_dialog.set_settings(self.serial_settings)
        if self.serial_dialog.exec_() == QDialog.Accepted:
            self.serial_settings = self.serial_dialog.settings()
            self.serial_connect()

    def serial_connect(self):
        try:
            self.serial_transport.open(self.serial_settings)
        except (ValueError, RuntimeError, OSError) as error:
            self._serial_error(str(error))
        self._sync_actions()

    def serial_disconnect(self):
        self.serial_transport.close()
        self._sync_actions()

    def download(self):
        if self._closing or self.compiling or self.build_result is None or self.current_document is not self._build_document:
            return
        try:
            self.serial_transport.download(self.build_result.binary)
        except (ValueError, RuntimeError, OSError) as error:
            self._serial_error(str(error))
        self._sync_actions()

    def _download_finished(self, count):
        self.message_showmessage(f'Download complete ({count} bytes).\n')
        self._sync_actions()

    def open_downloader(self):
        if self.downloader_window is None:
            from .downloader import DownloaderWindow
            self.downloader_window = DownloaderWindow(self)
        self.downloader_window.show()
        self.downloader_window.raise_()
        self.downloader_window.activateWindow()
        return self.downloader_window

    def about(self):
        QMessageBox.about(self, '关于', '简单IDE v1.0\n\n一个基于PyQt的简单集成开发环境。\n\n作者: Moon')

    def closeEvent(self, event):
        if not self._closing and not self._confirm_all_documents():
            event.ignore()
            return
        if not self._closing and self.downloader_window is not None and not self.downloader_window.close():
            event.ignore()
            return
        self._run_timer.stop()
        self._cancel_compilation()
        if self._compile_threads:
            self._closing = True
            self.centralWidget().setEnabled(False)
            self.menuBar().setEnabled(False)
            for toolbar in self.findChildren(QToolBar):
                toolbar.setEnabled(False)
            self._sync_actions()
            event.ignore()
            return
        self._closing = False
        self.serial_transport.close()
        self.serial_dialog.close()
        for editor in list(self._documents):
            self._remove_document(editor)
        event.accept()
