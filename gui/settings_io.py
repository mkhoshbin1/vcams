"""Functions for import and export of GUI settings."""

from configparser import ConfigParser
from pathlib import Path

from PyQt5.QtWidgets import QLineEdit, QComboBox, QPlainTextEdit, QMessageBox

"""This function assumes that the following fields are present in the GUI:
"""

# Zero-Based list corresponding to bc_type_button_group.
bc_type_list = ['No Boundary Conditions', 'Create Node Sets Only',
                'Periodic Boundary Conditions']
# Zero-Based list corresponding to output_mats_type_button_group.
output_mats_type = ['Non-Empty Materials', 'All Materials', 'Following Materials']


class InvalidFieldError(Exception):
    def __init__(self, field_obj):
        self.field_obj = field_obj
        # TODO: use https://doc.qt.io/qt-5/qformlayout.html#labelForField


def return_field_value(field_obj):
    if field_obj.hasAcceptableInput():
        if isinstance(field_obj, QLineEdit):
            return field_obj.text()
        else:
            raise NotImplementedError('field_obj has a type that has not been implemented.')
    else:
        raise InvalidFieldError(field_obj)


def set_focus(main_obj, field_obj):
    main_toolbox = main_obj.main_toolbox
    main_toolbox.setFocus()
    for i in range(main_toolbox.count()):
        if main_toolbox.widget(i).isAncestorOf(field_obj):
            main_toolbox.setCurrentIndex(i)
            field_obj.setFocus()
            # TODO: change border color.
            return
    raise RuntimeError('Could not find field_obj as a child of any of the main tabs.')


def export_settings(main_obj):
    config = ConfigParser()
    try:
        # Tab: Basic Model Information
        config['Basic'] = {}
        config['Basic']['part_name'] = return_field_value(main_obj.part_name_field)
        config['Basic']['dim'] = main_obj.dim_combo.currentText()
        config['Basic']['num_voxels_x'] = return_field_value(main_obj.num_voxels_x_field)
        config['Basic']['num_voxels_y'] = return_field_value(main_obj.num_voxels_y_field)
        config['Basic']['num_voxels_z'] = return_field_value(main_obj.num_voxels_z_field)
        config['Basic']['voxel_size_x'] = return_field_value(main_obj.voxel_size_x_field)
        config['Basic']['voxel_size_y'] = return_field_value(main_obj.voxel_size_y_field)
        config['Basic']['voxel_size_z'] = return_field_value(main_obj.voxel_size_z_field)
        config['Basic']['num_mats'] = str(main_obj.num_mats_combo.currentIndex())
        config['Basic']['part_description'] = main_obj.part_description_field.toPlainText()
        # TODO: check with long text.
        config['Basic']['working_dir'] = return_field_value(main_obj.working_dir_field)
        config['Basic']['log_debug'] = str(main_obj.log_debug_checkbox.isChecked())

        # Tab: Boundary Conditions
        config['BC'] = {}
        config['BC']['bc_type'] = str(main_obj.bc_type_button_group.checkedId())
        if config['BC']['bc_type'] == '2':
            config['BC']['strain11'] = return_field_value(main_obj.strain11_field)
            config['BC']['strain22'] = return_field_value(main_obj.strain22_field)
            config['BC']['strain33'] = return_field_value(main_obj.strain33_field)
            config['BC']['strain12'] = return_field_value(main_obj.strain12_field)
            config['BC']['strain13'] = return_field_value(main_obj.strain13_field)
            config['BC']['strain23'] = return_field_value(main_obj.strain23_field)

        # Tab: Output.
        config['Output'] = {}
        config['Output']['file_name'] = return_field_value(main_obj.file_name_field)
        config['Output']['elem_code'] = return_field_value(main_obj.elem_code_field)
        config['Output']['output_mats_type'] = \
            str(main_obj.output_mats_type_button_group.checkedId())
        if config['Output']['output_mats_type'] == '2':
            config['Output']['output_mats_select'] = \
                return_field_value(main_obj.output_mats_select_field)


    except InvalidFieldError as e:
        set_focus(main_obj, e.field_obj)
        QMessageBox.critical(main_obj, 'Export Failed!', 'One of the fields has an invalid value.')
        return

    # Write to output.
    working_dir_path = Path(main_obj.working_dir)
    working_dir_path.mkdir(parents=True, exist_ok=True)
    with open(working_dir_path.joinpath(main_obj.part_name + '.vcams'), 'w') as config_file:
        config.write(config_file)
