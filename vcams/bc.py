"""Functions used for creating boundary conditions.
The BC and it's information is stored in the VoxelPart object and written to the output with it."""
from numpy import ravel_multi_index, array, arange, meshgrid


def create_node_sets(part, dim):
    """Define node sets in a VoxelPart. They are created according to TODO

    Args:
        part (VoxelPart): The VoxelPart object on which the operation is performed.
        dim (str): Dimensionality of the output part. Valid values are '2D' and '3D'.
    """

    if dim not in ['2D', '3D']:
        raise ValueError("dim can only be one of '2D' or '3D'.")

    # TODO: Consider checking part.data for missing elements.

    # Define a ravel function based on numpy.ravel_multi_index.
    def custom_ravel(inds):
        return ravel_multi_index(multi_index=inds, dims=node_array_shape,
                                 mode='raise', order='C')

    # Define a numpy.array containing a single number 0.
    zro = array([0])
    # Define elem_array_shape.
    elem_array_shape = part.data.shape
    # In each direction, node array is larger by one.
    node_array_shape = tuple(i + 1 for i in elem_array_shape)
    if dim.upper() == '2D':
        max_x, max_y = elem_array_shape
    else:
        max_x, max_y, max_z = elem_array_shape
        inds_dir3 = arange(1, max_z)
    # Find indices of nodes in all directions. Indices for vertices are not included.
    inds_dir1 = arange(1, max_x)
    inds_dir2 = arange(1, max_y)

    # Define vertices.
    # Find IDs for vertices.
    if dim.upper() == '2D':
        vertex_coords = (array([0, max_x, max_x, 0]),
                         array([0, 0, max_y, max_y]))
    else:
        vertex_coords = (array([0, max_x, max_x, 0, 0, max_x, max_x, 0]),
                         array([0, 0, max_y, max_y, 0, 0, max_y, max_y]),
                         array([0, 0, 0, 0, max_z, max_z, max_z, max_z]))  # noqa F823
    # Find IDs and define node sets for the vertices.
    vertex_ids = custom_ravel(vertex_coords)
    for i in range(len(vertex_ids)):
        part.add_node_set(name='Vertex%i-NodeSet' % (i + 1), ids=vertex_ids[i])

    # Define edges.
    # Find IDs for edges. edge_ij refers to the edge formed by vertices i and j.
    edge_dict = dict()
    if dim.upper() == '2D':
        edge_dict['Edge12-NodeSet'] = custom_ravel((inds_dir1, zro))
        edge_dict['Edge23-NodeSet'] = custom_ravel((max_x, inds_dir2))
        edge_dict['Edge34-NodeSet'] = custom_ravel((inds_dir1, max_y))
        edge_dict['Edge14-NodeSet'] = custom_ravel((zro, inds_dir2))
    else:
        edge_dict['Edge12-NodeSet'] = custom_ravel((inds_dir1, zro, zro))
        edge_dict['Edge23-NodeSet'] = custom_ravel((max_x, inds_dir2, zro))
        edge_dict['Edge34-NodeSet'] = custom_ravel((inds_dir1, max_y, zro))
        edge_dict['Edge14-NodeSet'] = custom_ravel((zro, inds_dir2, zro))
        edge_dict['Edge56-NodeSet'] = custom_ravel((inds_dir1, zro, max_z))
        edge_dict['Edge67-NodeSet'] = custom_ravel((max_x, inds_dir2, max_z))
        edge_dict['Edge78-NodeSet'] = custom_ravel((inds_dir1, max_y, max_z))
        edge_dict['Edge58-NodeSet'] = custom_ravel((zro, inds_dir2, max_z))
        edge_dict['Edge15-NodeSet'] = custom_ravel((zro, zro, inds_dir3))  # noqa F823
        edge_dict['Edge26-NodeSet'] = custom_ravel((max_x, zro, inds_dir3))
        edge_dict['Edge37-NodeSet'] = custom_ravel((max_x, max_y, inds_dir3))
        edge_dict['Edge48-NodeSet'] = custom_ravel((zro, max_y, inds_dir3))
    # Define node sets for the edges.
    for name, ids in edge_dict.items():
        part.add_node_set(name=name, ids=ids)

    # Define faces.
    if dim.upper() == '3D':
        # Find IDs for faces. For face_ij, i refers the direction of normal vector
        # and j refers to whether this is the first or second edge in the direction.
        face_dict = dict()
        face_dict['Face11-NodeSet'] = custom_ravel(
            meshgrid(zro, inds_dir2, inds_dir3, sparse=True))
        face_dict['Face12-NodeSet'] = custom_ravel(
            meshgrid(max_x, inds_dir2, inds_dir3, sparse=True))
        face_dict['Face21-NodeSet'] = custom_ravel(
            meshgrid(inds_dir1, zro, inds_dir3, sparse=True))
        face_dict['Face22-NodeSet'] = custom_ravel(
            meshgrid(inds_dir1, max_y, inds_dir3, sparse=True))
        face_dict['Face31-NodeSet'] = custom_ravel(
            meshgrid(inds_dir1, inds_dir2, zro, sparse=True))
        face_dict['Face32-NodeSet'] = custom_ravel(
            meshgrid(inds_dir1, inds_dir2, max_z, sparse=True))
        # Define node sets for the edges.
        for name, ids in face_dict.items():
            part.add_node_set(name=name, ids=ids)
