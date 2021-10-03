import sys
from configparser import ConfigParser
from os import path
from pathlib import Path

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, QRegularExpression
from PyQt5.QtGui import QIntValidator, QValidator, QRegularExpressionValidator, QDoubleValidator
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QTableWidgetSelectionRange, QFileDialog


def return_default_results_path(part_name=None):  # TODO: remove this and import from vcams.
    parts = ['Desktop', 'VCAMS Working Directory']
    # Validate part_name.
    if part_name is None:
        pass  # No subfolder.
    else:
        parts.append(part_name)
    return Path.home().joinpath(*parts)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Load the UI Page
        uic.loadUi(path.join(path.dirname(__file__), 'main_window.ui'), self)

        # Connect signals for the menu.
        # self.action_import_settings.triggered.connect(self.import_settings)  # TODO
        self.action_export_settings.triggered.connect(self.export_settings)
        self.action_exit.triggered.connect(self.close)

        # Connect the signals.
        self.mask_add_pb.clicked.connect(self.table_mask_add)
        self.mask_delete_pb.clicked.connect(self.table_mask_delete_row)
        self.mask_move_up_pb.clicked.connect(self.table_mask_move_up)
        self.mask_move_down_pb.clicked.connect(self.table_mask_move_down)

        # Connect signals for the Basic Modeling Information tab.
        # part_name
        self.part_name = self.part_name_field.text()
        part_name_regex = "^(?=.*[ -~])(?=.*[^$&*~!()\[\]{}|;'`\",.?/\\])(?=^[A-Za-z])^.{1,37}[^_]$"
        self.part_name_field.setValidator(QRegularExpressionValidator(
            QRegularExpression(part_name_regex)))
        self.part_name_field_default_style = self.part_name_field.styleSheet()
        self.part_name_field.textChanged.connect(self.determine_validity_visually)
        self.part_name_field.textChanged.connect(self.part_name_changed)

        # num_voxels
        num_voxels_validator = QIntValidator(1, 999999999, self)
        self.num_voxels_x_field.setValidator(num_voxels_validator)
        self.num_voxels_y_field.setValidator(num_voxels_validator)
        self.num_voxels_z_field.setValidator(num_voxels_validator)
        self.num_voxels_x_field.textChanged.connect(self.determine_validity_visually)
        self.num_voxels_y_field.textChanged.connect(self.determine_validity_visually)
        self.num_voxels_z_field.textChanged.connect(self.determine_validity_visually)
        self.num_voxels_x_field.textChanged.connect(self.calculate_part_size)
        self.num_voxels_y_field.textChanged.connect(self.calculate_part_size)
        self.num_voxels_z_field.textChanged.connect(self.calculate_part_size)

        # voxel_size
        voxel_size_validator = QDoubleValidator(1e-6, 1e+6, 8)
        self.voxel_size_x_field.setValidator(voxel_size_validator)
        self.voxel_size_y_field.setValidator(voxel_size_validator)
        self.voxel_size_z_field.setValidator(voxel_size_validator)
        self.voxel_size_x_field.textChanged.connect(self.determine_validity_visually)
        self.voxel_size_y_field.textChanged.connect(self.determine_validity_visually)
        self.voxel_size_z_field.textChanged.connect(self.determine_validity_visually)
        self.voxel_size_x_field.textChanged.connect(self.calculate_part_size)
        self.voxel_size_y_field.textChanged.connect(self.calculate_part_size)
        self.voxel_size_z_field.textChanged.connect(self.calculate_part_size)

        # num_mats_combo
        self.num_mats_combo.currentIndexChanged.connect(self.calculate_part_size)

        # working_dir
        self.working_dir = str(return_default_results_path(part_name=self.part_name))
        self.custom_working_dir = None
        self.working_dir_select_button.clicked.connect(self.select_working_dir)

    def calculate_part_size(self):
        # For part_size fields.
        num_mats_combo_size_list = [1, 2, 4, 8]  # In bytes.
        if (self.num_voxels_x_field.hasAcceptableInput() and
                self.voxel_size_x_field.hasAcceptableInput()):
            self.part_size_x_field.setText(str(int(self.num_voxels_x_field.text())
                                               * float(self.voxel_size_x_field.text())))
        if (self.num_voxels_y_field.hasAcceptableInput() and
                self.voxel_size_y_field.hasAcceptableInput()):
            self.part_size_y_field.setText(str(int(self.num_voxels_y_field.text())
                                               * float(self.voxel_size_y_field.text())))
        if (self.num_voxels_z_field.hasAcceptableInput() and
                self.voxel_size_z_field.hasAcceptableInput()):
            self.part_size_z_field.setText(str(int(self.num_voxels_z_field.text())
                                               * float(self.voxel_size_z_field.text())))
        # For model_size_field.
        if (self.num_voxels_x_field.hasAcceptableInput() and
                self.num_voxels_y_field.hasAcceptableInput() and
                self.num_voxels_z_field.hasAcceptableInput()):
            num_elems = (int(self.num_voxels_x_field.text()) * int(self.num_voxels_y_field.text())
                         * int(self.num_voxels_z_field.text()))
            required_memory = (num_elems *
                               num_mats_combo_size_list[self.num_mats_combo.currentIndex()]
                               / 2 ** 20)  # In Megabytes.
            msg_1 = f'The model contains {num_elems:,} elements and consumes '
            if required_memory < 1:
                required_memory = required_memory * 2**10
                msg_2 = f'{required_memory:0.2f} KB of RAM.'
            else:
                msg_2 = f'{required_memory:0.2f} MB of RAM.'
            self.model_size_field.setText(msg_1+msg_2)


    def determine_validity_visually(self):
        if not self.sender().hasAcceptableInput():
            self.sender().setStyleSheet("border: 1px solid red;")  # FIXME: field size changes.
        else:
            self.sender().setStyleSheet("border: 1px solid black;")  # TODO: parameterize.

    def part_name_changed(self):
        self.part_name = self.part_name_field.text()
        if self.custom_working_dir is None:
            self.working_dir = str(return_default_results_path(part_name=self.part_name))
        else:
            self.working_dir = self.custom_working_dir
        self.working_dir_field.setText(self.working_dir)

    def select_working_dir(self):
        self.custom_working_dir = self.working_dir
        dir_str = QFileDialog.getExistingDirectory(self, 'Select the working directory.',
                                                   self.working_dir, QFileDialog.ShowDirsOnly)
        dir_str = path.normpath(dir_str)
        self.custom_working_dir = dir_str
        self.working_dir = dir_str
        self.working_dir_field.setText(dir_str)

    # def closeEvent(self, event):
    #     #TODO: add save prompt.
    #     reply = QMessageBox.question(self, 'Close Program?',
    #                                  'Are you sure you want to close the program?',
    #                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    #     if reply == QMessageBox.Yes:
    #         event.accept()
    #     else:
    #         event.ignore()

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

    def export_settings(self):
        config = ConfigParser()

        # TODO: loop over and if not .hasAcceptableInput(), move focus and mark it.

        # Tab: Basic Model Information
        config['Basic'] = {}
        config['Basic']['part_name'] = self.part_name_field.text()  # TODO: use for name of ini file
        config['Basic']['dim'] = self.dim_combo.currentText()
        config['Basic']['num_voxels_x'] = self.num_voxels_x_field.text()
        config['Basic']['num_voxels_y'] = self.num_voxels_y_field.text()
        config['Basic']['num_voxels_z'] = self.num_voxels_z_field.text()
        config['Basic']['voxel_size_x'] = self.voxel_size_x_field.text()
        config['Basic']['voxel_size_y'] = self.voxel_size_y_field.text()
        config['Basic']['voxel_size_z'] = self.voxel_size_z_field.text()
        config['Basic']['num_mats'] = str(self.num_mats_combo.currentIndex())
        # TODO: check with long text.
        config['Basic']['part_description'] = self.part_description_field.toPlainText()
        config['Basic']['working_dir'] = self.working_dir_field.text()
        config['Basic']['log_debug'] = str(self.log_debug_checkbox.isChecked())

        # Write to output.
        working_dir_path = Path(self.working_dir)
        working_dir_path.mkdir(parents=True, exist_ok=True)
        with open(working_dir_path.joinpath(self.part_name + '.vcams'), 'w') as config_file:
            config.write(config_file)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
