"""TODO"""
import numpy as np


def mask_from_function(mask_shape, func, voxel_size, **kwargs):
    mask = np.zeros(mask_shape, dtype=bool)

    for i in np.arange(mask_shape[0]):
        for j in np.arange(mask_shape[1]):
            for k in np.arange(mask_shape[2]):
                mask[i, j, k] = is_voxel_inside(i, j, k, voxel_size, func, **kwargs)

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
                         and can receive other key-word arguments. See **kwargs.
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
    xx = (x * voxel_size[0], x + 0.5 * voxel_size[0], x + voxel_size[0])
    yy = (y * voxel_size[1], y + 0.5 * voxel_size[1], y + voxel_size[1])
    zz = (z * voxel_size[2], z + 0.5 * voxel_size[2], z + voxel_size[2])

    # These can be combined into a list of coordinates using a number of
    # different methods. But for conceptual simplicity and speed,
    # this operation has been hard coded.
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

    if np.count_nonzero(func(x_array, y_array, z_array, **kwargs) < 0) >= 14:
        return True
    else:
        return False
