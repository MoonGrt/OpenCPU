"""One editable assembly/image document with synchronized text and table views."""
from pathlib import Path
import re

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QSplitter, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

from ..core.disassembler import Disassembler
from ..core.image import parse_binary
from ..core.isa import OPCODES
from ..core.toolchain import Toolchain
from .documents import Document


class AssemblyTab(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent=None, document=None):
        super().__init__(parent)
        self.document = document or Document(kind="assembly")
        self.toolchain = Toolchain()
        self.disassembler = Disassembler()
        self.text_mode = True
        self.error_message = ""
        self._syncing = False
        self._table_syncing = False
        self._editing_table = False
        self._draft_dirty = False
        self._last_editor = None
        self._saved_views = ("", "")
        layout = QVBoxLayout(self)
        self.splitter = QSplitter(Qt.Horizontal)
        self.editor_left = QTextEdit()
        self.editor_right = QTextEdit()
        for editor in (self.editor_left, self.editor_right):
            editor.setFont(QFont("Courier", 10))
            self.splitter.addWidget(editor)
        self.table_left = QTableWidget(0, 4)
        self.table_left.setHorizontalHeaderLabels(["instruction", "operand 1", "operand 2", "operand 3"])
        self.table_right = QTableWidget(0, 1)
        self.table_right.setHorizontalHeaderLabels(["16-bit machine word"])
        self.table_right.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_right.horizontalHeader().setStretchLastSection(True)
        for table in (self.table_left, self.table_right):
            self.splitter.addWidget(table)
            table.hide()
        layout.addWidget(self.splitter)
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #c62828;")
        self.error_label.hide()
        layout.addWidget(self.error_label)
        self.editor_left.textChanged.connect(self._assembly_changed)
        self.editor_right.textChanged.connect(self._binary_changed)
        self.table_left.itemChanged.connect(self._table_changed)
        QApplication.instance().focusChanged.connect(self._focus_changed)
        self.load_document(self.document)

    @property
    def dirty(self):
        return self.document.dirty or self._draft_dirty

    @property
    def title(self):
        title = self.document.title
        return title + ("*" if self.dirty and not title.endswith("*") else "")

    @property
    def binary(self):
        return self.editor_right.toPlainText()

    def _error(self, message=""):
        self.error_message = message
        self.error_label.setText(message)
        self.error_label.setVisible(bool(message))

    @staticmethod
    def _set_editor(editor, text):
        blocked = editor.blockSignals(True)
        try:
            editor.setPlainText(text)
        finally:
            editor.blockSignals(blocked)

    def _track_document(self):
        self.document.set_text(self.binary if self.document.kind == "binary" else self.editor_left.toPlainText())

    def _views(self):
        return self.editor_left.toPlainText(), self.binary

    def _focus_changed(self, _old, current):
        if current is not None and self.isAncestorOf(current):
            self._last_editor = current

    def load_document(self, document):
        self.document = document
        self._syncing = True
        try:
            if document.kind == "binary":
                self._set_editor(self.editor_right, document.text)
                try:
                    parse_binary(document.text)
                    self._set_editor(self.editor_left, self.disassembler.disassemble(document.text))
                    self._error()
                except ValueError as error:
                    self._set_editor(self.editor_left, "")
                    self._error(str(error))
            else:
                self._set_editor(self.editor_left, document.text)
                try:
                    self._set_editor(self.editor_right, self.toolchain.assemble(document.text).binary)
                    self._error()
                except ValueError as error:
                    self._set_editor(self.editor_right, "")
                    self._error(str(error))
            self._draft_dirty = False
            self._saved_views = self._views()
        finally:
            self._syncing = False
        if not self.text_mode:
            self._fill_assembly_table()
            self._fill_machine_table()
        self.changed.emit()

    def set_contents(self, assembly, binary, kind="assembly", saved=False):
        """Populate a newly generated view without reassembling raw words."""
        self._set_editor(self.editor_left, assembly)
        self._set_editor(self.editor_right, binary)
        self.document.kind = kind
        self._track_document()
        if saved:
            self.document.saved_text = self.document.text
            self._saved_views = self._views()
        self._draft_dirty = False
        self._error()
        if not self.text_mode:
            self._fill_assembly_table()
            self._fill_machine_table()
        self.changed.emit()

    def _assembly_changed(self):
        if self._syncing:
            return
        self._syncing = True
        try:
            generated = self.toolchain.assemble(self.editor_left.toPlainText()).binary
            try:
                unchanged = parse_binary(self.binary) == parse_binary(generated)
            except ValueError:
                unchanged = False
            if not unchanged:
                self._set_editor(self.editor_right, generated)
            self._error()
            self._draft_dirty = False
        except ValueError as error:
            self._set_editor(self.editor_right, "")
            self._error(str(error))
            self._draft_dirty = self._views() != self._saved_views
        finally:
            self._track_document()
            self._syncing = False
        if not self.text_mode:
            if not self._editing_table:
                self._fill_assembly_table()
            self._fill_machine_table()
        self.changed.emit()

    def _binary_changed(self):
        if self._syncing:
            return
        self._syncing = True
        try:
            words = parse_binary(self.binary)
            try:
                unchanged = self.toolchain.assemble(self.editor_left.toPlainText()).words == words
            except ValueError:
                unchanged = False
            if not unchanged:
                self._set_editor(self.editor_left, self.disassembler.disassemble(self.binary))
            self._error()
            self._draft_dirty = False
        except ValueError as error:
            self._set_editor(self.editor_left, "")
            self._error(str(error))
            self._draft_dirty = self._views() != self._saved_views
        finally:
            self._track_document()
            self._syncing = False
        if not self.text_mode:
            self._fill_assembly_table()
            self._fill_machine_table()
        self.changed.emit()

    def save(self, path=None):
        kind = self.document.kind
        if path is not None:
            suffix = Path(path).suffix.lower()
            if suffix == ".bin":
                kind = "binary"
            elif suffix in (".asm", ".s"):
                kind = "assembly"
        if kind == "binary":
            if self.error_message:
                raise ValueError(self.error_message)
            parse_binary(self.binary)
            text = self.binary
        else:
            text = self.editor_left.toPlainText()
            if self.error_message and not text and self.binary:
                raise ValueError("Correct the machine-code input before saving it as assembly")
        result = self.document.save(text=text, path=path)
        self.document.kind = kind
        self._draft_dirty = False
        self._saved_views = self._views()
        self.changed.emit()
        return result

    def discard_changes(self):
        self.document.set_text(self.document.saved_text)
        self.load_document(self.document)

    def _fill_machine_table(self):
        lines = self.binary.splitlines()
        self.table_right.setRowCount(len(lines))
        for row, text in enumerate(lines):
            self.table_right.setItem(row, 0, QTableWidgetItem(text))

    def _fill_assembly_table(self):
        self._table_syncing = True
        blocked = self.table_left.blockSignals(True)
        try:
            lines = self.editor_left.toPlainText().splitlines()
            self.table_left.clearContents()
            self.table_left.setRowCount(max(1, len(lines)))
            for row in range(self.table_left.rowCount()):
                line = lines[row] if row < len(lines) else ""
                fields = re.split(r"\s+", line.replace(",", " ").strip(), maxsplit=3) if line.strip() else []
                opcode = QComboBox()
                opcode.setEditable(True)
                opcode.addItems([""] + list(OPCODES) + ["nop", "call", "ret", "mov", "la", ".word"])
                opcode.setCurrentText(fields[0] if fields else "")
                self.table_left.setCellWidget(row, 0, opcode)
                for column in range(1, 4):
                    self.table_left.setItem(row, column, QTableWidgetItem(fields[column] if column < len(fields) else ""))
                opcode.currentTextChanged.connect(self._table_changed)
        finally:
            self.table_left.blockSignals(blocked)
            self._table_syncing = False

    def _table_changed(self, _value=None):
        if self._table_syncing:
            return
        lines = []
        for row in range(self.table_left.rowCount()):
            fields = []
            for column in range(4):
                widget = self.table_left.cellWidget(row, column)
                item = self.table_left.item(row, column)
                text = widget.currentText() if isinstance(widget, QComboBox) else item.text() if item else ""
                if text.strip():
                    fields.append(text.strip())
            lines.append(" ".join(fields))
        text = "\n".join(lines)
        if text == self.editor_left.toPlainText():
            return
        self._editing_table = True
        try:
            cursor = self.editor_left.textCursor()
            cursor.beginEditBlock()
            cursor.select(QTextCursor.Document)
            cursor.insertText(text)
            cursor.endEditBlock()
        finally:
            self._editing_table = False

    def toggle_mode(self):
        # Merely changing presentation must never rewrite a loaded image.
        if self.text_mode:
            self._fill_assembly_table()
            self._fill_machine_table()
        self.text_mode = not self.text_mode
        for editor in (self.editor_left, self.editor_right):
            editor.setVisible(self.text_mode)
        for table in (self.table_left, self.table_right):
            table.setVisible(not self.text_mode)
        self.changed.emit()

    def edit(self, operation):
        focused = QApplication.focusWidget()
        if focused is not None and self.isAncestorOf(focused):
            self._last_editor = focused
        target = self._last_editor
        if isinstance(target, (QTextEdit, QLineEdit)) and callable(getattr(target, operation, None)):
            getattr(target, operation)()
            return
        table = self.table_right if target is self.table_right or target is not None and self.table_right.isAncestorOf(target) else self.table_left
        if not self.text_mode and operation in ("copy", "cut"):
            rows = {}
            for index in table.selectedIndexes():
                widget = table.cellWidget(index.row(), index.column())
                item = table.item(index.row(), index.column())
                value = widget.currentText() if isinstance(widget, QComboBox) else item.text() if item else ""
                rows.setdefault(index.row(), {})[index.column()] = value
            QApplication.clipboard().setText("\n".join("\t".join(columns[key] for key in sorted(columns)) for _, columns in sorted(rows.items())))
            if operation == "cut" and table is self.table_left:
                self._table_syncing = True
                try:
                    for index in table.selectedIndexes():
                        self._set_table_value(index.row(), index.column(), "")
                finally:
                    self._table_syncing = False
                self._table_changed()
            return
        if not self.text_mode and operation == "paste":
            if table is self.table_right:
                return
            row, column = max(0, table.currentRow()), max(0, table.currentColumn())
            text = QApplication.clipboard().text()
            if "\t" not in text and column == 0:
                values = [re.split(r"\s+", line.replace(",", " ").strip(), maxsplit=3) for line in text.splitlines()]
            else:
                values = [line.split("\t") for line in text.splitlines()]
            self._table_syncing = True
            try:
                table.setRowCount(max(table.rowCount(), row + len(values)))
                for delta, fields in enumerate(values):
                    for offset, value in enumerate(fields):
                        if column + offset < 4:
                            self._set_table_value(row + delta, column + offset, value)
            finally:
                self._table_syncing = False
            self._table_changed()
            self._fill_assembly_table()
            return
        # Table edits are recorded as edit blocks in the assembly editor.
        getattr(self.editor_left, operation)()

    def _set_table_value(self, row, column, value):
        widget = self.table_left.cellWidget(row, column)
        if isinstance(widget, QComboBox):
            widget.setCurrentText(value)
        else:
            self.table_left.setItem(row, column, QTableWidgetItem(value))
