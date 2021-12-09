"""The voxelpart package contains the main VoxelPart class and its methods."""
import logging  # TODO: add function to close logger.
import os
import textwrap
from pathlib import Path
from configparser import ConfigParser
from typing import Union

import numpy as np

from . import __version__, __website__
from .bc import create_node_sets
from .helper import is_name_valid, return_default_results_path
from .mask.function import mask_from_function
from .mask.tpms import tpms_dict
from .output import write_abaqus_inp

logger = logging.getLogger(__name__)


# TODO: change size to shape.
# TODO: add shape as a variable with a getter.
# TODO: add a random inclusion mode. use np.arange + np.shuffle and np.reshape to proper size.

class VoxelPart:
    def __init__(self, size, fill_value=0, voxel_size=(1, 1, 1),
                 dtype='uint8', name='unnamed', description='',
                 results_path=None, overwrite_logs=True, log_debug=False):
        """
        Args:
            size (tuple): A tuple is the shape of (x,y,z) which determines
                          size :py:attr:`~data`, representing size of the
                          voxel mesh in the three dimensions.
                          The three values must be integers and for 2D structures,
                          size of the z dimension must be set to 1.

            fill_value (int): The value used for filling :py:attr:`~data`.
                              It is passed to numpy.full.
                              Make sure it is within the range specified by *dtype* #TODO: link
                              Defaults to 0 which represents empty space.

            voxel_size (tuple | numpy.ndarray): A tuple containing two or three floats which determine
                                the size of a voxel in the x, y, and z directions.
                                For example, if the tuple (0.02, 0.1, 1.5) is specified,
                                each voxel will have those dimensions in the x, y, and z directions.
                                If a part is 2D, the third value must be present but is not used.
                                If it's not present, a value of 1.0 is assigned.

            dtype (str): Data type used for creation of :py:attr:`~data`.
                         Because each number represents a material, data
                         must be of unsigned integer type. The number of
                         bytes can effectively determine the number materials
                         available for modeling. The user is cautioned to choose
                         the smallest possible value, because data type
                         has a huge impact on object size.
                         The following are available:

                         ======== ============== =================
                          Input    # Materials    numpy Equivalent
                         ======== ============== =================
                         'uint8'  255    + Empty numpy.uint8
                         'uint16' 65,535 + Empty numpy.uint16
                         'uint32' 2^32   + Empty numpy.uint32
                         'uint64' 2^64   + Empty numpy.uint64
                         ======== ============== =================

                         Defaults to 'uint8'.

            name (str): Name of the voxel part which is used for exporting the part.
                        Must be valid according to the documentation
                        for :py:meth:`helper.is_name_valid`.
                        Defaults to 'unnamed'.

            description (str): A short description of the part which is used
                               when exporting the part to Abaqus (TM).
                               Note that Abaqus only uses the first 80 characters
                               of the string.
                               Defaults to an empty string.

            results_path (str): Path to the folder where the intermediate and final results
                                and program logs will be stored.
                                Defaults to :py:obj:`None` which automatically
                                creates a suitable folder in the user's home directory.

            overwrite_logs (bool): If set to :py:obj:`True`, and the log file already exists,
                                   it will be overwritten. Otherwise, the file will be opened
                                   in append mode. Defaults to :py:obj:`True`.

            log_debug (bool): If set to :py:obj:`True`, debug information will be logged.
                              Defaults to :py:obj:`False`.
        """

        # Validate dtype. It seems that it can be passed as a string.
        # If any error is seen, it should be converted to the corresponding object.
        if not dtype.lower() in ('uint8', 'uint16', 'uint32', 'uint64'):
            raise ValueError('dtype can only be one of the following strings:' +
                             " 'uint8', 'uint16', 'uint32', 'uint64'")

        # It seems that numpy.zeros has a special implementation which
        # makes it faster. numpy.ones is the same as numpy.fill.
        # Source: https://stackoverflow.com/questions/31498784.
        if fill_value == 0:
            self.data = np.zeros(shape=size, dtype=dtype.lower())
        else:
            self.data = np.full(shape=size, fill_value=fill_value, dtype=dtype.lower())

        # Validate and set voxel_size. Make sure that it has three elements.
        voxel_size = np.array(voxel_size, dtype='float')  # This catches strings and such.
        if voxel_size.shape != (3,):
            if voxel_size.shape == (2,):  # Add 1.0 as the third element.
                voxel_size = np.append(voxel_size, 1.0)
            else:
                raise ValueError('Invalid value for voxel_size.')
        self.voxel_size = voxel_size  # TODO: Validate min and max. also check with gui.

        # Validate name.
        if not is_name_valid(name):
            raise ValueError('Invalid name. Check the documentation for validity criteria.')
        self.name = name

        # Validate description.
        if not (isinstance(description,
                           str) and description.isascii() and description.isprintable()):
            raise ValueError('Invalid description.')
        self.description = textwrap.fill(description, width=80)

        # Validate results_path.
        if results_path is None:  # TODO: rename to working_dir.
            results_path = return_default_results_path(part_name=self.name)
        else:
            results_path = Path(results_path)
        results_path.mkdir(parents=True, exist_ok=True)
        self.results_path = results_path

        # Create an empty dictionary for element and node sets.
        self.elem_sets = dict()
        self.node_sets = dict()

        # Create and configure the logger.
        filemode = 'w' if overwrite_logs else 'a'
        log_level = logging.DEBUG if log_debug else logging.INFO
        logging.basicConfig(filename=os.path.join(self.results_path, name + '.log'),
                            filemode=filemode, level=log_level,
                            format='%(asctime)s - %(levelname) 5s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

        # Log creation of the object.
        logger_stream = logger.root.handlers[0].stream
        logger_stream.writelines(
            ['Created using VCAMS v%s.\n' % __version__,
             'VCAMS is a free and open source program available at:\n%s\n' % __website__,
             'Author: Mohammadreza Khoshbin (www.mkhoshbin.com)\n\nProgram Log\n']
        )
        logger_stream.flush()

        logger.info("A VoxelPart object named '%s' was created" +
                    " with %s elements and an initial element value of %u.",
                    name, '*'.join(str(s) for s in size), fill_value)

    def output_abaqus_inp(self, file_name, elem_type, dim,
                          material_elem_sets, custom_elem_sets):
        """Output the part to an Abaqus (TM) input file.
        For a full list of parameters, see :py:meth:`output.write_abaqus_inp`.
        Note that the parameter *scale* is not used in this function and
        is equal to VoxelPart.voxel_size.
        Similarly, *folder_path* is equal to self.results_path
        """

        # Logging is done by the called function.
        write_abaqus_inp(self, file_name=file_name,
                         folder_path=self.results_path,
                         elem_code=elem_type, dim=dim,
                         scale=tuple(self.voxel_size),
                         material_elem_sets=material_elem_sets,
                         custom_elem_sets=custom_elem_sets,
                         write_assembly=True,
                         add_dummy_node=True,
                         keep_temp_files=False)

    def return_material_elem_set(self, mat_code, num_padding=0):
        """Return the IDs of the elements in the part that correspond to the given material code
        and a suitable name for the set.

        The name is a string with 'MAT-' prepended to the material code.

        Args:
            mat_code (int): Integer specifying the material for which element IDs must be found.
            num_padding (int): Number of padding zeros for the material name.
                               Defaults to 0, which means no padding.

        Returns:
            tuple: A tuple where the first element is the material name,
                   and the second element is numpy.ndarray A 1-D ndarray of element IDs.
        """

        name = 'MAT-{mat_code:0{num_padding}d}'.format(mat_code=mat_code, num_padding=num_padding)
        # Source: https://stackoverflow.com/a/32413139/7180705
        elem_ids = np.ravel_multi_index(multi_index=np.nonzero(self.data == mat_code),
                                        dims=self.data.shape, mode='raise', order='C').astype(
            'uint32')
        return name, elem_ids

    def add_custom_elem_set(self, name, ids, replace=True):
        """Add a custom element set to the part.

        Args:
            name (str): Name of the set. Must be valid according to the documentation
                        for :py:meth:`helper.is_name_valid`.

            ids (tuple): A tuple or numpy.ndarray of integer element IDs to
                         be added to the set. Element IDs should start
                         at zero (zero-based indexing), and the proper value is output later.
                         It is passed to numpy.unique to ensure that it is sorted,
                         unique, and a numpy ndarray, but is not validated in any other way.

            replace (bool): If set to :py:obj:`True` and a set with the same name
                            already  exists, the new set replaces the old one.
                            Otherwise, an error is raised.
                            Defaults to :py:obj:`True`.
        """

        if not is_name_valid(name):
            raise ValueError('Invalid name. Check the documentation for validity criteria.')
        if name in self.elem_sets and not replace:
            raise RuntimeError("An element set with the name '%s' already exists." % name)

        self.elem_sets[name] = np.unique(ids).astype('uint32')
        logger.debug("Added custom element set '%s' with %u elements.",
                     name, len(self.elem_sets[name]))

    def add_node_set(self, name, ids, replace=True):
        """Add a node set to the part.

        Args:
            name (str): Name of the set. Must be valid according to the documentation
                        for :py:meth:`helper.is_name_valid`.

            ids (tuple): A tuple or numpy.ndarray of integer node IDs to
                         be added to the set. Node IDs should start
                         at zero (zero-based indexing), and the proper value is output later.
                         It is passed to numpy.unique to ensure that it is sorted,
                         unique, and a numpy ndarray, but is not validated in any other way.

            replace (bool): If set to :py:obj:`True` and a set with the same name
                            already  exists, the new set replaces the old one.
                            Otherwise, an error is raised.
                            Defaults to :py:obj:`True`.
        """

        if not is_name_valid(name):
            raise ValueError('Invalid name. Check the documentation for validity criteria.')
        if name in self.node_sets and not replace:
            raise RuntimeError("A node set with the name '%s' already exists." % name)

        self.node_sets[name] = np.unique(ids).astype('uint32')
        logger.debug("Added custom node set '%s' with %u elements.",
                     name, len(self.node_sets[name]))

    def add_default_node_sets(self, dim):
        """Define default node sets in the VoxelPart. They are created according to TODO

        Args:
            dim (str): Dimensionality of the part which affects the created node sets.
                       Valid values are '2D' and '3D'.
        """
        create_node_sets(part=self, dim=dim)

    def apply_mask(self, mask, value):
        """Use a boolean mask to change values of the :py:attr:`~data` attribute.

        This function does some validations and then uses numpy.putmask().

        Args:
            mask (numpy.ndarray): Boolean mask to be used.

            value (int): Integer value to be assigned to the elements
                         of the :py:attr:`~data` attribute where
                         the boolean mask is :py:obj:`True`.
            """

        # Make sure mask is a boolean mask.
        if not mask.dtype == bool:
            raise ValueError("mask.dtype is not 'bool'.")

        # Make sure mask and self.data have the same shape.
        if mask.shape != self.data.shape:
            if self.data.ndim == 2 and mask.shape[2] == 1:
                pass
            else:
                raise ValueError('mask is not of the same shape as VoxelPart.data.')

        # Make sure mask and self.data have the same order (Fortran or C contiguity).
        if mask.flags.f_contiguous != self.data.flags.f_contiguous:
            raise ValueError('mask is not of the same order (Fortran or C contiguity) as '
                             'VoxelPart.data.')

        # Make sure value is a nonzero integer within the bounds of self.data.dtype.
        if not float(value).is_integer():
            raise ValueError('value is not an integer.')
        if value < 0:
            raise ValueError('value is less than zero.')
        if value > np.iinfo(self.data.dtype).max:
            raise ValueError('value is larger than the maximum supported by self.data.dtype,' +
                             ' which is %d.' % np.iinfo(self.data.dtype).max)

        # Apply the mask to self.data.
        np.putmask(self.data, mask, value)


def from_config_file(file_path):
    # TODO: log.
    config = ConfigParser()
    config.read(file_path)

    # Check validity of the imported settings.
    section_list = ('Basic', 'Modeling', 'BC', 'Output')
    for name in section_list:
        if name not in config.sections():
            raise ValueError('Section "%s" was not present in the settings file.' % name)

    # Basic: Information used for creating the part.
    part_creation_dict = dict()
    basic = config['Basic']
    dim = basic['dim']  # FIXME
    part_creation_dict['size'] = (int(basic['num_voxels_x']),
                                  int(basic['num_voxels_y']), int(basic['num_voxels_z']))
    if 'fill_value' in basic:
        part_creation_dict['fill_value'] = int(basic['fill_value'])
    else:
        part_creation_dict['fill_value'] = 0
    part_creation_dict['voxel_size'] = (float(basic['voxel_size_x']),
                                        float(basic['voxel_size_y']), float(basic['voxel_size_z']))
    num_mats = basic['num_mats']
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
    part_creation_dict['name'] = basic['part_name']
    part_creation_dict['description'] = basic['part_description']
    part_creation_dict['results_path'] = basic['working_dir']
    part_creation_dict['overwrite_logs'] = True
    part_creation_dict['log_debug'] = config.getboolean('Basic', 'log_debug')

    # Modeling: Manipulating the part.
    part_manipulation_dict = dict()
    modeling = config['Modeling']
    modeling_mode = modeling['modeling_mode']
    part_manipulation_dict['modeling_mode'] = modeling_mode
    if modeling_mode == '0':  # No further action.
        pass
    elif modeling_mode == '1':  # TPMS
        tpms_type = modeling['tpms_type']
        if int(tpms_type) in tpms_dict.keys():
            part_manipulation_dict['tpms_type'] = int(tpms_type)
        else:
            raise ValueError('Field "tpms_type" is set to %s, which is invalid.' % tpms_type)
        part_manipulation_dict['tpms_length'] = float(modeling['tpms_length'])
        part_manipulation_dict['tpms_constant'] = float(modeling['tpms_constant'])
    elif modeling_mode == '2':  # Planar Composite (Circular Inclusions)
        raise NotImplementedError('Addition of Circular Inclusions has not been implemented.')
    elif modeling_mode == '3':  # Spatial Composite (Spherical Inclusions)
        raise NotImplementedError('Addition of Spherical Inclusions has not been implemented.')
    else:
        raise ValueError('Field "modeling_mode" is set to %s, which is invalid.' % modeling_mode)

    # BC: Boundary Conditions.
    bc_dict = dict()
    bc = config['BC']
    bc_type = bc['bc_type']
    bc_dict['bc_type'] = bc_type
    if bc_type == '0':  # No BC.
        pass
    elif bc_type == '1':  # Sets only.
        raise NotImplementedError('Creation of sets has not been implemented.')  # TODO: pass
    elif bc_type == '2':  # Periodic BC.
        raise NotImplementedError('Periodic BC has not been implemented.')  # TODO
    else:
        raise ValueError('Field "bc_type" is set to %s, which is invalid.' % bc_type)

    part = VoxelPart(**part_creation_dict)

    modeling_mode = part_manipulation_dict['modeling_mode']
    if modeling_mode == '0':  # No further action.
        pass
    elif modeling_mode == '1':  # TPMS
        boolean_mask = mask_from_function(mask_shape=part.data.shape,
                                          func=tpms_dict[part_manipulation_dict['tpms_type']],
                                          voxel_size=part.voxel_size,
                                          l=part_manipulation_dict['tpms_length'],
                                          c=part_manipulation_dict['tpms_constant'])
        part.apply_mask(mask=boolean_mask, value=1)
    elif modeling_mode == '2':  # Planar Composite (Circular Inclusions)
        raise NotImplementedError('Addition of Circular Inclusions has not been implemented.')
    elif modeling_mode == '3':  # Spatial Composite (Spherical Inclusions)
        raise NotImplementedError('Addition of Spherical Inclusions has not been implemented.')
    else:
        raise ValueError(
            "Invalid value '%s' for part_manipulation_dict['modeling_mode']." % modeling_mode)

    bc_type = bc_dict['bc_type']
    if bc_type == '0':  # No BC.
        pass
    elif bc_type == '1':  # Sets only.
        part.add_default_node_sets(dim=dim)  # FIXME
    elif bc_type == '2':  # Periodic BC.
        raise NotImplementedError('Periodic BC has not been implemented.')  # TODO
    else:
        raise ValueError("Invalid value '%s' for bc_dict['bc_type']" % bc_type)



    return part
