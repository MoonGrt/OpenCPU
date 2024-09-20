import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton, QFileDialog, QMessageBox, QAction, QTabWidget, QSplitter
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.text_mode = True  # True 表示当前是文本模式, False 表示表格模式

        # 初始化窗口
        self.setWindowTitle("左右分屏编辑器")
        self.setGeometry(100, 100, 800, 600)

        # 创建标签页控件
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        # 创建菜单栏
        self.create_menu()

    def create_menu(self):
        menu_bar = self.menuBar()

        # 文件菜单
        file_menu = menu_bar.addMenu("文件")

        # 新建文件操作
        new_action = QAction("新建", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        # 打开文件操作
        open_action = QAction("打开", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # 保存文件操作
        save_action = QAction("保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        # 关闭文件操作
        close_action = QAction("关闭当前文件", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close_file)
        file_menu.addAction(close_action)

    def new_file(self):
        """创建新文件，清空编辑器内容，创建新标签页"""
        new_tab = FileTab(self)
        self.tabs.addTab(new_tab, "未命名文件")
        self.tabs.setCurrentWidget(new_tab)

    def open_file(self):
        """打开文件并在新标签页中显示"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "打开文件", "", "文本文件 (*.txt);;所有文件 (*)", options=options)
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as file:
                    content = file.read()

                new_tab = FileTab(self)
                new_tab.left_editor.setText(content)
                new_tab.current_file = file_name
                self.tabs.addTab(new_tab, file_name.split('/')[-1])
                self.tabs.setCurrentWidget(new_tab)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法读取文件: {e}")

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


class FileTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None  # 用于跟踪当前打开的文件路径
        self.text_mode = True  # True 表示当前是文本模式, False 表示表格模式

        # 创建左右分屏
        self.splitter = QSplitter(Qt.Horizontal)

        # 左侧的文本编辑框用于显示源代码
        self.left_editor = QTextEdit(self)
        self.left_editor.setFont(QFont("Courier", 10))
        self.left_editor.textChanged.connect(self.update_right_editor)  # 实时更新右侧内容
        self.splitter.addWidget(self.left_editor)

        # 右侧的文本编辑框用于显示译码内容
        self.right_editor = QTextEdit(self)
        self.right_editor.setFont(QFont("Courier", 10))
        self.splitter.addWidget(self.right_editor)

        # 创建表格控件，但初始化时隐藏
        self.left_table = QTableWidget(self)
        self.right_table = QTableWidget(self)
        self.left_table.setColumnCount(3)  # 假设每行三列数据
        self.right_table.setColumnCount(3)  # 同样设置为三列
        self.splitter.addWidget(self.left_table)
        self.splitter.addWidget(self.right_table)
        self.left_table.hide()
        self.right_table.hide()

        # 创建切换按钮
        self.switch_button = QPushButton("切换到表格模式", self)
        self.switch_button.clicked.connect(self.switch_mode)

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.splitter)
        layout.addWidget(self.switch_button)

        self.setLayout(layout)

    def update_right_editor(self):
        """实时更新右侧编辑器内容，显示处理后的结果"""
        if self.text_mode:
            source_code = self.left_editor.toPlainText().strip()
            lines = source_code.split('\n')

            processed_lines = []
            for line in lines:
                # 示例处理逻辑
                processed_line = f"Processed: {line}"
                processed_lines.append(processed_line)

            self.right_editor.setPlainText("\n".join(processed_lines))
        else:
            self.text_to_table()

    def switch_mode(self):
        """切换文本模式和表格模式"""
        if self.text_mode:
            # 文本模式 -> 表格模式
            self.text_to_table()
            self.left_editor.hide()
            self.right_editor.hide()
            self.left_table.show()
            self.right_table.show()
            self.switch_button.setText("切换到文本模式")
        else:
            # 表格模式 -> 文本模式
            self.table_to_text()
            self.left_table.hide()
            self.right_table.hide()
            self.right_editor.show()
            self.left_editor.show()
            self.switch_button.setText("切换到表格模式")
        self.text_mode = not self.text_mode

    def text_to_table(self):
        """将文本分割为表格"""
        text = self.left_editor.toPlainText().strip()
        lines = text.split('\n')

        self.left_table.setRowCount(len(lines))
        self.right_table.setRowCount(len(lines))

        for row, line in enumerate(lines):
            columns = line.split()  # 用空格分割文本为列
            for col, item in enumerate(columns):
                self.left_table.setItem(row, col, QTableWidgetItem(item))
                # 译码处理逻辑示例
                processed_item = f"Decoded: {item}"
                self.right_table.setItem(row, col, QTableWidgetItem(processed_item))

    def table_to_text(self):
        """将表格转换为文本"""
        row_count = self.left_table.rowCount()
        col_count = self.left_table.columnCount()

        text = []
        for row in range(row_count):
            row_data = []
            for col in range(col_count):
                item = self.left_table.item(row, col)
                if item:
                    row_data.append(item.text())
            text.append("    ".join(row_data))  # 用制表符连接每列

        self.right_editor.setPlainText("\n".join(text))

    def save_file(self):
        """保存文件"""
        if self.current_file:
            file_name = self.current_file
        else:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "文本文件 (*.txt);;所有文件 (*)", options=options)
            if not file_name:
                return

        try:
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(self.left_editor.toPlainText())
            self.current_file = file_name
            parent = self.parentWidget()
            if parent:
                tab_index = parent.tabs.indexOf(self)
                parent.tabs.setTabText(tab_index, file_name.split('/')[-1])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法保存文件: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = TextEditor()
    editor.show()
    sys.exit(app.exec_())
