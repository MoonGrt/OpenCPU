"""Standalone and IDE-owned downloader controller using shared services."""
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QDialog, QFileDialog, QMainWindow, QMessageBox

from ..core.image import parse_binary
from .assembly_tab import AssemblyTab
from .documents import Document
from .downloader_ui import DownloaderUI
from .serial_dialog import SerialDialog
from ..transport.serial import SerialTransport


class DownloaderWindow(QMainWindow):
    def __init__(self, parent=None, transport=None):
        super().__init__(parent, Qt.Window)
        self.transport = transport if transport is not None else SerialTransport(self)
        self.serial_dialog = SerialDialog(self)
        DownloaderUI().setup(self)
        self.file_pane.currentChanged.connect(self._update_actions)
        self.transport.received.connect(self._received)
        self.transport.connection_changed.connect(self._connection_changed)
        self.transport.error.connect(self._serial_error)
        self.transport.download_finished.connect(self._download_finished)
        self.transport.progress.connect(lambda _sent, _total: self._update_actions())
        self._update_actions()

    @property
    def current_tab(self):
        tab = self.file_pane.currentWidget()
        return tab if isinstance(tab, AssemblyTab) else None

    def _add_tab(self, tab):
        self.file_pane.addTab(tab, tab.title)
        tab.changed.connect(lambda: self._tab_changed(tab))
        self.file_pane.setCurrentWidget(tab)
        self._update_actions()
        return tab

    def new_file(self):
        return self._add_tab(AssemblyTab(self))

    def open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Open Files", "", "All Files (*)", options=QFileDialog.Options())
        for path in paths:
            self.open_file(path)

    def open_file(self, path):
        try:
            document = Document.open(path, kind="assembly")
            compact = "".join(document.text.split())
            if document.path.suffix.lower() == ".bin" or compact and set(compact) <= {"0", "1"}:
                document.kind = "binary"
            return self._add_tab(AssemblyTab(self, document=document))
        except (OSError, UnicodeError, ValueError) as error:
            self.log(f"Open error: {error}\n")
            return None

    def _tab_changed(self, tab):
        index = self.file_pane.indexOf(tab)
        if index >= 0:
            self.file_pane.setTabText(index, tab.title)
        self._update_actions()

    def _save_tab(self, tab, save_as=False):
        if tab is None:
            return False
        path = None
        if save_as or tab.document.path is None:
            path, _ = QFileDialog.getSaveFileName(self, "Save", str(tab.document.path or ""), "All Files (*)", options=QFileDialog.Options())
            if not path:
                return False
        try:
            tab.save(path=path)
            self._tab_changed(tab)
            return True
        except (OSError, UnicodeError, ValueError) as error:
            self.log(f"Save error: {error}\n")
            return False

    def save_file(self):
        return self._save_tab(self.current_tab)

    def save_as(self):
        return self._save_tab(self.current_tab, save_as=True)

    def save_all_files(self):
        selected = self.file_pane.currentWidget()
        for index in range(self.file_pane.count()):
            tab = self.file_pane.widget(index)
            self.file_pane.setCurrentWidget(tab)
            if not self._save_tab(tab):
                if selected:
                    self.file_pane.setCurrentWidget(selected)
                return False
        if selected:
            self.file_pane.setCurrentWidget(selected)
        return True

    def _confirm_close(self, tab, discarded=None):
        if not tab.dirty:
            return True
        answer = QMessageBox.question(self, "Unsaved changes", f"Save changes to {tab.document.path or 'Untitled'}?",
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
        if answer == QMessageBox.Cancel:
            return False
        if answer == QMessageBox.Save:
            return self._save_tab(tab)
        if discarded is not None:
            discarded.append(tab)
        return True

    def close_file(self):
        tab = self.current_tab
        if tab is None or not self._confirm_close(tab):
            return False
        self.file_pane.removeTab(self.file_pane.indexOf(tab))
        tab.deleteLater()
        return True

    def close_all_files(self):
        tabs = [self.file_pane.widget(index) for index in range(self.file_pane.count())]
        if not all(self._confirm_close(tab) for tab in tabs):
            return False
        for tab in tabs:
            self.file_pane.removeTab(self.file_pane.indexOf(tab))
            tab.deleteLater()
        return True

    def edit(self, operation):
        if self.current_tab:
            self.current_tab.edit(operation)

    def toggle_mode(self):
        if self.current_tab:
            self.current_tab.toggle_mode()

    def _update_actions(self, *_args):
        tab = self.current_tab
        valid = False
        if tab is not None and not tab.error_message:
            try:
                valid = bool(parse_binary(tab.binary))
            except ValueError:
                pass
        self.download_action.setEnabled(valid and self.transport.is_open and not self.transport.busy)
        self.serial_connect_button.setEnabled(not self.transport.is_open and not self.transport.busy)
        self.serial_disconnect_button.setEnabled(self.transport.is_open)

    def download(self):
        tab = self.current_tab
        if tab is None:
            return False
        if tab.error_message:
            self.log(f"Download error: {tab.error_message}\n")
            return False
        try:
            self.transport.download(tab.binary)
            self._update_actions()
            return True
        except (ValueError, RuntimeError, OSError) as error:
            self.log(f"Download error: {error}\n")
            self._update_actions()
            return False

    def log(self, message):
        self.serial_tab.moveCursor(QTextCursor.End)
        self.serial_tab.insertPlainText(message)
        self.serial_tab.moveCursor(QTextCursor.End)

    def serial_settings(self):
        return self.serial_dialog.exec_() == QDialog.Accepted

    def serial_connect(self):
        try:
            opened = self.transport.open(self.serial_dialog.settings())
            if opened:
                self.log("Port open successful\n")
        except (ValueError, RuntimeError, OSError) as error:
            self.log(f"Port open error: {error}\n")
            opened = False
        self._update_actions()
        return opened

    def serial_disconnect(self):
        self.transport.close()
        self.log("Port closed\n")
        self._update_actions()

    def serial_clear(self):
        self.serial_tab.clear()

    def _received(self, data):
        self.log(data.hex())

    def _connection_changed(self, _opened):
        self._update_actions()

    def _serial_error(self, message):
        self.log(f"Serial error: {message}\n")
        self._update_actions()

    def _download_finished(self, count):
        self.log(f"Download complete: {count} bytes\n")
        self._update_actions()

    def closeEvent(self, event):
        discarded = []
        for index in range(self.file_pane.count()):
            if not self._confirm_close(self.file_pane.widget(index), discarded):
                event.ignore()
                return
        for tab in discarded:
            tab.discard_changes()
        self.transport.close()
        self.serial_dialog.close()
        self._update_actions()
        event.accept()
