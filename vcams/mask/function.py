"""Functions used for creating a Boolean mask from a level set function.

The resulting masks can then be used
for manipulating a :class:`~vcams.voxelpart.VoxelPart` instance
using its :meth:`~vcams.voxelpart.VoxelPart.apply_mask` method.
See the :ref:`modeling-techniques` section for a complete explanation
of the basic concepts.
"""
from inspect import isclass
from logging import getLogger
from time import perf_counter
from typing import Callable

import numpy as np
from numpy import any, ceil, logical_or, max, ndarray, squeeze, array, zeros_like

logger = getLogger(__name__)


def mask_from_function(func: Callable | object, wrap_mask: bool = False,
                       do_log: bool = True,
                       part=None,
                       mask_shape: tuple[int, int, int] = None,
                       voxel_size: tuple[float, float, float] = None, **kwargs) -> ndarray:
    """Create a boolean mask based on a function describing a surface.

    Args:
        part (VoxelPart | None): The :class:`~.voxelpart.VoxelPart` based on which the mask is created.
                                 If *None*, arguments *mask_shape* and *voxel_size* must be specified
                                 otherwise they are ignored. Defaults to *None*.
        func: One of the following:

              + A function which evaluates a point and returns a value.
                This function must accept x, y, and z parameters (if not use them)
                and can receive other keyword arguments through *\\**kwargs*.
              + A class that defined a method named *func* working according
                to the aforementioned specs.
                For example, it is possible to pass a subclass of :class:`~.BaseTpms`
                and its *func* method is used for the operation.

              This function can represent anything, for example:

              - A level-set function such as the Schwarz P
                triply periodic minimal surface (TPMS).
              - The equation for a circle. In this case,
                the function receives the z variable, but does not use it.

        wrap_mask: If set to True, the function is wrapped around the boundaries of the working space.
                   This is useful for periodic structures, but is computationally expensive.
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

    if isclass(func) and hasattr(func, 'func') and callable(func.func):
        func = func.func

    start_time = perf_counter()
    x, y, z = np.ogrid[0:mask_shape[0], 0:mask_shape[1], 0:mask_shape[2]]
    mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
    if wrap_mask:
        # noinspection PyTypeChecker
        wrapping_mask = _find_wrapping_mask(mask, func, mask_shape, voxel_size, **kwargs)
        mask = logical_or(mask, wrapping_mask)
    # This is the regular for loop that can replace the above vectorized statements.
    # It used to be an option, but seeing that it will not work
    # for a wrapping mask it has been removed.
    # mask = np.zeros(mask_shape, dtype=bool)
    # for i in np.arange(mask_shape[0]):
    #     for j in np.arange(mask_shape[1]):
    #         for k in np.arange(mask_shape[2]):
    #             mask[i, j, k] = is_voxel_inside(i, j, k, voxel_size, func, **kwargs)

    if do_log:
        logger.info("Created a mask from the function named '%s' in %.2f seconds.",
                    func.__name__, perf_counter() - start_time)
    return squeeze(mask)


def is_voxel_inside(x: float | ndarray, y: float | ndarray, z: float | ndarray,
                    voxel_size: tuple[float, float, float] | ndarray, func: Callable, **kwargs) -> bool:
    """Determine if a voxel is inside a surface.

    A voxel is always cubic, and 27 points of interest (PoI) are defined on it as shown below:

    .. figure:: /images/voxel-poi.png
       :name: voxel-poi
       :scale: 40%
       :align: center
       :alt: Illustration of the 27 points of interest (PoI) checked in a voxel.

    This function compiles three vectors that together form the coordinates
    of these points and passes them to the vectorized function.
    Any other arguments that the surface function needs are passed to it using \\**kwargs.

    The result is a vector of values. If these values are negative,
    that particular PoI is considered to be inside the surface.
    If more than half of the 27 PoIs are inside,
    the voxel is considered inside the surface defined by *func*.
    This function is also vectorized for use with the output of numpy.ogrid,
    which is faster but that may consume a lot of memory.

    Note that this function performs no input validations to ensure efficiency.
    Extreme caution must be used when calling it to ensure correct results.

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
    # Contributors are discouraged from modifying this function.

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


def _find_wrapping_mask(original_mask, func, mask_shape, voxel_size, **kwargs) -> ndarray:
    """Find the wrapping mask for an original_mask and a function.
    This is a private function that should not be directly used."""
    # Contributors are discouraged from modifying this function.
    wrapping_mask = zeros_like(original_mask)
    is_3d = original_mask.shape[2] > 1
    end_x, end_y, end_z = np.shape(original_mask)  # The end variable will be used like the end keyword in Matlab.
    end_x, end_y, end_z = end_x - 1, end_y - 1, end_z - 1  # To satisfy zero-based indexing.
    num_step_list = ceil(array((0.05, 0.10, 0.15, 0.20, 0.25, 0.40, 0.50)) * max(mask_shape),
                         casting='unsafe', dtype=int)
    wrapping_failed_msg = ('Could not find a wrapping mask for the %s. '
                           'This is highly improbable and the package author would like to check the model.')

    # Edges or Faces:
    # Note that all =0 and all =end are the same, except for the fancy indexing parts.
    # Check the edge or face where x=0.
    if any(original_mask[0, :, :]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[-num_step:0, 0:mask_shape[1], 0:mask_shape[2]]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not any(new_mask[0, :, :]):
                wrapping_mask[-num_step:, :, :] = (
                    logical_or(wrapping_mask[-num_step:, :, :], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'edge or face where x=0')
    # Check edge or face where y=0.
    if any(original_mask[:, 0, :]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[0:mask_shape[0], -num_step:0, 0:mask_shape[2]]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not any(new_mask[:, 0, :]):
                wrapping_mask[:, -num_step:, :] = (
                    logical_or(wrapping_mask[:, -num_step:, :], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'edge or face where y=0')
    # Check the face where z=0.
    if is_3d and any(original_mask[:, :, 0]):  # Only for 3D arrays.
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[0:mask_shape[0], 0:mask_shape[1], -num_step:0]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not any(new_mask[:, :, 0]):
                wrapping_mask[:, :, -num_step:] = (
                    logical_or(wrapping_mask[:, :, -num_step:], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'edge or face where z=0')
    # Check edge or face where x=end.
    if any(original_mask[end_x, :, :]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[end_x:end_x + num_step, 0:mask_shape[1], 0:mask_shape[2]]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not any(new_mask[np.shape(new_mask)[0] - 1, :, :]):
                wrapping_mask[0:num_step, :, :] = (logical_or(wrapping_mask[0:num_step, :, :], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'edge or face where x=end')
    # Check edge or face where y=end.
    if any(original_mask[:, end_y, :]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[0:mask_shape[0], end_y:end_y + num_step, 0:mask_shape[2]]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not any(new_mask[:, np.shape(new_mask)[1] - 1, :]):
                wrapping_mask[:, 0:num_step, :] = (logical_or(wrapping_mask[:, 0:num_step, :], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'edge or face where y=end')
    # Check the face where z=end.
    if is_3d and any(original_mask[:, :, end_z]):  # Only for 3D arrays.
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[0:mask_shape[0], 0:mask_shape[1], end_z:end_z + num_step]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not any(new_mask[:, :, np.shape(new_mask)[2] - 1]):
                wrapping_mask[:, :, 0:num_step] = (logical_or(wrapping_mask[:, :, 0:num_step], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'face where z=end')

    # Vertices:
    # Note that each vertex is a combination of the indexing of two edge/face logics.
    # Check the vertex where x=0 and y=0.
    if any(original_mask[0, :, :]) or any(original_mask[:, 0, :]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[-num_step:0, -num_step:0, 0:mask_shape[2]]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[0, :, :]) or any(new_mask[:, 0, :])):
                wrapping_mask[-num_step:, -num_step:, :] = (
                    logical_or(wrapping_mask[-num_step:, -num_step:, :], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=0 and y=0')
    # Check the vertex where x=0 and y=end.
    if any(original_mask[0, :, :]) or any(original_mask[:, end_y, :]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[-num_step:0, end_y:end_y + num_step, 0:mask_shape[2]]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[0, :, :]) or any(new_mask[:, np.shape(new_mask)[1] - 1, :])):
                wrapping_mask[-num_step:, 0:num_step, :] = (
                    logical_or(wrapping_mask[-num_step:, 0:num_step, :], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=0 and y=0')
    # Check the vertex where x=end and y=0.
    if any(original_mask[end_x, :, :]) or any(original_mask[:, 0, :]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[end_x:end_x + num_step, -num_step:0, 0:mask_shape[2]]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[np.shape(new_mask)[0] - 1, :, :]) or any(new_mask[:, 0, :])):
                wrapping_mask[0:num_step, -num_step:, :] = (
                    logical_or(wrapping_mask[0:num_step, -num_step:, :], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=end and y=0')
    # Check the vertex where x=end and y=end.
    if any(original_mask[end_x, :, :]) or any(original_mask[:, end_y, :]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[end_x:end_x + num_step, end_y:end_y + num_step, 0:mask_shape[2]]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[np.shape(new_mask)[0] - 1, :, :]) or any(new_mask[:, np.shape(new_mask)[1] - 1, :])):
                wrapping_mask[0:num_step, 0:num_step, :] = (
                    logical_or(wrapping_mask[0:num_step, 0:num_step, :], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=end and y=end')

    # For 2D models, we are done.
    # A return statement is used instead of a conditional to reduce the indent and improve readability.
    if not is_3d:
        return wrapping_mask

    # Check the vertex where x=0 and z=0.
    if any(original_mask[0, :, :]) or any(original_mask[:, :, 0]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[-num_step:0, 0:mask_shape[1], -num_step:0]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[0, :, :]) or any(new_mask[:, :, 0])):
                wrapping_mask[-num_step:, :, -num_step:] = (
                    logical_or(wrapping_mask[-num_step:, :, -num_step:], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=0 and z=0')
    # Check the vertex where x=0 and z=end.
    if any(original_mask[0, :, :]) or any(original_mask[:, :, end_z]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[-num_step:0, 0:mask_shape[1], end_z:end_z + num_step]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[0, :, :]) or any(new_mask[:, :, np.shape(new_mask)[2] - 1])):
                wrapping_mask[-num_step:, :, 0:num_step] = (
                    logical_or(wrapping_mask[-num_step:, :, 0:num_step], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=0 and z=end')
    # Check the vertex where x=end and z=0.
    if any(original_mask[end_x, :, :]) or any(original_mask[:, :, 0]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[end_x:end_x + num_step, 0:mask_shape[1], -num_step:0]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[np.shape(new_mask)[0] - 1, :, :]) or any(new_mask[:, :, 0])):
                wrapping_mask[0:num_step, :, -num_step:] = (
                    logical_or(wrapping_mask[0:num_step, :, -num_step:], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=end and z=0')
    # Check the vertex where x=end and z=end.
    if any(original_mask[end_x, :, :]) or any(original_mask[:, :, end_z]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[end_x:end_x + num_step, 0:mask_shape[1], end_z:end_z + num_step]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[np.shape(new_mask)[0] - 1, :, :]) or any(new_mask[:, :, np.shape(new_mask)[2] - 1])):
                wrapping_mask[0:num_step, :, 0:num_step] = (
                    logical_or(wrapping_mask[0:num_step, :, 0:num_step], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=end and z=end')
    # Check the vertex where y=0 and z=0.
    if any(original_mask[:, 0, :]) or any(original_mask[:, :, 0]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[0:mask_shape[0], -num_step:0, -num_step:0]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[:, 0, :]) or any(new_mask[:, :, 0])):
                wrapping_mask[:, -num_step:, -num_step:] = (
                    logical_or(wrapping_mask[:, -num_step:, -num_step:], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where y=0 and z=0')
    # Check the vertex where y=0 and z=end.
    if any(original_mask[:, 0, :]) or any(original_mask[:, :, end_z]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[0:mask_shape[0], -num_step:0, end_z:end_z + num_step]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[:, 0, :]) or any(new_mask[:, :, np.shape(new_mask)[2] - 1])):
                wrapping_mask[:, -num_step:, 0:num_step] = (
                    logical_or(wrapping_mask[:, -num_step:, 0:num_step], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where y=0 and z=end')
    # Check the vertex where y=end and z=0.
    if any(original_mask[:, end_y, :]) or any(original_mask[:, :, 0]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[0:mask_shape[0], end_y:end_y + num_step, -num_step:0]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[:, np.shape(new_mask)[1] - 1, :]) or any(new_mask[:, :, 0])):
                wrapping_mask[:, 0:num_step, -num_step:] = (
                    logical_or(wrapping_mask[:, 0:num_step, -num_step:], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where y=end and z=0')
    # Check the vertex where y=end and z=end.
    if any(original_mask[:, end_y, :]) or any(original_mask[:, :, end_z]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[0:mask_shape[0], end_y:end_y + num_step, end_z:end_z + num_step]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[:, np.shape(new_mask)[1] - 1, :]) or any(new_mask[:, :, np.shape(new_mask)[2] - 1])):
                wrapping_mask[:, 0:num_step, 0:num_step] = (
                    logical_or(wrapping_mask[:, 0:num_step, 0:num_step], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where y=end and z=end')

    # The following are for the opposite vertex in 3D. Note that is_3d is assumed to be True and is NOT checked.
    # Check the vertex where x=0, y=0, and z=0.
    if any(original_mask[0, :, :]) or any(original_mask[:, 0, :]) or any(original_mask[:, :, 0]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[-num_step:0, -num_step:0, -num_step:0]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[0, :, :]) or any(new_mask[:, 0, :]) or any(new_mask[:, :, 0])):
                wrapping_mask[-num_step:, -num_step:, -num_step:] = (
                    logical_or(wrapping_mask[-num_step:, -num_step:, -num_step:], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=0, y=0, and z=0')
    # Check the vertex where x=0, y=0, and z=end.
    if any(original_mask[0, :, :]) or any(original_mask[:, 0, :]) or any(original_mask[:, :, end_z]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[-num_step:0, -num_step:0, end_z:end_z + num_step]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[0, :, :]) or any(new_mask[:, 0, :]) or any(new_mask[:, :, np.shape(new_mask)[2] - 1])):
                wrapping_mask[-num_step:, -num_step:, 0:num_step] = (
                    logical_or(wrapping_mask[-num_step:, -num_step:, 0:num_step], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=0, y=0, and z=end')
    # Check the vertex where x=0, y=end, and z=0.
    if any(original_mask[0, :, :]) or any(original_mask[:, end_y, :]) or any(original_mask[:, :, 0]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[-num_step:0, end_y:end_y + num_step, -num_step:0]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[0, :, :]) or
                    any(new_mask[:, np.shape(new_mask)[1] - 1, :]) or
                    any(new_mask[:, :, 0])):
                wrapping_mask[-num_step:, 0:num_step, -num_step:] = (
                    logical_or(wrapping_mask[-num_step:, 0:num_step:, -num_step:], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=0, y=end, and z=0')
    # Check the vertex where x=0, y=end, and z=end.
    if any(original_mask[0, :, :]) or any(original_mask[:, end_y, :]) or any(original_mask[:, :, end_z]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[-num_step:0, end_y:end_y + num_step, end_z:end_z + num_step]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[0, :, :]) or
                    any(new_mask[:, np.shape(new_mask)[1] - 1, :]) or
                    any(new_mask[:, :, np.shape(new_mask)[2] - 1])):
                wrapping_mask[-num_step:, 0:num_step, 0:num_step] = (
                    logical_or(wrapping_mask[-num_step:, 0:num_step, 0:num_step], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=0, y=end, and z=end')
    # Check the vertex where x=end, y=0, and z=0.
    if any(original_mask[end_x, :, :]) or any(original_mask[:, 0, :]) or any(original_mask[:, :, 0]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[end_x:end_x + num_step, -num_step:0, -num_step:0]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[np.shape(new_mask)[0] - 1, :, :]) or
                    any(new_mask[:, 0, :]) or
                    any(new_mask[:, :, 0])):
                wrapping_mask[0:num_step, -num_step:, -num_step:] = (
                    logical_or(wrapping_mask[0:num_step, -num_step:, -num_step:], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=end, y=0, and z=0')
    # Check the vertex where x=end, y=0, and z=end.
    if any(original_mask[end_x, :, :]) or any(original_mask[:, 0, :]) or any(original_mask[:, :, end_z]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[end_x:end_x + num_step, -num_step:0, end_z:end_z + num_step]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[np.shape(new_mask)[0] - 1, :, :]) or
                    any(new_mask[:, 0, :]) or
                    any(new_mask[:, :, np.shape(new_mask)[2] - 1])):
                wrapping_mask[0:num_step, -num_step:, 0:num_step] = (
                    logical_or(wrapping_mask[0:num_step, -num_step:, 0:num_step], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=end, y=0, and z=end')
    # Check the vertex where x=end, y=end, and z=0.
    if any(original_mask[end_x, :, :]) or any(original_mask[:, end_y, :]) or any(original_mask[:, :, 0]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[end_x:end_x + num_step, end_y:end_y + num_step, -num_step:0]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[np.shape(new_mask)[0] - 1, :, :]) or
                    any(new_mask[:, np.shape(new_mask)[1] - 1, :]) or
                    any(new_mask[:, :, 0])):
                wrapping_mask[0:num_step, 0:num_step, -num_step:] = (
                    logical_or(wrapping_mask[0:num_step, 0:num_step:, -num_step:], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=end, y=end, and z=0')
    # Check the vertex where x=end, y=end, and z=end.
    if any(original_mask[end_x, :, :]) or any(original_mask[:, end_y, :]) or any(original_mask[:, :, end_z]):
        wrapping_failed = True
        for num_step in num_step_list:
            x, y, z = np.ogrid[end_x:end_x + num_step, end_y:end_y + num_step, end_z:end_z + num_step]
            new_mask = is_voxel_inside(x, y, z, voxel_size, func, **kwargs)
            if not (any(new_mask[np.shape(new_mask)[0] - 1, :, :]) or
                    any(new_mask[:, np.shape(new_mask)[1] - 1, :]) or
                    any(new_mask[:, :, np.shape(new_mask)[2] - 1])):
                wrapping_mask[0:num_step, 0:num_step, 0:num_step] = (
                    logical_or(wrapping_mask[0:num_step, 0:num_step, 0:num_step], new_mask))
                wrapping_failed = False
                break
        if wrapping_failed:
            raise RuntimeError(wrapping_failed_msg % 'vertex where x=end, y=end, and z=end')

    return wrapping_mask
