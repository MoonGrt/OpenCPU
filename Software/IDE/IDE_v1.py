import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QAction, QFileDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QIcon
from Compiler import compiler
from Lexer import lexer
from Parser import parser
from Assembler import assembler

class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 设置应用图标
        self.setWindowIcon(QIcon('Document/icons/app.svg'))

        # 创建多个文本编辑器的选项卡
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)
        
        # 创建菜单栏
        menubar = self.menuBar()

        # 文件菜单
        file_Menu = menubar.addMenu('File')

        new_Action = QAction(QIcon('Document/icons/new.svg'), 'New', self) # 新建文件
        new_Action.setToolTip('New')
        new_Action.setShortcut('Ctrl+N')  # 设置快捷键
        new_Action.triggered.connect(self.newFile)
        file_Menu.addAction(new_Action)

        open_Action = QAction(QIcon('Document/icons/open.svg'), 'Open', self) # 打开动作
        open_Action.setToolTip('Open')
        open_Action.setShortcut('Ctrl+O')  # 设置快捷键
        open_Action.triggered.connect(self.openFile)
        file_Menu.addAction(open_Action)

        close_Action = QAction(QIcon('Document/icons/close.svg'), 'Close', self) # 关闭动作
        close_Action.setToolTip('Close')
        close_Action.setShortcut('Ctrl+W')  # 设置快捷键
        close_Action.triggered.connect(self.closeFile)
        file_Menu.addAction(close_Action)

        closeall_Action = QAction('Close All', self)  # 关闭所有动作
        # closeall_Action.setShortcut('Ctrl+Shift+W')  # 设置快捷键
        closeall_Action.triggered.connect(self.closeAllFiles)
        file_Menu.addAction(closeall_Action)

        file_Menu.addSeparator()  # 分隔线

        save_Action = QAction(QIcon('Document/icons/save.svg'), 'Save', self) # 保存动作
        save_Action.setToolTip('Save')
        save_Action.setShortcut('Ctrl+S')  # 设置快捷键
        save_Action.triggered.connect(self.saveFile)
        file_Menu.addAction(save_Action)

        saveas_Action = QAction('Save As...', self)  # 另存动作
        # saveas_Action.setShortcut('Ctrl+Shift+S')  # 设置快捷键
        saveas_Action.triggered.connect(self.saveasFile)
        file_Menu.addAction(saveas_Action)

        saveall_Action = QAction('Save All', self)  # 全部保存
        # saveall_Action.setShortcut('Ctrl+Alt+S')  # 设置快捷键
        saveall_Action.triggered.connect(self.saveAllFiles)
        file_Menu.addAction(saveall_Action)

        file_Menu.addSeparator()  # 分隔线

        exit_Action = QAction(QIcon('Document/icons/exit.svg'), 'Exit', self)  # 退出动作
        exit_Action.setToolTip('Exit')
        exit_Action.setShortcut('Ctrl+Q')  # 设置快捷键
        exit_Action.triggered.connect(self.close)
        file_Menu.addAction(exit_Action)

        # 编辑菜单
        edit_Menu = menubar.addMenu('Edit')

        undo_Action = QAction(QIcon('Document/icons/undo.svg'), 'Undo', self) # 撤销操作
        undo_Action.setToolTip('Undo')
        undo_Action.setShortcut('Ctrl+Z')  # 设置快捷键
        undo_Action.triggered.connect(self.undo)
        edit_Menu.addAction(undo_Action)

        redo_Action = QAction(QIcon('Document/icons/redo.svg'), 'Redo', self) # 重做操作
        redo_Action.setToolTip('Redo')
        redo_Action.setShortcut('Ctrl+Y')  # 设置快捷键
        redo_Action.triggered.connect(self.redo)
        edit_Menu.addAction(redo_Action)

        edit_Menu.addSeparator()  # 分隔线

        cut_Action = QAction(QIcon('Document/icons/cut.svg'), 'Cut', self) # 剪切操作
        cut_Action.setToolTip('Cut')
        cut_Action.setShortcut('Ctrl+X')  # 设置快捷键
        cut_Action.triggered.connect(self.cut)
        edit_Menu.addAction(cut_Action)
        
        copy_Action = QAction(QIcon('Document/icons/copy.svg'), 'Copy', self) # 复制操作
        copy_Action.setToolTip('Copy')
        copy_Action.setShortcut('Ctrl+C')  # 设置快捷键
        copy_Action.triggered.connect(self.copy)
        edit_Menu.addAction(copy_Action)

        paste_Action = QAction(QIcon('Document/icons/paste.svg'), 'Paste', self) # 粘贴操作
        paste_Action.setToolTip('Paste')
        paste_Action.setShortcut('Ctrl+V')  # 设置快捷键
        paste_Action.triggered.connect(self.paste)
        edit_Menu.addAction(paste_Action)

        # 运行菜单
        run_Menu = menubar.addMenu('Run')
        assemble_Action = QAction(QIcon('Document/icons/run.svg'), 'Assemble', self)
        assemble_Action.setToolTip('Assemble')
        assemble_Action.triggered.connect(self.runAssemble)
        run_Menu.addAction(assemble_Action)

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
        toolbar2.addAction(assemble_Action)
        # 添加其他工具栏项...



        # 创建用于显示Assemble产生的str的文本编辑器
        self.assemble_output_text_edit = QTextEdit(self)
        self.assemble_output_text_edit.setReadOnly(True)  # Set it to read-only
        self.assemble_output_text_edit.setMinimumSize(200, 100)  # Set a minimum size

        # 创建用于显示机械码的文本编辑器
        self.machine_code_text_edit = QTextEdit(self)
        self.machine_code_text_edit.setReadOnly(True)  # Set it to read-only
        self.machine_code_text_edit.setMinimumSize(200, 100)  # Set a minimum size

        # 创建一个水平布局，将Assemble产生的str文本编辑器和机械码文本编辑器并列
        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)

        # 创建一个水平布局，将两个文本编辑器并列
        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.assemble_output_text_edit)
        horizontal_layout.addWidget(self.machine_code_text_edit)

        # 将水平布局添加到主垂直布局中
        layout.addLayout(horizontal_layout)

        # 创建一个QWidget，作为主窗口的中央部件
        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)



        # 设置主窗口属性
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('IDE')
        self.show()

    def newFile(self):
        # 创建新的文本编辑器选项卡
        text_edit = QTextEdit(self)
        self.tab_widget.addTab(text_edit, "Untitled")

        # 切换到新创建的选项卡
        index = self.tab_widget.indexOf(text_edit)
        self.tab_widget.setCurrentIndex(index)

    def openFile(self):
        # 打开文件对话框
        options = QFileDialog.Options()
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Files", "", "Text Files (*.txt);;All Files (*)", options=options)

        for file_path in file_paths:
            if file_path:
                # 创建新的文本编辑器选项卡
                text_edit = QTextEdit(self)
                text_edit.file_path = file_path  # 设置文件路径属性
                self.tab_widget.addTab(text_edit, file_path.split("/")[-1])
                # 读取文件内容并显示在文本编辑器中
                with open(file_path, 'r') as file:
                    text_edit.setPlainText(file.read())

    def closeFile(self):
        # 获取当前活动的选项卡索引
        current_index = self.tab_widget.currentIndex()

        # 关闭当前选项卡
        if current_index != -1:
            self.tab_widget.removeTab(current_index)

    def closeAllFiles(self):
        # 关闭所有选项卡
        self.tab_widget.clear()
        
    def saveFile(self):
        # 获取当前活动的选项卡
        current_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.widget(current_index)

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
        current_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.widget(current_index)

        # 处理另存为文件逻辑
        if current_tab:
            options = QFileDialog.Options()
            fileName, _ = QFileDialog.getSaveFileName(self, "Save As", "", "Text Files (*.txt);;All Files (*)", options=options)
            if fileName:
                with open(fileName, 'w') as file:
                    file.write(current_tab.toPlainText())

    def saveAllFiles(self):
        # 迭代所有已打开的文件并保存它们
        for index in range(self.tab_widget.count()):
            current_tab = self.tab_widget.widget(index)
            file_path = getattr(current_tab, 'file_path', None)

            if current_tab and file_path:
                with open(file_path, 'w') as file:
                    file.write(current_tab.toPlainText())

    def undo(self):
        # 处理撤销逻辑
        current_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.widget(current_index)

        if current_tab:
            current_tab.undo()

    def redo(self):
        # 处理重做逻辑
        current_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.widget(current_index)

        if current_tab:
            current_tab.redo()

    def cut(self):
        # 处理剪切逻辑
        current_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.widget(current_index)

        if current_tab:
            current_tab.cut()

    def copy(self):
        # 处理复制逻辑
        current_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.widget(current_index)

        if current_tab:
            current_tab.copy()

    def paste(self):
        # 处理粘贴逻辑
        current_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.widget(current_index)

        if current_tab:
            current_tab.paste()

    def runAssemble(self):
        # 处理运行汇编逻辑
        
        # 获取当前活动的选项卡
        current_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.widget(current_index)

        program_code = current_tab.toPlainText()
        variable_list = []

        Compiler = compiler()
        assembly_code = Compiler.compiler("main", parser().parse(lexer().lexe(program_code)), variable_list)
        assembly_code = Compiler.hide_label(assembly_code)
        # print(assembly_code.expandtabs(4))

        machine_code = assembler().assemble(assembly_code)
        # print(machine_code)

        self.assemble_output_text_edit.setPlainText(assembly_code.expandtabs(4))
        self.machine_code_text_edit.setPlainText(machine_code)
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ide = IDE()
    sys.exit(app.exec_())
