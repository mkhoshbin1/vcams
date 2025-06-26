"""Various helper functions used throughout the library."""

import csv
from configparser import ConfigParser
from io import StringIO
from logging import getLogger
from pathlib import Path
from typing import Iterable

from numpy import unique
from numpy.typing import NDArray

from vcams.mask.image import image_thresh_mode_list
from vcams.mask.tpms import tpms_dict

logger = getLogger(__name__)


def is_name_valid(name: str) -> bool:
    # noinspection GrazieInspection
    """Check whether a string represents a valid name.
    Abaqus™ has many rules for names (labels) in the input files.
    The strictest combination is implemented here to ensure that
    a name is suitable for all purposes.

    This means that a name:

    + Must be 1-38 characters. This is because some object names
      in the abaqus scripting interface have a 38-character limit
      for their names.
    + May contain whitespace (if enclosed by double quotation marks).
    + Must start with a letter.
    + Must not begin or end with an underscore.
    + Must not include the following characters: ``$&*~!()[]{}|;'`",.?/\\``
    + Must not contain periods. This also means that any file names
      cannot contain any extensions. They will be added automatically.
    + Must be ASCII-compatible. This is checked by attempting :code:`str.decode('ascii')`
      and checking for :obj:`UnicodeDecodeError`.

    For more information, refer to:

    + *Labels* under the *Input Syntax Rules* section of the Abaqus Analysis User's Manual.
    + The documentation for the *InvalidNameError* object under
      the section *Standard Abaqus Scripting Interface Exceptions* of
      Abaqus Scripting User's Manual.

    Args:
        name: The string to be checked.

    Returns:
        Returns True for a valid name otherwise returns False.
    """
    # The regex ^(?=.*[ -~])(?=.*[^$&*~!()\[\]{}|;'`",.?/\\])(?=^[A-Za-z])^.{1,37}[^_]$
    # MAY be useful but the following method is easier to understand.
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


def return_default_working_dir(part_name: str = None) -> Path:
    """Return a suitable path in the user's Desktop for storing
    the intermediate and final results of the program.

    Args:
        part_name: Name of the part which is to be output
                   which must be valid according to :func:`is_name_valid`.
                   If set to *None*, the folder will be named :code:`results`.
                   Defaults to *None*.

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


def process_working_dir(working_dir: Path | str | None, part_name: str) -> Path:
    """Process and validate the working_dir which represents
    the path where the intermediate and final results of the program are stored.
    This function validates the given *working_dir* parameter
    and if set to *None*, creates a default value using the :func:`return_default_working_dir` function.
    Then, the directory is created and finally a Path object referring to it is returned.

    Args:
        working_dir: Path to the folder where the final results, temporary file, and log files will be stored.
                     If set to *None* a suitable folder is automatically created in the user's home directory.
        part_name: Name of the part which is to be output
                   which must be valid according to :func:`is_name_valid`.
                   If set to *None*, the folder will be named :code:`results`.
                   Defaults to *None*.

    Returns:
        A path object containing the full path of a valid working directory that exists.
    """
    if working_dir is None:
        working_dir = return_default_working_dir(part_name)
    else:
        working_dir = Path(working_dir)
    working_dir.mkdir(parents=True, exist_ok=True)
    return working_dir


def write_to_logger_streams(msg: str):
    """Write a message directly to all handlers of the module's root logger object.

    Args:
        msg: The message that is written.
    """
    for handler in logger.root.handlers:
        handler.stream.writelines(msg)


def read_configuration(file_path: str) -> tuple[dict, dict, dict, dict]:
    """Read a configuration file containing all the information used for creating
    a :class:`~.voxelpart.VoxelPart` and return the information as a list of dictionaries.

    Args:
        file_path: Path to the configuration file.

    Returns:
        A tuple of the following dictionaries (part_creation_dict, part_manipulation_dict, bc_dict, output_dict).
    """
    # Read the config file.
    logger.debug('Reading configuration file at %s' % file_path)
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
    if 'base_material' in basic_section:
        part_creation_dict['base_material'] = int(basic_section['base_material'])
    else:
        part_creation_dict['base_material'] = 0
    if dim == '2D':
        part_creation_dict['voxel_size'] = (float(basic_section['voxel_size_x']),
                                            float(basic_section['voxel_size_y']))
    elif dim == '3D':
        part_creation_dict['voxel_size'] = (float(basic_section['voxel_size_x']),
                                            float(basic_section['voxel_size_y']),
                                            float(basic_section['voxel_size_z']))
    else:
        raise ValueError('Field "dim" is set to %s, which is invalid.' % basic_section['dim'])
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
    part_creation_dict['working_dir'] = basic_section['working_dir']
    part_creation_dict['overwrite_logs'] = True
    part_creation_dict['log_debug'] = config.getboolean('Basic', 'log_debug')

    # Modeling: Manipulating the part.
    part_manipulation_dict = dict()
    modeling_section = config['Modeling']
    modeling_mode = modeling_section['modeling_mode']
    part_manipulation_dict['modeling_mode'] = modeling_mode
    part_manipulation_dict['dim'] = dim
    if modeling_mode == '0':  # No action selected. This is technically invalid, but is considered to be '1'.
        pass
    elif modeling_mode == '1':  # No Further Manipulation.
        pass
    elif modeling_mode == '2':  # Random Element Dispersion
        part_manipulation_dict['random_phase_fraction'] = float(modeling_section['random_phase_fraction'])
        part_manipulation_dict['random_phase_matcode'] = int(modeling_section['random_phase_matcode'])
    elif modeling_mode == '3':  # TPMS
        tpms_type = modeling_section['tpms_type']
        if int(tpms_type) in tpms_dict.keys():
            part_manipulation_dict['tpms_type'] = int(tpms_type)
        else:
            raise ValueError('Field "tpms_type" is set to %s, which is invalid.' % tpms_type)
        part_manipulation_dict['tpms_length'] = float(modeling_section['tpms_length'])
        part_manipulation_dict['tpms_constant'] = float(modeling_section['tpms_constant'])
        part_manipulation_dict['tpms_fill_value'] = int(modeling_section['tpms_fill_value'])
    elif modeling_mode == '4':  # Image Processing (Single 2D Image)
        part_manipulation_dict['single_image_path'] = modeling_section['single_image_path']
        part_manipulation_dict['single_image_scale'] = float(modeling_section['single_image_scale'])
        # Make sure the following is identical for single and multiple image modeling modes.
        image_thresh_key = 'single_image_thresh_mode'
        image_thresh_mode = modeling_section[image_thresh_key].lower()
        if image_thresh_mode in image_thresh_mode_list:
            part_manipulation_dict[image_thresh_key] = image_thresh_mode
        else:
            raise ValueError("Invalid value for field '%s'." % image_thresh_key)
        part_manipulation_dict['single_image_thresh_value'] = float(modeling_section['single_image_thresh_value'])
        part_manipulation_dict['single_image_denoise'] = config.getboolean('Modeling', 'single_image_denoise')
    elif modeling_mode == '5':  # Stack of 2D images for a 3D part.
        part_manipulation_dict['multi_image_path'] = modeling_section['multi_image_path']
        part_manipulation_dict['multi_image_scale'] = float(modeling_section['multi_image_scale'])
        # Make sure the following is identical for single and multiple image modeling modes.
        image_thresh_key = 'multi_image_thresh_mode'
        image_thresh_mode = modeling_section[image_thresh_key].lower()
        if image_thresh_mode in image_thresh_mode_list:
            part_manipulation_dict[image_thresh_key] = image_thresh_mode
        else:
            raise ValueError("Invalid value for field '%s'." % image_thresh_key)
        part_manipulation_dict['multi_image_thresh_value'] = float(modeling_section['multi_image_thresh_value'])
        part_manipulation_dict['multi_image_denoise'] = config.getboolean('Modeling', 'multi_image_denoise')
    elif modeling_mode == '6':  # Planar Composite (Circular Inclusions)
        part_manipulation_dict['circle_list'] = csv_string_to_list(modeling_section['modeling_circle_table'])
    elif modeling_mode == '7':  # Spatial Composite (Spherical Inclusions)
        part_manipulation_dict['sphere_list'] = csv_string_to_list(modeling_section['modeling_sphere_table'])
    else:
        raise ValueError('Field "modeling_mode" is set to %s, which is invalid.' % modeling_mode)

    # BC: Boundary Conditions.
    bc_dict = dict()
    bc_section = config['BC']
    bc_dict['dim'] = dim
    bc_type = bc_section['bc_type']
    bc_dict['bc_type'] = bc_type  # There are no parameters associated with BCs.

    # Output.
    output_dict = dict()
    output_section = config['Output']
    if is_name_valid(name=output_section['file_name']):
        output_dict['file_name'] = output_section['file_name']
    else:
        raise ValueError('Field "file_name" contains an invalid name.')
    output_dict['elem_code'] = output_section['elem_code']
    output_dict['dim'] = dim
    output_mats_type = output_section['output_mats_type']
    if output_mats_type == '0':  # All Materials.
        output_dict['material_elem_sets'] = 'All'
    elif output_mats_type == '1':  # Non-Empty Materials.
        output_dict['material_elem_sets'] = 'Non-Empty'
    elif output_mats_type == '2':  # Output Selected Materials.
        output_dict['material_elem_sets'] = [int(i) for i in output_section['output_mats_select'].split(',')]
    else:
        raise ValueError('Field "output_mats_type" is set to %s, which is invalid.' % output_mats_type)

    logger.debug('Configuration file read successfully.')
    return part_creation_dict, part_manipulation_dict, bc_dict, output_dict


def csv_string_to_list(csv_string: str) -> list:
    """Convert a csv string to a list. The csv dialect is sniffed using Python's *csv* module.

    Args:
        csv_string: A string of comma separated values created using Python's *csv* module.

    Returns:
        List of rows detected in the csv string.
    """
    buffer_io = StringIO(csv_string)
    dialect = csv.Sniffer().sniff(buffer_io.readline())
    buffer_io.seek(0)
    csv_reader = csv.reader(buffer_io, dialect)
    return [row for row in csv_reader]


def validate_dim(dim: str):
    """Validate the *dim* parameter used throughout the library.
    Returns:
        ValueError: If dim is not '2D' or '3D'.
    """
    if dim.upper() not in ['2D', '3D']:
        raise ValueError("dim can only be one of '2D' or '3D'.")


def validate_materials_to_be_output(part, material_list: str | int | Iterable | NDArray):
    """Validate the list of materials that are to be output and return a list of material codes.

    Args:
        part (VoxelPart): The *VoxelPart* instance for which the operation is performed.
        material_list: One of the following:

          + *'All'* which outputs all materials in *part*.
          + *'Non-Empty'* which outputs all non-zero (=non-empty) materials in *part*.
          + An integer or a tuple of integer material codes corresponding
            to the materials that should be written to the output.
            All material codes should exist in *part*.

    Returns:
        A list of valid integer material codes that have been selected.
    """
    # Validate and process material_elem_sets.
    valid_materials = unique(part.data)
    if isinstance(material_list, str):
        if material_list.upper() in ['ALL', 'NON-EMPTY']:
            selected_mats = list(valid_materials)
            if (0 in selected_mats) and (material_list.upper() == 'NON-EMPTY'):
                selected_mats.remove(0)
            material_list = selected_mats
        else:
            raise ValueError(f"Invalid string '{material_list}' for material_list."
                             f"Valid values are 'All' and 'Non-Empty'.")
    else:  # Will raise most errors.
        for mat in material_list:
            if mat not in valid_materials:
                raise ValueError(f'Material {mat} specified in material_list is not present in the model.')
    return material_list
