from io import StringIO
import csv

from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QKeySequence, QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QTableWidget, QAbstractItemView, QApplication, QTableWidgetItem, \
    QMessageBox, QStyledItemDelegate, QLineEdit


class CustomTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(QTableWidget, self).__init__(*args, **kwargs)
        self.installEventFilter(self)
        self.cellActivated.connect(self.add_row_to_end)

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and event.matches(QKeySequence.Copy):
            self.copy_selection()
            return True
        elif event.type() == QEvent.KeyPress and event.matches(QKeySequence.Paste):
            self.paste_selection()
            return True
        return super(QTableWidget, self).eventFilter(source, event)

    # noinspection PyUnusedLocal
    def add_row_to_end(self, row, column):
        sender_table = self.sender()
        if row == sender_table.rowCount() - 1:
            sender_table.insertRow(row + 1)

    def copy_selection(self):
        # The table must be set to contiguous selection. If not, show a critical error.
        if not self.selectionMode() == QAbstractItemView.ContiguousSelection:
            QMessageBox.critical(self, 'Copy Unsuccessful!',
                                 "Selection mode of the table must be set to ContiguousSelection.\n"
                                 "This error will prevent copy/paste operations and can only be "
                                 "fixed by contacting the Program's author.")
            return

        selection = self.selectedRanges()
        # If the selection list is empty, show an error box.
        if not selection:
            QMessageBox.critical(self, 'Copy Unsuccessful!',
                                 'Select some cells to be copied.')
            return
        # If the selection list contains more than one item, show an error box.
        if len(selection) > 1:
            QMessageBox.critical(self, 'Copy Unsuccessful!',
                                 "The selection list contains more than one item. Since the "
                                 "selection mode of the table must be set to ContiguousSelection, "
                                 "This error must not happen.\n"
                                 "This error will prevent copy/paste operations and can only be "
                                 "fixed by contacting the Program's author.")
            return
        selection = selection[0]

        # Create a csv in the memory based on table contents.
        csv_stream = StringIO()
        csv_writer = csv.writer(csv_stream, delimiter='\t', dialect='excel')  # Excel works with \t.
        for r in range(selection.topRow(), selection.bottomRow() + 1):
            row_list = []
            for c in range(selection.leftColumn(), selection.rightColumn() + 1):
                current_cell = self.item(r, c)
                if current_cell:
                    row_list.append(current_cell.text())
                else:
                    row_list.append('')
            csv_writer.writerow(row_list)

        # Put the csv_stream in the clipboard.
        QApplication.clipboard().setText(csv_stream.getvalue())
        return

    def paste_selection(self):
        # The table must be set to contiguous selection. If not, show a critical error.
        if not self.selectionMode() == QAbstractItemView.ContiguousSelection:
            QMessageBox.critical(self, 'Paste Unsuccessful!',
                                 "Selection mode of the table must be set to ContiguousSelection.\n"
                                 "This error will prevent copy/paste operations and can only be "
                                 "fixed by contacting the Program's author.")
            return

        # Validate the selection.
        selection = self.selectedRanges()
        # If the selection list is empty, show an error box.
        if not selection:
            QMessageBox.critical(self, 'Paste Unsuccessful!',
                                 'No cells are selected.\n'
                                 'Select one cell as the starting point for pasting or select a '
                                 'group of cells with the exact shape of the data you want to '
                                 'paste.')
            return
        # If the selection list contains more than one item, show an error box.
        if len(selection) > 1:
            QMessageBox.critical(self, 'Paste Unsuccessful!',
                                 "The selection list contains more than one item. Since the "
                                 "selection mode of the table must be set to ContiguousSelection, "
                                 "This error must not happen.\n"
                                 "This error will prevent copy/paste operations and can only be "
                                 "fixed by contacting the Program's author.")
            return
        selection = selection[0]
        start_row = selection.topRow()
        start_col = selection.leftColumn()

        # Create an array for the pasted cells.
        # Open the text in the clipboard.
        buffer = QApplication.clipboard().text()
        buffer_io = StringIO(buffer)
        # Sniff the dialect of the csv file. This is done because excel uses tab,
        # but many users may prefer commas.
        dialect = csv.Sniffer().sniff(buffer_io.readline())
        buffer_io.seek(0)
        csv_reader = csv.reader(buffer_io, dialect)

        # Get the text of each cell in every row.
        row_list = [row for row in csv_reader]
        num_csv_rows = len(row_list)
        num_csv_cols = max((len(r) for r in row_list))
        for r in row_list:
            if len(r) != num_csv_cols:
                QMessageBox.critical(self, 'Paste Unsuccessful!',
                                     "Number of columns is different for each row of the pasted "
                                     "table.\nThis error probably should not happen. Please "
                                     "contact the Program's author.")
                return
        # TODO: use self.itemDelegateForColumn.validator_obj.validate(string, 0)[0] to validate.

        # There are two valid selection types:
        # Case 1: Single cell which determines the beginning of the pasted cells.
        # Case 2: Multiple cells which must be of equal size to the pasted cell.

        # Case 1: Single cell.
        if (selection.topRow() == selection.bottomRow()) \
                and (selection.leftColumn() == selection.rightColumn()):

            # Make sure enough rows and columns exist. If not, create additional ones.
            while self.rowCount() < start_row + num_csv_rows:
                self.insertRow(self.rowCount())
            if self.columnCount() < start_col + num_csv_cols:
                QMessageBox.critical(self, 'Paste Unsuccessful!',
                                     'The pasted columns exceed the number of columns. '
                                     'Either the selection or the pasted cells are inappropriate.')
                return

            # Place the contents of row_list into the table.
            csv_r = 0
            for row in range(start_row, start_row + num_csv_rows):
                csv_c = 0
                for col in range(start_col, start_col + num_csv_cols):
                    self.setItem(row, col, QTableWidgetItem(row_list[csv_r][csv_c]))
                    csv_c += 1
                csv_r += 1

        # Case 2: Multiple cells selected which must be of the same size as the pasted table.
        else:
            if not ((selection.topRow() - selection.bottomRow() == num_csv_rows)
                    and (selection.leftColumn() - selection.rightColumn() == num_csv_cols)):
                QMessageBox.critical(self, 'Paste Unsuccessful!',
                                     'Dimensions of the selected and pasted cells are '
                                     'different. Either reselect cells or select a single cell '
                                     'as the  start point.')
                return

            # Place the contents of row_list into the table.
            csv_r = 0
            for row in range(start_row, start_row + num_csv_rows):
                csv_c = 0
                for col in range(start_col, start_col + num_csv_cols):
                    self.setItem(row, col, QTableWidgetItem(row_list[csv_r][csv_c]))
                    csv_c += 1
                csv_r += 1


class IntDelegate(QStyledItemDelegate):
    validator_obj = QIntValidator(1, 999999999)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(self.validator_obj)
        return editor


class FloatDelegate(QStyledItemDelegate):
    validator_obj = QDoubleValidator(1e-6, 1e+6, 12)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(self.validator_obj)
        return editor

    def setModelData(self, editor, model, index):
        model.setData(index, str(float(editor.text())))
