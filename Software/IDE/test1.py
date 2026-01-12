
import sys
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QTextCharFormat, QTextCursor, QSyntaxHighlighter, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QAction, QFileDialog, QMessageBox, QTabWidget

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = [
            (QRegExp("\\bdef\\b"), QTextCharFormat().setForeground(Qt.blue)),
            (QRegExp("\\bif\\b|\\belse\\b"), QTextCharFormat().setForeground(Qt.darkMagenta)),
            (QRegExp("\\bfor\\b|\\bwhile\\b"), QTextCharFormat().setForeground(Qt.darkGreen)),
            (QRegExp("\\bclass\\b"), QTextCharFormat().setForeground(Qt.darkRed)),
        ]

    def highlightBlock(self, text):
        for pattern, char_format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, char_format)
                index = expression.indexIn(text, index + length)

class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            /* 主窗口整体风格 */
            QMainWindow {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }

            /* 菜单栏 */
            QMenuBar {
                background-color: #2d2d30;
                color: #d4d4d4;
            }
            QMenuBar::item {
                background-color: #2d2d30;
                color: #d4d4d4;
            }
            QMenuBar::item:selected {
                background-color: #3daee9;
            }

            /* 菜单 */
            QMenu {
                background-color: #2d2d30;
                color: #d4d4d4;
            }
            QMenu::item:selected {
                background-color: #3daee9;
            }

            /* 工具栏 */
            QToolBar {
                background-color: #2d2d30;
                border: 1px solid #1e1e1e;
            }
            QToolButton {
                background-color: #2d2d30;
                color: #d4d4d4;
            }
            QToolButton::hover {
                background-color: #3daee9;
            }

            /* 选项卡窗口 */
            QTabWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #1e1e1e;
            }
            QTabBar::tab:selected {
                background-color: #2d2d30;
                color: #d4d4d4;
            }
            QTabBar::tab:!selected {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }

            /* 文本编辑器 */
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, Courier, monospace;
                font-size: 12pt;
            }

            /* 文件对话框 */
            QFileDialog {
                background-color: #2d2d30;
                color: #d4d4d4;
            }
            QFileDialog QLabel {
                color: #d4d4d4;
            }
            QFileDialog QListView {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QFileDialog QTreeView {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QFileDialog QLineEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }

            /* 按钮 */
            QPushButton {
                background-color: #2d2d30;
                color: #d4d4d4;
            }
            QPushButton::hover {
                background-color: #3daee9;
            }

            /* 标题栏 */
            QMenuBar::item {
                background: transparent;
            }
            QMainWindow::title {
                background-color: #000000 !important;  /* 黑色系 */
                color: #ffffff !important;  /* 白色 */
                padding: 3px;
            }
            QMenuBar::item:disabled {
                color: #d4d4d4 !important;
            }
            QMainWindow::close-button {
                background-color: #000000 !important;  /* 黑色系 */
                border: none;
            }
            QMainWindow::close-button:hover {
                background-color: #ff0000 !important;  /* 红色，或其他你想要的颜色 */
            }
        """)
        
        # 创建菜单栏和工具栏
        menubar = self.menuBar()

        # 文件菜单
        file_Menu = menubar.addMenu('File')
        new_Action = QAction('New', self)
        new_Action.triggered.connect(self.newFile)
        file_Menu.addAction(new_Action)

        open_Action = QAction('Open...', self)
        open_Action.triggered.connect(self.openFile)
        file_Menu.addAction(open_Action)

        close_Action = QAction('Close', self)
        close_Action.triggered.connect(self.closeFile)
        file_Menu.addAction(close_Action)

        closeall_Action = QAction('Close All', self)
        closeall_Action.triggered.connect(self.closeAllFiles)
        file_Menu.addAction(closeall_Action)
        
        file_Menu.addSeparator()

        save_Action = QAction('Save', self)
        save_Action.triggered.connect(self.saveFile)
        file_Menu.addAction(save_Action)

        saveas_Action = QAction('Save As...', self)
        saveas_Action.triggered.connect(self.saveasFile)
        file_Menu.addAction(saveas_Action)

        saveall_Action = QAction('Save All', self)
        saveall_Action.triggered.connect(self.saveAllFiles)
        file_Menu.addAction(saveall_Action)

        file_Menu.addSeparator()

        exit_Action = QAction('Exit', self)
        exit_Action.triggered.connect(self.close)
        file_Menu.addAction(exit_Action)

        # 创建多个文本编辑器的选项卡
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        # 设置主窗口属性
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('IDE')
        self.show()

    def newFile(self):
        # 创建新的文本编辑器选项卡
        text_edit = QTextEdit(self)
        highlighter = PythonSyntaxHighlighter(text_edit.document())
        self.tab_widget.addTab(text_edit, "Untitled")
    
    def openFile(self):
        # 打开文件对话框
        options = QFileDialog.Options()
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Files", "", "Text Files (*.txt);;All Files (*)", options=options)

        for file_path in file_paths:
            if file_path:
                # 创建新的文本编辑器选项卡
                text_edit = QTextEdit(self)
                highlighter = PythonSyntaxHighlighter(text_edit.document())
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

        # 打开文件对话框
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getSaveFileName()

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
            file_path = self.tab_widget.tabText(index)
            if current_tab:
                with open(file_path, 'w') as file:
                    file.write(current_tab.toPlainText())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ide = IDE()
    sys.exit(app.exec_())
