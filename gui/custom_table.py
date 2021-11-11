from io import StringIO
import csv

from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QTableWidget, QAbstractItemView, QApplication


# TODO: add the add_row functionality.
class CustomTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(QTableWidget, self).__init__(*args, **kwargs)
        self.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and event.matches(QKeySequence.Copy):
            self.copy_selection()
            return True
        elif event.type() == QEvent.KeyPress and event.matches(QKeySequence.Paste):
            self.paste_selection()
            return True
        return super(QTableWidget, self).eventFilter(source, event)

    def copy_selection(self):
        # The table must be set to contiguous selection. If not, show a critical error.
        if not self.selectionMode() == QAbstractItemView.ContiguousSelection:
            print('sdfg')  # TODO
            return

        selection = self.selectedRanges()
        # If the selection list is empty, show an error box.
        if not selection:
            print('sdfg')  # TODO
            return
        # If the selection list contains more than one item, show an error box.
        if len(selection) > 1:
            print('sdfg')  # TODO
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
        print('dfvgfdf')

    #     selection = self.selectedIndexes()
    #     if selection:
    #         model = self.model()
    #
    #         buffer = QApplication.clipboard().text()
    #         all_rows = []
    #         all_columns = []
    #         for index in selection:
    #             if not index.row() in all_rows:
    #                 all_rows.append(index.row())
    #             if not index.column() in all_columns:
    #                 all_columns.append(index.column())
    #         visible_rows = [row for row in all_rows if not self.isRowHidden(row)]
    #         visible_columns = [
    #             col for col in all_columns if not self.isColumnHidden(col)
    #         ]
    #
    #         reader = csv.reader(io.StringIO(buffer), delimiter="\t")
    #         arr = [[cell for cell in row] for row in reader]
    #         if len(arr) > 0:
    #             nrows = len(arr)
    #             ncols = len(arr[0])
    #             if len(visible_rows) == 1 and len(visible_columns) == 1:
    #                 # Only the top-left cell is highlighted.
    #                 for i in range(nrows):
    #                     insert_rows = [visible_rows[0]]
    #                     row = insert_rows[0] + 1
    #                     while len(insert_rows) < nrows:
    #                         row += 1
    #                         if not self.isRowHidden(row):
    #                             insert_rows.append(row)
    #                 for j in range(ncols):
    #                     insert_columns = [visible_columns[0]]
    #                     col = insert_columns[0] + 1
    #                     while len(insert_columns) < ncols:
    #                         col += 1
    #                         if not self.isColumnHidden(col):
    #                             insert_columns.append(col)
    #                 for i, insert_row in enumerate(insert_rows):
    #                     for j, insert_column in enumerate(insert_columns):
    #                         cell = arr[i][j]
    #                         model.setData(model.index(insert_row, insert_column), cell)
    #             else:
    #                 # Assume the selection size matches the clipboard data size.
    #                 for index in selection:
    #                     selection_row = visible_rows.index(index.row())
    #                     selection_column = visible_columns.index(index.column())
    #                     model.setData(
    #                         model.index(index.row(), index.column()),
    #                         arr[selection_row][selection_column],
    #                     )
    #     return
