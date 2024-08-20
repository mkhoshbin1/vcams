"""Functions used for exporting a :class:`~vcams.voxelpart.VoxelPart` instance
for use in other programs. Currently, only Abaqus™ is supported.

These functions are not meant to be directly used.
The main function (:func:`~write_abaqus_inp`) is called
by a part's :meth:`~.voxelpart.VoxelPart.output_abaqus_inp` method,
and it uses the *VoxelPart*'s attributes for determining what is exported.

Refer to the :ref:`export` section for instructions on how to properly output a model.
"""

import logging
import os
import shutil
import time
from pathlib import Path
from typing import Union, TextIO

import numpy as np
from numpy import savetxt, unravel_index, ravel_multi_index, array, unique, uint32, float64, \
    union1d, any, zeros, append, intersect1d, insert, vstack, ndarray
# noinspection PyPackageRequirements
from tabulate import tabulate  # The main module in the tabulate2 package is named tabulate.

from . import __version__, __website__
from . import helper
from .bc import create_bc
from .helper import validate_materials_to_be_output, validate_dim

logger = logging.getLogger(__name__)


def write_abaqus_inp(part, file_name: str, elem_code: str, dim: str,
                     scale: tuple, material_elem_sets: tuple | str,
                     custom_elem_sets: bool = True, keep_temp_files: bool = False) -> Path:
    """Write a VoxelPart instance to an Abaqus™ input file.
    This is the main function called by :meth:`.voxelpart.VoxelPart.output_abaqus_inp`.
    It should not be directly used.

    Only the elements selected by the *material_elem_sets* parameter are selected,
    and afterwards they are grouped into sets by the material code.
    If *custom_elem_sets* is True, the custom element set are also included.
    If an element is part of a custom element set but is not part of the selected materials,
    It is not written to the output.

    Args:
        part (VoxelPart): The :class:`~.voxelpart.VoxelPart` instance on which the operation is performed.
        file_name: Name of the file. Must be valid according to the documentation
                   for the :func:`.helper.is_name_valid` function and should not contain file extensions.
        elem_code: An uppercase string denoting the element code assigned to *all* elements in the model.
                   It must be a valid Abaqus element code such as *'CPE4R'* or *'C3D8R'*.
                   This parameter is not validated so care should be taken regarding validity and compatibility.
                   Currently, only 2D and 3D linear elements are supported.
                   To get around this, you can convert to quadratic elements after importing the model to Abaqus.
        dim: Dimensionality of the output part. Valid values are *'2D'* and *'3D'*.
        scale: A tuple containing two or three floats which are used to scale
               the pixels or voxels in the x, y, and z directions.
               For example, if the tuple ``(0.02, 0.1, 1.5)`` is specified,
               each voxel will have those dimensions in the x, y, and z directions.
        material_elem_sets: One of the following:

                            + *'All'* which outputs all materials in the VoxelPart.
                            + *'Non-Empty'* which outputs all non-zero (=non-empty) materials in the VoxelPart.
                            + A tuple of integer material codes corresponding
                              to the materials that should be written to the output.

        custom_elem_sets: If set to True, custom sets will be written to the output.
        keep_temp_files: If set to True, temporary files will not be deleted. Used for debugging.

        Returns:
            Path object pointing to final Abaqus™ input file.
        """
    logger.info("Attempting to output part '%s' to an Abaqus input file.", part.name)
    begin_time = time.perf_counter()
    folder_path = part.working_dir

    # Validate dim.
    validate_dim(dim)
    if dim == '2D' and len(part.size) == 3:
        raise ValueError('Attempted to export a 3D part as a 2D part. '
                         'This is not supported due to unnecessary complexity. '
                         'Instead, create a new 2D VoxelPart instance '
                         'with the desired slice of VoxelPart.data and export it.')

    # Validate file_name and add file extension.
    if not helper.is_name_valid(file_name):
        raise ValueError('Invalid file_name. Check the documentation for validity criteria.')
    file_name = file_name + '.inp'

    # Validate and process material_elem_sets.
    material_elem_sets = validate_materials_to_be_output(part, material_list=material_elem_sets)

    # Process BCs.
    # max_empty_border_elems has not been specified.
    constraint_list = create_bc(part, dim, mat_codes_to_accept=material_elem_sets)

    # Add the dummy nodes as node sets.
    # noinspection PyProtectedMember
    for name, node_id in part._dummy_node_dict.items():
        part.add_node_set(name=name, ids=node_id - 1)  # ids is zero-based.

    # Write element sets.
    (elem_set_file_path, elem_id_list, elem_set_stats) = \
        write_elem_set_def(part, material_elem_sets, folder_path, custom_elem_sets)

    # Write temporary element definition file.
    (elem_file_path, num_elems, node_id_list) = write_elem_def(part=part,
                                                               elem_id_list=elem_id_list,
                                                               elem_code=elem_code, dim=dim,
                                                               folder_path=folder_path)

    # Write temporary node definition file.
    (node_file_path, num_nodes, node_id_list) = write_node_def(part=part,
                                                               node_id_list=node_id_list,
                                                               scale=scale, dim=dim,
                                                               folder_path=folder_path)

    # Write node sets.
    (node_set_file_path, node_set_stats) = write_node_set_def(part, node_id_list, folder_path)

    # Write constraints.
    if constraint_list:
        num_constraints, constraints_file_path = write_constraints(folder_path, constraint_list)
    else:
        num_constraints = 0

    # Write the final Abaqus input file.
    main_file_path = os.path.join(folder_path, file_name)
    logger.debug("Assembling temporary files to the main input file at '%s'.", main_file_path)
    with open(main_file_path, 'w', encoding='latin1') as main_file:
        # Write program details as a comment on top.
        main_file.write(('** Input file generated by VCAMS v%s' % __version__ +
                         time.strftime(' on %Y-%m-%d at %H:%M:%S %Z.\n', time.localtime()) +
                         '** VCAMS is a free and open source program available at:\n' +
                         ('** %s\n' % __website__) +
                         '** Author: Mohammadreza Khoshbin (www.mkhoshbin.com)\n\n'))

        # Write part description as heading text.
        main_file.write('*HEADING\n%s\n\n' % part.description)

        # Declare the parts portion of the input file as a comment.
        main_file.write('**\n** Parts\n**\n\n')

        # Declare this part.
        main_file.write('*PART, NAME="%s"\n\n' % part.name)

        # Write nodes.
        with open(node_file_path, 'r') as node_file:
            shutil.copyfileobj(node_file, main_file)

        # Write elements.
        with open(elem_file_path, 'r') as elem_file:
            shutil.copyfileobj(elem_file, main_file)

        # Write element sets.
        with open(elem_set_file_path, 'r') as elem_set_file:
            shutil.copyfileobj(elem_set_file, main_file)

        # Declare the end of this part.
        main_file.write('*END PART\n**\n\n')

        # Write an instance of the part to the assembly.
        # Declare the assembly.
        main_file.write('**\n** Assembly\n**\n\n')
        main_file.write('*ASSEMBLY, NAME=Assembly\n\n')

        # Declare the instance.
        main_file.write('*INSTANCE, NAME="%s", PART="%s"\n' % (part.instance_name, part.name))
        main_file.write('*END INSTANCE\n**\n\n')

        # Write node sets.
        with open(node_set_file_path, 'r') as node_set_file:
            shutil.copyfileobj(node_set_file, main_file)

        # Write constraints.
        if constraint_list:
            # noinspection PyUnboundLocalVariable
            with open(constraints_file_path, 'r') as constraints_file:
                shutil.copyfileobj(constraints_file, main_file)

        # Declare the end of the assembly portion of the input file.
        main_file.write('*END ASSEMBLY\n**\n\n')

    # Delete temporary file.
    if not keep_temp_files:
        logger.debug('Deleting temporary files.')
        os.remove(node_file_path)
        os.remove(elem_file_path)
        os.remove(node_set_file_path)
        os.remove(elem_set_file_path)
        if constraint_list:
            os.remove(constraints_file_path)

    elapsed_time = time.perf_counter() - begin_time
    logger.info("Finished exporting part '%s' to the Abaqus™ input file at '%s'.",
                part.name, main_file_path)

    write_output_summary(part, dim, elem_code, num_nodes, num_elems,
                         elem_set_stats, node_set_stats, num_constraints, elapsed_time)
    return Path(main_file_path)


def write_elem_def(part, elem_id_list: ndarray, elem_code: str, dim: str,
                   folder_path: str) -> tuple[str, int, ndarray]:
    """Write the element definition portion of an Abaqus™ input file to a temporary file,
    which will be concatenated with other portions to form an input file.

    Element definition consists of specifying the element code and writing its connectivity table.
    In the finite element method, the connectivity table (or matrix) determines which nodes belong to each element.
    The first column is always element id and its nodes are written
    in rest of the columns in a specific order based on the element geometry.

    Args:
        part (VoxelPart): The VoxelPart instance on which the operation is performed.
        elem_id_list: A 1-D Numpy ndarray containing IDs of elements which must be output.
                      The function makes sure that it is unique and sorted.
                      Note that Abaqus only accepts element IDs that are positive and less than 999999999.
                      Element IDs must also be integers. This is not directly checked,
                      but an error will be raised once they are passed as indices to numpy.
        elem_code: An uppercase string denoting the element code assigned to *all* elements in the model.
                   It must be a valid Abaqus element code such as 'CPE4R' or 'C3D8R'.
                   This parameter is not validated so care should be taken regarding validity and compatibility.
                   Currently, only 2D and 3D linear elements are supported.
                   To get around this, you can convert to quadratic elements after importing the model to Abaqus.
        dim: Dimensionality of the output part. Valid values are *'2D'* and *'3D'*.
        folder_path: Path to the folder where the temporary element definition file will be placed.

    Returns:
        The tuple *(file_path, num_elems, node_id_list)* containing

          #. The path to the temporary element definition file;
          #. The number of elements which have been written to the file; and
          #. A numpy ndarray containing a sorted list of node IDs that are present in the model.
    """
    logger.debug("Attempting to write element definitions to the temporary file 'elem_def.tmp'.")
    # Validate elem_id_list. Note that values are not checked.
    if len(elem_id_list) == 0:
        raise ValueError('elem_id_list is empty. At least one element must be selected for output.')
    if any(elem_id_list < 0):
        raise ValueError('At least on element in elem_id_list is negative' +
                         ' which will result in a non-positive ID in the input file.')
    if max(elem_id_list) >= 999999999:
        raise RuntimeError(('At least one element has an ID greater than 999999999,' +
                            ' which is not supported by Abaqus™.'))

    # Validate dim.
    validate_dim(dim)

    # Make sure elem_id_list is unique and sorted.
    elem_id_list = unique(elem_id_list)

    # Preallocate memory for the connectivity table.
    if dim.upper() == '2D':
        elem_array_shape = part.size[0:2]
        num_cols = 5
    elif dim.upper() == '3D':
        elem_array_shape = part.size
        num_cols = 9
    else:
        raise RuntimeError('Unexpected value for dim. This should have been caught earlier.')
    connectivity_table = zeros((elem_id_list.size, num_cols), dtype=uint32, order='C')

    # In each direction, node array is larger by one.
    node_array_shape = tuple(i + 1 for i in elem_array_shape)

    # Find the coordinates for the elements in elem_id_list.
    elem_inds = unravel_index(elem_id_list, elem_array_shape, order='C')

    # Add elem_id_list as the first column.
    connectivity_table[:, 0] = elem_id_list + 1

    # For each element in elem_id_list, find its nodes.
    if dim.upper() == '2D':
        connectivity_table[:, 1] = ravel_multi_index(multi_index=(elem_inds[0], elem_inds[1]),
                                                     dims=node_array_shape, mode='raise',
                                                     order='C') + 1
        connectivity_table[:, 2] = ravel_multi_index(multi_index=(elem_inds[0] + 1, elem_inds[1]),
                                                     dims=node_array_shape, mode='raise',
                                                     order='C') + 1
        connectivity_table[:, 3] = ravel_multi_index(
            multi_index=(elem_inds[0] + 1, elem_inds[1] + 1),
            dims=node_array_shape, mode='raise', order='C') + 1
        connectivity_table[:, 4] = ravel_multi_index(multi_index=(elem_inds[0], elem_inds[1] + 1),
                                                     dims=node_array_shape, mode='raise',
                                                     order='C') + 1
    elif dim.upper() == '3D':
        connectivity_table[:, 1] = ravel_multi_index(
            multi_index=(elem_inds[0], elem_inds[1], elem_inds[2]),
            dims=node_array_shape, mode='raise', order='C') + 1
        connectivity_table[:, 2] = ravel_multi_index(
            multi_index=(elem_inds[0] + 1, elem_inds[1], elem_inds[2]),
            dims=node_array_shape, mode='raise', order='C') + 1
        connectivity_table[:, 3] = ravel_multi_index(
            multi_index=(elem_inds[0] + 1, elem_inds[1] + 1, elem_inds[2]),
            dims=node_array_shape, mode='raise', order='C') + 1
        connectivity_table[:, 4] = ravel_multi_index(
            multi_index=(elem_inds[0], elem_inds[1] + 1, elem_inds[2]),
            dims=node_array_shape, mode='raise', order='C') + 1
        connectivity_table[:, 5] = ravel_multi_index(
            multi_index=(elem_inds[0], elem_inds[1], elem_inds[2] + 1),
            dims=node_array_shape, mode='raise', order='C') + 1
        connectivity_table[:, 6] = ravel_multi_index(
            multi_index=(elem_inds[0] + 1, elem_inds[1], elem_inds[2] + 1),
            dims=node_array_shape, mode='raise', order='C') + 1
        connectivity_table[:, 7] = ravel_multi_index(
            multi_index=(elem_inds[0] + 1, elem_inds[1] + 1, elem_inds[2] + 1),
            dims=node_array_shape, mode='raise', order='C') + 1
        connectivity_table[:, 8] = ravel_multi_index(
            multi_index=(elem_inds[0], elem_inds[1] + 1, elem_inds[2] + 1),
            dims=node_array_shape, mode='raise', order='C') + 1
    else:
        raise RuntimeError('Unexpected value for dim. This should have been caught earlier.')

    # Write the element connectivity table to a temporary text file.
    file_path = os.path.join(folder_path, 'elem_def.tmp')
    # noinspection PyTypeChecker
    savetxt(fname=file_path, X=connectivity_table,
            fmt='%u', delimiter=',', comments='', encoding='latin1',
            header=('*ELEMENT, TYPE=%s' % elem_code.upper()), footer='\n')

    # Create a sorted array of unique node IDs in the connectivity matrix
    # and revert node IDs to zero-based indexing.
    node_id_list = unique(connectivity_table[:, 1:]) - 1
    num_elems = len(elem_id_list)

    logger.debug(f"Wrote {num_elems} {dim.upper()} elements "
                 f"of type '{elem_code.upper()}' to the temporary file 'elem_def.tmp'.")
    return file_path, num_elems, node_id_list


def write_node_def(part, node_id_list: ndarray, scale: tuple, dim: str, folder_path: str) -> tuple[str, int, ndarray]:
    """Write the node definition portion of an Abaqus™ input file to a temporary file,
    which will be concatenated with other portions to form an input file.

    Node definition consists of specifying the node ID and writing its coordinates in the x, y, and z directions.
    The code uses a global cartesian coordinate system which is compatible with its data structure and sufficient
    for our purposes.

    Args:
        part (VoxelPart): The :class:`~.voxelpart.VoxelPart` instance on which the operation is performed.
        node_id_list: A 1-D Numpy ndarray containing IDs of nodes which must be output.
                      The function makes sure that it is unique and sorted.
                      Note that Abaqus only accepts node IDs that are positive and less than 999999999
                      and this is reduced to 999999990 to account for possible dummy nodes.
                      Node IDs must also be integers. This is not directly checked,
                      but an error will be raised once they are passed as indices to numpy.
        scale: A tuple containing two or three floats which are used to scale
               the pixels or voxels in the x, y, and z directions.
               For example, if the tuple ``(0.02, 0.1, 1.5)`` is specified,
               each voxel will have those dimensions in the x, y, and z directions.
        dim: Dimensionality of the output part. Valid values are *'2D'* and *'3D'*.
        folder_path: Path to the folder where the temporary node definition file will be placed.

    Returns:
        The tuple *(file_path, num_nodes, node_id_list)* containing

          #. The path to the temporary node definition file;
          #. The number of nodes which have been written to the file; and
          #. A numpy ndarray containing the IDs of the nodes written to file
             which has been updated by adding the dummy nodes
    """
    logger.debug("Attempting to write node definitions to the temporary file 'node_def.tmp'.")
    # Validate node_id_list.
    if len(node_id_list) == 0:
        raise ValueError('node_id_list is empty. At least one node must be selected for output.')
    if any(node_id_list < 0):
        raise ValueError('At least on element in node_id_list is negative' +
                         ' which will result in a non-positive ID in the input file.')
    if max(node_id_list) >= 999999990:
        raise RuntimeError(('At least one node has an ID greater than 999999990,' +
                            ' which is not supported by Abaqus™.'))
    num_real_nodes = node_id_list.size

    # Validate dim.
    validate_dim(dim)

    # Get dummy_node_dict from the part.
    # noinspection PyProtectedMember
    dummy_node_dict = part._dummy_node_dict

    # Set format string and number of columns in node_coordinates based on dim.
    if dim.upper() == '2D':
        num_cols = 3
        fmt = [('%' + str(len(str(max(node_id_list)))) + 'u'), '%13.12G', '%13.12G']
    elif dim.upper() == '3D':
        num_cols = 4
        fmt = [('%' + str(len(str(max(node_id_list)))) + 'u'), '%13.12G', '%13.12G', '%13.12G']
    else:
        raise RuntimeError('Unexpected value for dim. This should have been caught earlier.')

    # Preallocate memory for node_coordinates.
    # The dummy nodes are added at the end, so allocate accordingly.
    node_table = zeros((num_real_nodes + len(dummy_node_dict), num_cols), dtype=float64, order='C')

    # Add node_id_list as the first column of node_table.
    node_table[:num_real_nodes, 0] = node_id_list + 1

    # Obtain Cartesian coordinates of each node by unraveling its index and multiplying it by scale.
    node_array_shape = tuple(i + 1 for i in part.size)
    raw_indices = unravel_index(node_id_list, node_array_shape, order='C')

    # Add node coordinates to node_table.
    node_table[:num_real_nodes, 1] = raw_indices[0] * scale[0]
    node_table[:num_real_nodes, 2] = raw_indices[1] * scale[1]
    if dim.upper() == '3D':
        node_table[:num_real_nodes, 3] = raw_indices[2] * scale[2]

    if dummy_node_dict:
        # Add the dummy node to the end of the table.
        dummy_nodes_list = []
        max_size = node_table.max(axis=0, initial=-1)
        offset = 0.05
        for name, node_id in dummy_node_dict.items():
            if name == 'RP0-NodeSet':
                dummy_nodes_list.append((insert((max_size * -0.05)[1:], 0, node_id, axis=None)))
            else:
                dummy_nodes_list.append((insert((max_size * (1 + offset))[1:], 0, node_id, axis=None)))
                offset += 0.05
        dummy_nodes_list_array = vstack(dummy_nodes_list)
        node_table[-1 * len(dummy_node_dict):, :] = dummy_nodes_list_array[dummy_nodes_list_array[:, 0].argsort()]
        node_id_list = append(node_id_list, [i - 1 for i in dummy_node_dict.values()])

    # Write node_table to a temporary text file.
    file_path = os.path.join(folder_path, 'node_def.tmp')
    # noinspection PyTypeChecker
    savetxt(fname=file_path, X=node_table,
            fmt=fmt, delimiter=',', comments='', encoding='latin1',
            header='*NODE', footer='\n')

    logger.debug("Wrote %u %s nodes to the temporary file 'node_def.tmp'.",
                 num_real_nodes, dim.upper())
    return file_path, num_real_nodes, node_id_list


def write_set_ids(file_obj: TextIO, kind: str, name: str, ids: ndarray,
                  instance_name: Union[str, None] = None) -> tuple[str, int]:
    """Write an element or node set to a file according to Abaqus™ input file syntax.

    Args:
        file_obj: The file object in which the set is written. It must be opened in text mode.
        kind: The kind of set that is to be output.
              Valid values are *'ELSET'* for an element set and *'NSET'* for a node set.
        name: Name of the set. Must be valid according to
              the documentation for the :func:`.helper.is_name_valid` function.
        ids: A 1-D Numpy ndarray containing zero-based IDs of nodes or elements which form the set.
             The function makes sure that it is unique and sorted.
             Note that Abaqus only accepts IDs that are positive and less than 999999999.
             IDs must also be integers, but this is not validated in this function.
        instance_name: If set to a string, the set is defined with an *'INS'* parameter
                       to signify it belonging to an instance.
                       If set to *None*, the set is defined without it which signifies it belonging to a part.

    Returns:
        A tuple containing set name and number of IDs in the set.
    """
    if kind.upper() not in ['ELSET', 'NSET']:
        raise ValueError("kind can only be one of 'ELSET' or 'NSET'.")

    if not helper.is_name_valid(name):
        raise ValueError('Invalid name. Check the documentation for validity criteria.')

    # Validate ids. Note that values are not checked.
    if len(ids) == 0:
        raise ValueError('ids is empty. At least one ID must be selected for output.')
    if any(ids < 0):
        raise ValueError('At least on element in ids is negative '
                         'which will result in a non-positive ID in the input file.')
    if max(ids) >= 999999999:
        raise RuntimeError('At least one ID is greater than 999999999, '
                           'which is not supported by Abaqus™.')
    # Make sure ids is unique and sorted.
    ids = unique(ids)

    # IDs start at zero (zero-based indexing).
    # Add the number 1 to all of them to account for that.
    ids = ids + 1

    # Write the set header manually.
    if instance_name:
        file_obj.write('*%s,%s="%s",INS="%s"\n' % (kind.upper(), kind.upper(), name, instance_name))
    else:
        file_obj.write('*%s,%s="%s"\n' % (kind.upper(), kind.upper(), name))

    # If there are 9 or fewer IDs, they are written manually.
    # Otherwise, they are written as chunks of 9 IDs, ensuring low line length.
    # numpy.savetxt can only write a 2D array, meaning that the extra IDs
    # need to be written separately.
    # For simplicity, the last 9 elements are always written separately.
    if len(ids) <= 9:
        extra_chunk = ids
    else:
        num_extra = ids.size % 9
        if num_extra == 0:
            num_extra = 9
        main_chunk = ids[:-num_extra].reshape((-1, 9))
        extra_chunk = ids[-num_extra:]
        # Write the main chunk using numpy.
        savetxt(fname=file_obj, X=main_chunk,
                fmt='%u', delimiter=',', newline=',\n', comments='', encoding='latin1',
                header='', footer='')

    # Write the extra chunk manually.
    file_obj.write(','.join(['%u'] * len(extra_chunk)) % tuple(extra_chunk))
    file_obj.write('\n\n')

    return name, len(ids)


def write_elem_set_def(part, material_elem_sets: tuple, folder_path: str,
                       custom_elem_sets: bool = True) -> tuple[str, ndarray, dict]:
    """Write the element set portion of an Abaqus™ input file to a temporary file.
    This function also returns which elements must be output.

    Args:
        part (VoxelPart): The :class:`~.voxelpart.VoxelPart` instance on which the operation is performed.
        material_elem_sets: A tuple containing integer values of the materials that should be output.
                            For each material *x*, a set named *'MAT-x'* is defined.
        custom_elem_sets: If set to True, the custom sets are defined and output.
        folder_path: Path to the folder where the temporary elemset definition file will be placed.

    Returns:
        The tuple *(elem_set_file_path, elem_id_list, elem_set_stats)* containing

          #. The path to the temporary element set definition file;
          #. A ndarray containing a unique and sorted list of all element IDs in the sets
          #. A dictionary where the keys are names of the element sets
             and the values are the number of elements in that set.
    """
    logger.debug("Attempting to write element sets to the temporary file 'elemset.tmp'.")
    elem_set_stats = dict()
    elem_id_list = array([], order='C', dtype='uint32')
    elem_set_file_path = os.path.join(folder_path, 'elemset.tmp')

    with open(elem_set_file_path, 'w', encoding='latin1') as file_obj:
        # Write custom element sets. The element IDs are unique and sorted.
        if custom_elem_sets and bool(part.elem_sets):
            for (name, elem_ids) in part.elem_sets.items():
                if elem_ids.size > 0:
                    (set_name, num_ids) = write_set_ids(file_obj=file_obj, kind='ELSET',
                                                        name=name, ids=elem_ids)
                    elem_id_list = union1d(elem_id_list, elem_ids)
                    elem_set_stats[set_name] = num_ids
        # Write the materials that should be output.
        for mat_code in material_elem_sets:
            # noinspection PyProtectedMember
            (name, elem_ids) = part._return_material_elem_set(mat_code)
            if elem_ids.size > 0:
                (set_name, num_ids) = write_set_ids(file_obj=file_obj, kind='ELSET',
                                                    name=name, ids=elem_ids)
                elem_id_list = union1d(elem_id_list, elem_ids)
                elem_set_stats[set_name] = num_ids

    logger.debug("Wrote %u element sets to the temporary file 'elemset.tmp'.", len(elem_set_stats))
    return elem_set_file_path, elem_id_list, elem_set_stats


def write_node_set_def(part, node_id_list: ndarray, folder_path: str) -> tuple[str, dict]:
    """Write the node set portion of an Abaqus™ input file to a temporary file.

    Args:
        part (VoxelPart): The :class:`~.voxelpart.VoxelPart` instance on which the operation is performed.
        node_id_list: A 1-D Numpy ndarray containing IDs of the nodes that have been written to the output.
                      It is used to determine which nodes from the node sets should be defined in the output.
        folder_path: Path to the folder where the temporary nodeset definition file will be placed.

    Returns:
        The path to the temporary node set definition file.
    """
    logger.debug("Attempting to write node sets to the temporary file 'nodeset.tmp'.")
    node_set_stats = dict()
    node_set_file_path = os.path.join(folder_path, 'nodeset.tmp')
    with open(node_set_file_path, 'w', encoding='latin1') as file_obj:
        # Write node sets.
        num_omitted = 0
        for (name, node_ids) in part.node_sets.items():
            node_set_ids = intersect1d(node_id_list, node_ids)
            if len(node_set_ids) == 0:
                num_omitted += 1
                logger.warning("Node set '%s' was not written to output because none of "
                               "its nodes and elements are set for output.", name)
            else:
                # noinspection PyTypeChecker
                write_set_ids(file_obj=file_obj, kind='NSET', name=name,
                              ids=node_set_ids, instance_name=part.instance_name)
                node_set_stats[name] = len(node_set_ids)

    logger.debug("Wrote %u node sets to the temporary file 'nodeset.tmp'.",
                 len(part.node_sets) - num_omitted)
    return node_set_file_path, node_set_stats


def write_constraints(folder_path: str, constraint_list: list) -> tuple[int, str]:
    """Write the defined constraints portion of an Abaqus™ input file to a temporary file.

    Args:
        constraint_list: Tuple of constraint objects defined in :doc:`bc-module`.
                         Their `repr()` function is written to the file.
        folder_path: Path to the folder where the temporary constraint definition file will be placed.

    Returns:
        A tuple containing the number of constraints and the path to the temporary constraint definition file.
    """
    # Note: Creation of a 2D PBC with 16M elements was tested.
    # Since the number of constrain equations are actually small (16000),
    # This function takes almost no time and so no further optimization is necessary.
    logger.debug("Attempting to write constraints to the temporary file 'constraints_def.tmp'.")
    constraints_file_path = os.path.join(folder_path, 'constraints_def.tmp')
    with open(constraints_file_path, 'w', encoding='latin1') as file_obj:
        file_obj.write('**\n** Constraints\n')
        for constraint_obj in constraint_list:
            file_obj.write(repr(constraint_obj))
        file_obj.write('** End Constraints\n\n')
    num_constraints = repr(constraint_list[0]).count('*Equation') * len(constraint_list)
    logger.debug("Wrote %u constraints to the temporary file 'constraints_def.tmp'.", num_constraints)
    return num_constraints, constraints_file_path


def write_output_summary(part, dim: str, elem_code: str, num_nodes: int, num_elems: int,
                         elem_set_stats: dict, node_set_stats: dict, num_constraints: int,
                         elapsed_time: float):
    """Write a summary of the output to the main log.

    Args:
        part (VoxelPart): The :class:`~.voxelpart.VoxelPart` instance on which the operation is performed.
        dim: Dimensionality of the output part. Valid values are *'2D'* and *'3D'*.
        elem_code: An uppercase string denoting the element code assigned to *all* elements in the model.
                   See :func:`write_abaqus_inp` for complete description.
        num_nodes: Number of nodes written to the output.
        num_elems: Number of elements written to the output.
        elem_set_stats: The dict object returned by :func:`write_elem_set_def`.
        node_set_stats: The dict object returned by :func:`write_node_set_def`.
        num_constraints: Number of constraint equations written to the output.
        elapsed_time: Elapsed time for the output process in seconds.
    """

    # noinspection PyProtectedMember
    part_bc_type = part._bc_type
    if part_bc_type is None:
        bc_name = 'None'
    elif part_bc_type.upper() == 'NODESET ONLY':
        bc_name = 'Nodeset Only'
    elif part_bc_type.upper() == 'LINEAR DISPLACEMENT':
        bc_name = 'Linear Displacement'
    elif part_bc_type.upper() == 'PERIODIC':
        bc_name = 'Periodic Boundary Conditions'
    else:
        raise RuntimeError(f'part has an invalid bc_type {part_bc_type}. '
                           f'This should have been caught earlier.')

    # Prepare part summary.
    part_summary = (
        ('Part Name', part.name),
        ('Number of Voxels', ' * '.join(str(i) for i in part.size)),
        ('Voxel Size', ' * '.join(str(i) for i in part.voxel_size)),
        ('Part Dimensions', ' * '.join(str(i) for i in part.real_size)),
        ('Output Dimensionality', dim.upper()),
        ('Element Type', elem_code),
        ('Number of Elements', num_elems),
        ('Number of Nodes', num_nodes),
        ('Number of Element Sets', len(elem_set_stats)),
        ('Number of Node Sets', len(node_set_stats)),
        ('Number of Material Codes', len(np.unique(part.data))),
        ('Requested BC Constraints', bc_name),
        ('Number of Constraint Equations', num_constraints),
        ('Total Output Time', time.strftime('%H:%M:%S', time.gmtime(elapsed_time)))
    )

    # Prepare set stats.
    mat_elem_sets = []
    custom_elem_sets = []
    elem_set_stats_list = sorted(elem_set_stats.items(), key=lambda x: x[1], reverse=True)
    node_set_stats_list = sorted(node_set_stats.items(), key=lambda x: x[1], reverse=True)
    for item in elem_set_stats_list:
        if item[0].upper().startswith('MAT-'):
            mat_elem_sets.append((item[0], item[1],
                                  '{:.2f}'.format((item[1] / num_elems) * 100),
                                  '{:.2f}'.format((item[1] / part.data.size) * 100)))
        else:
            custom_elem_sets.append(
                (item[0], item[1], '{:.2f}'.format((item[1] / num_elems) * 100)))
    summary_text = (
            '*Model Details*\n' +
            (tabulate(part_summary, tablefmt='pretty', colalign=('left', 'left')) + '\n') +
            '\n*Material Element Sets*\n' +
            (tabulate(mat_elem_sets, headers=('Set Name', 'Number of Elements',
                                              'Percent of All Elements', 'Percent of Model'),
                      tablefmt='pretty', colalign=('left', 'left', 'left')) + '\n')
    )
    if len(custom_elem_sets) == 0:
        summary_text += '\n*Custom Element Sets*\nNo custom element sets were defined.\n'
    else:
        summary_text += ('\n*Custom Element Sets*\n' +
                         tabulate(custom_elem_sets,
                                  headers=('Set Name', 'Number of Elements',
                                           'Percent of All Elements'),
                                  tablefmt='pretty') + '\n'
                         )
    if len(node_set_stats_list) == 0:
        summary_text += '\n*Node Sets*\nNo node sets were defined.\n'
    else:
        summary_text += ('\n*Node Sets*\n' +
                         tabulate(node_set_stats_list,
                                  headers=('Set Name', 'Number of Nodes'),
                                  tablefmt='pretty') + '\n'
                         )
    logger.info('A summary of the created part is as follows:\n***\n%s***\n' % summary_text)
