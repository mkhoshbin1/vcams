"""Functions used for creating boundary conditions."""
import numpy as np


def create_node_set_2d_edges(part):
    if not all(part.data[:, 0]):  # TODO
        raise RuntimeError('Edge 11 is has empty elements.')

    # Define elem_array_shape.
    elem_array_shape = part.data.shape
    # In each direction, node array is larger by one.
    node_array_shape = tuple(i + 1 for i in elem_array_shape)

    # For Edge 11, x and x+1 are used and y is the same.
    elem_x = np.arange(part.data.shape[0])
    elem_x = np.append(elem_x, elem_x + 1)
    elem_y = np.arange(part.data.shape[1])
    elem_y = np.append(elem_y, elem_y + 1)
    #TODO: x and y are reversed.
    ids11 = np.ravel_multi_index(multi_index=(elem_x, np.array([0])),
                                 dims=node_array_shape, mode='raise', order='C')
    ids12 = np.ravel_multi_index(multi_index=(elem_x, np.array(part.data.shape[1])),
                                 dims=node_array_shape, mode='raise', order='C')
    ids21 = np.ravel_multi_index(multi_index=(np.array([0]), elem_y),
                                 dims=node_array_shape, mode='raise', order='C')
    ids22 = np.ravel_multi_index(multi_index=(np.array(part.data.shape[0]), elem_y),
                                 dims=node_array_shape, mode='raise', order='C')

    part.add_node_set(name='Edge11-NodeSet', ids=ids11)
    part.add_node_set(name='Edge12-NodeSet', ids=ids12)
    part.add_node_set(name='Edge21-NodeSet', ids=ids21)
    part.add_node_set(name='Edge22-NodeSet', ids=ids22)




