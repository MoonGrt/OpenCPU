import sys
from PyQt5.QtWidgets import (
    QApplication, QTableWidget, QTableWidgetItem, QComboBox, QVBoxLayout, QWidget
)

class IOPlanningTable(QWidget):
    def __init__(self):
        super().__init__()

        # 定义允许的选项
        self.allowed_pins = [f'Pin {i}' for i in range(1, 6)]
        self.allowed_io_standards = ['LVCMOS33', 'LVCMOS18', 'LVTTL', 'HSTL']

        # 创建一个表格，初始0行3列
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

        # 示例数据，包括有效和无效的选项
        data = [
            ("Signal_1", "Pin 1", "LVCMOS33"),    # 全部有效
            ("Signal_2", "Pin 6", "LVTTL"),       # Pin 无效（Pin 6 不存在）
            ("Signal_3", "Pin 3", "InvalidIO"),   # I/O Standard 无效
            ("Signal_4", "Pin 2", "HSTL"),        # 全部有效
            ("Signal_5", "InvalidPin", "LVCMOS18")# Pin 和 I/O Standard 均无效
        ]

        # 填充数据
        for row_data in data:
            self.add_empty_row()  # 确保有足够的行
            self.fill_data(self.table.rowCount() - 1, *row_data)

    def add_empty_row(self):
        """向表格中添加一行空数据"""
        row_position = self.table.rowCount()  # 当前行数

        # 添加一个新的空行
        self.table.insertRow(row_position)

        # 第一列：信号名称，空
        self.table.setItem(row_position, 0, QTableWidgetItem(""))

        # 第二列：引脚选择，使用QComboBox，默认无选项
        pin_combo = QComboBox()
        pin_combo.addItems([""] + self.allowed_pins)  # 添加一个空选项
        self.table.setCellWidget(row_position, 1, pin_combo)

        # 第三列：I/O标准选择，使用QComboBox，默认无选项
        io_combo = QComboBox()
        io_combo.addItems([""] + self.allowed_io_standards)  # 添加一个空选项
        self.table.setCellWidget(row_position, 2, io_combo)

    def fill_data(self, row, signal_name, pin, io_standard):
        """向表格的指定行填入数据，只有当数据在允许的选项中时才填充"""
        # 设置信号名称
        self.table.setItem(row, 0, QTableWidgetItem(signal_name))

        # 设置引脚选择
        pin_combo = QComboBox()
        pin_combo.addItems([""] + self.allowed_pins)
        if pin in self.allowed_pins:
            pin_combo.setCurrentText(pin)  # 设置指定引脚
        else:
            pin_combo.setCurrentText("")  # 设置为空
        self.table.setCellWidget(row, 1, pin_combo)

        # 设置I/O标准选择
        io_combo = QComboBox()
        io_combo.addItems([""] + self.allowed_io_standards)
        if io_standard in self.allowed_io_standards:
            io_combo.setCurrentText(io_standard)  # 设置指定I/O标准
        else:
            io_combo.setCurrentText("")  # 设置为空
        self.table.setCellWidget(row, 2, io_combo)

    def check_and_add_row(self, row, column):
        """检查最后一行是否填写完整，如果是，则添加新行"""
        # 仅在最后一行变化时才检查
        if row != self.table.rowCount() - 1:
            return

        signal_item = self.table.item(row, 0)
        pin_combo = self.table.cellWidget(row, 1)
        io_combo = self.table.cellWidget(row, 2)

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
