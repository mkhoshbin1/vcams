"""The voxelpart package contains the main VoxelPart class and its methods.

See the :ref:`voxel-part` section for a complete explanation
of the basic concepts.
"""
import logging
import textwrap
from pathlib import Path
from typing import Union

import numpy as np
from numpy import ndarray, array

from . import __version__, __website__
from .helper import is_name_valid, read_configuration, process_working_dir
from .logger_conf import setup_main_logger
from .mask.function import mask_from_function
from .mask.image import mask_from_image, mask_from_image_sequence
from .mask.random import random_binary_mask
from .mask.shape import Circle, Sphere
from .mask.tpms import tpms_dict
from .output import write_abaqus_inp

logger = logging.getLogger(__name__)


class VoxelPart:
    """A class representing a rectangular or cuboid part made of voxels."""

    def __init__(self, size: tuple[int, int, int] | tuple[int, int],
                 base_material: int = 0,
                 voxel_size: tuple[float, float, float] | tuple[float, float] = (1.0, 1.0, 1.0),
                 dtype: str = 'uint8', name: str = 'unnamed', description: str = '',
                 working_dir: str | Path = None,
                 overwrite_logs: bool = True, log_debug: bool = False,
                 display_log: bool = True, main_logger_exists: bool = False):
        """
        Args:
            size: The tuple *(size_x, size_y, size_z)* which determines
                  the number of voxel elements in the three dimensions.

                  For 2D structures, *size_z* can be omitted,
                  but some parts of the program take it to be 1 for calculations.

                  This parameter determines the shape of the :attr:`data` attribute
                  and therefore must contain integers.

            base_material: The value used for filling :attr:`data` when the object is created.

                           Make sure it is within the range specified by the *dtype* parameter
                           (See the :ref:`materials` section).
                           Defaults to 0 which represents empty space.

            voxel_size: A tuple containing two or three floats which determines the size
                        of a voxel in the three directions.

                        For example, if the tuple (0.02, 0.1, 1.5) is specified,
                        each voxel will have those dimensions in the x, y, and z directions.

                        If a part is 2D, the third value can be omitted and the program assigns 1.0
                        as the rest of the library requires *voxel_size* to have three elements.

                        All values should be between 1E-5 and 1E+3.

            dtype: Data type used for creation of :attr:`data`.
                   Must be an unsigned integer type. Users are advised to study
                   the :ref:`materials` section for a thorough explanation of this parameter.

                   Defaults to *'uint8'ex_c11_* which allows for 256 materials in the model.

            name: Name of the voxel part which is used in a variety of places, including when exporting the part.
                  Must be valid according to the documentation for the :func:`.helper.is_name_valid` function.

                  Defaults to *'unnamed'*.

            description: A short description of the part which is used
                         in a variety of places, including when exporting the part.
                         Note that Abaqus™ only uses the first 80 characters of the string.
                         Defaults to an empty string.

            working_dir: Path to the folder where the final results, temporary file, and log files will be stored.
                         If set to *None* a suitable folder is automatically created in the user's home directory.

            overwrite_logs: If set to True, and the log file already exists, it will be overwritten.
                            Otherwise, the file will be opened in append mode.

            log_debug: If set to True, debug information will be written to program log.

            display_log: If set to True, all logs will be displayed on the screen
                         in addition to being written to file.

            main_logger_exists: If set to True, indicates that the main logger has already been created elsewhere.
                                Defaults to False which creates the main logger.
        """

        # Validate dtype.
        if not dtype.lower() in ('uint8', 'uint16', 'uint32', 'uint64'):
            raise ValueError("dtype can only be one of the following strings: "
                             "'uint8', 'uint16', 'uint32', 'uint64'")
        self.dtype = dtype
        """Data type used for the part."""

        # Set a temporary value for _data which is used by the data property.
        self._data = None

        # It seems that numpy.zeros has a special implementation which
        # makes it faster. numpy.ones is the same as numpy.fill.
        # Source: https://stackoverflow.com/questions/31498784.
        if base_material == 0:
            self.data = np.zeros(shape=size, dtype=dtype.lower())  #: data attribute.
        else:
            self.data = np.full(shape=size, fill_value=base_material, dtype=dtype.lower())
            """The *data* property of the *VoxelPart* instance.
            See the :ref:`data_structure` section for an in depth discussion."""

        # Validate and set voxel_size. Make sure that it has three elements.
        voxel_size = np.array(voxel_size, dtype='float')  # This catches strings and such.
        if voxel_size.shape != (3,):
            if voxel_size.shape == (2,):  # Add 1.0 as the third element.
                voxel_size = np.append(voxel_size, 1.0)
            else:
                raise ValueError('Invalid value for voxel_size.')
        if any(voxel_size <= 1E-5) or any(voxel_size >= 1E+3):
            raise ValueError('Invalid value for voxel_size. Values should be between 1E-5 and 1E+3.')
        self.voxel_size: ndarray = voxel_size
        """A numpy array containing three floats which determines the size of a voxel in the three directions."""

        # Validate name.
        if not is_name_valid(name):
            raise ValueError('Invalid name. Check the documentation for validity criteria.')
        self.name: str = name
        """Name of the voxel part which is used in a variety of places, including when exporting the part."""

        # Validate description.
        if not (isinstance(description, str) and description.isascii() and description.isprintable()):
            raise ValueError('Invalid description.')
        self.description: str = textwrap.fill(description, width=80)
        """A short description of the part which is used in a variety of places, including when exporting the part."""

        # Process and Validate working_dir.
        self.working_dir: Path = process_working_dir(working_dir, name)
        """Path to the folder where the final results, temporary file, and log files will be stored."""

        # Create an empty dictionary for element and node sets.
        self.elem_sets: dict = dict()
        """Dictionary in which keys are the names of the element sets
        and the values are and IDs of the elements in that set."""
        self.node_sets: dict = dict()
        """Dictionary in which keys are the names of the node sets
        and the values are and IDs of the elements in that set."""

        # Create variables for bcs and their sets.
        self._bc_type = None
        self._bc_nodeset_explicit = False
        self._bc_nodeset_simple = False
        self._dummy_node_dict = dict()

        # Create and configure the logger.
        if not main_logger_exists:
            self._log_file_path = setup_main_logger(part_name=name, working_dir=working_dir,
                                                    display_log=display_log, overwrite_logs=overwrite_logs,
                                                    log_debug=log_debug)
        else:
            self._log_file_path = None

        # Log creation of the object.
        logger.info('\n** Created using VCAMS v%s.'
                    '\n** VCAMS is a free and open source program available at: %s'
                    '\n** Author: Mohammadreza Khoshbin (www.mkhoshbin.com)\n',
                    __version__, __website__)
        logger.info("A VoxelPart object named '%s' was created" +
                    " with %s elements and an initial element value of %u.",
                    name, '*'.join(str(s) for s in size), base_material)

    @property
    def instance_name(self) -> str:
        """Name of the part instance which is name of the part + '-Ins'. Used for output to Abaqus™ input file."""
        return self.name + '-Ins'

    @property
    def size(self) -> ndarray:
        """Size of the *VoxelPart* instance.

        This is the shape of the part's *data* property, returned as a NumPy array.
        If the instance is 2D, it will have two elements, otherwise it will have three."""
        return array(self.data.shape)

    @property
    def real_size(self) -> ndarray:
        """Real size of the *VoxelPart* instance.

        This is defined as ``part.size * voxel_size``, and is returned as a NumPy array.
        If the instance is 2D, it will have two elements, otherwise it will have three."""
        return np.array([self.size[i] * self.voxel_size[i] for i in range(len(self.size))])

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value: ndarray):
        if not isinstance(value, ndarray):
            raise ValueError('data must be a numpy ndarray.')
        if not value.flags.c_contiguous:
            raise ValueError('data must be C-continuous.')
        if (self.data is not None) and (self.data.ndim != value.ndim):
            # Because in __init__, data is initially None.
            raise ValueError('The new value must have the exact ndim as the current data attribute.')
        if value.dtype != self.dtype:
            raise ValueError('The new value must have the exact dtype as the VoxelPart instance.')
        self._data = value.astype(dtype=self.dtype, order='C', casting='safe', subok=True, copy=True)

    def __del__(self):
        """Delete the object. The respective loggers are also flushed and closed."""
        logger_list = (logging.getLogger(__name__),)
        for lg in logger_list:
            for h in lg.handlers:
                # Handlers are only flushed and closed,
                # but not removed because I don't think it's necessary.
                h.flush()
                h.close()

    def __len__(self):
        return np.prod(self.size)

    def output_abaqus_inp(self, file_name: str, elem_code: str, dim: str,
                          material_elem_sets: str | tuple, custom_elem_sets: bool = True,
                          keep_temp_files: bool = False) -> Path:
        """Output the part to an Abaqus™ input file.

        Only the elements selected by the *material_elem_sets* parameter are selected,
        and afterwards they are grouped into sets by the material code.
        If *custom_elem_sets* is True, the custom element set are also included.
        If an element is part of a custom element set but is not part of the selected materials,
        It is not written to the output.

        This function simply calls :func:`.output.write_abaqus_inp`, except for the
        *scale* and *folder_path* parameters which are equal to :attr:`.VoxelPart.voxel_size`
        and :attr:`.VoxelPart.working_dir`, respectively.

        Args:
            file_name: Name of the file. Must be valid according to the documentation
                       for the :func:`.helper.is_name_valid` function and should not contain file extensions.
            elem_code: An uppercase string denoting the element code assigned to *all* elements in the model.
                       It must be a valid Abaqus element code such as *'CPE4R'* or *'C3D8R'*.
                       This parameter is not validated so care should be taken regarding validity and compatibility.
                       Currently, only 2D and 3D linear elements are supported.
                       To get around this, you can convert to quadratic elements after importing the model to Abaqus.
            dim: Dimensionality of the output part. Valid values are *'2D'* and *'3D'*.
            material_elem_sets: One of the following:

                                  + *'All'* which outputs all materials in the VoxelPart.
                                  + *'Non-Empty'* which outputs all non-zero (=non-empty) materials in the VoxelPart.
                                  + A tuple of integer material codes corresponding
                                    to the materials that should be written to the output.

            custom_elem_sets: If set to True, custom element sets will be written to the output.
            keep_temp_files: If set to True, temporary files will not be deleted. Used for debugging.

        Returns:
            Path object pointing to final Abaqus™ input file.
        """
        # Logging is done by the called function.
        return write_abaqus_inp(self, file_name=file_name,
                                elem_code=elem_code, dim=dim,
                                scale=tuple(self.voxel_size),
                                material_elem_sets=material_elem_sets,
                                custom_elem_sets=custom_elem_sets,
                                keep_temp_files=keep_temp_files)

    def add_custom_elem_set(self, name: str, ids: tuple | ndarray, replace: bool = True):
        """Add a custom element set to the part.

        Args:
            name: Name of the set. Must be valid according to the documentation for :func:`.helper.is_name_valid`.
            ids: A tuple or numpy array of integer element IDs to be added to the set.
                 The IDs should start at zero (zero-based indexing), and the proper value is output later.
                 The method converts it into a sorted, unique numpy array, but no other validation is performed.
            replace: If set to True and a set with the same name already  exists, the new set replaces the old one.
                     Otherwise, an error is raised.

                     Defaults to True.
        """
        if not is_name_valid(name):
            raise ValueError('Invalid name. Check the documentation for validity criteria.')
        if name in self.elem_sets and not replace:
            raise RuntimeError("An element set with the name '%s' already exists." % name)

        self.elem_sets[name] = np.unique(ids).astype('uint32')
        logger.debug("Added custom element set '%s' with %u elements.", name, len(self.elem_sets[name]))

    def add_node_set(self, name: str, ids: tuple | ndarray, replace: bool = True):
        """Add a node set to the part.

        Args:
            name: Name of the set. Must be valid according to the documentation for :func:`.helper.is_name_valid`.
            ids: A tuple or numpy array of integer node IDs to be added to the set.
                 The IDs should start at zero (zero-based indexing), and the proper value is output later.
                 The method converts it into a sorted, unique numpy array, but no other validation is performed.
            replace: If set to True and a set with the same name already  exists, the new set replaces the old one.
                     Otherwise, an error is raised.

                     Defaults to True.
        """
        if not is_name_valid(name):
            raise ValueError('Invalid name. Check the documentation for validity criteria.')
        if name in self.node_sets and not replace:
            raise RuntimeError(f"A node set with the name '{name}' already exists.")
        self.node_sets[name] = np.unique(ids).astype('uint32')
        logger.debug(f"Added custom node set '{name}' with {len(self.node_sets[name])} elements.")

    def add_bc(self, bc_type: str | None = None,
               explicit_nodesets: bool = False, simple_nodesets: bool = False):
        """Define a boundary condition (BC) for the part.
        Refer to the :ref:`boundary-conditions` section for a full explanation of the available BCs.

        The part must be a full square or cuboid. Also, if a BC is requested using *bc_type*,
        all necessary node sets are also created.
        For most use cases, that is the only parameter that must be specified.

        Args:
            bc_type: Type of the BC to be defined. Valid values are:

                     + None: No BCs will be defined.
                     + 'Nodeset Only': Only the node sets will be defined according to the other parameters.
                     + 'Linear Displacement': :ref:`boundary-conditions-lin-disp` will be created.
                     + 'Periodic': :ref:`boundary-conditions-pbc` will be created.

            explicit_nodesets: If True, explicit node sets are created for vertices, edges, and faces.
                               as described in the section titled :ref:`boundary-conditions-pbc`.
                               Defaults to *False*.
            simple_nodesets: If True, simplified node sets are created
                             which are the full faces for the 3D models or the edges for the 2D models,
                             as described in the section titled :ref:`boundary-conditions-lin-disp`.
                             Defaults to *True*.
        """
        if bc_type is None:
            self._bc_type = None
        elif bc_type.upper() in ['NODESET ONLY', 'LINEAR DISPLACEMENT', 'PERIODIC']:
            self._bc_type = bc_type.upper()
        else:
            raise ValueError('Invalid value for bc_type.')

        if (bc_type.upper() == 'NODESET ONLY') and not any([explicit_nodesets, simple_nodesets]):
            raise ValueError("bc_type is set to 'NODESET ONLY', but no node sets are requested."
                             "At least one of explicit_nodeset and simple_nodeset must be set to True.")
        self._bc_nodeset_explicit = explicit_nodesets
        self._bc_nodeset_simple = simple_nodesets

    def apply_mask(self, mask: ndarray, value: int):
        """Use a Boolean mask to select some elements of the part's :attr:`data` array
        and change them to a *value*.

        Args:
            mask: The Boolean mask to be used.
            value: Integer value to be assigned to the elements of the :attr:`data` attribute
                   where the Boolean mask is True.
        """
        # Make sure mask is a Boolean mask.
        if not mask.dtype == bool:
            raise ValueError("mask.dtype is not 'bool'.")
        # Make sure mask and self.data have the same shape.
        if not np.array_equal(self.size, mask.shape):
            if self.data.ndim == 2 and mask.shape[2] == 1:
                pass
            else:
                raise ValueError('mask is not of the same shape as VoxelPart.data.')
        # Make sure mask and self.data have the same order (Fortran or C contiguity).
        if mask.flags.f_contiguous != self.data.flags.f_contiguous:
            raise ValueError('mask is not of the same order (Fortran or C contiguity) as VoxelPart.data.')
        # Make sure value is a nonzero integer within the bounds of self.data.dtype.
        if not float(value).is_integer():
            raise ValueError('value is not an integer.')
        if value < 0:
            raise ValueError('value is less than zero.')
        if value > np.iinfo(self.data.dtype).max:
            raise ValueError(f'value is larger than the maximum supported by self.data.dtype, '
                             f'which is {np.iinfo(self.data.dtype).max}.')
        # Apply the mask to self.data.
        np.putmask(self.data, mask, value)

    def _add_dummy_nodes(self, fixed: bool = False, single_node: bool = False, three_nodes: bool = False):
        """Add the dummy nodes to the part.
        See :ref:`the relevant section on BCs <boundary-conditions-nodeset_only>` for more information.

        Args:
            fixed: If set to True, the dummy node for the fixed point is added with a node ID of 999999999.
            single_node: If set to True, the dummy node for a single moving point is added
                         with a node ID of 999999998.
            three_nodes: If set to True, the dummy node for three moving points is added
                         with a node IDs of 999999996, 999999997, and 999999998.
        """
        if not single_node ^ three_nodes:
            raise ValueError("Exactly one of single_node or three_nodes must be True.")
        if fixed:
            self._dummy_node_dict['RP0-NodeSet'] = 999999999
        if single_node:
            self._dummy_node_dict['RP1-NodeSet'] = 999999998
        if three_nodes:
            self._dummy_node_dict['RP1-NodeSet'] = 999999996
            self._dummy_node_dict['RP2-NodeSet'] = 999999997
            self._dummy_node_dict['RP3-NodeSet'] = 999999998

    def _return_material_elem_set(self, mat_code: int, num_padding: int = 0) -> tuple[str, ndarray]:
        """Return the IDs of the elements in the part that correspond to the given material code
        and a suitable name for the set.

        The name is a string with 'MAT-' prepended to the material code.

        Args:
            mat_code: Integer specifying the material for which element IDs must be found.
            num_padding: Number of padding zeros for the numerical portion of the material name.
                         Defaults to 0, which means no padding.

        Returns:
            A tuple where the first element is the material name,
            and the second element is a 1-D numpy array of element IDs.
        """
        name = 'MAT-{mat_code:0{num_padding}d}'.format(mat_code=mat_code, num_padding=num_padding)
        # Source: https://stackoverflow.com/a/32413139/7180705
        elem_ids = np.ravel_multi_index(multi_index=np.nonzero(self.data == mat_code),
                                        dims=self.size, mode='raise', order='C').astype('uint32')
        return name, elem_ids


def voxelpart_from_image(image_dim: str, image_path: str,
                         scale: float = 1.0, denoise: bool = True,
                         show_image: bool = False,
                         thresh_mode: str = 'otsu', thresh_value: float = None,
                         background_material: int = 0, foreground_material: int = 1,
                         voxel_size: tuple[float, float, float] | tuple[float, float] = (1.0, 1.0, 1.0),
                         dtype: str = 'uint8', name: str = 'unnamed',
                         description: str = '', working_dir: str | Path = None,
                         overwrite_logs: bool = True, log_debug: bool = False, display_log: bool = True,
                         **kwargs):
    """Create a :class:`VoxelPart` instance from a 2D or 3D image.

    This function creates a Boolean mask using either
    :func:`~vcams.mask.image.mask_from_image` or :func:`~vcams.mask.image.mask_from_image_sequence`,
    and then creates a :class:`VoxelPart` with the same size as the mask
    and properties given as input.
    The mask is then applied to the part using the *VoxelPart*'s :meth:`~VoxelPart.apply_mask` method.

    Args:
        image_dim: Dimensionality of the input image. Valid values are '2D' and '3D'.
        image_path:

          - For 2D images: The path string referring to the 2D image.
          - For 3D images: A string containing a loading pattern
            which describes the path of all images in the sequence.
            Use the *?* symbol as a placeholder for a single character.

        show_image: If set to True, the opened image and the final binary image
                    will be shown side by side in a figure.
                    The program may be paused while the window is open.
                    Currently, this has only been implemented for 2D images
                    and will be silently ignored for 3D images.
        scale: Scale to be applied to the image(s). Note that a scale greater than 1.0
               will introduce fake precision by interpolating the data and issues a warning.
        denoise: If set to True, the image will be denoised using a Bilateral filter.
        thresh_mode: The kind of threshold to be applied to the image.
                     Valid values are 'none', 'manual', and 'otsu'. Defaults to 'otsu'.
        thresh_value: If *thresh_mode* is set to 'manual', should be a float in the range (0, 1)
                      Which is used as a threshold for binarizing the image.
                      Defaults to *None* which raises an error when used.
        background_material: After the image is binarized, this material will be assigned to the *OFF* pixels.
        foreground_material: After the image is binarized, this material will be assigned to the *ON* pixels.
        voxel_size: See the documentation for the :meth:`VoxelPart.__init__` method.
        dtype: See the documentation for the :meth:`VoxelPart.__init__` method.
        name: See the documentation for the :meth:`VoxelPart.__init__` method.
        description: See the documentation for the :meth:`VoxelPart.__init__` method.
        working_dir: See the documentation for the :meth:`VoxelPart.__init__` method.
        overwrite_logs: See the documentation for the :meth:`VoxelPart.__init__` method.
        log_debug: See the documentation for the :meth:`VoxelPart.__init__` method.
        display_log: See the documentation for the :meth:`VoxelPart.__init__` method.

    Note that the size parameter used in the :meth:`VoxelPart.__init__` method
    is not one of the inputs and is determined from the image.
    """

    part_log_file_path = setup_main_logger(part_name=name, working_dir=working_dir,
                                           display_log=display_log, overwrite_logs=overwrite_logs,
                                           log_debug=log_debug)
    logger.info('Attempting to create a VoxelPart instance from image(s).')

    if image_dim.upper() not in ['2D', '3D']:
        raise ValueError("image_dim can only be one of '2D' or '3D'.")
    if image_dim.upper() == '2D':
        image_mask = mask_from_image(image_path=image_path, scale=scale,
                                     denoise=denoise, show_image=show_image,
                                     thresh_mode=thresh_mode, thresh_value=thresh_value)
    else:  # dim.upper() == '3D'
        image_mask = mask_from_image_sequence(load_pattern=image_path,
                                              scale=scale, denoise=denoise,
                                              thresh_mode=thresh_mode, thresh_value=thresh_value)
    # Create a VoxelPart instance.
    part_shape = image_mask.shape
    part = VoxelPart(size=part_shape, base_material=background_material, voxel_size=voxel_size,
                     dtype=dtype, name=name, description=description, working_dir=working_dir,
                     overwrite_logs=overwrite_logs, log_debug=log_debug, display_log=display_log,
                     main_logger_exists=True)
    part._log_file_path = part_log_file_path
    part.apply_mask(mask=image_mask, value=foreground_material)
    return part


def from_config_file(file_path: Union[str, Path]) -> VoxelPart:
    """Create a :class:`VoxelPart` object from a configuration file.

    Args:
        file_path: Full path to the configuration file. This file is usually created using the GUI
                   and although you can create or edit one, it's not recommended.
                   Scripts are much easier to work with and
                   this function is meant only as a bridge between the library and its GUI.

    Returns:
        The :class:`VoxelPart` object created based on the configuration file.
    """
    (part_creation_dict, part_manipulation_dict, bc_dict, output_dict) = read_configuration(file_path)

    logger.info('The model is being created from a configuration file loaded from %s' % file_path)
    modeling_mode = part_manipulation_dict['modeling_mode']
    if modeling_mode not in ('4', '5'):
        part = VoxelPart(**part_creation_dict)
    if modeling_mode == '0':  # No action selected. This is technically invalid, but consider it to be '1'.
        pass
    if modeling_mode == '1':  # No Further Manipulation.
        pass
    elif modeling_mode == '2':  # Random Element Dispersion
        boolean_mask = random_binary_mask(part=part, true_fraction=part_manipulation_dict['random_phase_fraction'])
        part.apply_mask(mask=boolean_mask, value=part_manipulation_dict['random_phase_matcode'])
    elif modeling_mode == '3':  # TPMS
        boolean_mask = mask_from_function(mask_shape=part.size,
                                          func=tpms_dict[part_manipulation_dict['tpms_type']],
                                          part=part,
                                          l=part_manipulation_dict['tpms_length'],
                                          c=part_manipulation_dict['tpms_constant'])
        part.apply_mask(mask=boolean_mask, value=part_manipulation_dict['tpms_fill_value'])
    elif modeling_mode == '4':  # Image Processing (Single 2D Image)
        part = voxelpart_from_image(image_dim='2D',
                                    image_path=part_manipulation_dict['single_image_path'],
                                    scale=part_manipulation_dict['single_image_scale'],
                                    thresh_mode=part_manipulation_dict['single_image_thresh_mode'],
                                    thresh_value=part_manipulation_dict['single_image_thresh_value'],
                                    denoise=part_manipulation_dict['single_image_denoise'],
                                    background_material=part_creation_dict['base_material'],
                                    foreground_material=2,  # This is hardcoded.
                                    **part_creation_dict)
    elif modeling_mode == '5':  # Stack of 2D images for a 3D part.
        part = voxelpart_from_image(image_dim='3D',
                                    image_path=part_manipulation_dict['multi_image_path'],
                                    scale=part_manipulation_dict['multi_image_scale'],
                                    thresh_mode=part_manipulation_dict['multi_image_thresh_mode'],
                                    thresh_value=part_manipulation_dict['multi_image_thresh_value'],
                                    denoise=part_manipulation_dict['multi_image_denoise'],
                                    background_material=part_creation_dict['base_material'],
                                    foreground_material=2,  # This is hardcoded.
                                    **part_creation_dict)
    elif modeling_mode == '6':  # Planar Composite (Circular Inclusions)
        for row in part_manipulation_dict['circle_list']:
            circle_obj = Circle(id=0, xc=float(row[0]), yc=float(row[1]), r=float(row[2]))
            part.apply_mask(mask=circle_obj.calculate_mask(part_shape=part.size, voxel_size=part.voxel_size),
                            value=int(row[3]))
    elif modeling_mode == '7':  # Spatial Composite (Spherical Inclusions)
        for row in part_manipulation_dict['sphere_list']:
            circle_obj = Sphere(id=0, xc=float(row[0]), yc=float(row[1]), zc=float(row[2]), r=float(row[3]))
            part.apply_mask(mask=circle_obj.calculate_mask(part_shape=part.size, voxel_size=part.voxel_size),
                            value=int(row[4]))
    else:
        raise ValueError("Invalid value '%s' for part_manipulation_dict['modeling_mode']." % modeling_mode)

    bc_type = bc_dict['bc_type']
    if bc_type == '0':  # No BC.
        pass
    elif bc_type == '1':  # Sets only.
        part.add_bc(bc_type='NODESET ONLY', explicit_nodesets=True, simple_nodesets=True)
    elif bc_type == '2':  # Linear Displacement Boundary Conditions.
        part.add_bc(bc_type='Linear Displacement')
    elif bc_type == '3':  # Periodic Boundary Condition.
        part.add_bc(bc_type='Periodic')
    else:
        raise ValueError("Invalid value '%s' for bc_dict['bc_type']" % bc_type)

    part.output_abaqus_inp(**output_dict)

    logger.info('Creation of the model from the configuration file completed successfully.')
    return part
