import csv
from io import StringIO

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

    def check_selection(self):
        """Check that selection mode is set to contiguous selection and verify
        that exactly one selection is set."""

        # The table must be set to contiguous selection. If not, show a critical error.
        if not self.selectionMode() == QAbstractItemView.ContiguousSelection:
            raise RuntimeError("Selection mode of the table must be set to ContiguousSelection.\n"
                               "This error will prevent copy/paste operations and can only be "
                               "fixed by contacting the program's author.")
        selection = self.selectedRanges()
        # If the selection list is empty, show an error box.
        if not selection:
            raise RuntimeError('No cells selected. Select some cells for the operation.')
        # If the selection list contains more than one item, show an error box.
        if len(selection) > 1:
            raise RuntimeError("The selection list contains more than one item. Since the "
                               "selection mode of the table must be set to ContiguousSelection, "
                               "This error should not have happened.\n"
                               "This error will prevent copy/paste operations and can only be "
                               "fixed by contacting the Program's author.")

    def return_csv_string(self, for_excel, selection=None):
        csv_stream = StringIO(newline='')
        if for_excel:
            csv_writer = csv.writer(csv_stream, delimiter='\t', dialect='excel')
        else:
            csv_writer = csv.writer(csv_stream, delimiter=',')
        if selection:
            row_range = range(selection.topRow(), selection.bottomRow() + 1)
            col_range = range(selection.leftColumn(), selection.rightColumn() + 1)
        else:
            row_range = range(self.rowCount())
            col_range = range(self.columnCount())
        for row in row_range:  # TODO: what about empty rows?
            row_list = []
            for col in col_range:
                current_cell = self.item(row, col)
                if current_cell:
                    row_list.append(current_cell.text())
                else:
                    row_list.append('')
            csv_writer.writerow(row_list)
        return csv_stream.getvalue().rstrip()

    def import_from_csv_string(self, csv_string, selection):
        buffer_io = StringIO(csv_string)
        # Sniff the dialect of the csv file because copy/paste uses tab but export uses comma.
        dialect = csv.Sniffer().sniff(buffer_io.readline())
        buffer_io.seek(0)
        csv_reader = csv.reader(buffer_io, dialect)
        row_list = [row for row in csv_reader]
        self.put_in_table(selection, row_list)

    def put_in_table(self, selection, row_list):
        """Put a selection of cells inside a certain place in the table."""

        # Validate row_list.
        num_csv_rows = len(row_list)
        num_csv_cols = max((len(r) for r in row_list))
        for r in row_list:
            if len(r) != num_csv_cols:
                raise ValueError('Number of columns is different for each row of the pasted table.')

        if selection:
            start_row = selection.topRow()
            end_row = selection.bottomRow()
            start_col = selection.leftColumn()
            end_col = selection.rightColumn()
        else:
            start_row = 0
            end_row = self.rowCount() - 1
            start_col = 0
            end_col = self.columnCount() - 1

        # Case 1: selection is a single cell.
        if (start_row == end_row) and (start_col == end_col):
            # Make sure enough rows and columns exist. Add rows if necessary.
            if self.columnCount() < start_col + num_csv_cols:
                raise ValueError('Number of columns in row_list exceeds the number of columns in '
                                 'the table. Either the selection or row_list are inappropriate')
            while self.rowCount() < start_row + num_csv_rows:
                self.insertRow(self.rowCount())
        else:  # Case 2: selection is multiple cells which must have the same size as row_list.
            if not ((end_row - start_row == num_csv_rows - 1)
                    and (end_col - start_col == num_csv_cols - 1)):
                raise ValueError('Dimensions of the selected and pasted cells are different. '
                                 'Either reselect cells or select a single cell as the start '
                                 'point.')

        # Validate contents of row_list using the table's validators.
        csv_r = 0
        for row in range(start_row, start_row + num_csv_rows):
            csv_c = 0
            for col in range(start_col, start_col + num_csv_cols):
                if self.itemDelegateForColumn(col). \
                        validator_obj.validate(row_list[csv_r][csv_c], 0)[0] != 2:
                    raise ValueError('Invalid data "%s" in row %i, column %i.'
                                     % (row_list[csv_r][csv_c], csv_r + 1, csv_c + 1))
                csv_c += 1
            csv_r += 1

        # Place the contents of row_list into the table.
        csv_r = 0
        for row in range(start_row, start_row + num_csv_rows):
            csv_c = 0
            for col in range(start_col, start_col + num_csv_cols):
                self.setItem(row, col, QTableWidgetItem(row_list[csv_r][csv_c]))
                csv_c += 1
            csv_r += 1

    def copy_selection(self):
        try:
            self.check_selection()
        except RuntimeError as err:
            QMessageBox.critical(self, 'Copy Unsuccessful!', str(err))
            return
        selection = self.selectedRanges()
        selection = selection[0]
        QApplication.clipboard().setText(
            self.return_csv_string(for_excel=True, selection=selection))

    def paste_selection(self):
        try:
            self.check_selection()
        except RuntimeError as err:
            QMessageBox.critical(self, 'Paste Unsuccessful!', str(err))
            return
        selection = self.selectedRanges()
        selection = selection[0]
        try:
            self.import_from_csv_string(csv_string=QApplication.clipboard().text(),
                                        selection=selection)
        except ValueError as err:
            QMessageBox.critical(self, 'Paste Unsuccessful!', str(err))
            return


class MatCodeDelegate(QStyledItemDelegate):
    validator_obj = QIntValidator(0, 999999999)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(self.validator_obj)
        return editor


class PositionFloatDelegate(QStyledItemDelegate):
    validator_obj = QDoubleValidator(-1e+6, 1e+6, 12)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(self.validator_obj)
        return editor

    def setModelData(self, editor, model, index):
        model.setData(index, str(float(editor.text())))


class RadiusFloatDelegate(QStyledItemDelegate):
    validator_obj = QDoubleValidator(1e-6, 1e+6, 12)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(self.validator_obj)
        return editor

    def setModelData(self, editor, model, index):
        model.setData(index, str(float(editor.text())))
