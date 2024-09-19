import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QTableWidget, QTableWidgetItem, QRadioButton, QButtonGroup

class ModeSwitcher(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        # 创建文本编辑框和表格控件
        self.text_edit = QTextEdit()
        self.table_widget = QTableWidget()
        self.table_widget.setVisible(False)  # 默认隐藏表格控件

        # 创建单选按钮
        self.text_mode_radio = QRadioButton('Text Mode')
        self.table_mode_radio = QRadioButton('Table Mode')

        # 将单选按钮分组
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.text_mode_radio)
        self.button_group.addButton(self.table_mode_radio)
        self.text_mode_radio.setChecked(True)  # 默认选择文本模式

        # 连接单选按钮的切换信号
        self.text_mode_radio.toggled.connect(self.switch_mode)
        self.table_mode_radio.toggled.connect(self.switch_mode)

        # 创建布局
        layout = QVBoxLayout()
        layout.addWidget(self.text_mode_radio)
        layout.addWidget(self.table_mode_radio)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.table_widget)
        self.setLayout(layout)

        self.setWindowTitle('Text and Table Mode Switcher')
        self.switch_mode()  # 初始化时设置显示模式

    def switch_mode(self):
        if self.text_mode_radio.isChecked():
            # 从表格模式转换到文本模式
            rows = self.table_widget.rowCount()
            text_lines = []
            for row in range(rows):
                cells = [self.table_widget.item(row, col).text() if self.table_widget.item(row, col) else '' for col in range(self.table_widget.columnCount())]
                text_lines.append(' '.join(cells))

            text = '\n'.join(text_lines)
            self.text_edit.setPlainText(text)
            self.text_edit.setVisible(True)
            self.table_widget.setVisible(False)
        elif self.table_mode_radio.isChecked():
            # 从文本模式转换到表格模式
            text = self.text_edit.toPlainText()
            lines = text.splitlines()
            self.table_widget.setRowCount(len(lines))
            self.table_widget.setColumnCount(1)  # 设置列数为1

            for row, line in enumerate(lines):
                # 将每行的文本分割成单元格
                cells = line.split()  # 可以自定义分隔符，如逗号、制表符等
                self.table_widget.setRowCount(len(cells))
                self.table_widget.setColumnCount(1)

                for col, cell in enumerate(cells):
                    self.table_widget.setItem(row, col, QTableWidgetItem(cell))

            self.text_edit.setVisible(False)
            self.table_widget.setVisible(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ModeSwitcher()
    window.show()
    sys.exit(app.exec_())
