import sys
from PyQt5.QtWidgets import  QVBoxLayout, QSplitter, QHBoxLayout, QTableWidgetItem, QTableWidget
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QAction, QFileDialog, QTabWidget, QWidget, QPushButton, QTabBar
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
from Assembler import assembler
from Disassembler import disassembler

# 操作码和寄存器字典
opcode_dictionary = {
    'add': '00000',      'addi': '10000',
    'sub': '00001',      'subi': '10001',
    'mul': '00010',      'muli': '10010',
    'and': '00011',      'andi': '10011',
    'or' : '00100',      'ori' : '10100',
    'xor': '00101',      'xori': '10101',
    'sll': '00110',      'slli': '10110',
    'srl': '00111',      'srli': '10111',
    'beq': '01000',      'lw'  : '11000',
    'blt': '01001',      'sw'  : '11001',

    'csrr': '11010',
    'csrw': '11011',
    'jal' : '11010',
    'jr'  : '11011',
    'li'  : '11001',
    'rc'  : '11111'
}
reg_dictionary = {
    's0': '000',
    'a1': '001',
    'a2': '010',
    'a3': '011',
    'a4': '100',
    'a5': '101',
    'ra': '110',
    'sp': '111'
}

class FileTab(QWidget):
    def __init__(self, parent=None, opcode_dict=opcode_dictionary, reg_dict=reg_dictionary):
        super().__init__(parent)
        self.opcode_dict = opcode_dict
        self.reg_dict = reg_dict

        self.current_file = None  # 用于跟踪当前打开的文件路径
        self.text_mode = True  # True 表示当前是文本模式, False 表示表格模式

        layout = QVBoxLayout()
        splitter = QSplitter(Qt.Horizontal)

        # 左侧文本编辑器
        self.editor_left = QTextEdit()
        self.editor_left.setFont(QFont("Courier", 10))
        splitter.addWidget(self.editor_left)
        # self.editor_left.textChanged.connect(self.update_right_editor)  # 实时更新右侧内容
        # 右侧文本编辑器
        self.editor_right = QTextEdit()
        self.editor_right.setFont(QFont("Courier", 10))
        splitter.addWidget(self.editor_right)

        # 左侧表格控件，初始化时隐藏
        self.table_left = QTableWidget(self)
        self.table_left.setColumnCount(4)  # 每行四列数据
        self.table_left.horizontalHeader().setDefaultSectionSize(85)  # 设置列的默认宽度为150
        self.table_left.verticalHeader().setDefaultSectionSize(30)  # 设置行的默认高度为40
        splitter.addWidget(self.table_left)
        self.table_left.hide()
        # 右侧表格控件，初始化时隐藏
        self.table_right = QTableWidget(self)
        self.table_right.setColumnCount(4)  # 每行四列数据
        self.table_right.horizontalHeader().setDefaultSectionSize(85)  # 设置列的默认宽度为150
        self.table_right.verticalHeader().setDefaultSectionSize(30)  # 设置行的默认高度为40
        splitter.addWidget(self.table_right)
        self.table_right.hide() # 设置右侧表格行高

        layout.addWidget(splitter)
        self.setLayout(layout)


    def mode(self):
        """切换文本模式和表格模式"""
        if self.text_mode:
            # 文本模式 -> 表格模式
            self.text_to_table()
            self.editor_left.hide()
            self.editor_right.hide()
            self.table_left.show()
            self.table_right.show()
        else:
            # 表格模式 -> 文本模式
            self.table_to_text()
            self.editor_left.show()
            self.editor_right.show()
            self.table_left.hide()
            self.table_right.hide()
        self.text_mode = not self.text_mode

    def code_decode(self, code):
        if code in self.opcode_dict:
            return self.opcode_dict[code]
        elif code in self.reg_dict:
            return self.reg_dict[code]
        else:
            return code

    def text_to_table(self):
        """将文本分割为表格"""
        text_left = self.editor_left.toPlainText().strip()
        lines_left = text_left.split('\n')
        self.table_left.setRowCount(len(lines_left))
        self.table_right.setRowCount(len(lines_left))  # lines_right
        for row, line in enumerate(lines_left):
            columns = line.split()  # 用空格分割文本为列
            for col, item in enumerate(columns):
                self.table_left.setItem(row, col, QTableWidgetItem(item))
                self.table_right.setItem(row, col, QTableWidgetItem(self.code_decode(item)))

    def table_to_text(self):
        """将表格转换为文本"""
        text_left = []
        row_cnt_left = self.table_left.rowCount()
        col_cnt_left = self.table_left.columnCount()
        for row in range(row_cnt_left):
            row_data = []
            for col in range(col_cnt_left):
                item = self.table_left.item(row, col)
                if item:
                    row_data.append(item.text())
            text_left.append("    ".join(row_data))  # 用制表符连接每列
        self.editor_left.setPlainText("\n".join(text_left))

        text_right = []
        row_cnt_right = self.table_right.rowCount()
        col_cnt_right = self.table_right.columnCount()
        for row in range(row_cnt_right):
            row_data = []
            for col in range(col_cnt_right):
                item = self.table_right.item(row, col)
                if item:
                    row_data.append(item.text())
            text_right.append("    ".join(row_data))  # 用制表符连接每列
        self.editor_right.setPlainText("\n".join(text_right))




class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.text_mode = True  # True 表示当前是文本模式, False 表示表格模式
        self.Assembler = assembler()
        self.Disassembler = disassembler()

        # 初始化窗口
        self.setWindowTitle("左右分屏编辑器")
        self.resize(800, 600)
        # 创建标签页控件
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)
        # 创建菜单栏
        self.create_menu()

    def create_menu(self):
        menu_bar = self.menuBar()

        # 文件菜单
        file_menu = menu_bar.addMenu("file")
        # 新建文件操作
        new_action = QAction(QIcon('icons/new.svg'), "new", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        # 打开文件操作
        open_action = QAction(QIcon('icons/open.svg'), "open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        # 保存文件操作
        save_action = QAction(QIcon('icons/save.svg'), "save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        # 关闭文件操作
        close_action = QAction(QIcon('icons/close.svg'), "close", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close_file)
        file_menu.addAction(close_action)
        # 切换模式操作
        mode_action = QAction(QIcon('icons/mode.svg'), 'Mode', self) # 模式操作
        mode_action.setToolTip('Mode')
        mode_action.setShortcut('M')  # 设置快捷键
        mode_action.triggered.connect(self.mode)
        file_menu.addAction(mode_action)

        toolbar1 = self.addToolBar('Toolbar1')
        toolbar1.addAction(new_action)
        toolbar1.addAction(open_action)
        toolbar1.addAction(save_action)
        toolbar1.addAction(close_action)
        toolbar1.addAction(mode_action)


    def new_file(self):
        """创建新文件，清空编辑器内容，创建新标签页"""
        new_tab = FileTab(self)
        self.tabs.addTab(new_tab, "未命名文件")
        self.tabs.setCurrentWidget(new_tab)

    def open_file(self):
        """打开文件并在新标签页中显示"""
        options = QFileDialog.Options()
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Files", "", "All Files (*)", options=options)
        for file_path in file_paths:
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = "".join(f.readlines())
                        data = file_content.strip().replace('\n', '')
                        if not all(char in '01' for char in data):
                            assemble_code = file_content
                            machine_code = self.Assembler.assemble(file_content)
                        else:
                            assemble_code = self.Disassembler.disassemble(file_content)
                            machine_code = file_content
                        # 创建并显示新的标签页，传入文件内容
                        new_tab = FileTab(self)
                        new_tab.editor_left.setText(assemble_code)
                        new_tab.editor_right.setText(machine_code)
                        new_tab.current_file = file_path
                        self.tabs.addTab(new_tab, file_path.split("/")[-1])
                        self.tabs.setCurrentWidget(new_tab)
                except Exception as e:
                    print(f"无法打开文件: {str(e)}")


    def save_file(self):
        """保存当前标签页中的文件"""
        current_tab = self.tabs.currentWidget()
        if isinstance(current_tab, FileTab):
            current_tab.save_file()

    def close_file(self):
        """关闭当前标签页"""
        current_tab_index = self.tabs.currentIndex()
        if current_tab_index != -1:
            self.tabs.removeTab(current_tab_index)

    # def mode(self):
    #     """切换文本模式和表格模式"""
    #     current_tab = self.tabs.currentWidget()
    #     if current_tab is None:
    #         return
    def mode(self):
        """切换文本模式和表格模式"""
        current_tab = self.tabs.currentWidget()  # 获取当前标签页
        if isinstance(current_tab, FileTab):  # 确保当前标签页是 FileTab 类型
            current_tab.mode()  # 调用 FileTab 的 mode 函数


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = TextEditor()
    editor.show()
    sys.exit(app.exec_())
