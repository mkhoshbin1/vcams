"""The voxelpart package contains the main VoxelPart class and its methods.

See the :ref:`voxel-part` section for a complete explanation
of the basic concepts.
"""
import logging  # TODO: add function to close logger.
import textwrap
from pathlib import Path
from typing import Union

import numpy as np
from numpy import ndarray, rot90

from . import __version__, __website__
from .helper import is_name_valid, return_default_results_path, read_configuration
from .logger_conf import setup_logger
from .mask.function import mask_from_function
from .mask.image import mask_from_image, mask_from_image_sequence
from .mask.shape import ShapeArray, Circle, Sphere
from .mask.tpms import tpms_dict
from .output import write_abaqus_inp

logger = logging.getLogger(__name__)


class VoxelPart:
    def __init__(self, size: Union[tuple[int, int, int], tuple[int, int]],
                 base_material: int = 0,
                 voxel_size: Union[tuple[float, float, float], tuple[float, float]] = (1.0, 1.0, 1.0),
                 dtype: str = 'uint8', name: str = 'unnamed', description: str = '',
                 results_path: Union[str, Path] = None,
                 overwrite_logs: bool = True, log_debug: bool = False):
        """
        Args:
            size: The tuple *(size_x, size_y, size_z)* which determines
                  the number of voxel elements in the three dimensions.

                  For 2D structures, *size_z* can be omitted,
                  but some part of the program take it to be 1 for calculations.

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

            dtype: Data type used for creation of :attr:`data`.
                   Must be an unsigned integer type. Users are advised to study
                   the :ref:`materials` section for a thorough explanation of this parameter.

                   Defaults to ``'uint8'`` which allows for 256 materials in the model.

            name: Name of the voxel part which is used in a variety of places, including when exporting the part.
                  Must be valid according to the documentation for the :func:`.helper.is_name_valid` function.

                  Defaults to ``'unnamed'``.

            description: A short description of the part which is used
                         in a variety of places, including when exporting the part.
                         Note that Abaqus™ only uses the first 80 characters of the string.
                         Defaults to an empty string.

            results_path: Path to the folder where the final results, temporary file, and log files will be stored.
                          If set to *None* a suitable folder is automatically created in the user's home directory.

            overwrite_logs: If set to True, and the log file already exists, it will be overwritten.
                            Otherwise, the file will be opened in append mode.

            log_debug: If set to True, debug information will be written to program log.
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
            """TODO after adding property."""

        # Validate and set voxel_size. Make sure that it has three elements.
        voxel_size = np.array(voxel_size, dtype='float')  # This catches strings and such.
        if voxel_size.shape != (3,):
            if voxel_size.shape == (2,):  # Add 1.0 as the third element.
                voxel_size = np.append(voxel_size, 1.0)
            else:
                raise ValueError('Invalid value for voxel_size.')
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

        # Validate results_path.
        if results_path is None:  # TODO: rename to working_dir.
            results_path = return_default_results_path(part_name=self.name)
        else:
            results_path = Path(results_path)
        results_path.mkdir(parents=True, exist_ok=True)
        self.results_path: Path = results_path
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
        self._bc_nodeset_vertices = False
        self._bc_nodeset_edges = False
        self._bc_nodeset_faces = False
        self._bc_nodeset_explicit = False
        self._bc_nodeset_simple = False
        self._dummy_node_dict = dict()

        # Create and configure the logger.
        self._log_file_path = Path(self.results_path) / (name + '.log')  # Make sure it's necessary.
        setup_logger(logger_name=__name__, log_file=self._log_file_path, display_log=False,
                     overwrite_logs=overwrite_logs, log_debug=log_debug)
        # TODO: add display_log as parameter.

        # Log creation of the object.
        logger.info('\n** Created using VCAMS v%s.'
                    '\n** VCAMS is a free and open source program available at: %s'
                    '\n** Author: Mohammadreza Khoshbin (www.mkhoshbin.com)\n',
                    __version__, __website__)
        logger.info("A VoxelPart object named '%s' was created" +
                    " with %s elements and an initial element value of %u.",
                    name, '*'.join(str(s) for s in size), base_material)

    @property
    def instance_name(self):
        """Name of the part instance which is name of the part + '-Ins'. Used for output to Abaqus™ input file."""
        return self.name + '-Ins'

    @property
    def size(self):  # TODO: use everywhere in refactor
        """Shape of the part's *data* property.
        May have two or three elements depending on how the part was defined."""
        return self.data.shape

    @property
    def real_size(self):
        """Real size of the part which is ``part.size * voxel_size``."""
        # TODO: how does this behave in case of 2D and 3D?
        return np.array([self.size[i] * self.voxel_size[i] for i in range(len(self.size))])

    @property
    def data(self):
        """TODO"""
        return self._data

    @data.setter
    def data(self, value):
        # TODO: check for ndim.
        if not isinstance(value, ndarray):
            raise ValueError('data must be a numpy ndarray.')
        if not value.flags.c_contiguous:
            raise ValueError('data must be C-continuous.')
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
                          material_elem_sets: Union[str, tuple], custom_elem_sets: bool = True,
                          keep_temp_files: bool = False) -> Path:
        """Output the part to an Abaqus™ input file.

        Only the elements selected by the *material_elem_sets* parameter are selected,
        and afterwards they are grouped into sets by the material code.
        If *custom_elem_sets* is True, the custom element set are also included.
        If an element is part of a custom element set but is not part of the selected materials,
        It is not written to the output.

        This function simply calls :func:`.output.write_abaqus_inp`, except for the
        *scale* and *folder_path* parameters which are equal to :attr:`.VoxelPart.voxel_size`
        and :attr:`.VoxelPart.results_path`, respectively.

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

    def add_custom_elem_set(self, name: str, ids: Union[tuple, ndarray], replace: bool = True):
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

    def add_node_set(self, name: str, ids: Union[tuple, ndarray], replace: bool = True):
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
            raise RuntimeError("A node set with the name '%s' already exists." % name)
        self.node_sets[name] = np.unique(ids).astype('uint32')
        logger.debug("Added custom node set '%s' with %u elements.", name, len(self.node_sets[name]))

    def add_bc(self, bc_type: Union[str, None] = None,
               vertices_nodeset: bool = True, edges_nodeset: bool = True, faces_nodeset: bool = True,
               explicit_nodeset: bool = False, simple_nodeset: bool = False):
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

            vertices_nodeset: Add the individual vertices as node sets.
            edges_nodeset: Add the individual edges as node sets.
            faces_nodeset: Add the individual faces as node sets.
            explicit_nodeset: Add the explicit node sets requested by *vertices_nodeset*,
                              *edges_nodeset*, and *faces_nodeset*.
            simple_nodeset: Add the simple node sets which are the full faces
                            for the 3D models or the edges for the 2D models.
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

    def apply_mask(self, mask: ndarray, value: int):
        """Use a boolean mask to select some elements of the part's :attr:`data` array
        and change them to a *value*.

        Args:
            mask: The Boolean mask to be used.
            value: Integer value to be assigned to the elements of the :attr:`data` attribute
                   where the boolean mask is True.
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
            raise ValueError('mask is not of the same order (Fortran or C contiguity) as VoxelPart.data.')
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
            self._dummy_node_dict['RP0-NodeSet'] = 999999999  # TODO: change max nodes to reflect.
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
                                        dims=self.data.shape, mode='raise', order='C').astype('uint32')
        return name, elem_ids


def voxelpart_from_image(image_dim: str, image_path: str,
                         scale: float = 1.0, denoise: bool = True,
                         show_image: bool = False,
                         thresh_mode: str = 'otsu', thresh: float = None,
                         background_material: int = 0, foreground_material: int = 1,
                         voxel_size: Union[tuple[float, float, float], tuple[float, float]] = (1.0, 1.0, 1.0),
                         dtype: str = 'uint8', name: str = 'unnamed',
                         description: str = '', results_path: Union[str, Path] = None,
                         overwrite_logs: bool = True, log_debug: bool = False, **kwargs):
    """Create a :class:`VoxelPart` object from an image.

    Args:
        image_dim: Dimensionality of the input image. Valid values are '2D' and '3D':
                   - If '2D', *image_path* refers to the path of the input image.
                   - If '3D', *image_path* refers the the path string used by the (TODO) function.
        image_path: The path referring to a 2D image, or the path string (TODO) referring to a 3D image.
        show_image: See TODO for docs.
        scale: See TODO for docs.
        denoise: See TODO for docs.
        thresh_mode: See TODO for docs.
        thresh: See TODO for docs.
        background_material: After the image is binarized, this material will be assigned to the *OFF* pixels.
        foreground_material: After the image is binarized, this material will be assigned to the *ON* pixels.
        voxel_size: See TODO for docs.
        dtype: See TODO for docs.
        name: See TODO for docs.
        description: See TODO for docs.
        results_path: See TODO for docs.
        overwrite_logs: See TODO for docs.
        log_debug: See TODO for docs
        **kwargs: TODO: used for preventing errors associated with unexpectd input.

        Note: The size parameter used for creating a :class:`VoxelPart` is determined from the image (expand).
        Note: This function uses TODO and TODO.
        Read the appropriate documentation (expand).
    """

    # TODO: can we add a logger here? Examples take a long time and then just finish.
    # TODO:  it seems to be logged in the GUI, check why/how
    # TODO:  it also seems to have duplicates. why?
    if image_dim.upper() not in ['2D', '3D']:
        raise ValueError("image_dim can only be one of '2D' or '3D'.")
    if image_dim.upper() == '2D':
        image_mask = mask_from_image(image_path=image_path, scale=scale,
                                     denoise=denoise, show_image=show_image,
                                     thresh_mode=thresh_mode, thresh=thresh)
    else:  # dim.upper() == '3D'
        # TODO: add show_image here.
        image_mask = mask_from_image_sequence(load_pattern=image_path,
                                              scale=scale, denoise=denoise,
                                              thresh_mode=thresh_mode, thresh=thresh)

    # TODO: determine voxel size array (2 or 3 elements?). (Make sure a 1*3 array is always OK)
    # TODO: same for part shape.
    image_mask = rot90(image_mask, -1)
    image_shape = image_mask.shape
    part = VoxelPart(size=image_shape, base_material=background_material,
                     voxel_size=voxel_size, dtype=dtype,
                     name=name, description=description,
                     results_path=results_path,
                     overwrite_logs=overwrite_logs, log_debug=log_debug)
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

    part = VoxelPart(**part_creation_dict)
    logger.info('The model is being created from a configuration file loaded from %s' % file_path)

    modeling_mode = part_manipulation_dict['modeling_mode']
    if modeling_mode == '0':  # No action selected. This is technically invalid, but consider it to be '1'.
        pass
    if modeling_mode == '1':  # No Further Manipulation.
        pass
    elif modeling_mode == '2':  # TPMS
        boolean_mask = mask_from_function(mask_shape=part.data.shape,
                                          func=tpms_dict[part_manipulation_dict['tpms_type']],
                                          part=part,
                                          l=part_manipulation_dict['tpms_length'],
                                          c=part_manipulation_dict['tpms_constant'])
        part.apply_mask(mask=boolean_mask, value=part_manipulation_dict['tpms_fill_value'])
    elif modeling_mode == '3':  # Image Processing (Single 2D Image)
        part = voxelpart_from_image(image_dim='2D',
                                    image_path=part_manipulation_dict['single_image_path'],
                                    scale=part_manipulation_dict['single_image_scale'],
                                    denoise=part_manipulation_dict['single_image_denoise'],
                                    background_material=1, foreground_material=2,  # Note: This is built-in.
                                    **part_creation_dict)
    elif modeling_mode == '4':  # Stack of 2D images for a 3D part.
        part = voxelpart_from_image(image_dim='3D',
                                    image_path=part_manipulation_dict['multi_image_path'],
                                    scale=part_manipulation_dict['multi_image_scale'],
                                    denoise=part_manipulation_dict['multi_image_denoise'],
                                    background_material=0, foreground_material=1,  # Note: This is built-in.
                                    **part_creation_dict)
    elif modeling_mode == '5':  # Planar Composite (Circular Inclusions)
        for row in part_manipulation_dict['circle_list']:
            circle_obj = Circle(id=0, a=float(row[0]), b=float(row[1]), r=float(row[2]))
            part.apply_mask(mask=circle_obj.calculate_mask(part_shape=part.data.shape, voxel_size=part.voxel_size),
                            value=int(row[3]))
    elif modeling_mode == '6':  # Spatial Composite (Spherical Inclusions)
        for row in part_manipulation_dict['sphere_list']:
            circle_obj = Sphere(id=0, a=float(row[0]), b=float(row[1]), c=float(row[2]), r=float(row[3]))
            part.apply_mask(mask=circle_obj.calculate_mask(part_shape=part.data.shape, voxel_size=part.voxel_size),
                            value=int(row[4]))
    else:
        raise ValueError("Invalid value '%s' for part_manipulation_dict['modeling_mode']." % modeling_mode)

    bc_type = bc_dict['bc_type']
    if bc_type == '0':  # No BC.
        pass
    elif bc_type == '1':  # Sets only.
        part.add_bc(bc_type='NODESET ONLY', vertices_nodeset=True, edges_nodeset=True, faces_nodeset=True,
                    explicit_nodeset=True, simple_nodeset=True)
    elif bc_type == '2':  # Linear Displacement Boundary Conditions.
        part.add_bc(bc_type='Linear Displacement')
    elif bc_type == '3':  # Periodic Boundary Condition.
        part.add_bc(bc_type='Periodic')
    else:
        raise ValueError("Invalid value '%s' for bc_dict['bc_type']" % bc_type)

    part.output_abaqus_inp(**output_dict)

    logger.info('Creation of the model from the configuration file completed successfully.')
    return part

# TODO: 2D part with 3d size and voxel size.
# TODO: Fix example 3
# TODO: unconnected regions: https://stackoverflow.com/questions/46737409
# TODO: add only some of the bc node sets.
# TODO: nodeset -> nset
# TODO: face, edge, vertex -> f, e, v
# TODO: add ddbc based on walters2021, eq 24. x is node coordinates.
# TODO: 2d pbc edges does not have shear components.
# TODO: add disp values for all bcs.
# TODO: add min and max values for voxel_size.
# TODO: redo ndarray types. see https://stackoverflow.com/questions/35673895
# TODO: change size to shape.
# TODO: add shape as a variable with a getter.
# TODO: add a random inclusion mode. use np.arange + np.shuffle and np.reshape to proper size.
# TODO: in docs change output to export.
# TODO: change results_path to working_directory
#  add Open Results Folder to the run menu of the GUI.
# TODO: typo in doc and readme.md: it's -> its
# TODO: check various errors when 2D/3D doesn't match across part size, voxel size, etc.
# TODO: Add docs for random including examples.
# TODO: update to Python 3.10.
# TODO: In Python 3.10, use | instead of Union for type hints.
#       See https://medium.com/techtofreedom/8-levels-of-using-type-hints-in-python-a6717e28f8fd
# TODO: type annotation can be used for specific values.
#  See https://stackoverflow.com/q/58114837 and https://stackoverflow.com/q/39398138
