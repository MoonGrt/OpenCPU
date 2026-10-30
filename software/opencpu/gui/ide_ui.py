"""Unchanged IDE window layout, separated from document and execution behavior."""
from PyQt5.QtWidgets import (
    QAction, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSplitter, QTabBar,
    QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIcon, QTransform
from .resources import icon

class IDELayout:
    def setup_ui(self):
        self.setWindowIcon(icon("app.svg"))

        self.setGeometry(200, 200, 1600, 900)
        self.setWindowTitle('IDE')
        self.setWindowState(self.windowState() | Qt.WindowMaximized)
        
        menubar = self.menuBar()

        file_Menu = menubar.addMenu('File')

        new_Action = QAction(icon("new.svg"), 'New', self) # 新建文件
        new_Action.setToolTip('New')
        new_Action.setShortcut('Ctrl+N') # 设置快捷键
        new_Action.triggered.connect(self.new_file)
        file_Menu.addAction(new_Action)

        open_Action = QAction(icon("open.svg"), 'Open', self) # 打开动作
        open_Action.setToolTip('Open')
        open_Action.setShortcut('Ctrl+O')  # 设置快捷键
        open_Action.triggered.connect(self.open_files)
        file_Menu.addAction(open_Action)

        close_Action = QAction(icon("close.svg"), 'Close', self) # 关闭动作
        close_Action.setToolTip('Close')
        close_Action.setShortcut('Ctrl+W') # 设置快捷键
        close_Action.triggered.connect(self.close_file)
        file_Menu.addAction(close_Action)

        closeall_Action = QAction('Close All', self) # 关闭所有动作
        closeall_Action.triggered.connect(self.close_all_files)
        file_Menu.addAction(closeall_Action)

        file_Menu.addSeparator()  # 分隔线

        save_Action = QAction(icon("save.svg"), 'Save', self) # 保存动作
        save_Action.setToolTip('Save')
        save_Action.setShortcut('Ctrl+S')  # 设置快捷键
        save_Action.triggered.connect(self.save_file)
        file_Menu.addAction(save_Action)

        saveas_Action = QAction('Save As...', self) # 另存动作
        saveas_Action.triggered.connect(self.save_as)
        file_Menu.addAction(saveas_Action)

        saveall_Action = QAction('Save All', self) # 全部保存
        saveall_Action.triggered.connect(self.save_all_files)
        file_Menu.addAction(saveall_Action)

        file_Menu.addSeparator()  # 分隔线

        exit_Action = QAction(icon("exit.svg"), 'Exit', self) # 退出动作
        exit_Action.setToolTip('Exit')
        exit_Action.setShortcut('Ctrl+Q')  # 设置快捷键
        exit_Action.triggered.connect(self.close)
        file_Menu.addAction(exit_Action)

        edit_Menu = menubar.addMenu('Edit')

        undo_Action = QAction(icon("undo.svg"), 'Undo', self) # 撤销操作
        undo_Action.setToolTip('Undo')
        undo_Action.setShortcut('Ctrl+Z')  # 设置快捷键
        undo_Action.triggered.connect(self.undo)
        edit_Menu.addAction(undo_Action)

        redo_Action = QAction(icon("redo.svg"), 'Redo', self) # 重做操作
        redo_Action.setToolTip('Redo')
        redo_Action.setShortcut('Ctrl+Y')  # 设置快捷键
        redo_Action.triggered.connect(self.redo)
        edit_Menu.addAction(redo_Action)

        edit_Menu.addSeparator()  # 分隔线

        cut_Action = QAction(icon("cut.svg"), 'Cut', self) # 剪切操作
        cut_Action.setToolTip('Cut')
        cut_Action.setShortcut('Ctrl+X')  # 设置快捷键
        cut_Action.triggered.connect(self.cut)
        edit_Menu.addAction(cut_Action)
        
        copy_Action = QAction(icon("copy.svg"), 'Copy', self) # 复制操作
        copy_Action.setToolTip('Copy')
        copy_Action.setShortcut('Ctrl+C')  # 设置快捷键
        copy_Action.triggered.connect(self.copy)
        edit_Menu.addAction(copy_Action)

        paste_Action = QAction(icon("paste.svg"), 'Paste', self) # 粘贴操作
        paste_Action.setToolTip('Paste')
        paste_Action.setShortcut('Ctrl+V')  # 设置快捷键
        paste_Action.triggered.connect(self.paste)
        edit_Menu.addAction(paste_Action)

        run_Menu = menubar.addMenu('Run')

        assemble_Action = QAction(icon("assemble.svg"), 'Assemble', self) # 编译
        assemble_Action.setToolTip('Assemble')
        assemble_Action.triggered.connect(self.assemble)
        run_Menu.addAction(assemble_Action)

        self.run_action = QAction(icon("run.svg"), 'Run', self) # 运行代码
        self.run_action.setToolTip('Run')
        self.run_action.triggered.connect(self.run)
        self.run_action.setEnabled(False)
        run_Menu.addAction(self.run_action)

        self.run_step_action = QAction(QIcon(icon("run_step.svg").pixmap(22, 22)), 'Run step', self) # 单步运行
        self.run_step_action.setToolTip('Run step')
        self.run_step_action.triggered.connect(self.run_step)
        self.run_step_action.setEnabled(False)
        run_Menu.addAction(self.run_step_action)

        self.run_undo_action = QAction(QIcon(icon("run_step.svg").pixmap(22, 22).transformed(QTransform().scale(-1, 1))), 'Run undo', self) # 单步退回
        self.run_undo_action.setToolTip('Run undo')
        self.run_undo_action.triggered.connect(self.run_undo)
        self.run_undo_action.setEnabled(False)
        run_Menu.addAction(self.run_undo_action)

        self.reset_action = QAction(icon("reset.svg"), 'Reset', self) # 重启
        self.reset_action.setToolTip('Reset')
        self.reset_action.triggered.connect(self.reset)
        self.reset_action.setEnabled(False)
        run_Menu.addAction(self.reset_action)

        self.stop_action = QAction(icon("stop.svg"), 'Stop', self) # 停止运行
        self.stop_action.setToolTip('Stop')
        self.stop_action.triggered.connect(self.stop)
        self.stop_action.setEnabled(False)
        run_Menu.addAction(self.stop_action)

        self.download_action = QAction(icon("download.svg"), 'Download', self) # 烧录
        self.download_action.setToolTip('Download')
        self.download_action.triggered.connect(self.download)
        self.download_action.setEnabled(False)
        run_Menu.addAction(self.download_action)

        tools_menu = menubar.addMenu('Tools')
        self.downloader_window_action = QAction('Downloader', self)
        self.downloader_window_action.triggered.connect(self.open_downloader)
        tools_menu.addAction(self.downloader_window_action)

        help_Menu = menubar.addMenu('Help')

        about_Action = QAction('About', self) # 关于
        about_Action.setToolTip('About')
        about_Action.triggered.connect(self.about)
        help_Menu.addAction(about_Action)

        toolbar1 = self.addToolBar('Toolbar1')
        toolbar1.addAction(new_Action)
        toolbar1.addAction(open_Action)
        toolbar1.addAction(close_Action)
        toolbar1.addAction(save_Action)

        toolbar2 = self.addToolBar('Toolbar2')
        toolbar2.addAction(undo_Action)
        toolbar2.addAction(redo_Action)
        toolbar2.addAction(cut_Action)
        toolbar2.addAction(copy_Action)
        toolbar2.addAction(paste_Action)

        toolbar3 = self.addToolBar('Toolbar3')
        toolbar3.addAction(assemble_Action)
        toolbar3.addAction(self.run_action)
        toolbar3.addAction(self.run_step_action)
        toolbar3.addAction(self.run_undo_action)
        toolbar3.addAction(self.reset_action)
        toolbar3.addAction(self.stop_action)
        toolbar3.addAction(self.download_action)

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        splitter = QSplitter(main_widget)

        main_pane = QTabWidget(splitter)
        file_tab = QWidget()
        execute_tab = QWidget()
        main_pane.addTab(file_tab, "File")
        main_pane.addTab(execute_tab, "Execute")

        file_tab_layout = QHBoxLayout(file_tab)

        self.edit_area = QTabWidget(file_tab)
        file_tab_layout.addWidget(self.edit_area, stretch=4)

        compile_result_layout = QVBoxLayout() # 创建垂直布局
        self.assemble_code_area = QTextEdit()
        self.machine_code_area = QTextEdit()
        self.assemble_code_area.setReadOnly(True)
        self.machine_code_area.setReadOnly(True)
        compile_result_layout.addWidget(self.assemble_code_area)
        compile_result_layout.addWidget(self.machine_code_area)

        file_tab_layout.addLayout(compile_result_layout, stretch=1)

        execute_layout = QGridLayout(execute_tab)

        self.code_table = QTableWidget(32, 4)
        self.label_table = QTableWidget(8, 2)
        self.data_table = QTableWidget(32, 9)
        self.register_table = QTableWidget(8, 3)

        self.initialize_tables()
        
        text_label = QLabel(" Text")
        label_label = QLabel(" Label")
        data_label = QLabel(" Data")
        register_label = QLabel(" Register")

        execute_layout.addWidget(text_label, 0, 0)
        execute_layout.addWidget(self.code_table, 1, 0)
        execute_layout.addWidget(label_label, 0, 1)
        execute_layout.addWidget(self.label_table, 1, 1)
        execute_layout.addWidget(data_label, 2, 0)
        execute_layout.addWidget(self.data_table, 3, 0)
        execute_layout.addWidget(register_label, 2, 1)
        execute_layout.addWidget(self.register_table, 3, 1)

        execute_layout.setRowStretch(0, 1)    # 设置第一行的伸展因子
        execute_layout.setRowStretch(1, 10)   # 设置第二行的伸展因子
        execute_layout.setRowStretch(2, 1)    # 设置第三行的伸展因子
        execute_layout.setRowStretch(3, 10)   # 设置第四行的伸展因子
        execute_layout.setColumnStretch(0, 3) # 设置第一列的伸展因子
        execute_layout.setColumnStretch(1, 1) # 设置第二列的伸展因子

        messages_pane = QTabWidget(splitter)
        self.message_tab = QTextEdit()
        self.serial_tab = QTextEdit()
        messages_pane.addTab(self.message_tab, "Message  ")
        messages_pane.addTab(self.serial_tab, "Serial  ")

        message_clear_bottom = QPushButton(QIcon(icon("clear.svg").pixmap(15, 15)), '')
        message_clear_bottom.setFlat(True)
        message_clear_bottom.setFixedHeight(22)
        message_clear_bottom.setFixedWidth(22)
        message_clear_bottom.clicked.connect(self.message_clear)
        messages_pane.tabBar().setTabButton(0, QTabBar.RightSide, message_clear_bottom)

        button_layout = QHBoxLayout()
        
        serial_setting_bottom = QPushButton(QIcon(icon("setting.svg").pixmap(15, 15)), '')
        serial_setting_bottom.setFlat(True)
        serial_setting_bottom.setFixedHeight(22)
        serial_setting_bottom.setFixedWidth(22)
        serial_setting_bottom.clicked.connect(self.serial_setting)
        button_layout.addWidget(serial_setting_bottom)

        self.connect_button = QPushButton(QIcon(icon("connect.svg").pixmap(15, 15)), '')
        self.connect_button.setFlat(True)
        self.connect_button.setFixedHeight(22)
        self.connect_button.setFixedWidth(22)
        self.connect_button.clicked.connect(self.serial_connect)
        button_layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton(QIcon(icon("disconnect.svg").pixmap(15, 15)), '')
        self.disconnect_button.setFlat(True)
        self.disconnect_button.setFixedHeight(22)
        self.disconnect_button.setFixedWidth(22)
        self.disconnect_button.clicked.connect(self.serial_disconnect)
        self.disconnect_button.setEnabled(False)
        button_layout.addWidget(self.disconnect_button)

        serial_clear_bottom = QPushButton(QIcon(icon("clear.svg").pixmap(15, 15)), '')
        serial_clear_bottom.setFlat(True)
        serial_clear_bottom.setFixedHeight(22)
        serial_clear_bottom.setFixedWidth(22)
        serial_clear_bottom.clicked.connect(self.serial_clear)
        button_layout.addWidget(serial_clear_bottom)

        button_layout.setContentsMargins(0, 3, 0, 3)

        container = QWidget()
        container.setLayout(button_layout)
        messages_pane.tabBar().setTabButton(1, QTabBar.RightSide, container)

        splitter_layout = QVBoxLayout(main_widget)
        splitter_layout.addWidget(splitter)  # 将QSplitter添加到布局中
        main_widget.setLayout(splitter_layout)

        splitter.setOrientation(Qt.Vertical)
        splitter.setSizes([445, 100]) # 设置 edit_tab 和 execute_tab 的大小比例

    def initialize_tables(self):
        self.code_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.label_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.register_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.code_table.setHorizontalHeaderLabels(["Address", "Code", "Basic", "Source"])
        self.label_table.setHorizontalHeaderLabels(["Label", "Address"])
        self.data_table.setHorizontalHeaderLabels(["Address", "Value(+0)", "Value(+1)", "Value(+2)", "Value(+3)", "Value(+4)", "Value(+5)", "Value(+6)", "Value(+7)"])
        self.register_table.setHorizontalHeaderLabels(["Register", "Name", "Value"])

        self.code_table.verticalHeader().setVisible(False)
        self.label_table.verticalHeader().setVisible(False)
        self.data_table.verticalHeader().setVisible(False)
        self.register_table.verticalHeader().setVisible(False)

        self.set_column_widths(self.code_table, 9)
        self.set_column_widths(self.label_table, 8)
        self.set_column_widths(self.data_table, 8)
        self.set_column_widths(self.register_table, 8)

        self.set_row_heights()

        for row in range(self.code_table.rowCount()):
            for col in range(self.code_table.columnCount()):
                item = QTableWidgetItem('-')
                item.setTextAlignment(Qt.AlignCenter)
                self.code_table.setItem(row, col, item)

        for row in range(self.label_table.rowCount()):
            for col in range(self.label_table.columnCount()):
                item = QTableWidgetItem('-')
                item.setTextAlignment(Qt.AlignCenter)
                self.label_table.setItem(row, col, item)

        data_index = 0
        for row in range(self.data_table.rowCount()):
            for col in range(self.data_table.columnCount()):
                if col == 0:
                    address = "0x{:04X}".format(data_index*8)
                    item = QTableWidgetItem(address)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.data_table.setItem(row, col, item)
                    data_index += 1
                else:
                    item = QTableWidgetItem('0x0000')
                    item.setTextAlignment(Qt.AlignCenter)
                    self.data_table.setItem(row, col, item)

        register_init = [
            ["r0", "zero", "0x0000"],
            ["r1", "a1", "0x0000"],
            ["r2", "a2", "0x0000"],
            ["r3", "a3", "0x0000"],
            ["r4", "a4", "0x0000"],
            ["r5", "fp", "0x0000"],
            ["r6", "ra", "0x0000"],
            ["r7", "sp", "0x0000"],
        ]
        for row in range(self.register_table.rowCount()):
            for col in range(self.register_table.columnCount()):
                item = QTableWidgetItem(register_init[row][col])
                item.setTextAlignment(Qt.AlignCenter)
                self.register_table.setItem(row, col, item)

        for tabel in [self.code_table, self.label_table, self.data_table, self.register_table]:
            for row in range(self.code_table.rowCount()):
                self.set_row_background(tabel, row, None)

    def set_row_background(self, tabel, row, color):
        if row % 2 == 0:
            for col in range(tabel.columnCount()):
                item = tabel.item(row, col)
                if item is not None:
                    if color:
                        item.setBackground(color)
                    else:
                        item.setBackground(QColor(220, 220, 220)) # Light gray
        else:
            for col in range(tabel.columnCount()):
                item = tabel.item(row, col)
                if item is not None:
                    if color:
                        item.setBackground(color)
                    else:
                        item.setBackground(QColor(200, 200, 200)) # Darker gray

    def set_row_heights(self):
        for table_widget in [self.label_table, self.register_table, self.code_table, self.data_table]:
            for row in range(table_widget.rowCount()):
                table_widget.setRowHeight(row, 32)

    def set_column_widths(self, table, line_num):
        if table == self.code_table:
            self.code_table.setColumnWidth(0, 134)  # Address
            self.code_table.setColumnWidth(1, 413)  # Code
            self.code_table.setColumnWidth(2, 413)  # Basic
            self.code_table.setColumnWidth(3, 413)  # Source
        elif table == self.label_table:
            if line_num > 8:
                self.label_table.setColumnWidth(0, 230)  # Label
                self.label_table.setColumnWidth(1, 230)  # Address
            else:
                self.label_table.setColumnWidth(0, 232)  # Label
                self.label_table.setColumnWidth(1, 232)  # Address
        elif table == self.data_table:
            self.data_table.setColumnWidth(0, 134)  # Address
            for row in range(self.data_table.rowCount()-1):
                self.data_table.setColumnWidth(row+1, 155)  # Address
        elif table == self.register_table:
            self.register_table.setColumnWidth(0, 154)  # Register
            self.register_table.setColumnWidth(1, 155)  # Name
            self.register_table.setColumnWidth(2, 155)  # Value

    def find_code_row(self, data):
        for row in range(self.code_table.rowCount()):
            item = self.code_table.item(row, 0)  # 第一列的item
            if item and item.text() == str(data):  # 判断item存在且文本与data相等
                return row  # 返回找到的行数
        return -1  # 未找到返回-1
