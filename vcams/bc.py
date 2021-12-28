"""Functions used for creating boundary conditions.
The BC and it's information is stored in the VoxelPart object and written to the output with it."""

import logging
from collections import namedtuple
from numpy import ravel_multi_index, array, arange, meshgrid, concatenate

logger = logging.getLogger(__name__)


class TieConstraint:
    def __init__(self, dof, rp_set_name, slave_set_name, rp_set_coeff=1, slave_set_coeff=-1):
        self.dof = dof
        self.rp_set_name = rp_set_name
        self.slave_set_name = slave_set_name
        self.rp_set_coeff = rp_set_coeff
        self.slave_set_coeff = slave_set_coeff

    def return_output_string(self):
        return (f'*Equation\n2\n'
                f'"{self.slave_set_name}", {self.dof}, {self.slave_set_coeff}\n'
                f'"{self.rp_set_name}", {self.dof}, {self.rp_set_coeff}\n')


# noinspection PyProtectedMember
def create_bc(part, dim):
    """TODO"""

    if dim.upper() not in ['2D', '3D']:
        raise ValueError("dim can only be one of '2D' or '3D'.")

    bc_def_list = []
    bc_type = part._bc_type
    if bc_type is None:
        part._bc_add_dummy_nodes = False
        logger.info('No BCs have been created.')
        return

    elif bc_type.upper() == 'NODESET ONLY':
        part._bc_add_dummy_nodes = True
        create_node_sets(part, dim, vertices=part._bc_nodeset_vertices,
                         edges=part._bc_nodeset_edges, faces=part._bc_nodeset_faces,
                         explicit_sets=part._bc_nodeset_explicit, simple_sets=part._bc_nodeset_simple)
        return [], []

    elif bc_type.upper() == 'LINEAR DISPLACEMENT':
        part._bc_add_dummy_nodes = True
        create_node_sets(part, dim, vertices=part._bc_nodeset_vertices,
                         edges=part._bc_nodeset_edges, faces=part._bc_nodeset_faces,
                         explicit_sets=part._bc_nodeset_explicit, simple_sets=True)
        if dim.upper() == '2D':
            constraint_list = (TieConstraint(dof=1, rp_set_name='RP1-NodeSet', slave_set_name='Simple-Edge11-NodeSet'),
                               TieConstraint(dof=2, rp_set_name='RP1-NodeSet', slave_set_name='Simple-Edge21-NodeSet'),
                               TieConstraint(dof=1, rp_set_name='RP2-NodeSet', slave_set_name='Simple-Edge12-NodeSet'),
                               TieConstraint(dof=2, rp_set_name='RP2-NodeSet', slave_set_name='Simple-Edge22-NodeSet'))
        else:  # dim.upper() == '3D'
            constraint_list = (TieConstraint(dof=1, rp_set_name='RP1-NodeSet', slave_set_name='Simple-Face11-NodeSet'),
                               TieConstraint(dof=2, rp_set_name='RP1-NodeSet', slave_set_name='Simple-Face21-NodeSet'),
                               TieConstraint(dof=3, rp_set_name='RP1-NodeSet', slave_set_name='Simple-Face31-NodeSet'),
                               TieConstraint(dof=1, rp_set_name='RP2-NodeSet', slave_set_name='Simple-Face12-NodeSet'),
                               TieConstraint(dof=2, rp_set_name='RP2-NodeSet', slave_set_name='Simple-Face22-NodeSet'),
                               TieConstraint(dof=3, rp_set_name='RP2-NodeSet', slave_set_name='Simple-Face32-NodeSet'))

        return constraint_list, bc_def_list

    elif bc_type.upper() == 'PERIODIC':
        raise NotImplementedError('PERIODIC')
    else:
        raise ValueError('Invalid value for bc_type.')


def create_node_sets(part, dim, vertices=True, edges=True, faces=True, explicit_sets=False, simple_sets=True):
    """Define node sets in a VoxelPart. They are created according to TODO

    Args:
        part (VoxelPart): The VoxelPart object on which the operation is performed.
        dim (str): Dimensionality of the output part. Valid values are '2D' and '3D'.
        vertices (bool): If :py:obj:`True`, node sets corresponding to the vertices in #TODO will be created.
        edges (bool): If :py:obj:`True`, node sets corresponding to the edges in #TODO will be created.
        faces (bool): If :py:obj:`True`, node sets corresponding to the faces in #TODO will be created.
                      If dim is set to '2D', this variable will be automatically set to :py:obj:`False`.
        explicit_sets (bool): If :py:obj:`True`, explicit node sets are created for vertices, edges, and faces.
                            as described in #TODO. Defaults to :py:obj:`True`.
        simple_sets (bool): If :py:obj:`True`, simplified node sets are created for complete faces
                            as described in #TODO. Defaults to :py:obj:`True`.
    """

    # TODO: use func for concatenation of edges and vertices and faces which correctly handles empties.

    if dim.upper() not in ['2D', '3D']:
        raise ValueError("dim can only be one of '2D' or '3D'.")
    if dim.upper() == '2D':
        faces = False

    if not any([vertices, edges, faces]):
        raise ValueError("At least one of vertices, edges and faces must be set to True.")

    if not any([explicit_sets, simple_sets]):
        raise ValueError("At least one of explicit_sets and simple_sets must be set to True.")

    # TODO: Consider checking part.data for missing elements.

    # Define a ravel function based on numpy.ravel_multi_index.
    def custom_ravel(inds):
        return ravel_multi_index(multi_index=inds, dims=node_array_shape,
                                 mode='raise', order='C').flatten()

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

    # Define dictionaries for the sets.
    vertex_dict = dict()
    edge_dict = dict()
    face_dict = dict()
    simple_sets_dict = dict()

    if vertices:
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
            vertex_dict['Vertex%i-NodeSet' % (i + 1)] = vertex_ids[i]

    if edges:
        # Define edges.
        # Find IDs for edges. edge_ij refers to the edge formed by vertices i and j.
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

    if faces:
        # Define faces.
        # Find IDs for faces. For face_ij, i refers the direction of normal vector
        # and j refers to whether this is the first or second edge in the direction.
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

    if simple_sets:
        if dim == '2D':
            simple_sets_dict['Simple-Edge11-NodeSet'] = concatenate((edge_dict['Edge14-NodeSet'],
                                                                     array((vertex_dict['Vertex1-NodeSet'],
                                                                            vertex_dict['Vertex4-NodeSet']))),
                                                                    axis=0)
            simple_sets_dict['Simple-Edge12-NodeSet'] = concatenate((edge_dict['Edge23-NodeSet'],
                                                                     array((vertex_dict['Vertex2-NodeSet'],
                                                                            vertex_dict['Vertex3-NodeSet']))),
                                                                    axis=0)
            simple_sets_dict['Simple-Edge21-NodeSet'] = concatenate((edge_dict['Edge12-NodeSet'],
                                                                     array((vertex_dict['Vertex1-NodeSet'],
                                                                            vertex_dict['Vertex2-NodeSet']))),
                                                                    axis=0)
            simple_sets_dict['Simple-Edge22-NodeSet'] = concatenate((edge_dict['Edge34-NodeSet'],
                                                                     array((vertex_dict['Vertex3-NodeSet'],
                                                                            vertex_dict['Vertex4-NodeSet']))),
                                                                    axis=0)
        else:  # dim == '3D'
            simple_sets_dict['Simple-Face11-NodeSet'] = concatenate((face_dict['Face11-NodeSet'],
                                                                     edge_dict['Edge14-NodeSet'],
                                                                     edge_dict['Edge48-NodeSet'],
                                                                     edge_dict['Edge58-NodeSet'],
                                                                     edge_dict['Edge15-NodeSet'],
                                                                     array((vertex_dict['Vertex1-NodeSet'],
                                                                            vertex_dict['Vertex4-NodeSet'],
                                                                            vertex_dict['Vertex8-NodeSet'],
                                                                            vertex_dict['Vertex5-NodeSet']))),
                                                                    axis=None)
            simple_sets_dict['Simple-Face12-NodeSet'] = concatenate((face_dict['Face12-NodeSet'],
                                                                     edge_dict['Edge23-NodeSet'],
                                                                     edge_dict['Edge37-NodeSet'],
                                                                     edge_dict['Edge67-NodeSet'],
                                                                     edge_dict['Edge26-NodeSet'],
                                                                     array((vertex_dict['Vertex2-NodeSet'],
                                                                            vertex_dict['Vertex3-NodeSet'],
                                                                            vertex_dict['Vertex7-NodeSet'],
                                                                            vertex_dict['Vertex6-NodeSet']))),
                                                                    axis=None)
            simple_sets_dict['Simple-Face21-NodeSet'] = concatenate((face_dict['Face21-NodeSet'],
                                                                     edge_dict['Edge12-NodeSet'],
                                                                     edge_dict['Edge26-NodeSet'],
                                                                     edge_dict['Edge56-NodeSet'],
                                                                     edge_dict['Edge15-NodeSet'],
                                                                     array((vertex_dict['Vertex1-NodeSet'],
                                                                            vertex_dict['Vertex2-NodeSet'],
                                                                            vertex_dict['Vertex6-NodeSet'],
                                                                            vertex_dict['Vertex5-NodeSet']))),
                                                                    axis=None)
            simple_sets_dict['Simple-Face22-NodeSet'] = concatenate((face_dict['Face22-NodeSet'],
                                                                     edge_dict['Edge34-NodeSet'],
                                                                     edge_dict['Edge37-NodeSet'],
                                                                     edge_dict['Edge78-NodeSet'],
                                                                     edge_dict['Edge48-NodeSet'],
                                                                     array((vertex_dict['Vertex4-NodeSet'],
                                                                            vertex_dict['Vertex3-NodeSet'],
                                                                            vertex_dict['Vertex7-NodeSet'],
                                                                            vertex_dict['Vertex8-NodeSet']))),
                                                                    axis=None)
            simple_sets_dict['Simple-Face31-NodeSet'] = concatenate((face_dict['Face31-NodeSet'],
                                                                     edge_dict['Edge12-NodeSet'],
                                                                     edge_dict['Edge23-NodeSet'],
                                                                     edge_dict['Edge34-NodeSet'],
                                                                     edge_dict['Edge14-NodeSet'],
                                                                     array((vertex_dict['Vertex1-NodeSet'],
                                                                            vertex_dict['Vertex2-NodeSet'],
                                                                            vertex_dict['Vertex3-NodeSet'],
                                                                            vertex_dict['Vertex4-NodeSet']))),
                                                                    axis=None)
            simple_sets_dict['Simple-Face32-NodeSet'] = concatenate((face_dict['Face32-NodeSet'],
                                                                     edge_dict['Edge56-NodeSet'],
                                                                     edge_dict['Edge67-NodeSet'],
                                                                     edge_dict['Edge78-NodeSet'],
                                                                     edge_dict['Edge58-NodeSet'],
                                                                     array((vertex_dict['Vertex5-NodeSet'],
                                                                            vertex_dict['Vertex6-NodeSet'],
                                                                            vertex_dict['Vertex7-NodeSet'],
                                                                            vertex_dict['Vertex8-NodeSet']))),
                                                                    axis=None)
        # Define the simple node sets.
        for name, ids in simple_sets_dict.items():
            part.add_node_set(name=name, ids=ids)

        # Define the individual node sets for vertices, edges and faces.
        if explicit_sets:
            # Define node sets for the vertices.
            for name, ids in vertex_dict.items():
                part.add_node_set(name=name, ids=ids)
            # Define node sets for the edges.
            for name, ids in edge_dict.items():
                part.add_node_set(name=name, ids=ids)
            if faces:
                # Define node sets for the faces.
                for name, ids in face_dict.items():
                    part.add_node_set(name=name, ids=ids)
