"""#TODO: add docs and examples."""

from logging import getLogger
from numpy import ndarray, zeros, prod, floor
from numpy.random import shuffle

logger = getLogger(__name__)


def random_binary_mask(part=None, array_shape: tuple[int, int, int] = None,
                       true_fraction: float = 0.5) -> ndarray:
    """TODO

    Args:
        part (VoxelPart | None): The VoxelPart object (TODO) based on which the random array is created.
                                 If None, *array_shape* must be specified.
        array_shape: A tuple containing three integers which determines
                    the shape of the random array. Ignored if *part* is passed.
        true_fraction: Fraction of the True values in the random array.
                       If the number of elements in the random array is not dividable,
                       it is rounded down.

    Returns:
        A Boolean mask with the desired fraction of randomly distributed True elements.
    """

    if part:
        array_shape = part.size
    num_array_elems = prod(array_shape)
    num_true = int(floor(true_fraction * num_array_elems))
    random_array = zeros(num_array_elems, dtype=bool, order='C')
    random_array[:num_true] = True
    shuffle(random_array)
    return random_array.reshape(array_shape, order='C')
