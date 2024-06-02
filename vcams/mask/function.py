"""Functions used for creating a boolean mask from a level set function.

These resulting mask can then be used
for manipulating :class:`~vcams.voxelpart.VoxelPart` object
using its :meth:`~vcams.voxelpart.VoxelPart.apply_mask` method.
See the :ref:`modeling-techniques` section for a complete explanation
of the basic concepts.
"""
from logging import getLogger
from time import perf_counter
from inspect import isclass
from typing import Union, Callable

import numpy as np
from numpy import ndarray, squeeze

from .tpms import BaseTpms

logger = getLogger(__name__)


# TODO: the definition for level set is reversed. fix.
#  See J. Liu et al. / Advances in Engineering Software 87 (2015) 13–29

def mask_from_function(func: Callable | BaseTpms, vectorized: bool = True,
                       do_log: bool = True,
                       part=None,
                       mask_shape: tuple[int, int, int] = None,
                       voxel_size: tuple[float, float, float] = None, **kwargs) -> ndarray:
    """Create a boolean mask based on a function describing a surface.

    Args:
        part (VoxelPart | None): The :class:`~.voxelpart.VoxelPart` based on which the mask is created.
                                 If *None*, arguments *mask_shape* and *voxel_size* must be specified
                                 otherwise they are ignored. Defaults to *None*.
        func: A function object which evaluates a point and returns a value.
              This function must accept x, y, and z parameters (if not use them)
              and can receive other keyword arguments. See *\**kwargs*.
              This function can represent anything, for example:

              + A level-set function such as the Schwarz P
                triply periodic minimal surface (TPMS).
              + The equation for a circle. In this case,
                the function receives the z variable, but does not use it.
                It is possible to pass a subclass of :class:`~.BaseTpms`.
                to this function. In that case, it's function is used for the operation.
        vectorized: If set to True, this function is run in a vectorized manner
                    which is very fast but uses more memory (Strongly recommended).
                    Otherwise, this function calls the others in a simple
                    for-loop which is slower but needs less memory.
                    In any case, the functions called are always vectorized.
        do_log: If set to True, name of the function and elapsed time is
                written to the log at the end of the operation.
        mask_shape: A tuple containing three integers which determine
                    the shape of the returned boolean mask. Ignored if *part* is passed.
        voxel_size: A tuple containing three floats which determine the size of a voxel
                    in the x, y, and z directions. Ignored if *part* is passed.
        **kwargs: Any keyword arguments passed to this function are passed to *func*.
                  If any of them is a vector, care should be taken to ensure that the
                  function can accept them as vectors.

    Returns:
        A numpy ndarray with a dtype of bool representing the resulting boolean mask.
        It can be combined with other masks or be applied using :meth:`.VoxelPart.apply_mask`.
    """

    if part:
        mask_shape = part.size
        voxel_size = part.voxel_size

    # Validate voxel_size and convert to numpy array.
    voxel_size = np.array(voxel_size, dtype=float)
    if len(voxel_size) == 3:
        pass
    elif len(voxel_size) == 2:
        voxel_size = np.append(voxel_size, 1)
    else:
        raise ValueError('voxel_size must have a length of 2 or 3.')

    # Validate mask_shape and convert to numpy array.
    mask_shape = np.array(mask_shape, dtype=float)
    if len(mask_shape) == 3:
        pass
    elif len(mask_shape) == 2:
        mask_shape = np.append(mask_shape, 1)
    else:
        raise ValueError('mask_shape must have a length of 2 or 3.')

    # noinspection PyTypeChecker
    if isclass(func) and issubclass(func, BaseTpms):  # TODO: maybe check for function / rename?
        func = func.func

    start_time = perf_counter()
    if vectorized:
        x, y, z = np.ogrid[0:mask_shape[0], 0:mask_shape[1], 0:mask_shape[2]]
        mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
    else:
        mask = np.zeros(mask_shape, dtype=bool)
        for i in np.arange(mask_shape[0]):
            for j in np.arange(mask_shape[1]):
                for k in np.arange(mask_shape[2]):
                    mask[i, j, k] = is_voxel_inside(i, j, k, voxel_size, func, **kwargs)

    if do_log:
        logger.info("Created a mask from the function named '%s' in %.2f seconds.",
                    func.__name__, perf_counter() - start_time)
    return squeeze(mask)


def is_voxel_inside(x: Union[float, ndarray], y: Union[float, ndarray], z: Union[float, ndarray],
                    voxel_size: tuple[float, float, float], func: Callable, **kwargs) -> bool:
    """Determine if a voxel is inside a surface.

    A voxel is always cubic, and 27 points of interest (PoI) are defined on it as shown below:

    .. figure:: /images/voxel-poi.png
       :name: voxel-poi
       :scale: 40%
       :align: center
       :alt: Illustration of the 27 points of interest (PoI) checked in a voxel.

    This function compiles three vectors that together form the coordinates
    of these points and passes them to the vectorized function.
    Any other arguments that the surface function needs are passed to it using \**kwargs.

    The result is a vector of values. If these values are negative,
    that particular PoI is considered to be inside the surface.
    If more than half of the 27 PoIs are inside,
    the voxel is considered inside the surface defined by *func*.
    This function is also vectorized for use with the output of numpy.ogrid,
    which is faster but that may consume a lot of memory.

    Args:
        x: The x index of the voxel. It is multiplied by *voxel_size[0]* to obtain the x coordinate.
        y: The y index of the voxel. It is multiplied by *voxel_size[1]* to obtain the y coordinate.
        z: The z index of the voxel. It is multiplied by *voxel_size[2]* to obtain the z coordinate.
        voxel_size: A tuple containing exactly three floats
                    which determine the size of a voxel in the x, y, and z directions.
                    For 2D parts, the third dimension can be any float, preferably 1.0.
        func: See the *func* parameter of :func:`mask_from_function`.
        **kwargs: Any keyword arguments passed to this function are passed to *func*.
                  If any of them is a vector, care should be taken to ensure that the
                  function can accept them as vectors.

    Returns:
        Returns True if the voxel is inside the surface defined by *func* and False if outside.
    """
    # TODO: type annotations.
    # See https://stackoverflow.com/questions/71109838,
    #     https://github.com/ramonhagenaars/nptyping,
    #     https://pypi.org/project/nptyping2/ (which is quite new),
    # and https://peps.python.org/pep-0646/

    # The coordinates of the 27 PoI have three unique values along each axis, Which are:
    xx = np.array((x, x + 0.5, x + 1.0)) * voxel_size[0]
    yy = np.array((y, y + 0.5, y + 1.0)) * voxel_size[1]
    zz = np.array((z, z + 0.5, z + 1.0)) * voxel_size[2]

    # These can be combined into a list of coordinates using a number of
    # different methods, including np.meshgrid.
    # But a hard coded approach is faster.
    x_array = np.array((xx[0], xx[0], xx[0], xx[0], xx[0], xx[0], xx[0], xx[0], xx[0],
                        xx[1], xx[1], xx[1], xx[1], xx[1], xx[1], xx[1], xx[1], xx[1],
                        xx[2], xx[2], xx[2], xx[2], xx[2], xx[2], xx[2], xx[2], xx[2]))
    y_array = np.array((yy[0], yy[0], yy[0], yy[1], yy[1], yy[1], yy[2], yy[2], yy[2],
                        yy[0], yy[0], yy[0], yy[1], yy[1], yy[1], yy[2], yy[2], yy[2],
                        yy[0], yy[0], yy[0], yy[1], yy[1], yy[1], yy[2], yy[2], yy[2]))
    z_array = np.array((zz[0], zz[1], zz[2], zz[0], zz[1], zz[2], zz[0], zz[1], zz[2],
                        zz[0], zz[1], zz[2], zz[0], zz[1], zz[2], zz[0], zz[1], zz[2],
                        zz[0], zz[1], zz[2], zz[0], zz[1], zz[2], zz[0], zz[1], zz[2]))

    # Call the function using the coordinate arrays and kwargs.
    # The result is a vector of values. If these values are negative,
    # that particular PoI is considered inside the surface.
    # If more than half of the 27 PoIs are inside,
    # the voxel is considered inside the surface defined by the function.
    return np.count_nonzero(func(x_array, y_array, z_array, **kwargs) < 0, axis=0) >= 14
