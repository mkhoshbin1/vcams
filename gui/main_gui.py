import sys
from os import path

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QTableWidgetSelectionRange


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Load the UI Page
        uic.loadUi(path.join(path.dirname(__file__), 'main_window.ui'), self)

        # Connect the signals.
        self.mask_add_pb.clicked.connect(self.table_mask_add)
        self.mask_delete_pb.clicked.connect(self.table_mask_delete_row)
        self.mask_move_up_pb.clicked.connect(self.table_mask_move_up)
        self.mask_move_down_pb.clicked.connect(self.table_mask_move_down)

    def table_mask_add(self, row=1, items=('asd', 'asd', '')):
        # TODO: add exception for row 0.
        self.mask_table.insertRow(row)
        self.mask_table.setItem(row, 0, QTableWidgetItem(0))
        self.mask_table.setItem(row, 1, QTableWidgetItem(items[0]))
        self.mask_table.setItem(row, 2, QTableWidgetItem(items[0]))
        self.mask_table.setItem(row, 3, QTableWidgetItem(items[0]))
        self.table_mask_clean()

    def table_mask_delete_row(self):
        selected_rows = set(i.row() for i in self.mask_table.selectedItems())
        if 0 in selected_rows:
            QMessageBox.information(self, "Error!",
                                    "The 'Initial Fill' Operation cannot be edited, deleted, "
                                    "or moved.")
            self.table_mask_select_moved(selected_rows, direction=0)
            return
        for r in selected_rows:
            self.mask_table.removeRow(r)
        self.table_mask_clean()

    def table_mask_move_up(self):
        selected_rows = set(i.row() for i in self.mask_table.selectedItems())
        self.table_mask_move_rows(selected_rows, direction=-1)

    def table_mask_move_down(self):
        selected_rows = set(i.row() for i in self.mask_table.selectedItems())
        if self.mask_table.rowCount() - 1 in selected_rows:
            QMessageBox.information(self, 'Error!', 'The last row cannot be moved any lower!')
            self.table_mask_select_moved(selected_rows, direction=0)
            return
        self.table_mask_move_rows(selected_rows, direction=+1)

    def table_mask_move_rows(self, selected_rows, direction):
        if 0 in selected_rows:
            QMessageBox.information(self, "Error!",
                                    "The 'Initial Fill' Operation cannot be edited, deleted, "
                                    "or moved.")
            self.table_mask_select_moved(selected_rows, direction=0)
            return
        selected_rows = list(selected_rows)
        if direction == +1:
            selected_rows.sort(reverse=True)
        elif direction == -1:
            selected_rows.sort(reverse=False)
        else:
            raise ValueError('direction must be +1 or -1 for moving down and up, respectively.')
        num_columns = self.mask_table.columnCount()
        for r in selected_rows:
            row_items = [self.mask_table.takeItem(r, c) for c in range(num_columns)]
            self.mask_table.removeRow(r)
            self.mask_table.insertRow(r + direction)
            [self.mask_table.setItem(r + direction, c, row_items[c]) for c in range(num_columns)]
            self.mask_table.repaint()
        self.table_mask_clean()
        self.table_mask_select_moved(selected_rows, direction)

    def table_mask_clean(self):
        # Update step numbers and center all texts.
        for r in range(self.mask_table.rowCount()):
            self.mask_table.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            for c in range(self.mask_table.columnCount() - 1):
                item = self.mask_table.item(r, c)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)

    def table_mask_select_moved(self, selected_rows, direction):
        sel_range = QTableWidgetSelectionRange(max(0, min(selected_rows) + direction), 0,
                                               max(selected_rows) + direction,
                                               self.mask_table.columnCount() - 1)
        self.mask_table.setRangeSelected(sel_range, True)
        self.mask_table.setFocus()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
