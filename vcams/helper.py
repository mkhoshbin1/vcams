"""Various helper functions."""
import csv
from configparser import ConfigParser
import logging
from io import StringIO
from pathlib import Path

from vcams.mask.tpms import tpms_dict

logger = logging.getLogger(__name__)


def is_name_valid(name):
    """ Check whether a string represents a valid name.
    Abaqus (TM) has many rules for names (labels) in the input files.
    Here, The most strict combination is implemented here to ensure that
    a name is suitable for all purposes.

    This means that a name:
      + Must be 1-38 characters. This is because some object names
        in the abaqus scripting interface have a 38-character limit
        for their names.
      + May contain whitespace (If enclosed by whitespace).
      + Must start with a letter.
      + Must no begin or end with an underscore.
      + Must no include the following characters: $&*~!()[]{}|;'`",.?/\
      + Must not contains periods. This also means that any file names
        cannot contain any extensions. They will be added automatically.
      + Must be ASCII-compatible. This is checked by attempting str.decode('ascii')
        and checking for :py:obj:`UnicodeDecodeError`.

    For more information, refer to:
      + "Labels" under "Input Syntax Rules" of the Abaqus Analysis User's Manual.
      + The documentation for the InvalidNameError object under
        "Standard Abaqus Scripting Interface exceptions" of
        Abaqus Scripting User's Manual.

    Args:
        name (str): The string to be checked.

    Returns:
        bool: :py:obj:`True` for a valid name.
    """

    # TODO: consider regex: ^(?=.*[ -~])(?=.*[^$&*~!()\[\]{}|;'`",.?/\\])(?=^[A-Za-z])^.{1,37}[^_]$
    forbidden_chars = "$&*~!()[]{}|;\'`\",.?/\\"
    if not isinstance(name, str):
        return False
    elif len(name) < 1:
        return False
    elif len(name) > 38:
        return False
    elif not name[0].isalpha():
        return False
    elif name.endswith('_'):  # The beginning is checked above.
        return False
    elif any((n in forbidden_chars) for n in name):
        return False
    elif not (name.isascii() and name.isprintable()):
        # Source: https://stackoverflow.com/a/51141941/7180705.
        return False
    else:
        return True


def return_default_results_path(part_name=None):
    """Return a suitable path in the user's Desktop
       for storing the intermediate and final results of the program.

    Args:
        part_name (str): Name of the part which is to be output
                         which must be valid according to #TODO.
                         If set to :py:obj:`None`, the folder will simply be named 'results'.
                         Defaults to :py:obj:`None`.

    Returns:
        A path object containing the full path of a suitable folder in the users Desktop.
    """

    parts = ['Desktop', 'VCAMS Working Directory']
    # Validate part_name.
    if part_name is None:
        pass  # No subfolder.
    elif is_name_valid(part_name):
        parts.append(part_name)
    else:
        raise ValueError('part_name is not valid.')

    return Path.home().joinpath(*parts)


def read_configuration(file_path):
    """Read a configuration file containing all the information used for creating a VoxelPart
    and return the information as a list of dictionaries.

    Args:
        file_path (str): Path to the configuration file.

    Returns:
        tuple: A tuple of the following dictionaries:
               (part_creation_dict, part_manipulation_dict, bc_dict, output_dict)
    """

    # Read the config file.
    logger.debug('Trying to read configuration file at %s' % file_path)
    config = ConfigParser()
    config.read(file_path)

    # Check validity of the imported settings.
    section_list = ('Basic', 'Modeling', 'BC', 'Output')
    for name in section_list:
        if name not in config.sections():
            raise ValueError('Section "%s" was not present in the settings file.' % name)

    # Process various part of the config file.
    # Basic: Information used for creating the part.
    part_creation_dict = dict()
    basic_section = config['Basic']
    dim = basic_section['dim'].upper()
    if dim == '2D':
        part_creation_dict['size'] = (int(basic_section['num_voxels_x']),
                                      int(basic_section['num_voxels_y']))
    elif dim == '3D':
        part_creation_dict['size'] = (int(basic_section['num_voxels_x']),
                                      int(basic_section['num_voxels_y']),
                                      int(basic_section['num_voxels_z']))
    else:
        raise ValueError('Field "dim" is set to %s, which is invalid.' % basic_section['dim'])
    if 'fill_value' in basic_section:
        part_creation_dict['fill_value'] = int(basic_section['fill_value'])
    else:
        part_creation_dict['fill_value'] = 0
    part_creation_dict['voxel_size'] = (float(basic_section['voxel_size_x']),
                                        float(basic_section['voxel_size_y']),
                                        float(basic_section['voxel_size_z']))
    num_mats = basic_section['num_mats']
    if num_mats == '0':
        part_creation_dict['dtype'] = 'uint8'
    elif num_mats == '1':
        part_creation_dict['dtype'] = 'uint16'
    elif num_mats == '2':
        part_creation_dict['dtype'] = 'uint32'
    elif num_mats == '3':
        part_creation_dict['dtype'] = 'uint54'
    else:
        raise ValueError("Invalid value for field 'num_mats'.")
    part_creation_dict['name'] = basic_section['part_name']
    part_creation_dict['description'] = basic_section['part_description']
    part_creation_dict['results_path'] = basic_section['working_dir']
    part_creation_dict['overwrite_logs'] = True
    part_creation_dict['log_debug'] = config.getboolean('Basic', 'log_debug')

    # Modeling: Manipulating the part.
    part_manipulation_dict = dict()
    modeling_section = config['Modeling']
    modeling_mode = modeling_section['modeling_mode']
    part_manipulation_dict['modeling_mode'] = modeling_mode
    part_manipulation_dict['dim'] = dim
    if modeling_mode == '0':  # No further action.
        pass
    elif modeling_mode == '1':  # TPMS
        tpms_type = modeling_section['tpms_type']
        if int(tpms_type) in tpms_dict.keys():
            part_manipulation_dict['tpms_type'] = int(tpms_type)
        else:
            raise ValueError('Field "tpms_type" is set to %s, which is invalid.' % tpms_type)
        part_manipulation_dict['tpms_length'] = float(modeling_section['tpms_length'])
        part_manipulation_dict['tpms_constant'] = float(modeling_section['tpms_constant'])
    elif modeling_mode == '2':  # Planar Composite (Circular Inclusions)
        part_manipulation_dict['circle_list'] = \
            csv_string_to_list(modeling_section['modeling_circle_table'])
    elif modeling_mode == '3':  # Spatial Composite (Spherical Inclusions)
        part_manipulation_dict['sphere_list'] = \
            csv_string_to_list(modeling_section['modeling_sphere_table'])
    else:
        raise ValueError('Field "modeling_mode" is set to %s, which is invalid.' % modeling_mode)

    # BC: Boundary Conditions.
    bc_dict = dict()
    bc_section = config['BC']
    bc_dict['dim'] = dim
    bc_type = bc_section['bc_type']
    bc_dict['bc_type'] = bc_type
    if bc_type == '0':  # No BC.
        pass
    elif bc_type == '1':  # Sets only.
        pass
    elif bc_type == '2':  # Periodic BC.
        bc_dict['strain11'] = float(bc_section['strain11'])
        bc_dict['strain22'] = float(bc_section['strain22'])
        bc_dict['strain33'] = float(bc_section['strain33'])
        bc_dict['strain12'] = float(bc_section['strain12'])
        bc_dict['strain13'] = float(bc_section['strain13'])
        bc_dict['strain23'] = float(bc_section['strain23'])
        raise NotImplementedError('Periodic BC has not been implemented.')  # TODO
    else:
        raise ValueError('Field "bc_type" is set to %s, which is invalid.' % bc_type)

    # Output.
    output_dict = dict()
    output_section = config['Output']
    if is_name_valid(name=output_section['file_name']):
        output_dict['file_name'] = output_section['file_name']
    else:
        raise ValueError('Field "file_name" contains an invalid name.')
    output_dict['elem_type'] = output_section['elem_code']
    output_dict['dim'] = dim
    output_mats_type = output_section['output_mats_type']
    if output_mats_type == '0':  # All Materials.
        output_dict['material_elem_sets'] = 'All'
    elif output_mats_type == '1':  # Non-Empty Materials.
        output_dict['material_elem_sets'] = 'Non-Empty'
    elif output_mats_type == '2':  # Output Selected Materials.
        output_dict['material_elem_sets'] = \
            [int(i) for i in output_section['output_mats_select'].split(',')]
    else:
        raise ValueError(
            'Field "output_mats_type" is set to %s, which is invalid.' % output_mats_type)

    return part_creation_dict, part_manipulation_dict, bc_dict, output_dict


def csv_string_to_list(csv_string):
    buffer_io = StringIO(csv_string)
    dialect = csv.Sniffer().sniff(buffer_io.readline())
    buffer_io.seek(0)
    csv_reader = csv.reader(buffer_io, dialect)
    return [row for row in csv_reader]