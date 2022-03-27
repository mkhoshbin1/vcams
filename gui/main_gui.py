import logging
import sys
from collections import namedtuple
import logging
from pathlib import Path

from matplotlib import rcParams
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
# noinspection PyUnresolvedReferences
from PyQt5 import uic
from PyQt5.QtCore import Qt, QRegularExpression, QUrl, QCoreApplication
from PyQt5.QtGui import QIntValidator, QRegularExpressionValidator, QDoubleValidator, \
    QImage, QPixmap, QDesktopServices
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QTableWidgetSelectionRange, \
    QFileDialog, QButtonGroup, QMainWindow, QApplication, QStyleFactory

from custom_table import IntDelegate, RadiusFloatDelegate, PositionFloatDelegate
from settings_io import export_settings, import_settings

from vcams import __name__ as vcams_name
from vcams import __repo__ as repo_url, __docs__ as docs_url, gui_footer_notice, about_vcams
from vcams.helper import return_default_results_path
from vcams.mask.tpms import tpms_dict
from vcams.voxelpart import from_config_file

logger = logging.getLogger(vcams_name)

ModelingMode = namedtuple('ModelingMode', ('name', 'dim', 'page_id', 'description'))
modeling_mode_list = (ModelingMode('Please select a modeling mode...', 0, 0,
                                   'This form will be used to model a structure after you select '
                                   'the modeling mode.'),
                      ModelingMode('No Further Manipulation',
                                   0, 1,
                                   'This option does noting.\n'
                                   'The model will completely consist of the elements '
                                   'with the base material specified in the previous tab.'),
                      ModelingMode('Triply Periodic Minimal Surface (TPMS)',
                                   3, 2,
                                   'This form is used to model a triply periodic minimal '
                                   'surface (TPMS) in the 3D space:'),
                      ModelingMode('Planar Particle Reinforced Composite (Circular Inclusions)',
                                   2, 3,
                                   'This form is used to model a planar particle reinforced '
                                   'composite with circular particles:'),
                      ModelingMode('Spatial Particle Reinforced Composite (Spherical Inclusions)',
                                   3, 4,
                                   'This form is used to model a spatial particle reinforced '
                                   'composite with spherical particles:'),
                      # ModelingMode('Image Processing (Single Image)',
                      #              2, 4,
                      #              'This form is used to create a 2D model based on a single'
                      #              'binary or grayscale image:')
                      )


def mathtex_to_qpixmap(math_tex, font_size):  # TODO: see if you can make it shorter.
    rcParams['mathtext.fontset'] = 'cm'
    # Create a figure.
    fig = plt.figure()
    fig.patch.set_facecolor('none')
    fig.set_canvas(FigureCanvasAgg(fig))
    renderer = fig.canvas.get_renderer()
    # Add the plot.
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')
    ax.patch.set_facecolor('none')
    t = ax.text(0, 0, math_tex, ha='left', va='bottom', fontsize=font_size)
    # Fit figure size to text artist.
    fwidth, fheight = fig.get_size_inches()
    fig_bbox = fig.get_window_extent(renderer)
    text_bbox = t.get_window_extent(renderer)
    tight_fwidth = text_bbox.width * fwidth / fig_bbox.width
    tight_fheight = text_bbox.height * fheight / fig_bbox.height
    fig.set_size_inches(tight_fwidth, tight_fheight)
    # Convert figure to QPixmap.
    buf, size = fig.canvas.print_to_buffer()
    qimage = QImage.rgbSwapped(QImage(buf, size[0], size[1],
                                      QImage.Format_ARGB32))
    qpixmap = QPixmap(qimage)
    return qpixmap


class QTextEditLogger(logging.Handler):
    """Logging handler for displaying the log in a QPlainTextEdit.
    Adapted from: https://stackoverflow.com/a/51641943/7180705
    """

    def __init__(self, plaintextedit_obj):
        super().__init__()
        self.widget = plaintextedit_obj
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)
        self.widget.repaint()  # The preferred way is a QThread, but this should be OK.


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Load the UI Page.
        uic.loadUi(Path.joinpath(Path(__file__).resolve().parent, 'main_window.ui'), self)
        # Update the footer notice.
        self.footer_label.setText(gui_footer_notice)

        # Connect signals for the menu.
        self.action_import_settings.triggered.connect(self.import_config)
        self.action_export_settings.triggered.connect(self.export_config)
        self.action_exit.triggered.connect(self.close)
        self.action_docs.triggered.connect(lambda x: QDesktopServices.openUrl(QUrl(docs_url)))
        self.action_code.triggered.connect(lambda x: QDesktopServices.openUrl(QUrl(repo_url)))
        self.action_about.triggered.connect(self.open_about)
        self.action_create_model.triggered.connect(self.create_model)

        # Code and signals for tab: Basic Modeling Information.
        # part_name
        self.part_name = 'unnamed'
        self.part_name_field.setText(self.part_name)
        part_name_regex = r"^(?=.*[ -~])(?=.*[^$&*~!()\[\]{}|;'`\",.?/\\])(?=^[A-Za-z])^.{1,37}[^_]$"
        self.part_name_field.setValidator(QRegularExpressionValidator(
            QRegularExpression(part_name_regex)))
        self.part_name_field_default_style = self.part_name_field.styleSheet()
        self.part_name_field.textChanged.connect(self.determine_validity_visually)
        self.part_name_field.textChanged.connect(self.part_name_changed)
        # dim_combo
        self.dim_combo.currentTextChanged.connect(self.modeling_mode_changed)
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
        # base_material_field
        self.base_material_field.setValidator(QIntValidator(0, 999999999, self))
        # working_dir
        self.working_dir = str(return_default_results_path(part_name=self.part_name))
        self.custom_working_dir = None
        self.working_dir_select_button.clicked.connect(self.select_working_dir)

        # Code and signals for tab: Basic Modeling Information.
        # bc_type
        self.bc_type_button_group = QButtonGroup(self.bc_type_group_box)
        self.bc_type_button_group.setExclusive(True)
        self.bc_type_button_group.addButton(self.no_bc_radio, 0)
        self.bc_type_button_group.addButton(self.bc_set_only_radio, 1)
        self.bc_type_button_group.addButton(self.periodic_bc_radio, 2)
        self.no_bc_radio.toggled.connect(self.toggle_bc_type)
        self.bc_set_only_radio.toggled.connect(self.toggle_bc_type)
        self.periodic_bc_radio.toggled.connect(self.toggle_bc_type)
        # strain
        strain_validator = QDoubleValidator(-1e+6, 1e+6, 8)
        self.strain11_field.setValidator(strain_validator)
        self.strain22_field.setValidator(strain_validator)
        self.strain33_field.setValidator(strain_validator)
        self.strain12_field.setValidator(strain_validator)
        self.strain13_field.setValidator(strain_validator)
        self.strain23_field.setValidator(strain_validator)
        self.strain11_field.textChanged.connect(self.determine_validity_visually)
        self.strain22_field.textChanged.connect(self.determine_validity_visually)
        self.strain33_field.textChanged.connect(self.determine_validity_visually)
        self.strain12_field.textChanged.connect(self.determine_validity_visually)
        self.strain13_field.textChanged.connect(self.determine_validity_visually)
        self.strain23_field.textChanged.connect(self.determine_validity_visually)

        # Code and signals for tab: Modeling.
        # Modeling: TPMS
        self.formula_font_size = 20
        # modeling_mode_combo
        for modeling_mode in modeling_mode_list:
            self.modeling_mode_combo.addItem(modeling_mode.name, userData=modeling_mode)
        self.modeling_mode_combo.setCurrentIndex(0)
        self.modeling_mode_combo.currentTextChanged.connect(self.modeling_mode_changed)
        self.modeling_mode_changed()
        for tpms_type in tpms_dict.values():
            self.select_tpms_combo.addItem(tpms_type.name, userData=tpms_type)
        self.select_tpms_combo.currentTextChanged.connect(self.tpms_type_changed)
        self.tpms_type_changed()
        # tpms_length_field and tpms_constant_field
        self.tpms_length_field.setValidator(QDoubleValidator(1e-5, 1e+6, 8))
        self.tpms_constant_field.setValidator(QDoubleValidator(-1e+6, 1e+6, 8))
        # tpms_fill_value_field
        self.tpms_fill_value_field.setValidator(QIntValidator(0, 999999999, self))

        # Modeling: Planar Composite (Circular Inclusions)
        self.modeling_circle_table.setItemDelegateForColumn(0, PositionFloatDelegate(self))
        self.modeling_circle_table.setItemDelegateForColumn(1, PositionFloatDelegate(self))
        self.modeling_circle_table.setItemDelegateForColumn(2, RadiusFloatDelegate(self))
        self.modeling_circle_table.setItemDelegateForColumn(3, IntDelegate(self))

        # Modeling: Spatial Composite (Spherical Inclusions)
        self.modeling_sphere_table.setItemDelegateForColumn(0, PositionFloatDelegate(self))
        self.modeling_sphere_table.setItemDelegateForColumn(1, PositionFloatDelegate(self))
        self.modeling_sphere_table.setItemDelegateForColumn(2, PositionFloatDelegate(self))
        self.modeling_sphere_table.setItemDelegateForColumn(3, RadiusFloatDelegate(self))
        self.modeling_sphere_table.setItemDelegateForColumn(4, IntDelegate(self))

        # Modeling: Single Image
        # TODO

        # Code and signals for tab: Output.
        # output_mats  # TODO: move all signals from QtDesigner to python.
        self.output_mats_type_button_group = QButtonGroup(self.output_mats_layout1)
        self.output_mats_type_button_group.setExclusive(True)
        self.output_mats_type_button_group.addButton(self.output_mats_all_radio, 0)
        self.output_mats_type_button_group.addButton(self.output_mats_non_empty_radio, 1)
        self.output_mats_type_button_group.addButton(self.output_mats_select_radio, 2)
        self.output_mats_non_empty_radio.toggled.connect(self.toggle_output_mats_type)
        self.output_mats_all_radio.toggled.connect(self.toggle_output_mats_type)
        self.output_mats_select_radio.toggled.connect(self.toggle_output_mats_type)
        # output_mats_select_field
        output_mats_select_regex = r"((?:\d+[, \t]*)+)?\d+"  # TODO: add as parameter.
        self.output_mats_select_field.setValidator(QRegularExpressionValidator(
            QRegularExpression(output_mats_select_regex)))

        # Code and signals for tab: Run.
        self.run_export_button.clicked.connect(self.export_config)
        self.run_create_model_button.clicked.connect(self.create_model)
        self.run_open_dir_button.clicked.connect(self.open_working_dir)

    def toggle_output_mats_type(self):
        self.output_mats_select_field.setEnabled(self.output_mats_select_radio.isChecked())

    def toggle_bc_type(self):
        self.strain_group_box.setEnabled(self.periodic_bc_radio.isChecked())

    def tpms_type_changed(self):
        tpms_type = self.select_tpms_combo.currentData()
        self.tpms_formula_real_label.setPixmap(
            mathtex_to_qpixmap(tpms_type.formula, self.formula_font_size))

    def modeling_mode_changed(self):
        modeling_mode = self.modeling_mode_combo.currentData()
        self.modeling_stacked_widget.setCurrentIndex(modeling_mode.page_id)
        self.modeling_description_label.setText(modeling_mode.description)
        if modeling_mode.dim == 0:
            self.modeling_dim_label.setText('')
        elif self.dim_combo.currentText().startswith(str(modeling_mode.dim)):
            self.modeling_dim_label.setText('')
            self.modeling_stacked_widget.currentWidget().setEnabled(True)
            self.modeling_description_label.setEnabled(True)
        else:
            self.modeling_dim_label.setText('This modeling method is inappropriate for the '
                                            'modeling space defined in the previous section.')
            self.modeling_stacked_widget.currentWidget().setEnabled(False)
            self.modeling_description_label.setEnabled(False)

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
                required_memory = required_memory * 2 ** 10
                msg_2 = f'{required_memory:0.2f} KB of RAM.'
            else:
                msg_2 = f'{required_memory:0.2f} MB of RAM.'
            self.model_size_field.setText(msg_1 + msg_2)

    def determine_validity_visually(self):
        if not self.sender().hasAcceptableInput():
            self.sender().setStyleSheet("border: 1px solid red;")  # TODO: field size changes.
        else:
            self.sender().setStyleSheet("border: 1px solid black;")  # TODO: parameterize.

    def part_name_changed(self):
        self.part_name = self.part_name_field.text()
        if self.custom_working_dir is None:
            self.working_dir = str(return_default_results_path(part_name=self.part_name))
        else:
            self.working_dir = self.custom_working_dir
        self.working_dir_field.setText(self.working_dir)
        self.file_name_field.setText(self.part_name)

    def select_working_dir(self):
        self.custom_working_dir = self.working_dir  # TODO: what is custom_working_dir used for?
        dir_str = QFileDialog.getExistingDirectory(self, 'Select the working directory.',
                                                   self.working_dir, QFileDialog.ShowDirsOnly)
        dir_str = str(Path(dir_str).resolve(strict=False))

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
        self.mask_table.setItem(row, 2, QTableWidgetItem(items[1]))
        self.mask_table.setItem(row, 3, QTableWidgetItem(items[2]))
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

    # Functions used for actions.
    def import_config(self):
        default_path = str(Path(self.working_dir))
        (file_name, _) = QFileDialog.getOpenFileName(self, 'Import Model Settings', default_path,
                                                     'VCAMS configuration file (*.vcams)')
        import_settings(main_obj=self, file_path_str=file_name)

    def export_config(self):
        default_path = str(Path(self.working_dir) / self.part_name)
        (file_name, _) = QFileDialog.getSaveFileName(self, 'Export Model Settings', default_path,
                                                     'VCAMS configuration file (*.vcams)')
        export_settings(main_obj=self, file_path_str=file_name)

    def open_about(self):
        QMessageBox.information(self, 'About VCAMS', about_vcams)  # TODO: add icon
        return

    def create_model(self):
        default_path = str(Path(self.working_dir) / (self.part_name + '.vcams'))
        export_settings(main_obj=self, file_path_str=default_path)
        try:
            self.main_toolbox.setCurrentWidget(self.run_page)
            gui_logging_handler = QTextEditLogger(self.log_field)
            gui_logging_handler.setFormatter(
                logging.Formatter(
                    fmt='%(asctime)s - %(levelname) 5s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
            logger.addHandler(gui_logging_handler)
            from_config_file(file_path=default_path)  # TODO: show a QProgressDialog.
        except Exception as err:
            QMessageBox.critical(self, 'Model Creation Failed!', str(err))
        else:
            QMessageBox.information(self, 'Done!',
                                    ('Model Created Successfully!\n'
                                     'You can find all files at:\n%s' % self.working_dir))

    def open_working_dir(self):
        import webbrowser
        dir_path = Path(self.working_dir)
        if dir_path.exists() and dir_path.is_dir():
            webbrowser.open(self.dir_path)
        else:
            QMessageBox.critical(self, 'Error!',
                                 'The results folder does not exist.\nHave you run the model?')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('fusion'))
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
