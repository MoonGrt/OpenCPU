import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QAction, QFileDialog, QMessageBox, QTabWidget, QWidget, QVBoxLayout, QSplitter
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QFileInfo, Qt


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # 创建菜单
        self.init_menu()

        # 窗口标题和大小
        self.setWindowTitle("多文件文本编辑器")
        self.setGeometry(100, 100, 800, 600)

    def init_menu(self):
        # 创建菜单栏
        menu_bar = self.menuBar()

        # 创建文件菜单
        file_menu = menu_bar.addMenu("文件")

        # 创建新建文件动作
        new_action = QAction(QIcon(None), "新建", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        # 创建打开文件动作
        open_action = QAction(QIcon(None), "打开", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # 创建保存文件动作
        save_action = QAction(QIcon(None), "保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        # 创建关闭文件动作
        close_action = QAction(QIcon(None), "关闭", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close_current_tab)
        file_menu.addAction(close_action)

        # 创建关闭所有文件动作
        close_all_action = QAction(QIcon(None), "关闭所有", self)
        close_all_action.triggered.connect(self.close_all_tabs)
        file_menu.addAction(close_all_action)

        # 创建退出动作
        exit_action = QAction(QIcon(None), "退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def create_tab(self, file_content=None, file_name="未命名"):
        """
        创建一个标签页，并在左右两侧添加文本编辑器。
        左侧显示文件内容，右侧显示处理后的数据。
        :param file_content: 文件内容（如果新建文件则为空）
        :param file_name: 文件名（如果是新建文件则为 '未命名'）
        """
        new_tab = QWidget()
        layout = QVBoxLayout()

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧文本编辑器
        text_edit_left = QTextEdit()
        if file_content:
            text_edit_left.setPlainText("".join(file_content))
        splitter.addWidget(text_edit_left)

        # 右侧文本编辑器（处理后的数据）
        text_edit_right = QTextEdit()
        if file_content:
            processed_content = self.process_file_lines(file_content)
            text_edit_right.setPlainText(processed_content)
        splitter.addWidget(text_edit_right)

        # 设置左右部分的比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)
        new_tab.setLayout(layout)

        # 将标签页添加到QTabWidget中
        self.tab_widget.addTab(new_tab, file_name)
        self.tab_widget.setCurrentWidget(new_tab)

    def new_file(self):
        """新建一个空白文件标签页"""
        self.create_tab()  # 新建文件时不传入内容

    def open_file(self):
        """打开已有文件"""
        options = QFileDialog.Options()
        file_names, _ = QFileDialog.getOpenFileNames(self, "打开文件", "", "文本文件 (*.txt);;所有文件 (*)", options=options)
        if file_names:
            for file_name in file_names:
                try:
                    with open(file_name, 'r', encoding='utf-8') as f:
                        file_content = f.readlines()
                        # 创建并显示新的标签页，传入文件内容
                        self.create_tab(file_content, QFileInfo(file_name).fileName())
                except Exception as e:
                    QMessageBox.warning(self, "打开失败", f"无法打开文件: {str(e)}")

    def save_file(self):
        """保存当前标签页的文件"""
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            return
        splitter = current_tab.layout().itemAt(0).widget()
        text_edit_left = splitter.widget(0)

        # 检查当前标签页是否有文件名
        current_tab_index = self.tab_widget.currentIndex()
        current_tab_title = self.tab_widget.tabText(current_tab_index)

        if current_tab_title == "未命名":
            # 如果文件尚未保存过，弹出保存对话框
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "文本文件 (*.txt);;所有文件 (*)", options=options)
            if file_name:
                try:
                    with open(file_name, 'w', encoding='utf-8') as f:
                        file_content = text_edit_left.toPlainText()
                        f.write(file_content)
                        # 更新标签名称为保存的文件名
                        self.tab_widget.setTabText(current_tab_index, QFileInfo(file_name).fileName())
                except Exception as e:
                    QMessageBox.warning(self, "保存失败", f"无法保存文件: {str(e)}")
        else:
            # 如果文件已经有名称，直接保存
            try:
                with open(current_tab_title, 'w', encoding='utf-8') as f:
                    file_content = text_edit_left.toPlainText()
                    f.write(file_content)
            except Exception as e:
                QMessageBox.warning(self, "保存失败", f"无法保存文件: {str(e)}")

    def close_current_tab(self):
        """关闭当前标签页"""
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            self.tab_widget.removeTab(current_index)

    def close_all_tabs(self):
        """关闭所有标签页"""
        self.tab_widget.clear()

    def process_file_lines(self, lines):
        """
        模拟处理文件每行的内容。
        可以根据需求自定义处理逻辑，这里是一个简单的示例，将每行的长度作为处理结果。
        """
        processed_lines = []
        for index, line in enumerate(lines):
            processed_line = f"第 {index + 1} 行: 长度为 {len(line.strip())}"
            processed_lines.append(processed_line)
        return "\n".join(processed_lines)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = TextEditor()
    editor.show()
    sys.exit(app.exec_())
