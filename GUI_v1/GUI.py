import sys
from PyQt5.QtWidgets import  QVBoxLayout, QSplitter, QHBoxLayout, QTableWidgetItem, QTableWidget
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QAction, QFileDialog, QTabWidget, QWidget, QPushButton, QTabBar
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from Serial import Serial
from FileTab import FileTab

class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.Serial = Serial()
        self.text_mode = True  # True 表示当前是文本模式, False 表示表格模式
        self.init_ui()

    def init_ui(self):
        # 设置应用图标
        self.setWindowIcon(QIcon('icons/app.svg'))

        # 设置主窗口属性
        self.resize(900, 800)  # 默认居中
        self.setWindowTitle('Downloader')

        # 创建菜单栏
        self.create_menu()

        # 创建主窗口
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        # 创建QSplitter
        splitter = QSplitter(main_widget)

        # 创建主窗格
        self.file_pane = QTabWidget(splitter)
        # 创建消息窗格
        self.messages_pane = QTabWidget(splitter)
        self.serial_tab = QTextEdit()
        self.messages_pane.addTab(self.serial_tab, "Serial")


        # Serial窗口添加按钮
        button_layout = QHBoxLayout()

        serial_setting_bottom = QPushButton(QIcon(QIcon("icons/setting.svg").pixmap(15, 15)), '')
        serial_setting_bottom.setFlat(True)
        serial_setting_bottom.setFixedHeight(22)
        serial_setting_bottom.setFixedWidth(22)
        serial_setting_bottom.clicked.connect(self.serial_setting)
        button_layout.addWidget(serial_setting_bottom)
        self.serial_connect_bottom = QPushButton(QIcon(QIcon("icons/connect.svg").pixmap(15, 15)), '')
        self.serial_connect_bottom.setFlat(True)
        self.serial_connect_bottom.setFixedHeight(22)
        self.serial_connect_bottom.setFixedWidth(22)
        self.serial_connect_bottom.clicked.connect(self.serial_connect)
        button_layout.addWidget(self.serial_connect_bottom)
        self.serial_disconnect_bottom = QPushButton(QIcon(QIcon("icons/disconnect.svg").pixmap(15, 15)), '')
        self.serial_disconnect_bottom.setFlat(True)
        self.serial_disconnect_bottom.setFixedHeight(22)
        self.serial_disconnect_bottom.setFixedWidth(22)
        self.serial_disconnect_bottom.clicked.connect(self.serial_disconnect)
        self.serial_disconnect_bottom.setEnabled(False)
        button_layout.addWidget(self.serial_disconnect_bottom)
        serial_clear_bottom = QPushButton(QIcon(QIcon("icons/clear.svg").pixmap(15, 15)), '')
        serial_clear_bottom.setFlat(True)
        serial_clear_bottom.setFixedHeight(22)
        serial_clear_bottom.setFixedWidth(22)
        serial_clear_bottom.clicked.connect(self.serial_clear)
        button_layout.addWidget(serial_clear_bottom)

        button_layout.setContentsMargins(0, 3, 0, 3)

        container = QWidget()
        container.setLayout(button_layout)
        self.messages_pane.tabBar().setTabButton(0, QTabBar.RightSide, container)


        # 设置布局
        splitter_layout = QVBoxLayout(main_widget)
        splitter_layout.addWidget(splitter)  # 将QSplitter添加到布局中
        main_widget.setLayout(splitter_layout)

        # 设置分隔窗格
        splitter.setOrientation(Qt.Vertical)
        splitter.setSizes([250, 100]) # 设置 edit_tab 和 execute_tab 的大小比例


    def create_menu(self):
        # 文件菜单
        file_Menu = self.menuBar().addMenu('File')

        new_Action = QAction(QIcon('icons/new.svg'), 'New', self) # 新建文件
        new_Action.setToolTip('New')
        # new_Action.setShortcut('Ctrl+N') # 设置快捷键
        new_Action.triggered.connect(self.newFile)
        file_Menu.addAction(new_Action)
        open_Action = QAction(QIcon('icons/open.svg'), 'Open', self) # 打开动作
        open_Action.setToolTip('Open')
        # open_Action.setShortcut('Ctrl+O')  # 设置快捷键
        open_Action.triggered.connect(self.openFile)
        file_Menu.addAction(open_Action)
        close_Action = QAction(QIcon('icons/close.svg'), 'Close', self) # 关闭动作
        close_Action.setToolTip('Close')
        # close_Action.setShortcut('Ctrl+W') # 设置快捷键
        close_Action.triggered.connect(self.closeFile)
        file_Menu.addAction(close_Action)
        closeall_Action = QAction('Close All', self) # 关闭所有动作
        # closeall_Action.setShortcut('Ctrl+Shift+W') # 设置快捷键
        closeall_Action.triggered.connect(self.closeAllFiles)
        file_Menu.addAction(closeall_Action)
        file_Menu.addSeparator()  # 分隔线
        save_Action = QAction(QIcon('icons/save.svg'), 'Save', self) # 保存动作
        save_Action.setToolTip('Save')
        # save_Action.setShortcut('Ctrl+S')  # 设置快捷键
        save_Action.triggered.connect(self.saveFile)
        file_Menu.addAction(save_Action)
        saveas_Action = QAction('Save As...', self) # 另存动作
        # saveas_Action.setShortcut('Ctrl+Shift+S') # 设置快捷键
        saveas_Action.triggered.connect(self.saveasFile)
        file_Menu.addAction(saveas_Action)
        saveall_Action = QAction('Save All', self) # 全部保存
        # saveall_Action.setShortcut('Ctrl+Alt+S') # 设置快捷键
        saveall_Action.triggered.connect(self.saveAllFiles)
        file_Menu.addAction(saveall_Action)
        file_Menu.addSeparator()  # 分隔线
        exit_Action = QAction(QIcon('icons/exit.svg'), 'Exit', self) # 退出动作
        exit_Action.setToolTip('Exit')
        # exit_Action.setShortcut('Ctrl+Q')  # 设置快捷键
        exit_Action.triggered.connect(self.close)
        file_Menu.addAction(exit_Action)

        # 编辑菜单
        edit_Menu = self.menuBar().addMenu('Edit')

        undo_Action = QAction(QIcon('icons/undo.svg'), 'Undo', self) # 撤销操作
        undo_Action.setToolTip('Undo')
        # undo_Action.setShortcut('Ctrl+Z')  # 设置快捷键
        undo_Action.triggered.connect(self.undo)
        edit_Menu.addAction(undo_Action)
        redo_Action = QAction(QIcon('icons/redo.svg'), 'Redo', self) # 重做操作
        redo_Action.setToolTip('Redo')
        # redo_Action.setShortcut('Ctrl+Y')  # 设置快捷键
        redo_Action.triggered.connect(self.redo)
        edit_Menu.addAction(redo_Action)
        edit_Menu.addSeparator()  # 分隔线
        cut_Action = QAction(QIcon('icons/cut.svg'), 'Cut', self) # 剪切操作
        cut_Action.setToolTip('Cut')
        # cut_Action.setShortcut('Ctrl+X')  # 设置快捷键
        cut_Action.triggered.connect(self.cut)
        edit_Menu.addAction(cut_Action)
        copy_Action = QAction(QIcon('icons/copy.svg'), 'Copy', self) # 复制操作
        copy_Action.setToolTip('Copy')
        # copy_Action.setShortcut('Ctrl+C')  # 设置快捷键
        copy_Action.triggered.connect(self.copy)
        edit_Menu.addAction(copy_Action)
        paste_Action = QAction(QIcon('icons/paste.svg'), 'Paste', self) # 粘贴操作
        paste_Action.setToolTip('Paste')
        # paste_Action.setShortcut('Ctrl+V')  # 设置快捷键
        paste_Action.triggered.connect(self.paste)
        edit_Menu.addAction(paste_Action)
        edit_Menu.addSeparator()  # 分隔线
        mode_Action = QAction(QIcon('icons/mode.svg'), 'Mode', self) # 模式操作
        mode_Action.setToolTip('Mode')
        # mode_Action.setShortcut('M')  # 设置快捷键
        mode_Action.triggered.connect(self.mode)
        edit_Menu.addAction(mode_Action)

        # 运行菜单
        run_Menu = self.menuBar().addMenu('Run')

        self.download_Action = QAction(QIcon('icons/download.svg'), 'Download', self) # 烧录
        self.download_Action.setToolTip('Download')
        self.download_Action.triggered.connect(self.download)
        self.download_Action.setEnabled(False)
        run_Menu.addAction(self.download_Action)

        # 工具栏
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
        toolbar2.addAction(mode_Action)

        toolbar3 = self.addToolBar('Toolbar3')
        toolbar3.addAction(self.download_Action)

    def newFile(self):
        """创建新文件，创建新标签页"""
        new_tab = FileTab(self)
        self.file_pane.addTab(new_tab, "Untitled*")
        self.file_pane.setCurrentWidget(new_tab)

    def openFile(self):
        """打开文件并在新标签页中显示"""
        options = QFileDialog.Options()
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Files", "", "All Files (*)", options=options)
        for file_path in file_paths:
            if file_path:
                try:
                    # 创建并显示新的标签页，传入文件路径
                    new_tab = FileTab(self)
                    new_tab.open_file(file_path)
                    self.file_pane.addTab(new_tab, file_path.split("/")[-1])
                    self.file_pane.setCurrentWidget(new_tab)
                except Exception as e:
                    print(f"无法打开文件: {str(e)}")

    def closeFile(self):
        # 获取当前活动的选项卡索引
        current_index = self.file_pane.currentIndex()
        # 关闭当前选项卡
        if current_index != -1:
            self.file_pane.removeTab(current_index)

    def closeAllFiles(self):
        # 关闭所有选项卡
        self.file_pane.clear()

    def saveFile(self):  # TODO: 保存哪个文件，有问题
        """保存当前标签页的文件，如果是未命名文件则调用另存为"""
        current_tab = self.file_pane.currentWidget()
        if current_tab is None:
            return
        splitter = current_tab.layout().itemAt(0).widget()
        editor_left = splitter.widget(0)

        # 检查当前标签页是否有文件名
        current_tab_index = self.file_pane.currentIndex()
        current_tab_title = self.file_pane.tabText(current_tab_index)

        if current_tab_title == "Untitled*":
            # 未命名文件则执行另存为
            self.saveasFile()
        else:
            # 文件已有文件名，直接保存
            try:
                with open(current_tab_title, 'w', encoding='utf-8') as f:
                    file_content = editor_left.toPlainText()
                    f.write(file_content)
            except Exception as e:
                print("保存失败", f"无法保存文件: {str(e)}")

    def saveasFile(self):  # TODO: 保存哪个文件，有问题
        """弹出另存为对话框，保存当前文件为指定名称"""
        current_tab = self.file_pane.currentWidget()
        if current_tab is None:
            return
        splitter = current_tab.layout().itemAt(0).widget()
        editor_left = splitter.widget(0)

        # 弹出保存对话框
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save", "", "All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    file_content = editor_left.toPlainText()
                    f.write(file_content)
                    # 更新标签名称为保存的文件名
                    current_tab_index = self.file_pane.currentIndex()
                    self.file_pane.setTabText(current_tab_index, file_name.split("/")[-1])
            except Exception as e:
                print("另存为失败", f"无法保存文件: {str(e)}")

    def saveAllFiles(self):  # TODO: 保存哪个文件，有问题
        """保存所有打开的文件，如果有未命名的文件，则弹出保存对话框"""
        for i in range(self.file_pane.count()):
            self.file_pane.setCurrentIndex(i)
            # 获取每个标签页的标题（文件名）
            tab_title = self.file_pane.tabText(i)
            if tab_title == "未命名":
                # 如果是未命名文件，弹出保存对话框
                self.saveasFile()
            else:
                # 文件已命名，直接保存
                self.saveFile()

    def undo(self):
        # 处理撤销逻辑
        current_tab = self.file_pane.currentWidget()
        if current_tab:
            current_tab.undo()

    def redo(self):
        # 处理重做逻辑
        current_tab = self.file_pane.currentWidget()
        if current_tab:
            current_tab.redo()

    def cut(self):  # TODO: 剪切哪个文件，有问题
        """剪切选中的文本到剪贴板"""
        current_tab = self.file_pane.currentWidget()
        if current_tab is None:
            return
        splitter = current_tab.layout().itemAt(0).widget()
        editor_left = splitter.widget(0)
        editor_left.cut()

    def copy(self):  # TODO: 复制在使用快捷键的时候有问题   复制到哪个文件，有问题
        """复制选中的文本到剪贴板"""
        current_tab = self.file_pane.currentWidget()
        if current_tab is None:
            return
        splitter = current_tab.layout().itemAt(0).widget()
        editor_left = splitter.widget(0)
        editor_left.copy()

    def paste(self):  # TODO: 粘贴到哪个文件，有问题
        """粘贴剪贴板中的文本到当前位置"""
        current_tab = self.file_pane.currentWidget()
        if current_tab is None:
            return
        splitter = current_tab.layout().itemAt(0).widget()
        editor_left = splitter.widget(0)
        editor_left.paste()

    def mode(self):
        """切换文本模式和表格模式"""
        current_tab = self.file_pane.currentWidget()  # 获取当前标签页
        if isinstance(current_tab, FileTab):  # 确保当前标签页是 FileTab 类型
            current_tab.mode()  # 调用 FileTab 的 mode 函数

    def download(self):
        # 下载
        current_tab = self.file_pane.currentWidget()
        if current_tab is None:
            return
        self.Serial.download(current_tab.editor_right.toPlainText())

    def serial_showmessage(self, message):
        # 将内容添加到messages
        current_content = self.serial_tab.toPlainText()
        updated_content = current_content + message
        self.serial_tab.setPlainText(updated_content)

    def serial_setting(self):
        # 打开串口配置窗口
        self.Serial.download_setting()

    def serial_recv(self):
        """读取接收的数据"""
        if self.Serial.serial_port.isOpen():
            try:
                data = self.Serial.serial_port.readAll()
                if not data.isEmpty():
                    self.serial_showmessage(data.toHex().data().decode('utf-8'))
                    # print(f"recv ({len(data)} bytes): {data.toHex().data().decode('utf-8')}")
            except:
                pass

    def serial_connect(self):
        # 连接串口
        self.Serial.serial_port.readyRead.connect(self.serial_recv)   # 连接 readyRead 信号到 read_data 槽
        if self.Serial.open():
            self.download_Action.setEnabled(True)
            self.serial_connect_bottom.setEnabled(False)
            self.serial_disconnect_bottom.setEnabled(True)
            self.serial_showmessage("Port open successful\n")
        else:
            self.serial_showmessage("Port open error!\n")

    def serial_disconnect(self):
        # 断开连接
        self.Serial.close()
        self.download_Action.setEnabled(False)
        self.serial_connect_bottom.setEnabled(True)
        self.serial_disconnect_bottom.setEnabled(False)
        self.serial_showmessage("Port closed\n")

    def serial_clear(self):
        # 清除 serial message
        self.serial_tab.setPlainText('')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ide = GUI()
    ide.show()  # 开启窗口
    sys.exit(app.exec_())
