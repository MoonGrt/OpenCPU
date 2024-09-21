import sys
from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QVBoxLayout, QWidget, QHBoxLayout

class ComboTableWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ComboBox with Input Example")
        
        # 创建表格
        self.table_widget = QTableWidget(5, 2)  # 5 行 2 列
        self.table_widget.setHorizontalHeaderLabels(["Item", "Options"])
        
        # 添加下拉框和输入框
        for row in range(5):
            item = QTableWidgetItem(f"Item {row + 1}")
            self.table_widget.setItem(row, 0, item)
            
            combo_box = QComboBox()
            combo_box.addItems(["Option 1", "Option 2", "Option 3"])
            
            # 输入框
            input_field = QLineEdit()
            input_field.setPlaceholderText("Add option...")
            
            # 布局
            h_layout = QHBoxLayout()
            h_layout.addWidget(combo_box)
            h_layout.addWidget(input_field)

            # 输入框内容变化时更新下拉框
            input_field.textChanged.connect(lambda text, cb=combo_box: self.update_combobox(text, cb))

            # 设置单元格的布局
            cell_widget = QWidget()
            cell_widget.setLayout(h_layout)
            self.table_widget.setCellWidget(row, 1, cell_widget)

        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        self.setLayout(layout)

    def update_combobox(self, text, combo_box):
        if text and text not in combo_box.items():  # 避免重复添加
            combo_box.addItem(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ComboTableWidget()
    window.show()
    sys.exit(app.exec_())
