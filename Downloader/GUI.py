import sys
from PyQt5.QtWidgets import  QVBoxLayout, QSplitter, QHBoxLayout
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QAction, QFileDialog, QTabWidget, QWidget, QPushButton, QTabBar, QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from Downloader import downloader

class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.Downloader = downloader()
        self.init_ui()

    def init_ui(self):
        # 设置应用图标
        self.setWindowIcon(QIcon('icons/app.svg'))

        # 设置主窗口属性
        self.resize(900, 700)  # 默认居中
        self.setWindowTitle('Downloader')

        # 创建菜单栏
        menubar = self.menuBar()

        # 文件菜单
        file_Menu = menubar.addMenu('File')

        new_Action = QAction(QIcon('icons/new.svg'), 'New', self) # 新建文件
        new_Action.setToolTip('New')
        new_Action.setShortcut('Ctrl+N') # 设置快捷键
        new_Action.triggered.connect(self.newFile)
        file_Menu.addAction(new_Action)

        open_Action = QAction(QIcon('icons/open.svg'), 'Open', self) # 打开动作
        open_Action.setToolTip('Open')
        open_Action.setShortcut('Ctrl+O')  # 设置快捷键
        open_Action.triggered.connect(self.openFile)
        file_Menu.addAction(open_Action)

        close_Action = QAction(QIcon('icons/close.svg'), 'Close', self) # 关闭动作
        close_Action.setToolTip('Close')
        close_Action.setShortcut('Ctrl+W') # 设置快捷键
        close_Action.triggered.connect(self.closeFile)
        file_Menu.addAction(close_Action)

        closeall_Action = QAction('Close All', self) # 关闭所有动作
        # closeall_Action.setShortcut('Ctrl+Shift+W') # 设置快捷键
        closeall_Action.triggered.connect(self.closeAllFiles)
        file_Menu.addAction(closeall_Action)

        file_Menu.addSeparator()  # 分隔线

        save_Action = QAction(QIcon('icons/save.svg'), 'Save', self) # 保存动作
        save_Action.setToolTip('Save')
        save_Action.setShortcut('Ctrl+S')  # 设置快捷键
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
        exit_Action.setShortcut('Ctrl+Q')  # 设置快捷键
        exit_Action.triggered.connect(self.close)
        file_Menu.addAction(exit_Action)

        # 编辑菜单
        edit_Menu = menubar.addMenu('Edit')

        undo_Action = QAction(QIcon('icons/undo.svg'), 'Undo', self) # 撤销操作
        undo_Action.setToolTip('Undo')
        undo_Action.setShortcut('Ctrl+Z')  # 设置快捷键
        undo_Action.triggered.connect(self.undo)
        edit_Menu.addAction(undo_Action)

        redo_Action = QAction(QIcon('icons/redo.svg'), 'Redo', self) # 重做操作
        redo_Action.setToolTip('Redo')
        redo_Action.setShortcut('Ctrl+Y')  # 设置快捷键
        redo_Action.triggered.connect(self.redo)
        edit_Menu.addAction(redo_Action)

        edit_Menu.addSeparator()  # 分隔线

        cut_Action = QAction(QIcon('icons/cut.svg'), 'Cut', self) # 剪切操作
        cut_Action.setToolTip('Cut')
        cut_Action.setShortcut('Ctrl+X')  # 设置快捷键
        cut_Action.triggered.connect(self.cut)
        edit_Menu.addAction(cut_Action)

        copy_Action = QAction(QIcon('icons/copy.svg'), 'Copy', self) # 复制操作
        copy_Action.setToolTip('Copy')
        copy_Action.setShortcut('Ctrl+C')  # 设置快捷键
        copy_Action.triggered.connect(self.copy)
        edit_Menu.addAction(copy_Action)

        paste_Action = QAction(QIcon('icons/paste.svg'), 'Paste', self) # 粘贴操作
        paste_Action.setToolTip('Paste')
        paste_Action.setShortcut('Ctrl+V')  # 设置快捷键
        paste_Action.triggered.connect(self.paste)
        edit_Menu.addAction(paste_Action)

        # 运行菜单
        run_Menu = menubar.addMenu('Run')

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

        toolbar3 = self.addToolBar('Toolbar3')
        toolbar3.addAction(self.download_Action)


        # 创建主窗口
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        # 创建QSplitter
        splitter = QSplitter(main_widget)


        # 创建主窗格
        main_pane = QTabWidget(splitter)
        file_tab = QWidget()
        main_pane.addTab(file_tab, "File")

        # 创建水平布局
        file_tab_layout = QHBoxLayout(file_tab)
        # 创建编辑区域
        self.edit_area = QTabWidget(file_tab)
        file_tab_layout.addWidget(self.edit_area)

        # 创建消息窗格
        messages_pane = QTabWidget(splitter)
        self.serial_tab = QTextEdit()
        messages_pane.addTab(self.serial_tab, "Serial")


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
        messages_pane.tabBar().setTabButton(0, QTabBar.RightSide, container)


        # 设置布局
        splitter_layout = QVBoxLayout(main_widget)
        splitter_layout.addWidget(splitter)  # 将QSplitter添加到布局中
        main_widget.setLayout(splitter_layout)

        # 设置分隔窗格
        splitter.setOrientation(Qt.Vertical)
        splitter.setSizes([250, 100]) # 设置 edit_tab 和 execute_tab 的大小比例

        # 开启窗口
        self.show()

    def newFile(self):
        # 创建新的文本编辑器选项卡
        text_edit = QTextEdit(self)
        self.edit_area.addTab(text_edit, "Untitled*")
        # 切换到新创建的选项卡
        index = self.edit_area.indexOf(text_edit)
        self.edit_area.setCurrentIndex(index)

    def openFile(self):
        # 打开文件对话框
        options = QFileDialog.Options()
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Files", "", "All Files (*)", options=options)
        for file_path in file_paths:
            if file_path:
                # 创建新的文本编辑器选项卡
                text_edit = QTextEdit(self)
                text_edit.file_path = file_path  # 设置文件路径属性
                self.edit_area.addTab(text_edit, file_path.split("/")[-1])
                # 读取文件内容并显示在文本编辑器中
                with open(file_path, 'r') as file:
                    text_edit.setPlainText(file.read())

    def closeFile(self):
        # 获取当前活动的选项卡索引
        current_index = self.edit_area.currentIndex()
        # 关闭当前选项卡
        if current_index != -1:
            self.edit_area.removeTab(current_index)

    def closeAllFiles(self):
        # 关闭所有选项卡
        self.edit_area.clear()

    def saveFile(self):
        # 获取当前活动的选项卡
        current_index = self.edit_area.currentIndex()
        current_tab = self.edit_area.widget(current_index)
        # 获取当前文件路径
        file_path = getattr(current_tab, 'file_path', None)
        # 如果没有文件路径，则调用另存为逻辑
        if not file_path:
            self.saveasFile()
            return
        # 将当前选项卡的文本编辑器内容保存到文件中
        if current_tab and file_path:
            with open(file_path, 'w') as file:
                file.write(current_tab.toPlainText())

    def saveasFile(self):
        # 获取当前活动的选项卡
        current_index = self.edit_area.currentIndex()
        current_tab = self.edit_area.widget(current_index)
        # 处理另存为文件逻辑
        if current_tab:
            options = QFileDialog.Options()
            fileName, _ = QFileDialog.getSaveFileName(self, "Save As", "", "Text Files (*.txt);;All Files (*)", options=options)
            if fileName:
                with open(fileName, 'w') as file:
                    file.write(current_tab.toPlainText())

    def saveAllFiles(self):
        # 迭代所有已打开的文件并保存它们
        for index in range(self.edit_area.count()):
            current_tab = self.edit_area.widget(index)
            file_path = getattr(current_tab, 'file_path', None)
            if current_tab and file_path:
                with open(file_path, 'w') as file:
                    file.write(current_tab.toPlainText())

    def undo(self):
        # 处理撤销逻辑
        current_index = self.edit_area.currentIndex()
        current_tab = self.edit_area.widget(current_index)
        if current_tab:
            current_tab.undo()

    def redo(self):
        # 处理重做逻辑
        current_index = self.edit_area.currentIndex()
        current_tab = self.edit_area.widget(current_index)
        if current_tab:
            current_tab.redo()

    def cut(self):
        # 处理剪切逻辑
        current_index = self.edit_area.currentIndex()
        current_tab = self.edit_area.widget(current_index)
        if current_tab:
            current_tab.cut()

    def copy(self):
        # 处理复制逻辑
        current_index = self.edit_area.currentIndex()
        current_tab = self.edit_area.widget(current_index)
        if current_tab:
            current_tab.copy()

    def paste(self):
        # 处理粘贴逻辑
        current_index = self.edit_area.currentIndex()
        current_tab = self.edit_area.widget(current_index)
        if current_tab:
            current_tab.paste()

    def download(self):
        # 下载
        current_index = self.edit_area.currentIndex()
        current_tab = self.edit_area.widget(current_index)
        self.Downloader.download(current_tab.toPlainText())

    def serial_showmessage(self, message):
        # 将内容添加到messages
        current_content = self.serial_tab.toPlainText()
        updated_content = current_content + message
        self.serial_tab.setPlainText(updated_content)

    def serial_setting(self):
        # 打开串口配置窗口
        self.Downloader.download_setting()
        self.serial_connect()  # 默认设置后马上就进行连接

    def serial_connect(self):
        # 连接串口
        if self.Downloader.download_open():
            self.download_Action.setEnabled(True)
            self.serial_connect_bottom.setEnabled(False)
            self.serial_disconnect_bottom.setEnabled(True)
            self.serial_showmessage("Port open successful\n")
        else:
            self.serial_showmessage("Port occupied\n")
        
    def serial_disconnect(self):
        # 断开连接
        self.Downloader.download_close()
        # self.Downloader.stop_receiving()
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
    sys.exit(app.exec_())

