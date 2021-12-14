"""Functions for import and export of GUI settings."""
from configparser import ConfigParser
from pathlib import Path

from PyQt5.QtWidgets import QLineEdit, QMessageBox, QComboBox, QPlainTextEdit, QCheckBox, \
    QTableWidget, QButtonGroup

"""This function assumes that the following fields are present in the GUI:
"""

# Zero-Based list corresponding to bc_type_button_group.
# bc_type_list = ['No Boundary Conditions', 'Create Node Sets Only',
#                'Periodic Boundary Conditions']
# Zero-Based list corresponding to output_mats_type_button_group.
# output_mats_type = ['Non-Empty Materials', 'All Materials', 'Following Materials']


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


def set_field_value(field_obj, field_name, field_dict, combo_index_mode=False):
    if field_name not in field_dict:
        field_obj.setFocus()
        raise ValueError('Field "%s" is not in the settings file.' % field_name)
    value = field_dict[field_name]

    if isinstance(field_obj, QLineEdit):
        return set_qlineedit_value(field_obj, field_name, value)
    elif isinstance(field_obj, QPlainTextEdit):
        field_obj.setPlainText(value)
    elif isinstance(field_obj, QComboBox):
        set_qcombobox_value(field_obj, field_name, value, combo_index_mode)
    elif isinstance(field_obj, QCheckBox):
        field_obj.setCheckState(value)
    elif isinstance(field_obj, QTableWidget):
        set_qtablewidget_value(field_obj, field_name, value)
    elif isinstance(field_obj, QButtonGroup):
        set_qbuttongroup_value(field_obj, field_name, value)
    else:
        field_obj.setFocus()
        raise NotImplementedError('field_obj has a type that has not been implemented.')


def set_qlineedit_value(qlineedit_obj, field_name, value):
    validator = qlineedit_obj.validator()
    if validator is None:
        qlineedit_obj.setText(value)
    else:
        validator_result = validator.validate(value, 0)[0]
        if validator_result == 2:
            qlineedit_obj.setText(value)
        else:
            qlineedit_obj.setFocus()
            raise ValueError('Invalid value in field "%s".' % field_name)


def set_qcombobox_value(qcombobox_obj, field_name, value, combo_index_mode=False):
    if combo_index_mode:
        qcombobox_obj.setCurrentIndex(int(value))
        return
    else:
        ind = qcombobox_obj.findText(value)
        if ind == -1:
            qcombobox_obj.setFocus()
            raise ValueError('Invalid value in field "%s".' % field_name)
        else:
            qcombobox_obj.setCurrentIndex(ind)


def set_qtablewidget_value(qtablewidget_obj, field_name, value):
    # Validation is done in inside the function as the ValueError is caught by the calling function.
    try:
        qtablewidget_obj.import_from_csv_string(csv_string=value, selection=None)
    except ValueError as err:
        qtablewidget_obj.setFocus()
        raise ValueError('Invalid value in field "%s".\n%s' % (field_name, str(err)))


def set_qbuttongroup_value(qbuttongroup_obj, field_name, value):
    button = qbuttongroup_obj.button(int(value))
    if button:
        button.setChecked(True)
    else:
        qbuttongroup_obj.parent().setFocus()
        raise ValueError('Invalid value in field "%s".' % field_name)


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


def export_settings(main_obj, file_path_str):
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
        config['Basic']['working_dir'] = main_obj.working_dir
        config['Basic']['log_debug'] = str(main_obj.log_debug_checkbox.isChecked())

        # Tab: Modeling.
        config['Modeling'] = {}
        config['Modeling']['modeling_mode'] = str(main_obj.modeling_mode_combo.currentIndex())
        if config['Modeling']['modeling_mode'] == '0':  # No further action.
            QMessageBox.critical(main_obj, 'Invalid Data!',
                                 'No modeling mode is selected in the Model Manipulations section.')
        elif config['Modeling']['modeling_mode'] == '1':  # TPMS
            config['Modeling']['tpms_type'] = str(main_obj.select_tpms_combo.currentIndex())
            config['Modeling']['tpms_length'] = return_field_value(main_obj.tpms_length_field)
            config['Modeling']['tpms_constant'] = return_field_value(main_obj.tpms_constant_field)
        elif config['Modeling']['modeling_mode'] == '2':  # Planar Composite (Circular Inclusions)
            config['Modeling']['modeling_circle_table'] = \
                main_obj.modeling_circle_table.return_csv_string(for_excel=False)
        elif config['Modeling']['modeling_mode'] == '3':  # Spatial Composite (Spherical Inclusions)
            config['Modeling']['modeling_sphere_table'] = \
                main_obj.modeling_sphere_table.return_csv_string(for_excel=False)
        else:
            raise ValueError('Invalid value for modeling_mode which should not happen.')

        # Tab: Boundary Conditions
        config['BC'] = {}
        config['BC']['bc_type'] = str(main_obj.bc_type_button_group.checkedId())
        if config['BC']['bc_type'] == '2':  # Periodic Boundary Condition.
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
    file_path = Path(file_path_str)
    file_path.parents[0].mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', newline='\n') as config_file:
        config.write(config_file)


def import_settings(main_obj, file_path_str):
    config = ConfigParser()
    config.read(file_path_str)

    # Check validity of the imported settings.
    section_list = ('Basic', 'Modeling', 'BC', 'Output')
    for name in section_list:
        if name not in config.sections():
            QMessageBox.critical(main_obj, 'Import Failed!',
                                 'Section "%s" was not present in the settings file.' % name)

    # Tab: Basic Model Information
    basic = config['Basic']
    try:
        set_field_value(main_obj.part_name_field, 'part_name', basic)
        set_field_value(main_obj.dim_combo, 'dim', basic)
        set_field_value(main_obj.num_voxels_x_field, 'num_voxels_x', basic)
        set_field_value(main_obj.num_voxels_y_field, 'num_voxels_y', basic)
        set_field_value(main_obj.num_voxels_z_field, 'num_voxels_z', basic)
        set_field_value(main_obj.voxel_size_x_field, 'voxel_size_x', basic)
        set_field_value(main_obj.voxel_size_y_field, 'voxel_size_y', basic)
        set_field_value(main_obj.voxel_size_z_field, 'voxel_size_z', basic)
        set_field_value(main_obj.num_mats_combo, 'num_mats', basic, combo_index_mode=True)
        set_field_value(main_obj.part_description_field, 'part_description', basic)
        set_field_value(main_obj.working_dir_field, 'working_dir', basic)
        main_obj.log_debug_checkbox.setChecked(config.getboolean('Basic', 'log_debug'))
    except ValueError as err:
        main_obj.main_toolbox.setCurrentIndex(0)
        QMessageBox.critical(main_obj, 'Import Failed!', str(err))

    # Tab: Modeling.
    modeling = config['Modeling']
    try:
        set_field_value(main_obj.modeling_mode_combo, 'modeling_mode', modeling,
                        combo_index_mode=True)
        modeling_mode = str(main_obj.modeling_mode_combo.currentIndex())
        if modeling_mode == '0':  # No further action.
            raise ValueError('Field "modeling_mode" is set to 0, which is invalid.')
        elif modeling_mode == '1':  # TPMS
            set_field_value(main_obj.select_tpms_combo, 'tpms_type', modeling,
                            combo_index_mode=True)
            set_field_value(main_obj.tpms_length_field, 'tpms_length', modeling)
            set_field_value(main_obj.tpms_constant_field, 'tpms_constant', modeling)
        elif modeling_mode == '2':  # Planar Composite (Circular Inclusions)
            set_field_value(main_obj.modeling_circle_table, 'modeling_circle_table', modeling)
        elif modeling_mode == '3':  # Spatial Composite (Spherical Inclusions)
            set_field_value(main_obj.modeling_sphere_table, 'modeling_sphere_table', modeling)
        else:
            raise ValueError(
                'Field "modeling_mode" is set to %s, which is invalid.' % modeling_mode)
    except ValueError as err:
        main_obj.main_toolbox.setCurrentIndex(1)
        QMessageBox.critical(main_obj, 'Import Failed!', str(err))

    # Tab: Boundary Conditions.
    bc = config['BC']
    try:
        set_field_value(main_obj.bc_type_button_group, 'bc_type', bc)
        selected_bc_type = str(main_obj.bc_type_button_group.checkedId())
        if selected_bc_type == '2':  # Periodic Boundary Condition.
            set_field_value(main_obj.strain11_field, 'strain11', bc)
            set_field_value(main_obj.strain22_field, 'strain22', bc)
            set_field_value(main_obj.strain33_field, 'strain33', bc)
            set_field_value(main_obj.strain12_field, 'strain12', bc)
            set_field_value(main_obj.strain13_field, 'strain13', bc)
            set_field_value(main_obj.strain23_field, 'strain23', bc)
    except ValueError as err:
        main_obj.main_toolbox.setCurrentIndex(2)
        QMessageBox.critical(main_obj, 'Import Failed!', str(err))

    # Tab: Output.
    output = config['Output']
    try:
        set_field_value(main_obj.file_name_field, 'file_name', output)
        set_field_value(main_obj.elem_code_field, 'elem_code', output)
        set_field_value(main_obj.output_mats_type_button_group, 'output_mats_type', output)
        selected_output_mats_type = str(main_obj.output_mats_type_button_group.checkedId())
        if selected_output_mats_type == '2':  # Output Selected Materials.
            set_field_value(main_obj.output_mats_select_field, 'output_mats_select', output)
    except ValueError as err:
        main_obj.main_toolbox.setCurrentIndex(3)
        QMessageBox.critical(main_obj, 'Import Failed!', str(err))
