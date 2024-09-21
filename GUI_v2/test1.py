import sys
from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QComboBox, QVBoxLayout, QWidget

class IOPlanningTable(QWidget):
    def __init__(self):
        super().__init__()

        # 创建一个表格，初始1行3列
        self.table = QTableWidget(0, 3)  
        self.table.setHorizontalHeaderLabels(['Signal Name', 'Pin', 'I/O Standard'])

        # 初始化时插入一行空数据
        self.add_empty_row()

        # 连接信号：当单元格内容改变时，检查是否需要添加新行
        self.table.cellChanged.connect(self.check_and_add_row)

        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

    def add_empty_row(self):
        """向表格中添加一行空数据"""
        row_position = self.table.rowCount()  # 当前行数

        # 添加一个新的空行
        self.table.insertRow(row_position)

        # 第一列：信号名称，空
        self.table.setItem(row_position, 0, QTableWidgetItem(""))

        # 第二列：引脚选择，使用QComboBox，默认无选项
        pin_combo = QComboBox()
        pin_combo.addItems([""] + [f'Pin {i}' for i in range(1, 6)])  # 添加一个空选项
        self.table.setCellWidget(row_position, 1, pin_combo)

        # 第三列：I/O标准选择，使用QComboBox，默认无选项
        io_combo = QComboBox()
        io_combo.addItems([""] + ['LVCMOS33', 'LVCMOS18', 'LVTTL', 'HSTL'])  # 添加一个空选项
        self.table.setCellWidget(row_position, 2, io_combo)

    def check_and_add_row(self):
        """检查最后一行是否填写完整，如果是，则添加新行"""
        row_position = self.table.rowCount() - 1  # 当前最后一行的索引
        signal_item = self.table.item(row_position, 0)
        pin_combo = self.table.cellWidget(row_position, 1)
        io_combo = self.table.cellWidget(row_position, 2)

        # 检查当前行是否填写完整（信号名称不为空，且两个QComboBox有选项）
        if (signal_item is not None and signal_item.text().strip() != "") and \
           (pin_combo.currentText().strip() != "") and \
           (io_combo.currentText().strip() != ""):
            # 添加新的一行
            self.add_empty_row()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = IOPlanningTable()
    window.setWindowTitle('I/O Planning Table')
    window.show()
    sys.exit(app.exec_())
