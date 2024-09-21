import sys
from PyQt5.QtWidgets import  QVBoxLayout, QSplitter, QTableWidgetItem, QTableWidget
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QAction, QFileDialog, QTabWidget, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
from Assembler import assembler
from Disassembler import disassembler

opcode_dictionary = {
    'add': '00000',      'addi': '10000',    'csrr': '11010',
    'sub': '00001',      'subi': '10001',    'csrw': '11011',
    'mul': '00010',      'muli': '10010',    'jal' : '11010',
    'and': '00011',      'andi': '10011',    'jr'  : '11011',
    'or' : '00100',      'ori' : '10100',    'li'  : '11001',
    'xor': '00101',      'xori': '10101',    'rc'  : '11111',
    'sll': '00110',      'slli': '10110',
    'srl': '00111',      'srli': '10111',
    'beq': '01000',      'lw'  : '11000',
    'blt': '01001',      'sw'  : '11001'
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.Assembler = assembler()
        self.Disassembler = disassembler()

        self.current_file = None  # 用于跟踪当前打开的文件路径
        self.text_mode = True  # True 表示当前是文本模式, False 表示表格模式
        self.editor_syncing = False  # 防止循环调用的标志位
        self.table_syncing = False  # 防止循环调用的标志位

        layout = QVBoxLayout()
        splitter = QSplitter(Qt.Horizontal)

        # 左侧文本编辑器
        self.editor_left = QTextEdit()
        self.editor_left.setFont(QFont("Courier", 10))
        splitter.addWidget(self.editor_left)
        # 右侧文本编辑器
        self.editor_right = QTextEdit()
        self.editor_right.setFont(QFont("Courier", 10))
        splitter.addWidget(self.editor_right)

        # 左侧表格控件，初始化时隐藏
        self.table_left = QTableWidget(self)
        self.table_left.setColumnCount(4)  # 每行四列数据
        self.table_left.setHorizontalHeaderLabels(['opcode', 'rd', 'rs/IMM', 'imm/IMM'])
        self.table_left.horizontalHeader().setDefaultSectionSize(85)  # 设置列的默认宽度为150
        self.table_left.verticalHeader().setDefaultSectionSize(30)  # 设置行的默认高度为40
        self.table_left.itemChanged.connect(self.update_right_table)  # 实时更新右侧表格内容
        splitter.addWidget(self.table_left)
        self.table_left.hide()
        # 右侧表格控件，初始化时隐藏
        self.table_right = QTableWidget(self)
        self.table_right.setColumnCount(4)  # 每行四列数据
        self.table_right.setHorizontalHeaderLabels(['opcode', 'rd', 'rs/IMM', 'imm/IMM'])
        self.table_right.horizontalHeader().setDefaultSectionSize(85)  # 设置列的默认宽度为150
        self.table_right.verticalHeader().setDefaultSectionSize(30)  # 设置行的默认高度为40
        self.table_right.itemChanged.connect(self.update_left_table)  # 实时更新右侧表格内容
        splitter.addWidget(self.table_right)
        self.table_right.hide() # 设置右侧表格行高

        layout.addWidget(splitter)
        self.setLayout(layout)


    def open_file(self, file_path):
        """打开文件并在新标签页中显示"""
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
                self.editor_left.setText(assemble_code)
                self.editor_right.setText(machine_code)
                self.editor_left.textChanged.connect(self.update_right_editor)  # 实时更新右侧内容
                self.editor_right.textChanged.connect(self.update_left_editor)  # 实时更新左侧内容
                self.current_file = file_path
        except Exception as e:
            print(f"无法打开文件: {str(e)}")

    def update_left_editor(self):
        """右侧编辑框变化时同步更新左侧"""
        if not self.editor_syncing:  # 避免循环调用
            self.editor_syncing = True
            self.editor_right.blockSignals(True)  # 暂时屏蔽右侧的信号
            try:
                machine_code = self.editor_right.toPlainText()
                assemble_code = self.Disassembler.disassemble(machine_code)
                self.editor_left.setText(assemble_code + '0000000000000000')
            except:
                pass
            self.editor_right.blockSignals(False)  # 恢复右侧信号
            self.editor_syncing = False

    def update_right_editor(self):
        """左侧编辑框变化时同步更新右侧"""
        if not self.editor_syncing:  # 避免循环调用
            self.editor_syncing = True
            self.editor_left.blockSignals(True)  # 暂时屏蔽左侧的信号
            try:
                assemble_code = self.editor_left.toPlainText()
                self.Assembler.clear()
                machine_code = self.Assembler.assemble(assemble_code)
                self.editor_right.setText(machine_code)
            except:
                pass
            self.editor_left.blockSignals(False)  # 恢复左侧信号
            self.editor_syncing = False

    def merge_cells(self):
        """从右侧开始检测表格内容，若为空白则将该单元格与左侧单元格合并"""
        row_count = self.table_left.rowCount()
        col_count = self.table_left.columnCount()
        for row in range(row_count):
            empty_columns = []  # 存储连续的空单元格列号
            col = col_count - 1  # 从最右侧开始遍历
            while col >= 0:
                item = self.table_left.item(row, col)
                if item is None or item.text().strip() == "":
                    # 如果单元格为空，将其列号加入到空单元格列表中
                    empty_columns.append(col)
                else:
                    # 如果遇到非空单元格，合并之前的空单元格
                    if empty_columns:
                        self.table_left.setSpan(row, col, 1, len(empty_columns) + 1)  # 合并当前非空单元格和空白单元格
                        # 清空合并后的单元格内容
                        for empty_col in empty_columns:
                            self.table_left.setItem(row, empty_col, None)
                    break  # 找到第一个非空单元格后停止遍历
                col -= 1  # 继续向左遍历

        row_count = self.table_right.rowCount()
        col_count = self.table_right.columnCount()
        for row in range(row_count):
            empty_columns = []  # 存储连续的空单元格列号
            col = col_count - 1  # 从最右侧开始遍历
            while col >= 0:
                item = self.table_right.item(row, col)
                if item is None or item.text().strip() == "":
                    # 如果单元格为空，将其列号加入到空单元格列表中
                    empty_columns.append(col)
                else:
                    # 如果遇到非空单元格，合并之前的空单元格
                    if empty_columns:
                        self.table_right.setSpan(row, col, 1, len(empty_columns) + 1)  # 合并当前非空单元格和空白单元格
                        # 清空合并后的单元格内容
                        for empty_col in empty_columns:
                            self.table_right.setItem(row, empty_col, None)
                    break  # 找到第一个非空单元格后停止遍历
                col -= 1  # 继续向左遍历

    def mode(self):
        """切换文本模式和表格模式"""
        if self.text_mode:
            # 文本模式 -> 表格模式
            self.text_to_table()
            self.editor_left.hide()
            self.editor_right.hide()
            self.table_left.show()
            self.table_right.show()
            self.merge_cells()
        else:
            # 表格模式 -> 文本模式
            self.table_to_text()
            self.editor_left.show()
            self.editor_right.show()
            self.table_left.hide()
            self.table_right.hide()
        self.text_mode = not self.text_mode

    def text_to_table(self):
        """将文本分割为表格"""
        text_left = self.editor_left.toPlainText().strip()
        lines_left = text_left.split('\n')
        self.table_left.setRowCount(len(lines_left))
        self.table_right.setRowCount(len(lines_left))

        for row, line in enumerate(lines_left):
            columns = line.split()  # 用空格分割文本为列
            opcode = columns[0]
            if opcode == 'rc':
                self.table_left.setItem(row, 0, QTableWidgetItem(opcode))
            elif opcode in ('jal', 'jr', 'li'):
                rd = columns[1]
                IMM = columns[2]
                self.table_left.setItem(row, 0, QTableWidgetItem(opcode))
                self.table_left.setItem(row, 1, QTableWidgetItem(rd))
                self.table_left.setItem(row, 2, QTableWidgetItem(IMM))
            else:
                rd = columns[1]
                rs = columns[2]
                imm = columns[3]
                self.table_left.setItem(row, 0, QTableWidgetItem(opcode))
                self.table_left.setItem(row, 1, QTableWidgetItem(rd))
                self.table_left.setItem(row, 2, QTableWidgetItem(rs))
                self.table_left.setItem(row, 3, QTableWidgetItem(imm))

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
                    row_data.append(item.text().ljust(5)[:5])  # 如果不够5字符则补空格，超过则截断
            text_left.append("".join(row_data))  # 直接连接列数据
        self.editor_left.setPlainText("\n".join(text_left))

    def update_left_table(self, item):
        if not self.table_syncing:  # 避免循环调用
            self.table_syncing = True
            self.table_right.blockSignals(True)  # 暂时屏蔽右侧的信号

            row = item.row()  # 获取单元格的行号
            col = item.column()  # 获取单元格的列号
            value = item.text()  # 获取单元格的新值
            text = self.code_encode(value)
            if col == 3:
                self.table_left.setItem(row, col, QTableWidgetItem(str(int(value, 2))))
            elif col == 2 and not text:
                self.table_left.setItem(row, col, QTableWidgetItem(str(int(value, 2))))
            else:
                self.table_left.setItem(row, col, QTableWidgetItem(text))

            self.table_right.blockSignals(False)  # 恢复右侧信号
            self.table_syncing = False

    def code_encode(self, code):
        if code in self.Disassembler.opcode_dict:
            return self.Disassembler.opcode_dict[code]
        elif code in self.Disassembler.reg_dict:
            return bin(self.Disassembler.reg_dict[code])[2:].zfill(3)

    def update_right_table(self, item):
        if not self.table_syncing:  # 避免循环调用
            self.table_syncing = True
            self.table_left.blockSignals(True)  # 暂时屏蔽左侧的信号

            row = item.row()  # 获取单元格的行号
            col = item.column()  # 获取单元格的列号
            value = item.text()  # 获取单元格的新值
            text = self.code_decode(value)
            if text:
                self.table_right.setItem(row, col, QTableWidgetItem(text))
            else:
                try:
                    if col == 2:  # IMM
                        value = format(int(value), '08b')
                        self.table_right.setItem(row, col, QTableWidgetItem(value))
                    else:
                        value = format(int(value), '05b')
                        self.table_right.setItem(row, col, QTableWidgetItem(value))
                except:
                    self.table_right.setItem(row, col, QTableWidgetItem(''))
                    print("Invalid input")

            self.table_left.blockSignals(False)  # 恢复左侧信号
            self.table_syncing = False

    def code_decode(self, code):
        if code in self.Assembler.opcode_dict:
            return self.Assembler.opcode_dict[code]
        elif code in self.Assembler.reg_dict:
            return bin(self.Assembler.reg_dict[code])[2:].zfill(3)






class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化窗口
        self.setWindowTitle("Test")
        self.resize(800, 600)
        # 创建标签页控件
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)
        # 创建菜单栏
        self.create_menu()

    def create_menu(self):
        # 文件菜单
        file_menu = self.menuBar().addMenu("file")
        # 新建文件操作
        new_action = QAction(QIcon('icons/new.svg'), "new", self)
        # new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        # 打开文件操作
        open_action = QAction(QIcon('icons/open.svg'), "open", self)
        # open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        # 保存文件操作
        save_action = QAction(QIcon('icons/save.svg'), "save", self)
        # save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        # 关闭文件操作
        close_action = QAction(QIcon('icons/close.svg'), "close", self)
        # close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close_file)
        file_menu.addAction(close_action)
        # 切换模式操作
        mode_action = QAction(QIcon('icons/mode.svg'), 'Mode', self) # 模式操作
        # mode_action.setShortcut('M')  # 设置快捷键
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
        self.tabs.addTab(new_tab, "Untitled*")
        self.tabs.setCurrentWidget(new_tab)

    def open_file(self):
        """打开文件并在新标签页中显示"""
        options = QFileDialog.Options()
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Files", "", "All Files (*)", options=options)
        for file_path in file_paths:
            if file_path:
                try:
                    # 创建并显示新的标签页，传入文件路径
                    new_tab = FileTab(self)
                    new_tab.open_file(file_path)
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
