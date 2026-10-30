"""IDE document, build and execution controller for the retained window layout."""
import hashlib
import os
from pathlib import Path
import threading

from PyQt5.QtCore import QFileSystemWatcher, QThread, QTimer
from PyQt5.QtGui import QColor, QTextCursor
from PyQt5.QtWidgets import QAction, QActionGroup, QApplication, QDialog, QFileDialog, QInputDialog, QMainWindow, QMessageBox, QTableWidgetItem, QTextEdit, QToolBar

from ..core.disassembler import Disassembler
from ..core.simulator import Simulator
from ..core.toolchain import Toolchain
from .documents import Document
from .ide_ui import IDELayout
from .serial_dialog import SerialDialog
from ..transport.serial import SerialTransport


class _CompileWorker(QThread):
    """Only the toolchain runs here; widgets are updated by the owner thread."""

    def __init__(self, parent, toolchain, document, request_id, *, project=None, documents=(), llvm_bin_dir=None):
        super().__init__(parent)
        self.toolchain = toolchain
        self.document = document
        self.request_id = request_id
        self.revision = document.revision
        self.source = document.text
        self.backend = document.backend
        self.language = document.language
        self.source_name = str(document.path or ("untitled.c" if self.language == "c" else "untitled.ll"))
        self.project = project
        self.llvm_bin_dir = llvm_bin_dir
        self.snapshots = {item: (item.revision, item.text, item.path) for item in documents}
        self.buffers = {item.path: item.text for item in documents if item.path is not None}
        if self.language == 'c' and document.path is None:
            self.buffers[Path(self.source_name).resolve()] = self.source
        self.disk_snapshots = {}
        for name in parent._dependency_watcher.files():
            path = Path(name).resolve()
            try:
                self.disk_snapshots[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                pass
        self.cancel_event = threading.Event()
        self.result = None
        self.error = None

    def run(self):
        try:
            if self.project is not None:
                self.result = self.toolchain.compile_project(
                    self.project, buffers=self.buffers, llvm_bin_dir=self.llvm_bin_dir,
                    cancel_event=self.cancel_event,
                )
            else:
                self.result = self.toolchain.compile(
                    self.source, backend=self.backend, language=self.language,
                    source_name=self.source_name, llvm_bin_dir=self.llvm_bin_dir,
                    cancel_event=self.cancel_event,
                )
        except Exception as error:
            # An uncaught exception in a Qt worker would terminate the GUI.
            self.error = str(error)


class IDEWindow(QMainWindow, IDELayout):
    """One current document owns a build; edits and tab changes invalidate it."""

    RUN_BATCH_SIZE = 64
    RUN_STEP_LIMIT = 10000
    C_RUN_STEP_LIMIT = 200000

    def __init__(self, parent=None, *, transport=None, toolchain=None):
        super().__init__(parent)
        self.toolchain = toolchain or Toolchain()
        self.serial_transport = transport or SerialTransport(self)
        self.serial_dialog = SerialDialog(self)
        self.serial_settings = self.serial_dialog.settings()
        self.downloader_window = None
        self.build_result = None
        self.simulator = None
        self.simulation_dialog = None
        self._breakpoints = set()
        self._documents = {}
        self._focused_editor = None
        self._build_document = None
        self._compile_document = None
        self._compile_worker = None
        self._compile_threads = set()
        self._compile_request_id = 0
        self._project = None
        self._project_path = None
        self._llvm_bin_dir = None
        self._build_snapshots = {}
        self._build_overlay_paths = set()
        self._build_hashes = {}
        self._build_disk_hashes = {}
        self._dependency_watcher = QFileSystemWatcher(self)
        self._dependency_watcher.fileChanged.connect(self._dependency_changed)
        self._dependency_watcher.directoryChanged.connect(self._dependency_changed)
        self._closing = False
        self._steps_remaining = 0
        self._run_step_budget = self.RUN_STEP_LIMIT
        self._run_timer = QTimer(self)
        self._run_timer.setInterval(0)
        self._run_timer.timeout.connect(self._run_batch)
        self.setup_ui()
        self._setup_compiler_menu()
        self._setup_simulation_menu()
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
        for backend, label in (('simple', 'Simple (.oc)'), ('llvm', 'LLVM')):
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda _checked, name=backend: self.set_compiler_backend(name))
            self._backend_group.addAction(action)
            self.compiler_menu.addAction(action)
            self._backend_actions[backend] = action
        self.language_menu = tools.addMenu('LLVM input language')
        self._language_group = QActionGroup(self)
        self._language_actions = {}
        for language, label in (('c', 'C (.c)'), ('llvm-ir', 'LLVM IR (.ll)')):
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda _checked, name=language: self.set_compiler_language(name))
            self._language_group.addAction(action)
            self.language_menu.addAction(action)
            self._language_actions[language] = action
        self.llvm_tools_action = QAction('LLVM tool directory...', self)
        self.llvm_tools_action.triggered.connect(self.choose_llvm_bin_dir)
        tools.addAction(self.llvm_tools_action)
        file_menu = next(action.menu() for action in self.menuBar().actions() if action.text() == 'File')
        file_menu.addSeparator()
        self.open_project_action = QAction('Open C project...', self)
        self.open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(self.open_project_action)
        self.close_project_action = QAction('Close C project', self)
        self.close_project_action.triggered.connect(self.close_project)
        file_menu.addAction(self.close_project_action)

    def _setup_simulation_menu(self):
        run_menu = next(action.menu() for action in self.menuBar().actions() if action.text() == 'Run')
        run_menu.addSeparator()
        self.breakpoints_menu = run_menu.addMenu('PC breakpoints')
        self.toggle_breakpoint_action = QAction('Toggle current PC', self)
        self.toggle_breakpoint_action.setShortcut('F9')
        self.toggle_breakpoint_action.triggered.connect(self.toggle_breakpoint)
        self.breakpoints_menu.addAction(self.toggle_breakpoint_action)
        self.edit_breakpoints_action = QAction('Edit PC breakpoints...', self)
        self.edit_breakpoints_action.triggered.connect(self.edit_breakpoints)
        self.breakpoints_menu.addAction(self.edit_breakpoints_action)
        self.clear_breakpoints_action = QAction('Clear breakpoints', self)
        self.clear_breakpoints_action.triggered.connect(lambda: self.set_breakpoints(()))
        self.breakpoints_menu.addAction(self.clear_breakpoints_action)
        tools_menu = next(action.menu() for action in self.menuBar().actions() if action.text() == 'Tools')
        self.simulation_action = QAction('Simulation...', self)
        self.simulation_action.triggered.connect(self.open_simulation)
        tools_menu.addAction(self.simulation_action)

    def set_breakpoints(self, addresses):
        if self._closing or self.running or self.compiling:
            return False
        limit = self.simulator.rom_depth if self.simulator is not None else 1024
        points = set(addresses)
        if any(type(address) is not int or not 0 <= address < limit for address in points):
            raise ValueError(f'Breakpoint PCs must be word addresses in 0..{limit - 1}')
        self._breakpoints = points
        if self.simulator is not None:
            self.simulator.breakpoints = points.copy()
        self._refresh_execution()
        self._sync_actions()
        return True

    def toggle_breakpoint(self, _checked=False, *, pc=None):
        if self._closing or self.running or self.compiling or self.simulator is None:
            return False
        address = self.simulator.pc if pc is None else pc
        points = set(self.simulator.breakpoints)
        if address in points:
            points.remove(address)
        else:
            points.add(address)
        try:
            return self.set_breakpoints(points)
        except ValueError as error:
            self.message_showmessage(f'Breakpoint error: {error}\n')
            return False

    def edit_breakpoints(self, _checked=False):
        if self._closing or self.running or self.compiling:
            return False
        points = self.simulator.breakpoints if self.simulator is not None else self._breakpoints
        text, accepted = QInputDialog.getText(
            self, 'PC breakpoints', 'Word addresses, separated by spaces or commas (decimal or 0x hex):',
            text=', '.join(f'0x{address:04X}' for address in sorted(points)))
        if not accepted:
            return False
        try:
            addresses = [int(token, 0) for token in text.replace(',', ' ').split()]
            return self.set_breakpoints(addresses)
        except ValueError as error:
            self.message_showmessage(f'Breakpoint error: {error}\n')
            return False

    def open_simulation(self, _checked=False):
        if self._closing:
            return None
        if self.simulation_dialog is None:
            from .simulation_dialog import SimulationDialog
            self.simulation_dialog = SimulationDialog(self)
        self.simulation_dialog.refresh_state()
        self.simulation_dialog.show()
        self.simulation_dialog.raise_()
        self.simulation_dialog.activateWindow()
        return self.simulation_dialog

    def set_compiler_language(self, language):
        document = self.current_document
        if document is None or document.kind not in ('source', 'header'):
            return False
        revision = document.revision
        document.set_language(language)
        if document.revision != revision:
            self._invalidate_build()
        self._sync_actions()
        return True

    def choose_llvm_bin_dir(self):
        path = QFileDialog.getExistingDirectory(self, 'LLVM tool directory', str(self._llvm_bin_dir or ''))
        if path:
            self.set_llvm_bin_dir(path)

    def set_llvm_bin_dir(self, path):
        selected = Path(path).expanduser().resolve() if path else None
        if selected != self._llvm_bin_dir:
            self._llvm_bin_dir = selected
            self._invalidate_build()

    def open_project(self, _checked=False, *, path=None):
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, 'Open C project', '', 'OpenCPU project (*.opencpu.json);;JSON (*.json)')
        if not path:
            return False
        try:
            from ..core.compiler.llvm import CProject
            project = CProject.load(path)
        except (OSError, UnicodeError, ValueError, TypeError) as error:
            self.message_showmessage(f'Project error: {error}\n')
            return False
        self._invalidate_build()
        self._project = project
        self._project_path = Path(path).expanduser().resolve()
        self.setWindowTitle(f'IDE — {self._project_path.name}')
        opened = self.open_files(paths=project.sources)
        if opened:
            self.edit_area.setCurrentWidget(opened[0])
        self._watch_dependencies()
        self._sync_actions()
        self.message_showmessage(f'C project: {self._project_path}\n')
        return True

    def close_project(self, _checked=False):
        self._invalidate_build()
        self._project = self._project_path = None
        self.setWindowTitle('IDE')
        self._watch_dependencies()
        self._sync_actions()

    def _project_for_document(self, document):
        if self._project is None or document is None or document.path is None:
            return None
        if document.path in self._project.sources:
            return self._project
        roots = [*self._project.include_dirs, self._project_path.parent]
        if document.kind == 'header' and any(document.path.is_relative_to(root) for root in roots):
            return self._project
        return None

    def set_compiler_backend(self, backend):
        document = self.current_document
        if document is None or document.kind not in ('source', 'header'):
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

    def new_file(self, _checked=False, *, text='', kind='source', backend=None, language=None):
        document = Document(kind=kind, backend=backend, language=language)
        if language in ('c', 'llvm-ir'):
            document.set_language(language)
        document.set_text(text)
        return self._add_document(document)

    def open_files(self, _checked=False, *, paths=None):
        if paths is None:
            paths, _ = QFileDialog.getOpenFileNames(
                self, 'Open Files', '', 'OpenCPU files (*.c *.h *.oc *.ll *.asm *.s *.bin *.txt *.opencpu.json);;All Files (*)', options=QFileDialog.Options())
        opened = []
        for path in paths:
            try:
                if str(path).endswith('.opencpu.json'):
                    self.open_project(path=path)
                    continue
                resolved = Path(path).expanduser().resolve()
                existing = next((editor for editor, item in self._documents.items() if item.path == resolved), None)
                if existing is not None:
                    self.edit_area.setCurrentWidget(existing)
                    opened.append(existing)
                    continue
                suffix = Path(path).suffix.lower()
                kind = ('assembly' if suffix in ('.asm', '.s') else 'binary' if suffix == '.bin'
                        else 'header' if suffix == '.h' else 'source')
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
        if (document is self._build_document or document is self._compile_document
                or document in self._build_snapshots
                or self._compile_worker is not None and document in self._compile_worker.snapshots
                or self._project_path is not None and document.path == self._project_path):
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
        if document.revision != previous_revision and (document in (self._build_document, self._compile_document)
                or document in self._build_snapshots
                or self._compile_worker is not None and document in self._compile_worker.snapshots):
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
        document = self._documents.get(editor)
        if (document in (self._build_document, self._compile_document) or document in self._build_snapshots
                or self._compile_worker is not None and document in self._compile_worker.snapshots):
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

    @staticmethod
    def _snapshots_current(snapshots, documents):
        return all(item in documents and (item.revision, item.text, item.path) == snapshot
                   for item, snapshot in snapshots.items())

    @staticmethod
    def _hashes_current(hashes, overlay_paths):
        for name, expected in hashes.items():
            path = Path(name).resolve()
            if path in overlay_paths:
                continue
            try:
                if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                    return False
            except OSError:
                return False
        return True

    @classmethod
    def _disk_dependencies_current(cls, result, overlay_paths):
        return cls._hashes_current(getattr(result, 'dependency_hashes', {}), overlay_paths)

    def _ensure_build_current(self):
        if self.build_result is None:
            return False
        if (not self._snapshots_current(self._build_snapshots, self._documents.values())
                or not self._hashes_current(self._build_disk_hashes, set())
                or not self._hashes_current(self._build_hashes, self._build_overlay_paths)):
            self._invalidate_build()
            self.message_showmessage('Build dependencies changed; compile again before running or downloading.\n')
            return False
        return True

    def _watch_dependencies(self, extra=()):
        previous = self._dependency_watcher.files() + self._dependency_watcher.directories()
        if previous:
            self._dependency_watcher.removePaths(previous)
        files = {Path(item).resolve() for item in extra}
        roots = set()
        if self._project is not None:
            files.update(self._project.sources)
            files.add(self._project_path)
            roots.update(self._project.include_dirs)
            roots.update(path.parent for path in self._project.sources)
            roots.add(self._project_path.parent)
        document = self.current_document
        if document is not None and document.language == 'c' and document.path is not None:
            files.add(document.path)
            roots.add(document.path.parent)
        directories = set()
        for root in roots:
            if not root.is_dir():
                continue
            directories.add(root)
            for directory, children, names in os.walk(root):
                children[:] = [name for name in children if not name.startswith('.')
                               and name not in ('build', '__pycache__', 'thirdpartys', 'node_modules')]
                directories.add(Path(directory))
                files.update(Path(directory) / name for name in names
                             if Path(name).suffix.lower() in ('.h', '.c'))
        files.update(item.path for item in self._documents.values()
                     if item.path is not None and item.language == 'c')
        paths = [str(path) for path in files | directories if path.exists()]
        if paths:
            self._dependency_watcher.addPaths(paths)

    def _dependency_changed(self, _path):
        had_result = self.build_result is not None or self.compiling
        self._invalidate_build()
        self._watch_dependencies()
        if had_result:
            self.message_showmessage('Source, header or project configuration changed; compile again.\n')

    def _invalidate_build(self):
        self._run_timer.stop()
        self._cancel_compilation()
        had_build = self.build_result is not None
        self.build_result = None
        self._build_document = None
        self._build_snapshots = {}
        self._build_overlay_paths = set()
        self._build_hashes = {}
        self._build_disk_hashes = {}
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
        if document.kind in ('source', 'header') and document.backend == 'llvm':
            project = None
            if document.language == 'c':
                try:
                    from ..core.compiler.llvm import CProject
                    if self._project_path is not None:
                        config = next((item for item in self._documents.values() if item.path == self._project_path), None)
                        if config is not None and config.dirty:
                            raise ValueError('Save the project manifest before building')
                        self._project = CProject.load(self._project_path)
                    project = self._project_for_document(document)
                    if project is None:
                        if document.kind == 'header':
                            raise ValueError('Open a C project to build a header document')
                        if document.path is None or document.path.suffix.lower() == '.c':
                            project = CProject(sources=(document.path or Path('untitled.c').resolve(),))
                except (OSError, ValueError, TypeError) as error:
                    self.message_showmessage(f'Project error: {error}\n')
                    return False
            snapshots = (tuple(item for item in self._documents.values() if item.language == 'c')
                         if document.language == 'c' else (document,))
            self._watch_dependencies()
            worker = _CompileWorker(self, self.toolchain, document, self._compile_request_id,
                                    project=project, documents=snapshots, llvm_bin_dir=self._llvm_bin_dir)
            self._compile_worker = worker
            self._compile_document = document
            self._compile_threads.add(worker)
            worker.finished.connect(self._compile_finished)
            self.message_showmessage(f'LLVM {"C" if document.language == "c" else "IR"}: compiling...\n')
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
            and worker.language == worker.document.language
            and self._snapshots_current(worker.snapshots, self._documents.values())
            and self._hashes_current(worker.disk_snapshots, set())
            and (worker.result is None or self._disk_dependencies_current(worker.result, set(worker.buffers)))
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
                self._apply_build(worker.document, worker.result, snapshots=worker.snapshots,
                                  overlay_paths=set(worker.buffers), disk_snapshots=worker.disk_snapshots)
        worker.deleteLater()
        self._sync_actions()
        if self._closing and not self._compile_threads:
            QTimer.singleShot(0, self.close)

    def _apply_build(self, document, result, *, snapshots=None, overlay_paths=(), disk_snapshots=None):
        self.build_result = result
        self._build_document = document
        self._build_snapshots = snapshots or {document: (document.revision, document.text, document.path)}
        self._build_overlay_paths = set(overlay_paths)
        self._build_disk_hashes = dict(disk_snapshots or {})
        self._build_hashes = dict(getattr(result, 'dependency_hashes', {}))
        self._watch_dependencies(getattr(result, 'dependencies', ()))
        self.simulator = Simulator(getattr(result, 'entry_pc', 0))
        self.simulator.inst_mem = list(result.words)
        self.simulator.breakpoints = self._breakpoints.copy()
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
        self.simulation_action.setEnabled(not self._closing)
        self.breakpoints_menu.setEnabled(not self._closing and not active and not compiling)
        self.toggle_breakpoint_action.setEnabled(built and not active and not compiling)
        points = self.simulator.breakpoints if self.simulator is not None and hasattr(self.simulator, 'breakpoints') else self._breakpoints
        self.clear_breakpoints_action.setEnabled(bool(points) and not active and not compiling)
        if self.simulation_dialog is not None:
            self.simulation_dialog.sync_controls()
        document = self.current_document
        source = document is not None and document.kind in ('source', 'header') and not self._closing
        self.compiler_menu.setEnabled(source)
        self.language_menu.setEnabled(source and document.backend == 'llvm')
        self.close_project_action.setEnabled(self._project is not None and not self._closing)
        for backend, action in self._backend_actions.items():
            action.setChecked(document is not None and document.backend == backend)
        for language, action in self._language_actions.items():
            action.setChecked(document is not None and document.backend == 'llvm' and document.language == language)

    def run(self, _checked=False):
        if self._closing or not self._ensure_build_current() or self.simulator is None or self.simulator.halted or self.simulator.faulted or self.running:
            return
        self._run_step_budget = (self.C_RUN_STEP_LIMIT if getattr(self.build_result, 'language', '') == 'c'
                                 else self.RUN_STEP_LIMIT)
        self._steps_remaining = self._run_step_budget
        self._run_timer.start()
        self._sync_actions()

    def _run_batch(self):
        if not self._ensure_build_current():
            self._run_timer.stop()
            return
        model = self.simulator
        if model is None:
            self._run_timer.stop()
            self._sync_actions()
            return
        count = model.run(min(self.RUN_BATCH_SIZE, self._steps_remaining))
        self._steps_remaining -= count
        reason = model.stop_reason
        finished = reason in ('halt', 'fault', 'stopped', 'breakpoint') or self._steps_remaining == 0
        if finished:
            self._run_timer.stop()
            if model.faulted:
                self._show_execution_fault()
            elif reason == 'breakpoint':
                self.message_showmessage(f'Breakpoint at PC=0x{model.breakpoint_hit:04X}; Run continues, Step executes this instruction.\n')
            elif self._steps_remaining == 0 and not model.halted and not model.faulted:
                model.limit_reached = True
                model.stop_reason = 'limit'
                self.message_showmessage(
                    f'Step limit reached ({self._run_step_budget} instructions); '
                    'Run continues from the current instruction.\n')
            elif model.halted:
                self.message_showmessage('HALT\n')
        elif reason == 'limit':
            # This is a scheduling batch boundary, not the user's run budget.
            model.limit_reached = False
            model.stop_reason = None
        self._refresh_execution()
        self._sync_actions()

    def run_step(self, _checked=False):
        if self._closing or not self._ensure_build_current() or self.simulator is None or self.running:
            return
        self.simulator.stopped = False
        self.simulator.step()
        self._refresh_execution()
        self._sync_actions()
        if self.simulator.faulted:
            self._show_execution_fault()

    def _show_execution_fault(self):
        model = self.simulator
        details = []
        if model.fault_pc is not None:
            details.append(f'PC=0x{model.fault_pc:04X}')
        if model.fault_inst is not None:
            details.append(f'instruction=0x{model.fault_inst:04X}')
        if model.fault_code is not None:
            details.append(f'code={model.fault_code}')
        context = f' ({", ".join(details)})' if details else ''
        self.message_showmessage(f'Execution fault: {model.fault_reason}{context}\n')

    def run_undo(self, _checked=False):
        if self._closing or not self._ensure_build_current() or self.simulator is None or self.running:
            return
        self.simulator.run_undo()
        self._refresh_execution()
        self._sync_actions()

    def reset(self, _checked=False):
        if self._closing or not self._ensure_build_current() or self.simulator is None:
            return
        self._run_timer.stop()
        points = self.simulator.breakpoints.copy()
        self.simulator.reset()
        self.simulator.breakpoints = points
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
        data = dict(self.simulator.data_mem)
        data.update((address, self.simulator.peek_data(address)) for address in range(0xff00, 0xff60))
        self.fill_data(data)
        if self.simulation_dialog is not None:
            self.simulation_dialog.refresh_state()
        for row in range(self.code_table.rowCount()):
            address = int(self.code_table.item(row, 0).text()) if self.code_table.item(row, 0) else -1
            marked = address in self.simulator.breakpoints
            self.set_row_background(self.code_table, row, QColor(255, 223, 128) if marked else None)
            if self.code_table.item(row, 0) is not None:
                self.code_table.item(row, 0).setToolTip('PC breakpoint' if marked else '')
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
        if self._closing or self.compiling or not self._ensure_build_current() or self.current_document is not self._build_document:
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
        if self.simulation_dialog is not None:
            self.simulation_dialog.close()
        for editor in list(self._documents):
            self._remove_document(editor)
        event.accept()
