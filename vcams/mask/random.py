"""Functions used for creating random Boolean masks.

The resulting masks can then be used
for manipulating a :class:`~vcams.voxelpart.VoxelPart` instance
using its :meth:`~vcams.voxelpart.VoxelPart.apply_mask` method.

See the :ref:`boolean-masks` section for an explanation of Boolean masks
and examples :doc:`C-3 </examples/example-c3>`
and :doc:`C-4 </examples/example-c4>` for sample scripts.
"""

# For some reason, the numpy.random.shuffle() function
# is added to the sphinx documentation.
# To fix this, the ":exclude-members: shuffle" directive is
# added to random-module.rst.


from logging import getLogger

from numpy import ndarray, zeros, prod, floor
from numpy.random import shuffle

logger = getLogger(__name__)


def random_binary_mask(part=None, array_shape: tuple[int, int, int] = None,
                       true_fraction: float = 0.5) -> ndarray:
    """Return a Boolean mask containing a random dispersion of True and False values.

    Args:
        part (VoxelPart | None): The *VoxelPart* instance based on which the random array is created.
                                 If *None*, *array_shape* must be specified.
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
