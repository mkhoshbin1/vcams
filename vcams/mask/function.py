"""Functions used for creating a boolean mask from a function."""
import logging
import time

import numpy as np

logger = logging.getLogger(__name__)

# TODO: the definition for level set is reversed. fix. see J. Liu et al. / Advances in Engineering Software 87 (2015) 13–29

def mask_from_function(mask_shape, func, voxel_size, vectorized=True,
                       do_log=True, **kwargs):
    """Create a boolean mask based on a function describing a surface.

    Args:
        mask_shape (tuple): A tuple containing three integers which determine
                            the shape of the returned boolean mask.
        func (function): A function object which evaluates a point and returns a value.
                         This function must accept x, y, and z parameters (if not use them)
                         and can receive other keyword arguments. See **kwargs.
                         This function can represent anything, for example:
                           + A level-set function such as the Schwarz P
                           triply periodic minimal surface (TPMS).
                           + The equation for a circle. In this case,
                           the function receives the z variable, but does not use it.

        voxel_size (tuple): A tuple containing three floats which determine the size of a voxel
                            in the x, y, and z directions.
                            Usually, VoxelPart.voxel_size is passed to this.

        vectorized (bool): If set to :py:obj:`True`, this function is run
                           in a vectorized manner which is faster but uses more memory.
                           Otherwise, this function calls the others in a simple
                           for-loop which is slower but needs less memory.
                           In any case, the functions called are always vectorized.
                           Defaults to :py:obj:`True`.

        do_log (bool): If set to :py:obj:`True`, name of the function and
                       elapsed time is written to log at the end of the operation.
                       Defaults to :py:obj:`True`.

        **kwargs: Any keyword arguments passed to this function are passed to *func*.
                  If any of them is a vector, care should be taken to ensure that the
                  function can accept them as vectors.

    Returns: bool
        The resulting boolean mask.
    """

    if len(mask_shape) == 2:
        mask_shape = np.append(mask_shape, 1)

    start_time = time.perf_counter()
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
                    func.__name__, time.perf_counter() - start_time)
    return mask


def is_voxel_inside(x, y, z, voxel_size, func, **kwargs):
    """Determine if a voxel is inside a surface.

    A voxel is cubic in shape, and 27 points of interest (PoI) are defined
    on it. TODO: add image.
    This function compiles three vectors that together form the coordinates
    of these points and passes them to the vectorized function.
    Any other arguments that the surface function needs are passed to it
    using **kwargs.

    The result is a vector of values. If these values are negative,
    that particular PoI is considered to be inside the surface.
    If more than half of the 27 PoIs are inside,
    the voxel is considered inside the surface defined by the function.
    This function is also vectorized for use with the output of numpy.ogrid,
    but that may consume a lot of memory.

    Args:
        x (float): The x index of the voxel.
                   It is multiplied by voxel_size[0] to obtain the x coordinate.

        y (float): The y index of the voxel.
                   It is multiplied by voxel_size[1] to obtain the y coordinate.

        z (float): The z index of the voxel.
                   It is multiplied by voxel_size[2] to obtain the z coordinate.

        voxel_size (tuple): A tuple containing three floats which determine the size of a voxel
                            in the x, y, and z directions.
                            Usually, VoxelPart.voxel_size is passed to this.

        func (function): A function object which evaluates a point and returns a value.
                         This function must accept x, y, and z parameters (if not use them)
                         and can receive other keyword arguments. See **kwargs.
                         This function can represent anything, for example:
                           + A level-set function such as the Schwarz P
                           triply periodic minimal surface (TPMS).
                           + The equation for a circle. In this case,
                           the function receives the z variable, but does not use it.

        **kwargs: Any keyword arguments passed to this function are passed to *func*.
                  If any of them is a vector, care should be taken to ensure that the
                  function can accept them as vectors.

    Returns: bool
        Returns :py:obj:`True` if the voxel is inside the surface.
    """

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
