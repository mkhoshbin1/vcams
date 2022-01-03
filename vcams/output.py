"""Functions used for outputting models for use in other programs.
Currently, only Abaqus (TM) is supported."""
import logging
import os
import shutil
import time

from numpy import savetxt, unravel_index, ravel_multi_index, array, unique, uint32, float64, \
    union1d, any, zeros, append, intersect1d, insert, vstack
from tabulate import tabulate

from . import __version__, __website__
from . import helper
from .bc import create_bc

logger = logging.getLogger(__name__)


def write_abaqus_inp(part, file_name, folder_path, elem_code, dim,
                     scale, material_elem_sets,
                     custom_elem_sets=True, write_assembly=True, keep_temp_files=False):
    """Write a VoxelPart object to an Abaqus (TM) input file.

    Args:
        part (VoxelPart): The VoxelPart object which is to be output.

        file_name (str): Name of the file. Must be valid according to the documentation
                         for :py:meth:`helper.is_name_valid`.
                         Also, it should not contain any file extensions.

        folder_path (str): Path to the folder where the temporary element definition file
                           will be placed.

        elem_code (str): An uppercase string denoting the element code assigned to *all* elements.
                         It must be a valid Abaqus element code such as 'CPE4R' or 'C3D8R'.
                         No validation is performed by the function.

        dim (str): Dimensionality of the output part. Valid values are '2D' and '3D'.
                   If a 3D part is set to be output as a 2D plate,
                   only the first row will be printed.

        scale (tuple): A tuple containing two or three floats which are used to scale
                       the pixels or voxels in the x, y, and z direction.
                       For example, if the tuple (0.02, 0.1, 1.5) is specified,
                       each voxel will have those dimensions in the x, y, and z directions.

        material_elem_sets (str | tuple): One of the following:
                                            + The string 'All' which corresponds to all elements
                                              present in the VoxelPart.
                                            + The string 'Non-Empty' which corresponds to all
                                              non-zero elements present in the VoxelPart.
                                            + A tuple of integer material codes corresponding
                                              to the materials that should be written to the output.

        custom_elem_sets (bool): If set to :py:obj:`True`, custom sets will be written to the output.
                                 Defaults to :py:obj:`True`.

        write_assembly (bool): If set to :py:obj:`True`, an instance of the part will be
                               written to the assembly without any translation or rotation.
                               Some features such as constraints require this to be :py:obj:`True`.
                               Defaults to :py:obj:`True`.

        keep_temp_files (bool): If set to :py:obj:`True`, temporary files will not be deleted.
                                Defaults to :py:obj:`False`.
    """

    logger.info("Attempting to output part '%s' to an Abaqus input file.", part.name)
    # TODO: recheck everything about BCs. especially sets and args.
    # TODO: add BC type to report.

    begin_time = time.perf_counter()

    # Validate file_name and add file extension.
    if not helper.is_name_valid(file_name):
        raise ValueError('Invalid file_name. Check the documentation for validity criteria.')
    file_name = file_name + '.inp'

    # Validate and process material_elem_sets.
    valid_materials = unique(part.data)
    if isinstance(material_elem_sets, str):
        if material_elem_sets.upper() in ['ALL', 'NON-EMPTY']:
            selected_mats = list(valid_materials)
            if (0 in selected_mats) and (material_elem_sets.upper() == 'NON-EMPTY'):
                selected_mats.remove(0)
            material_elem_sets = selected_mats
        else:
            raise ValueError("Invalid string '%s' for material_elem_sets. Valid values are 'All' "
                             "and 'Non-Empty'." % material_elem_sets)
    else:  # Will raise most errors.
        for mat in material_elem_sets:
            if mat not in valid_materials:
                raise ValueError('Material %i specified in material_elem_sets is not present in '
                                 'the model.' % mat)

    # Process BCs.
    constraint_list = create_bc(part, dim)

    # Add the dummy nodes as node sets.
    # noinspection PyProtectedMember
    for name, node_id in part._dummy_node_dict.items():
        part.add_node_set(name=name, ids=node_id-1)  # ids is zero-based.

    # Write element sets.
    (elem_set_file_path, elem_id_list, elem_set_stats) = \
        write_elem_set_def(part, material_elem_sets, folder_path, custom_elem_sets)

    # Write temporary element definition file.
    (elem_file_path, num_elems, node_id_list) = write_elem_def(part_data_shape=part.data.shape,
                                                               elem_id_list=elem_id_list,
                                                               elem_type=elem_code, dim=dim,
                                                               folder_path=folder_path)

    # Write temporary node definition file.
    (node_file_path, num_nodes, node_id_list) = write_node_def(part=part,
                                                               node_id_list=node_id_list,
                                                               scale=scale, dim=dim,
                                                               folder_path=folder_path)

    # Write node sets.
    node_set_file_path = write_node_set_def(part, node_id_list, folder_path)

    # Write constraints.
    if constraint_list:
        constraints_file_path = write_constraints(folder_path, constraint_list)

    # Write the final input file.  #TODO: better logging.
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
        if write_assembly:
            # Declare the assembly portion of the input file as a comment
            # and create an assembly.
            main_file.write('**\n** Assembly\n**\n\n')

            # Declare the assembly.
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
    logger.info("Finished exporting part '%s' to the Abaqus input file at '%s'.",
                part.name, main_file_path)

    write_output_summary(part, dim, elem_code, num_nodes, num_elems, elem_set_stats, elapsed_time)


def write_elem_def(part_data_shape, elem_id_list, elem_type, dim, folder_path):
    """Write the element definition portion of an Abaqus input file to a temporary file,
    which will be concatenated with other portions to form an input file.

    Element definition consists of specifying the element code and writing its connectivity table.
    In the finite element method, the connectivity table (or matrix) determines
    which nodes belong to each element.
    The first column is always element id and its nodes are written
    in rest of the columns in a specific order based on the element geometry.

    Currently, only 2D and 3D linear elements are supported.
    To get around this, you can convert to quadratic elements after importing the model to Abaqus.

    Args:
        part_data_shape (tuple): Shape of :py:attr:`VoxelPart.~data`
                                 which can be obtained using its *shape()* method.

        elem_id_list (numpy.ndarray): A 1-D Numpy ndarray containing IDs of elements
                                      which must be output.
                                      The function makes sure that it is unique and sorted.
                                      Note that Abaqus only accepts element IDs that are positive
                                      and less than 999999999.
                                      Element IDs must also be integers, but this is not
                                      directly checked. However, they will raise an error
                                      once they are passed as indices to numpy.

        elem_type (str): An uppercase string denoting the element code assigned to *all* elements.
                         It must be a valid Abaqus element code such as 'CPE4R' or 'C3D8R'.
                         No validation is performed by the function.

        dim (str): Dimensionality of the output part. Valid values are '2D' and '3D'.
                   If a 3D part is set to be output as a 2D plate,

        folder_path (str): Path to the folder where the temporary element definition file
                           will be placed.

    Returns:
        tuple: The tuple *(file_path, num_elems, node_id_list)* containing
        the path to the temporary element definition file,
        the number of elements which have been written to the file,
        and a numpy ndarray containing a sorted list of node IDs that are present in the model.
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
                            ' which is not supported by Abaqus (TM).'))

    # Validate dim.
    if dim.upper() not in ['2D', '3D']:
        raise ValueError("dim can only be one of '2D' or '3D'.")

    # Make sure elem_id_list is unique and sorted.
    elem_id_list = unique(elem_id_list)

    # Preallocate memory for the connectivity table.
    if dim.upper() == '2D':
        elem_array_shape = part_data_shape[0:2]
        num_cols = 5
    elif dim.upper() == '3D':
        elem_array_shape = part_data_shape
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
            header=('*ELEMENT, TYPE=%s' % elem_type), footer='\n')

    # Create a sorted array of unique node IDs in the connectivity matrix
    # and revert node IDs to zero-based indexing.
    node_id_list = unique(connectivity_table[:, 1:]) - 1
    num_elems = len(elem_id_list)

    logger.debug("Wrote %u %s elements of type '%s' to the temporary file 'elem_def.tmp'.",
                 num_elems, dim.upper(), elem_type)
    return file_path, num_elems, node_id_list


def write_node_def(part, node_id_list, scale, dim, folder_path):
    """Write the node definition portion of an Abaqus input file to a temporary file,
    which will be concatenated with other portions to form an input file.

    Node definition consists of specifying the node ID and writing its coordinates
    in the x, y, and z directions.

    Currently, only cartesian global coordinates are supported.

    Args:
        part (VoxelPart): Size and dummy nodes are taken from it. #TODO

        node_id_list (numpy.ndarray): A 1-D Numpy ndarray containing IDs of nodes which must be output.
                                      The function makes sure that it is unique and sorted.
                                      Note that Abaqus only accepts node IDs that are positive and less than 999999999.
                                      Node IDs must also be integers, but this is not directly checked.
                                      However, they will raise an error once they are passed as indices to numpy.

        scale (tuple): A tuple containing two or three floats which are used to scale the pixels or voxels
                       in the x, y, and z direction. For example, if the tuple (0.02, 0.1, 1.5) is specified,
                       each voxel will have those dimensions in the x, y, and z directions.

        dim (str): Dimensionality of the output part. Valid values are '2D' and '3D'.
                   If a 3D part is set to be output as a 2D plate,

        folder_path (str): Path to the folder where the temporary node definition file will be placed.

    Returns:
        tuple: The tuple *(file_path, num_nodes, node_id_list)* containing
        the path to the temporary element definition file,
        the number of nodes which have been written to the file,
        and the id of the nodes written to file which has been updated by adding the dummy node.
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
                            ' which is not supported by Abaqus (TM).'))
    num_real_nodes = node_id_list.size

    # Validate dim.
    if dim.upper() not in ['2D', '3D']:
        raise ValueError("dim can only be one of '2D' or '3D'.")

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
        node_table[-1 * len(dummy_node_dict):, :] = dummy_nodes_list_array[dummy_nodes_list_array[:,0].argsort()]
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


def write_set_ids(file_obj, kind, name, ids, instance_name=None):
    """Write an element or node set to a file according to Abaqus (TM) input file syntax.

    Args:
        file_obj (file): The file object in which the set is written.
        kind (str): The kind of set that is to be output.
                    Valid values are 'ELSET' for an element set and 'NSET' for a Node set.

        name (str): Name of the set. Must be valid according to the documentation
                    for :py:meth:`helper.is_name_valid`.

        ids (numpy.ndarray): A 1-D Numpy ndarray containing zero-based IDs of nodes or elements
                             which form the set.
                             The function makes sure that it is unique and sorted.
                             Note that Abaqus only accepts node IDs that are positive
                             and less than 999999999.
                             IDs must also be integers, but this is not directly checked.

    Returns:
        tuple: A tuple containing set name and number of IDs.
    """
    if kind.upper() not in ['ELSET', 'NSET']:
        raise ValueError("kind can only be one of 'ELSET' or 'NSET'.")

    if not helper.is_name_valid(name):
        raise ValueError('Invalid name. Check the documentation for validity criteria.')

    # Validate ids. Note that values are not checked.
    if len(ids) == 0:
        raise ValueError('ids is empty. At least one ID must be selected for output.')
    if any(ids < 0):
        raise ValueError('At least on element in ids is negative' +
                         ' which will result in a non-positive ID in the input file.')
    if max(ids) >= 999999999:
        raise RuntimeError(('At least one ID is greater than 999999999,' +
                            ' which is not supported by Abaqus (TM).'))
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
    # numpy.savetxt can only write a full 2D array, meaning that sometimes
    # the array needs to be broken into chunks.
    # For simplicity, the array is always broken into two chunks.
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


def write_elem_set_def(part, material_elem_sets, folder_path, custom_elem_sets=True):
    """Write the element set portion of an Abaqus input file to a temporary file.
    This function also returns which elements must be output.

    Args:
        part (VoxelPart): The VoxelPart object which is to be output.

        material_elem_sets (tuple): A tuple containing integer values of the materials
                                    that should be output. For each material *x*,
                                    a set named *'MAT-x'* is defined.

        custom_elem_sets (bool): If set to :py:obj:`True`, custom sets are defined and output.
                                 Defaults to :py:obj:`True`.

        folder_path (str): Path to the folder where the temporary node definition file
                           will be placed.

    Returns:
        tuple: The tuple (elem_set_file_path, elem_id_list, elem_set_stats) where
               The first element is the path to the temporary set definition file,
               the second element is a unique and sorted list of all element IDs in the sets,
               and the third element is a dictionary where the keys are names
               of the element sets and the values are the number of elements in that set.
    """

    logger.debug("Attempting to write element sets to the temporary file 'elemset.tmp'.")
    elem_set_stats = dict()
    elem_id_list = array([], order='C', dtype='uint32')
    elem_set_file_path = os.path.join(folder_path, 'elemset.tmp')

    with open(elem_set_file_path, 'w', encoding='latin1') as file_obj:
        # Write custom element sets. The element IDs are unique and sorted.
        if custom_elem_sets and bool(part.elem_sets):
            for (name, elem_ids) in part.elem_sets.items():
                (set_name, num_ids) = write_set_ids(file_obj=file_obj, kind='ELSET',
                                                    name=name, ids=elem_ids)
                elem_id_list = union1d(elem_id_list, elem_ids)
                elem_set_stats[set_name] = num_ids
        # Write the the materials that should be output.
        # TODO: make sure all materials have at least one element.
        for mat_code in material_elem_sets:
            (name, elem_ids) = part.return_material_elem_set(mat_code)
            (set_name, num_ids) = write_set_ids(file_obj=file_obj, kind='ELSET',
                                                name=name, ids=elem_ids)
            elem_id_list = union1d(elem_id_list, elem_ids)
            elem_set_stats[set_name] = num_ids

    logger.debug("Wrote %u element sets to the temporary file 'elemset.tmp'.", len(elem_set_stats))
    return elem_set_file_path, elem_id_list, elem_set_stats


def write_node_set_def(part, node_id_list, folder_path):
    """Write the node and element set portion of an Abaqus input file to a temporary file.
    This function also returns which elements must be output.

    Args:
        part (VoxelPart): The VoxelPart object which is to be output.

        node_id_list (numpy.ndarray): A 1-D Numpy ndarray containing IDs of the nodes
                                      that have been written to the output. It is used
                                      to determine which nodes from the node set
                                      should actually be defined in the output.

        folder_path (str): Path to the folder where the temporary node definition file
                           will be placed.

    Returns:
        str: The path to the temporary set definition file.
    """

    logger.debug("Attempting to write node sets to the temporary file 'nodeset.tmp'.")
    node_set_file_path = os.path.join(folder_path, 'nodeset.tmp')
    # TODO: add node sets to summary.
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

    logger.debug("Wrote %u node sets to the temporary file 'nodeset.tmp'.",
                 len(part.node_sets) - num_omitted)
    return node_set_file_path


def write_constraints(folder_path, constraint_list):
    constraints_file_path = os.path.join(folder_path, 'constraints_def.tmp')
    with open(constraints_file_path, 'w', encoding='latin1') as file_obj:
        file_obj.write('**\n** Constraints\n')
        for constraint_obj in constraint_list:
            file_obj.write(repr(constraint_obj))
        file_obj.write('** End Constraints\n\n')
    return constraints_file_path


def write_output_summary(part, dim, elem_type, num_nodes, num_elems,
                         elem_set_stats, elapsed_time):
    """Write a summary of the output to the main log.

    The log file is extracted from the root logger.

    Args:
        part (VoxelPart): The VoxelPart object which is to be output.

        dim (str): Dimensionality of the output part. Valid values are '2D' and '3D'.

        elem_type (str): An uppercase string denoting the element code assigned to *all* elements.
                         It must be a valid Abaqus element code such as 'CPE4R' or 'C3D8R'.
                         No validation is performed by the function.

        num_nodes (int): Number of nodes written to the output.

        num_elems (int): Number of elements written to the output.

        elem_set_stats (dict): Dictionary returned by :py:meth:`output.write_elem_set_def`.

        elapsed_time (float): Elapsed time for the output process in seconds.
    """

    # Prepare part summary.
    part_summary = (
        ('Part Name', part.name),
        ('Part   Dimensions', '*'.join(str(i) for i in part.data.shape)),
        ('Output Dimensions', dim.upper()),
        ('Element Type', elem_type),
        ('Number of Elements', num_elems),
        ('Number of Nodes', num_nodes),
        ('Total Output Time', time.strftime('%H:%M:%S', time.gmtime(elapsed_time)))
    )

    # Prepare set stats.
    mat_elem_sets = []
    custom_elem_sets = []
    elem_set_stats_list = sorted(elem_set_stats.items(), key=lambda x: x[1], reverse=True)
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
    logger.info('A summary of the created part is as follows:\n***\n%s***\n' % summary_text)
