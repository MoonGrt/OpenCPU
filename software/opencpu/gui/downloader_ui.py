"""Downloader widget construction; controllers contain no layout definitions."""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QHBoxLayout, QPushButton, QSplitter, QTabBar, QTabWidget, QTextEdit, QVBoxLayout, QWidget

from .resources import icon


class DownloaderUI:
    def setup(self, window):
        window.setWindowIcon(icon("app.svg"))
        window.resize(900, 800)
        window.setWindowTitle("Downloader")
        self._menus(window)
        main_widget = QWidget(window)
        window.setCentralWidget(main_widget)
        window.splitter = QSplitter(main_widget)
        window.file_pane = QTabWidget(window.splitter)
        window.messages_pane = QTabWidget(window.splitter)
        window.serial_tab = QTextEdit()
        window.messages_pane.addTab(window.serial_tab, "Serial")
        buttons = QHBoxLayout()
        for name, resource, callback in (
            ("serial_settings_button", "setting.svg", window.serial_settings),
            ("serial_connect_button", "connect.svg", window.serial_connect),
            ("serial_disconnect_button", "disconnect.svg", window.serial_disconnect),
            ("serial_clear_button", "clear.svg", window.serial_clear),
        ):
            button = QPushButton(QIcon(icon(resource).pixmap(15, 15)), "")
            button.setFlat(True)
            button.setFixedSize(22, 22)
            button.clicked.connect(callback)
            buttons.addWidget(button)
            setattr(window, name, button)
        window.serial_disconnect_button.setEnabled(False)
        buttons.setContentsMargins(0, 3, 0, 3)
        container = QWidget()
        container.setLayout(buttons)
        window.messages_pane.tabBar().setTabButton(0, QTabBar.RightSide, container)
        layout = QVBoxLayout(main_widget)
        layout.addWidget(window.splitter)
        window.splitter.setOrientation(Qt.Vertical)
        window.splitter.setSizes([250, 100])

    @staticmethod
    def _action(window, text, callback, resource=None):
        action = QAction(icon(resource), text, window) if resource else QAction(text, window)
        action.setToolTip(text)
        action.triggered.connect(callback)
        return action

    def _menus(self, window):
        file_menu = window.menuBar().addMenu("File")
        edit_menu = window.menuBar().addMenu("Edit")
        run_menu = window.menuBar().addMenu("Run")
        specifications = (
            ("new_action", "New", window.new_file, "new.svg"),
            ("open_action", "Open", window.open_files, "open.svg"),
            ("close_action", "Close", window.close_file, "close.svg"),
            ("close_all_action", "Close All", window.close_all_files, None),
            ("save_action", "Save", window.save_file, "save.svg"),
            ("save_as_action", "Save As...", window.save_as, None),
            ("save_all_action", "Save All", window.save_all_files, None),
            ("exit_action", "Exit", window.close, "exit.svg"),
        )
        for index, (name, text, callback, resource) in enumerate(specifications):
            if index in (4, 7):
                file_menu.addSeparator()
            action = self._action(window, text, callback, resource)
            setattr(window, name, action)
            file_menu.addAction(action)
        for index, (name, text, resource, operation) in enumerate((
            ("undo_action", "Undo", "undo.svg", "undo"),
            ("redo_action", "Redo", "redo.svg", "redo"),
            ("cut_action", "Cut", "cut.svg", "cut"),
            ("copy_action", "Copy", "copy.svg", "copy"),
            ("paste_action", "Paste", "paste.svg", "paste"),
        )):
            if index == 2:
                edit_menu.addSeparator()
            action = self._action(window, text, lambda _checked=False, op=operation: window.edit(op), resource)
            setattr(window, name, action)
            edit_menu.addAction(action)
        edit_menu.addSeparator()
        window.mode_action = self._action(window, "Mode", window.toggle_mode, "mode.svg")
        edit_menu.addAction(window.mode_action)
        window.download_action = self._action(window, "Download", window.download, "download.svg")
        window.download_action.setEnabled(False)
        run_menu.addAction(window.download_action)
        for title, names in (
            ("Toolbar1", ("new_action", "open_action", "close_action", "save_action")),
            ("Toolbar2", ("undo_action", "redo_action", "cut_action", "copy_action", "paste_action", "mode_action")),
            ("Toolbar3", ("download_action",)),
        ):
            toolbar = window.addToolBar(title)
            for name in names:
                toolbar.addAction(getattr(window, name))
