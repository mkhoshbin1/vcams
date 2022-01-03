"""The voxelpart package contains the main VoxelPart class and its methods."""
import logging  # TODO: add function to close logger.
import os
import textwrap
from pathlib import Path
from typing import Union

import numpy as np

from . import __version__, __website__
# from .bc import create_node_sets
from .helper import is_name_valid, return_default_results_path, read_configuration, \
    write_to_logger_streams
from .mask.function import mask_from_function
from .mask.shape import ShapeArray, Circle, Sphere
from .mask.tpms import tpms_dict
from .output import write_abaqus_inp

logger = logging.getLogger(__name__)


# TODO: change size to shape.
# TODO: add shape as a variable with a getter.
# TODO: add a random inclusion mode. use np.arange + np.shuffle and np.reshape to proper size.

class VoxelPart:
    def __init__(self, size, base_material=0, voxel_size=(1, 1, 1),
                 dtype='uint8', name='unnamed', description='',
                 results_path=None, overwrite_logs=True, log_debug=False):
        """
        Args:
            size (tuple): A tuple is the shape of (x,y,z) which determines
                          size :py:attr:`~data`, representing size of the
                          voxel mesh in the three dimensions.
                          The three values must be integers and for 2D structures,
                          size of the z dimension must be set to 1.

            base_material (int): The value used for filling :py:attr:`~data`.
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
        if base_material == 0:
            self.data = np.zeros(shape=size, dtype=dtype.lower())
        else:
            self.data = np.full(shape=size, fill_value=base_material, dtype=dtype.lower())

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

        # Create variables for bcs and their sets.
        self._bc_type = None
        self._bc_nodeset_vertices = False
        self._bc_nodeset_edges = False
        self._bc_nodeset_faces = False
        self._bc_nodeset_explicit = False
        self._bc_nodeset_simple = False
        self._dummy_node_dict = dict()

        # Create and configure the logger.
        filemode = 'w' if overwrite_logs else 'a'
        log_level = logging.DEBUG if log_debug else logging.INFO
        log_file_path = Path(self.results_path) / (name + '.log')
        logging.basicConfig(filename=log_file_path, filemode=filemode, level=log_level,
                            format='%(asctime)s - %(levelname) 5s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

        # Log creation of the object.
        logger.info('\n**Created using VCAMS v%s.'
                    '\n**VCAMS is a free and open source program available at: %s'
                    '\n**Author: Mohammadreza Khoshbin (www.mkhoshbin.com)\n',
                    __version__, __website__)
        logger.info("A VoxelPart object named '%s' was created" +
                    " with %s elements and an initial element value of %u.",
                    name, '*'.join(str(s) for s in size), base_material)

    @property
    def instance_name(self):  # TODO: doc
        return self.name + '-Ins'

    @property
    def size(self):  # TODO: doc, use everywhere in refactor
        return self.data.shape

    @property
    def real_size(self):  # TODO: doc
        return np.array([self.size[i] * self.voxel_size[i] for i in range(len(self.size))])

    def output_abaqus_inp(self, file_name, elem_type, dim,
                          material_elem_sets, custom_elem_sets=True):
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

    def add_dummy_nodes(self, fixed=True, single_node=False, three_nodes=False):

        if not single_node ^ three_nodes:
            raise ValueError("Exactly one of single_node or three_nodes must be True.")

        if fixed:
            self._dummy_node_dict['RP0-NodeSet'] = 999999999  # TODO: change max nodes to reflect.
        if single_node:
            self._dummy_node_dict['RP1-NodeSet'] = 999999998
        if three_nodes:
            self._dummy_node_dict['RP1-NodeSet'] = 999999996
            self._dummy_node_dict['RP2-NodeSet'] = 999999997
            self._dummy_node_dict['RP3-NodeSet'] = 999999998



    def add_bc(self, bc_type=None, vertices_nodeset=True, edges_nodeset=True, faces_nodeset=True,
               explicit_nodeset=False, simple_nodeset=False):
        """Define default node sets in the VoxelPart. They are created according to TODO

        Args:
            bc_type (str): #TODO
        """

        # TODO: reconsider and simplify interface.
        if bc_type is None:
            self._bc_type = None
        elif bc_type.upper() in ['NODESET ONLY', 'LINEAR DISPLACEMENT', 'PERIODIC']:
            self._bc_type = bc_type.upper()
        else:
            raise ValueError('Invalid value for bc_type.')

        if not any([vertices_nodeset, edges_nodeset, faces_nodeset]):
            raise ValueError("At least one of vertices_nodeset, edges_nodeset and faces_nodeset must be set to True.")
        self._bc_nodeset_vertices = vertices_nodeset
        self._bc_nodeset_edges = edges_nodeset
        self._bc_nodeset_faces = faces_nodeset
        self._bc_nodeset_explicit = explicit_nodeset
        self._bc_nodeset_simple = simple_nodeset

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
    (part_creation_dict, part_manipulation_dict, bc_dict, output_dict) = \
        read_configuration(file_path)

    part = VoxelPart(**part_creation_dict)
    logger.info('The model is being created from a configuration file loaded from %s' % file_path)

    modeling_mode = part_manipulation_dict['modeling_mode']
    if modeling_mode == '0':  # No further action.
        pass
    elif modeling_mode == '1':  # TPMS
        boolean_mask = mask_from_function(mask_shape=part.data.shape,
                                          func=tpms_dict[part_manipulation_dict['tpms_type']],
                                          voxel_size=part.voxel_size,
                                          l=part_manipulation_dict['tpms_length'],
                                          c=part_manipulation_dict['tpms_constant'])
        part.apply_mask(mask=boolean_mask, value=part_manipulation_dict['tpms_fill_value'])
    elif modeling_mode == '2':  # Planar Composite (Circular Inclusions)
        for row in part_manipulation_dict['circle_list']:
            circle_obj = Circle(id=0, a=float(row[0]), b=float(row[1]), r=float(row[2]))
            part.apply_mask(mask=circle_obj.calculate_mask(part_shape=part.data.shape,
                                                           voxel_size=part.voxel_size),
                            value=int(row[3]))
    elif modeling_mode == '3':  # Spatial Composite (Spherical Inclusions)
        for row in part_manipulation_dict['sphere_list']:
            circle_obj = Sphere(id=0, a=float(row[0]), b=float(row[1]),
                                c=float(row[2]), r=float(row[3]))
            part.apply_mask(mask=circle_obj.calculate_mask(part_shape=part.data.shape,
                                                           voxel_size=part.voxel_size),
                            value=int(row[4]))
    else:
        raise ValueError(
            "Invalid value '%s' for part_manipulation_dict['modeling_mode']." % modeling_mode)

    bc_type = bc_dict['bc_type']
    if bc_type == '0':  # No BC.
        pass
    elif bc_type == '1':  # Sets only.
        part.add_bc(bc_type='NODESET ONLY', vertices_nodeset=True, edges_nodeset=True, faces_nodeset=True,
                    explicit_nodeset=True, simple_nodeset=True)
    elif bc_type == '2':  # Periodic BC.
        raise NotImplementedError('Periodic BC has not been implemented.')  # TODO
    else:
        raise ValueError("Invalid value '%s' for bc_dict['bc_type']" % bc_type)

    part.output_abaqus_inp(**output_dict)

    logger.info('Creation of the model from the configuration file completed successfully.')
    return part
