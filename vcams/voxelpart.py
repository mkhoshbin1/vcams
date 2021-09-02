"""The voxelpart package contains the main VoxelPart class and its methods."""
import logging  # TODO: add function to close logger.
import os
import textwrap

import numpy as np

from . import __version__, __website__
from . import helper
from .output import write_abaqus_inp

logger = logging.getLogger(__name__)


# TODO: change size to shape.
# TODO: add shape as a variable with a getter.

class VoxelPart:
    def __init__(self, size, fill_value=0, voxel_size=(1, 1, 1),
                 dtype='uint8', name='unnamed', description='',
                 logger_path=os.path.expanduser('~'),
                 overwrite_logs=True, log_debug=False):
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

            voxel_size (tuple): A tuple containing two or three floats which determine
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

            logger_path (str): Path to the folder where the log file will be created.
                               Defaults to the user's home directory.

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
        self.voxel_size = voxel_size

        # Validate name.
        if not helper.is_name_valid(name):
            raise ValueError('Invalid name. Check the documentation for validity criteria.')
        self.name = name

        # Validate description.
        if not (isinstance(description,
                           str) and description.isascii() and description.isprintable()):
            raise ValueError('Invalid description.')
        self.description = textwrap.fill(description, width=80)

        # Create an empty dictionary for element sets.
        self.elem_sets = dict()

        # Create and configure the logger.
        filemode = 'w' if overwrite_logs else 'a'
        log_level = logging.DEBUG if log_debug else logging.INFO
        logging.basicConfig(filename=os.path.join(logger_path, name + '.log'),
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

    def output_abaqus_inp(self, file_name, folder_path, elem_type, dim,
                          material_elem_sets, custom_elem_sets):
        """Output the part to an Abaqus (TM) input file.
        For a full list of parameters, see :py:meth:`output.write_abaqus_inp`.
        Note that the parameter *scale* is not used in this function and
        is equal to VoxelPart.voxel_size.
        """

        # Logging is done by the called function.
        write_abaqus_inp(self, file_name, folder_path, elem_type, dim,
                         scale=tuple(self.voxel_size),
                         material_elem_sets=material_elem_sets,
                         custom_elem_sets=custom_elem_sets)

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

    def add_custom_elem_set(self, name, elem_ids, replace=True):
        """Add a custom element set to the part.

        Args:
            name (str): Name of the set. Must be valid according to the documentation
                        for :py:meth:`helper.is_name_valid`.

            elem_ids (tuple): A tuple or numpy.ndarray of integer element IDs to
                              be added to the set. Element IDs should start
                              at zero (zero-based indexing), and the proper value is output later.
                              It is passed to numpy.unique to ensure that it is sorted,
                              unique, and a numpy ndarray, but is not validated in any other way.

            replace (bool): If set to :py:obj:`True` and a set with the same name
                            already  exists, the new set replaces the old one.
                            Otherwise, an error is raised.
                            Defaults to :py:obj:`True`.
        """

        if not helper.is_name_valid(name):
            raise ValueError('Invalid name. Check the documentation for validity criteria.')
        if name in self.elem_sets and not replace:
            raise RuntimeError("An element set with the name '%s' already exists." % name)

        self.elem_sets[name] = np.unique(elem_ids).astype('uint32')
        logger.debug("Added custom element set '%s' with %u elements.",
                     name, len(self.elem_sets[name]))

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
