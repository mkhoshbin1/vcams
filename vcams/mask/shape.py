"""Classes defining geometrical shapes which can be used to create Boolean masks.

The resulting masks can then be used
for manipulating a :class:`~vcams.voxelpart.VoxelPart` instance
using its :meth:`~vcams.voxelpart.VoxelPart.apply_mask` method.
See the :ref:`predefined-shape` section for a complete explanation
of the basic concepts.
"""
from abc import ABC, abstractmethod
from collections.abc import Iterable
from copy import deepcopy
from itertools import count
from typing import Union

import numpy as np
from numpy import logical_or, ndarray, sin, cos, radians, any, logical_and, full, pi, count_nonzero, \
    prod, isscalar, array

from vcams.mask.function import mask_from_function


class BaseShape(ABC):
    """Abstract base class describing a shape.

    All shapes must inherit from this class.
    Subclasses define their dimensionality using the *dim* class attribute
    which can be either be '2D' or '3D',
    and define the level-set function *func* describing the shape in 3D space.
    It must be compatible with :func:`vcams.mask.function.mask_from_function`.
    """

    def __init__(self):
        self.part_shape = None
        self.voxel_size = None
        self.voxel_volume = None
        self.num_workspace_voxels = None
        self._num_true_voxels = None
        self._real_shape_volume = None
        self._shape_volume_fraction = None

    @property
    @abstractmethod
    def dim(self):
        """The dimensionality of the shape. Must be defined by subclasses to be '2D' or '3D'."""
        pass

    @property
    @abstractmethod
    def analytical_volume(self):
        """Volume of the shape calculated using analytical equations.
        For 2D shapes, surface area is returned. This should only be used as an approximation as
        it does not take into account voxelization errors and contacts with the boundary."""
        pass

    @property
    def num_true_voxels(self):
        """Number of *True* voxels in the voxelized shape (:math:`N_{Shape}^{True}`),
        calculated and set by the :meth:`calculate_mask` function.
        It is initially set to *None* which raises an error when accessed."""
        if self._num_true_voxels is None:
            raise RuntimeError('The number of voxels in the object has not been calculated yet. '
                               'Has calculate_mask() been called yet?')
        else:
            return self._num_true_voxels

    @property
    def real_shape_volume(self):
        """Real volume of the voxelized shape calculated as :math:`N_{Shape}^{True} \\times V_{Voxel}`
        where :math:`N_{Shape}^{True}` is :attr:`num_true_voxels`
        and :math:`V_{Voxel}` is the volume of each voxel.

        The :meth:`calculate_mask` function needs to be called first, otherwise an error is raised."""
        return self.num_true_voxels * self.voxel_volume

    @property
    def real_workspace_volume(self):
        """Real volume of the voxelized workspace (the :class:`~.voxelpart.VoxelPart` object)
        containing the shape.
        It is calculated as :math:`\\prod_{i=x,y,z} N_i L_i`
        where for each dimension :math:`i`, :math:`N_i` is the number of voxels
        and :math:`L_i` is the length of voxels in that direction.

        The :meth:`calculate_mask` function needs to be called first, otherwise an error is raised."""
        if self.voxel_volume is None:
            raise RuntimeError("The object's calculate_mask() has not been called yet.")
        else:
            return self.num_workspace_voxels * self.voxel_volume

    @property
    def shape_volume_fraction(self):
        """Volume fraction of the voxelized shape.
        It is calculated as :math:`\\frac{N_{Shape}^{True}}{N_{Workspace}}`
        where :math:`N_{Shape}^{True}` is the number of *True* voxels
        in the shape (See :attr:`num_true_voxels`)
        and :math:`N_{Workspace}` is the total number of voxels in the workspace.
        Size of each voxel is not relevant to the calculation.

        The :meth:`calculate_mask` function needs to be called first, otherwise an error is raised."""
        if self.num_workspace_voxels is None:
            raise RuntimeError("The object's calculate_mask() has not been called yet.")
        else:
            return self.num_true_voxels / self.num_workspace_voxels

    @abstractmethod
    def func(self, x: float | ndarray, y: float | ndarray, z: float | ndarray,
             boundary_on: bool = False) -> float | ndarray:
        """The level-set function describing the shape in 3D space

        It must be compatible with :func:`vcams.mask.function.mask_from_function`.

        Args:
            x: A float or numpy 1D array of x-coordinates.
            y: A float or numpy 1D array of y-coordinates.
            z: A float or numpy 1D array of z-coordinates.
            boundary_on: A boolean specifying whether shape boundary
            must be considered when evaluating the function.
            The boolean itself is added to the equations as a multiplier and
            evaluates to 0 or 1 which allows for a single expression.

        Returns:
            An array of floats which may be negative, zero, or positive.
            If scalar values are passed, a float is returned instead of an array.
            See :ref:`level-set-functions` for interpretation of the results.
        """

    pass

    def calculate_mask(self, part=None,
                       part_shape: tuple[int, int, int] = None,
                       voxel_size: tuple[float, float, float] = None,
                       wrap_mask: bool = False, boundary_on: bool = False) -> ndarray:
        """Calculate the boolean mask based on this shape.
        This is a wrapper for :func:`vcams.mask.function.mask_from_function`.

        Args:
            part (VoxelPart | None): The *VoxelPart* instance based on which a mask is created.
                                     If *None*, *part_shape* and *voxel_size* must be specified
                                     otherwise they are ignored. Defaults to *None*.
            part_shape: A tuple containing three integers which determine
                        the shape of the returned boolean mask.
                        Defaults to *None* and ignored if *part* is passed.
            voxel_size: A tuple containing three floats which determine the size of a voxel
                        in the x, y, and z directions.
                        Defaults to *None* and ignored if *part* is passed.
            wrap_mask: If set to True, the shape's function is wrapped around
                       the boundaries of the working space.
                       This is useful for periodic structures, but is computationally expensive.
            boundary_on: A boolean specifying whether shape boundary
                         must be considered when evaluating the function.

        Returns:
            A numpy ndarray with a dtype of bool representing the current shape.
        """

        # Set part_shape and voxel_size.
        if part:
            part_shape = part.size
            voxel_size = part.voxel_size
        self.part_shape = part_shape
        self.voxel_size = voxel_size

        # Shape mask is calculated here but is not stored to save memory.
        shape_mask = mask_from_function(part=None, wrap_mask=wrap_mask, mask_shape=part_shape,
                                        voxel_size=voxel_size, func=self.func, boundary_on=boundary_on,
                                        do_log=False)
        self._num_true_voxels = count_nonzero(shape_mask)
        # Calculate shape properties related to voxel_size and part shape.
        if self.dim == '2D':
            self.voxel_volume = prod(voxel_size[:2])
            self.num_workspace_voxels = prod(part_shape[:2])
        else:
            self.voxel_volume = prod(voxel_size)
            self.num_workspace_voxels = prod(part_shape)
        return shape_mask


class ShapeArray:
    """Class for an array of shapes where each shape's parameters and location is predefined.
    The array may contain any number of shapes of any class as long as they
    are subclasses of :class:`.shape.BaseShape` and have the same *dim* attribute.
    """

    def __init__(self, dim: str, part=None,
                 part_shape: tuple[int, int] | tuple[int, int, int] = None,
                 voxel_size: tuple[float, float] | tuple[float, float, float] = None,
                 is_mask_calculation_lazy: bool = True, wrap_mask: bool = False):
        """Constructor for the *ShapeArray* class.

        Args:
            dim: Dimensionality of the shape array which determines the shapes that
                 can be added to the shape array. Valid values are '2D' and '3D'.
            part (VoxelPart | None): The *VoxelPart* instance based on which the shape array is created.
                                     If *None*, *part_shape* and *voxel_size* must be specified,
                                     otherwise they are ignored. Defaults to *None*.
            part_shape: A tuple containing two or three integers which determine
                        the shape of the returned boolean mask.
                        Defaults to *None* and ignored if *part* is passed.
            voxel_size: A tuple containing two or three floats which determine the size of a voxel
                        in the x, y, and z directions.
                        Defaults to *None* and ignored if *part* is passed.
            is_mask_calculation_lazy: If True, the instance's private *_mask* property is updated
                                      only when necessary which greatly improves performance.
                                      Otherwise, it is updated everytime a shape is added to the array.
            wrap_mask: If set to True, the shapes' function is wrapped around
                       the boundaries of the working space, enabling periodic structures.
        """
        if dim.upper() not in ['2D', '3D']:
            raise ValueError("dim can only be one of '2D' or '3D'.")
        self.dim = dim.upper()
        """Dimensionality of the *ShapeArray* instance which determines the shapes that
           can be added to the shape array.
           It is when creating the instance and must not be changed."""

        if part:
            self.part_name = part.name
            self.part_shape = part.size
            self.voxel_size = part.voxel_size
            self.base_mask = (part.data == 0)
            self._part_log_file_path = part._log_file_path  # noqa: PyProtectedMember
        else:
            if (part_shape is None) or (voxel_size is None):
                raise ValueError('The part argument is not specified,'
                                 'therefore both part_shape and voxel_size must be specified.')
            self.part_name = None
            """Name of the part for which the *ShapeArray* instance is created.
            If a pert is not passed, it is set to *None* and it is not used."""
            self.part_shape = array(part_shape)
            """See :meth:`.__init__`."""
            self.voxel_size = array(voxel_size)
            """See :meth:`.__init__`."""
            self.base_mask = full(part_shape, False, dtype=bool)
            """A Boolean mask for the part which contains the background where the shapes are dispersed.
            If a VoxelPart instance is passed, its nonzero elements are considered occupied,
            otherwise a blank mask is used.
            Also in the child :class:`~.shape_dispersion.ShapeDispersionArray` class,
            the boundary pixels, as determined by the *num_bound_pixels* parameter,
            are considered occupied."""
            self._part_log_file_path = None

        # Validate and fix part_shape and voxel_size.
        if self.part_shape.size not in [2, 3]:
            raise ValueError(f'part_shape must have 2 or 3 elements, '
                             f'but it has {self.part_shape.size}.')
        if self.voxel_size.size not in [2, 3]:
            raise ValueError(f'voxel_size must have 2 or 3 elements, '
                             f'but it has {self.voxel_size.size}.')
        if dim.upper() == '2D':
            self.part_shape = self.part_shape[:2]
            self.voxel_size = self.voxel_size[:2]
        else:
            if self.part_shape.size != 3:
                raise ValueError(f'The shape array is defined as 3D, '
                                 f'but part_shape has {self.part_shape.size} elements.')
            if self.voxel_size.size != 3:
                raise ValueError(f'The shape array is defined as 3D, '
                                 f'but voxel_size has {self.voxel_size.size} elements.')
        self.part_volume = prod(self.part_shape * self.voxel_size)

        self.is_mask_calculation_lazy = is_mask_calculation_lazy
        """See :meth:`.__init__`."""
        self.wrap_mask = wrap_mask
        """See :meth:`.__init__`."""
        self._deferred_masks = []
        # Private attribute for masks that are have not been calculated
        # in the _calculate_mask method due to is_mask_calculation_lazy being True.
        # They will be included and this list will be emptied when necessary.
        self._mask = None  # Private attribute for the mask property.
        self._full_mask = None  # Private attribute for the _full_mask property.
        self.shapes = dict()
        """A dictionary containing the shapes in the instance.
        Keys are integer shape IDs, and values are subclasses of :class:`.shape.BaseShape`."""

        self._backup_dict = dict()
        """A dictionary containing the state of the instance
        which is used by :meth:`_backup_state` and :meth:`_restore_state`.
        It should not be used directly."""

    def __len__(self):
        return len(self.shapes)

    id_iter: iter = count()
    """An iterable keeping track of the number of shapes in the ShapeArray."""

    @property
    def mask(self):
        """A Boolean mask representing the union (logical OR) of the shapes in ShapeArray.
        This is guaranteed to be up-to-date.
        """
        if self._deferred_masks or (self._mask is None):
            self._calculate_mask(shape_id=self._deferred_masks)
            # Updates both self._mask and self._full_mask.
        return self._mask

    @property
    def full_mask(self):
        """A Boolean containing both the background and current dispersed shapes.
        It is a union (logical OR) of the ShapeArray's :attr:`base_mask` and :attr:`mask` attributes
        and is stored to reduce repetitive computations. This is guaranteed to be up-to-date.
        """
        if self._deferred_masks or (self._mask is None):
            self._calculate_mask(shape_id=self._deferred_masks)
            # Updates both self._mask and self._full_mask.
        return self._full_mask

    @property
    def shape_array_volume_fraction(self):
        """Ratio of the occupied (*True*) voxels in the instance
        to the instance's total number of voxels.
        This only includes the voxels in :attr:`mask` and the voxels
        in the background (:attr:`base_mask`) are not included."""
        return np.count_nonzero(self.mask) / prod(self.part_shape)

    def _check_shape_class(self, shape):
        """Validate the given shape class or instance.
         Currently, only its dimensionality (*dim* attribute)
         is checked against that of the shape array."""
        if shape.dim != self.dim:
            raise ValueError(
                'The specified shape is %s, but the shape array has been defined for %s shapes.'
                % (shape.dim, self.dim))

    def _calculate_mask(self, shape_id: int | Iterable | None = None):
        """Calculate the Boolean mask for the entire ShapeArray or only the given shapes.

        Args:
            shape_id: An integer ID or iterable of IDs of shapes for which Boolean masks
                      need to be calculated and added to the shape.
                      If set to *None*, all shapes will have their Boolean masks recalculated.
                      Defaults to *None*.
        """

        # Make sure there are shapes in the ShapeArray.
        if len(self) == 0:
            self._mask = None
            self._full_mask = None

        if (self._mask is None) or (shape_id is None):  # All masks need to be calculated.
            recalculate_all = True
            # Create an empty boolean array for the mask.
            self._mask = full(self.part_shape, False, dtype=bool)
            # Get id_list from the shapes dictionary.
            id_list = list(self.shapes.keys())
        else:  # Some masks need to be calculated.
            recalculate_all = False
            if isscalar(shape_id):
                shape_id = (shape_id,)
            id_list = shape_id

        # Either way, we iterate over id_list and call logical_or.
        for i in id_list:
            self._mask = logical_or(self._mask,
                                    self.shapes[i].calculate_mask(
                                        part_shape=self.part_shape, voxel_size=self.voxel_size,
                                        wrap_mask=self.wrap_mask))
            try:
                self._deferred_masks.remove(i)
            except ValueError:
                pass

        # If all is calculated, empty _deferred_masks.
        if recalculate_all:
            self._deferred_masks = []

        # Update self._full_mask.
        self._full_mask = logical_or(self._mask, self.base_mask)

    def _add_shape_obj(self, shape_obj: BaseShape):
        """Add an existing shape object to the ShapeArray."""
        idd = next(self.id_iter)
        shape_obj.id = idd
        self.shapes[idd] = shape_obj
        if not self.is_mask_calculation_lazy:
            self._calculate_mask(shape_id=idd)
        else:
            self._deferred_masks.append(idd)

    def _backup_state(self):
        """Backup the state of the instance, so it can be restored later.

        This is a private function intended for use by the methods of
        the :class:`~.shape_dispersion.ShapeDispersionArray` subclass
        and should not be directly called by the users.
        In case of a mistake in the *ShapeArray*, start from scratch."""
        self._backup_dict = dict()  # Remove previous backup.
        self._backup_dict['id_iter'] = deepcopy(self.id_iter)
        self._backup_dict['wrap_mask'] = self.wrap_mask
        self._backup_dict['base_mask'] = ndarray.copy(self.base_mask)
        self._backup_dict['shapes'] = deepcopy(self.shapes)
        if len(self.shapes) == 0:  # Set mask and full_mask the same as self.__init__().
            self._backup_dict['mask'] = None
            self._backup_dict['full_mask'] = None
        else:
            self._backup_dict['mask'] = ndarray.copy(self.mask)
            self._backup_dict['full_mask'] = ndarray.copy(self.full_mask)
        if len(self._deferred_masks) != 0:  # It is emptied by mask() and full_mask().
            raise RuntimeError("The instance's _deferred_masks attribute"
                               "is not an empty list, but it should be.")

    def _restore_state(self, backup_dict=None):
        """Restore the state of the instance to the previous backup.

        This is a private function intended for use by the methods of
        the :class:`~.shape_dispersion.ShapeDispersionArray` subclass
        and should not be directly called by the users.
        In case of a mistake in the *ShapeArray*, start from scratch.

        Args:
            backup_dict: The :attr:`_backup_dict` dictionary.
                         If set to *None*, the instance's *_backup_dict* is used.
                         Otherwise, another dictionary can be passed which should
                         ideally be a deep copy of an existing _backup_dict.
        """
        if backup_dict is None:
            backup_dict = self._backup_dict
        if not backup_dict:
            raise RuntimeError("The instance's _backup_dict property is empty."
                               "Has _backup_state() been called before? This may also happen after "
                               "a successful run of ShapeDispersionArray.disperse_shapes().")
        self.id_iter = deepcopy(backup_dict['id_iter'])
        self.wrap_mask = backup_dict['wrap_mask']
        self.base_mask = ndarray.copy(backup_dict['base_mask'])
        if backup_dict['mask'] is None:
            self._mask = None
        else:
            self._mask = ndarray.copy(backup_dict['mask'])
        if backup_dict['mask'] is None:
            self._full_mask = None
        else:
            self._full_mask = ndarray.copy(backup_dict['full_mask'])
        self.shapes = deepcopy(backup_dict['shapes'])

    def add_shape(self, cls, intersect_ok: bool = True, **kwargs) -> bool:
        """Add a shape to the ShapeArray using its class,
        while checking for intersection with other shapes.
        The arguments are passed as *\\*\\*kwargs* and the shape ID is set automatically.

        Args:
            cls: The shape class that should be added.
                 It should be a subclass of :class:`.shape.BaseShape`.
                 Arguments are passed as *kwargs*.
            intersect_ok: Whether intersection of the new shape with the rest is OK.
                          If *True*, shapes are added without checking for intersection.
                          If *False*, the function checks the union (logical OR)
                          of the new shape's Boolean mask and the ShapeArray's :attr:`full_mask`
                          and if they intersect, the shape is not added.
                          Defaults to *True*.
            **kwargs: A dictionary where the keys are the arguments for the shape class
                      and the values are either scalar or dispersion objects
                      from the :mod:`.shape_dispersion` module.

        Returns:
            *True* if the shape was added and *False* otherwise.
        """

        # Validate the shape class.
        self._check_shape_class(cls)
        # Create the new shape object.
        new_shape_obj = cls(id=-1, **kwargs)

        if intersect_ok:
            # Just add the shape.
            self._add_shape_obj(shape_obj=new_shape_obj)
            return True
        else:
            # Calculate the new shape's mask and
            # add only if the shape does not intersect existing shapes or the background.
            new_shape_mask = new_shape_obj.calculate_mask(
                part_shape=self.part_shape, voxel_size=self.voxel_size,
                wrap_mask=self.wrap_mask, boundary_on=True)
            if any(logical_and(self.full_mask, new_shape_mask)):
                # If they intersect, return False for an unsuccessful operation.
                # The shape will be discarded.
                return False
            else:
                # If they don't intersect, return True for a successful operation,
                # and add the shape to the array.
                self._add_shape_obj(shape_obj=new_shape_obj)
                return True

    def remove_shape(self, id_list: int | Iterable[int]):
        """Remove shapes from the :class:`ShapeDispersionArray` instance and update the masks.

        Args:
            id_list: Scalar ID of the shape to be removed, or an iterable of the IDs.
        """

        # Validate id_list.
        if isscalar(id_list):
            id_list = (id_list,)
        for shape_id in id_list:
            if shape_id not in self.shapes.keys():
                raise ValueError(f'{shape_id} is not a valid shape ID.')

        # Delete all shapes from id_list from the shapes dictionary.
        for shape_id in id_list:
            del self.shapes[shape_id]

        # Recalculate self._mask and self._full_mask.
        self._calculate_mask()  # shape_id defaults to None which recalculates all.


class Circle(BaseShape):
    """Class describing a 2D Circle with the implicit equation:

    .. math::
       :label: shape-circle-eq

       (x-x_c)^2 + (y-y_c)^2 - r^2 = 0
    """

    def __init__(self, id: int, xc: float, yc: float, r: float, br: float = 0):
        """
        Args:
            id: ID of the shape which should be must be unique.
            xc: x-coordinate of the center of the circle. It must be positive.
            yc: y-coordinate of the center of the circle. It must be positive.
            r: Radius of the circle. It must be positive.
            br: Radial boundary added to *r* when dispersing the shape. Defaults to 0.
        """
        super().__init__()
        self.id = id
        self.xc = xc
        self.yc = yc
        self.br = br
        if r <= 0:
            raise ValueError(f'r must be positive but is {r:.6f}')
        else:
            self.r = r

    dim: str = '2D'
    """This class attribute means that shape can be used for 2D models."""

    @property
    def analytical_volume(self):
        """Volume of the circle calculated using the analytical equation :math:`\\pi r^2`.
        Because of the voxel meshing, actual volume will be different.
        This should only be used as an approximation as
        it does not take into account voxelization errors and contacts with the boundary.
        Note that the word volume is used instead of surface to simplify the interface."""
        return pi * self.r ** 2

    def func(self, x: float | ndarray, y: float | ndarray, z: float | ndarray,
             boundary_on: bool = False) -> float | ndarray:
        return (x - self.xc) ** 2 + (y - self.yc) ** 2 - (self.r + boundary_on * self.br) ** 2


class Sphere(BaseShape):
    """Class describing a 3D Sphere with the implicit equation:

    .. math::
       :label: shape-sphere-eq

       (x-x_c)^2 + (y-y_c)^2 + (z-z_c)^2 - r^2 = 0
    """

    def __init__(self, id, xc: float, yc: float, zc: float, r: float, br: float = 0):
        """
        Args:
            id: ID of the shape which should be must be unique.
            xc: x-coordinate of the center of the sphere. It must be positive.
            yc: y-coordinate of the center of the sphere. It must be positive.
            zc: y-coordinate of the center of the sphere. It must be positive.
            r: Radius of the sphere. It must be positive.
            br: Radial boundary added to *r* when dispersing the shape. Defaults to 0.
        """
        super().__init__()
        self.id = id
        self.xc = xc
        self.yc = yc
        self.zc = zc
        self.br = br
        if r <= 0:
            raise ValueError(f'r must be positive but is {r:.6f}')
        else:
            self.r = r

    dim: str = '3D'
    """This class attribute means that shape can be used for 3D models."""

    @property
    def analytical_volume(self):
        """Volume of the sphere calculated using the analytical equation
        :math:`\\frac{4}{3} \\pi r ^3`.
        This should only be used as an approximation as
        it does not take into account voxelization errors and contacts with the boundary."""
        return (4 * pi * self.r ** 3) / 3

    def func(self, x: float | ndarray, y: float | ndarray, z: float | ndarray,
             boundary_on: bool = False) -> float | ndarray:
        return (x - self.xc) ** 2 + (y - self.yc) ** 2 + (z - self.zc) ** 2 \
               - (self.r + (boundary_on * self.br)) ** 2


class Cylinder(BaseShape):
    """Class describing a 3D Cylinder with the axis in one of x, y, or z directions.
    """

    def __init__(self, id, dir: str, a: float, b: Union[float, None], c: Union[float, None], r: Union[float, None]):
        """
        Args:
            id:  ID of the shape which should be must be unique.
            dir: Direction of the axis. Can be 'x', 'y', or 'z'.
            a:   x-coordinate of the center of the cylinder or *None* if it's in the direction of axis.
            b:   y-coordinate of the center of the cylinder or *None* if it's in the direction of axis.
            c:   z-coordinate of the center of the cylinder or *None* if it's in the direction of axis.
            r:   Radius of the cylinder.
        """
        super().__init__()
        if dir.lower() not in ('x', 'y', 'z'):
            raise ValueError("dir must be one of 'x', 'y', or 'z'.")
        self.dir = dir.lower()
        self.id = id
        self.a = a
        self.b = b
        self.c = c
        self.r = r

    dim: str = '3D'
    """This class attribute means that shape can be used for 3D models."""

    @property
    def analytical_volume(self):
        raise NotImplementedError('This functionality has not been implemented.')

    def func(self, x: float | ndarray, y: float | ndarray, z: float | ndarray,
             boundary_on: bool = False) -> float | ndarray:
        if self.dir == 'x':
            return (x - x) + (y - self.b) ** 2 + (z - self.c) ** 2 - self.r ** 2
        elif self.dir == 'y':
            return (x - self.a) ** 2 + (y - y) + (z - self.c) ** 2 - self.r ** 2
        elif self.dir == 'z':
            return (x - self.a) ** 2 + (y - self.b) ** 2 + (z - z) - self.r ** 2
        else:
            raise RuntimeError("self.dir is equal to '%s' which is not valid and"
                               "should have been caught in the constructor."
                               "Please contact the author." % self.dir)


class Ellipse(BaseShape):
    """Class describing a 2D Ellipse with the implicit equation:

    .. math::
       :label: shape-ellipse_eq

       \\frac{((x-x_c)\\cos(\\alpha) - (y-y_c)\\sin(\\alpha))^2}{a^2}
       + \\frac{((x-x_c) \\sin(\\alpha) + (y-y_c) \\cos(\\alpha))^2}{b^2}
       - 1 = 0

    Where :math:`(x_c, y_c)` is the center of the ellipse,
    :math:`a` and :math:`b` are the length of the semi-axes along the unrotated x and y axes,
    and :math:`\\alpha` is the rotation of the ellipse around the z-axis.

    Note that :math:`\\alpha` is counterclockwise when viewed in the direction of the z-axis,
    but this is not the default view in most viewers. This means that it may be viewed as clockwise.

    This formula is a simple form of the equations developed for :class:`~Ellipsoid`.
    See the docs for that class for a general ellipsoid.
    """

    def __init__(self, id: int, alpha: float, xc: float, yc: float,
                 a: float, b: float, ba: float = 0, bb: float = 0):
        """
        Args:
            id: ID of the shape which should be must be unique.
            alpha: Counterclockwise rotation of the ellipse around the z-axis.
                   It must be in the range [0, 360] in degrees.
            xc: x-coordinate of the center of the ellipse where semi-axes meet.
            yc: y-coordinate of the center of the ellipse where semi-axes meet.
            a: Semi-axis of the ellipse along the unrotated x-axis. It must be positive.
            b: Semi-axis of the ellipse along the unrotated y-axis. It must be positive.
            ba: Boundary added to *a* when dispersing the shape. Defaults to 0.
            bb: Boundary added to *b* when dispersing the shape. Defaults to 0.
        """
        super().__init__()
        self.id = id
        self.xc = xc
        self.yc = yc
        self.ba = ba
        self.bb = bb
        if a <= 0:
            raise ValueError(f'a must be positive but is {a:.6f}')
        else:
            self.a = a
        if b <= 0:
            raise ValueError(f'b must be positive but is {b:.6f}')
        else:
            self.b = b
        # print(alpha)
        if alpha > 360 or alpha < 0:
            raise ValueError(f'alpha must be in the range [0, 360], but is {alpha:.6f}')
        else:
            self.alpha = radians(alpha)

    dim: str = '2D'
    """This class attribute means that shape can be used for 2D models."""

    @property
    def analytical_volume(self):
        """Volume of the ellipse calculated using the analytical equation :math:`\\pi a b`,
        where :math:`a` and :math:`b` are the semi-axes.
        This should only be used as an approximation as
        it does not take into account voxelization errors and contacts with the boundary.
        Note that the word volume is used instead of surface to simplify the interface."""
        return pi * self.a * self.b

    def func(self, x: float | ndarray, y: float | ndarray, z: float | ndarray,
             boundary_on: bool = False) -> float | ndarray:
        return (
                ((((x - self.xc) * cos(self.alpha) - (y - self.yc) * sin(self.alpha)) ** 2)
                 / (self.a + boundary_on * self.ba) ** 2)
                + ((((x - self.xc) * sin(self.alpha) + (y - self.yc) * cos(self.alpha)) ** 2)
                   / (self.b + boundary_on * self.bb) ** 2)
                - 1)


class EllipseFromAspectRatio(Ellipse):
    """Class describing a 2D Ellipse defined using one axis and the ellipse's aspect ratio.

    See :class:`.Ellipse` for the parent class.
    """

    def __init__(self, id: int, alpha: float, xc: float, yc: float,
                 a: float, aspect_ratio: float, ba: float = 0, bb: float = 0):
        """
        Args:
            id: ID of the shape which should be must be unique.
            alpha: Counterclockwise rotation of the ellipse around the z-axis.
                   It must be in the range [0, 360] in degrees.
            xc: x-coordinate of the center of the ellipse where semi-axes meet.
            yc: y-coordinate of the center of the ellipse where semi-axes meet.
            a: Semi-axis of the ellipse along the unrotated x-axis. It must be positive.
            aspect_ratio: The ratio b/a.
                          The attribute b (the semi-axes along the unrotated y-axis) is
                          calculated as aspect_ratio × a.
            ba: Boundary added to *a* when dispersing the shape. Defaults to 0.
            bb: Boundary added to *b* when dispersing the shape. Defaults to 0.
        """

        # Everything is checked in Ellipse.__init__().
        # We only need to check a and calculate b and then pass it to that function.
        if a <= 0:
            raise ValueError(f'a must be positive but is {a:.6f}')
        if aspect_ratio < 0:
            raise ValueError(f'aspect_ratio must be positive but is {aspect_ratio:.6f}')
        else:
            self.aspect_ratio = aspect_ratio
            b = a * aspect_ratio
        super().__init__(id=id, alpha=alpha, xc=xc, yc=yc,
                         a=a, b=b, ba=ba, bb=bb)


class Ellipsoid(BaseShape):
    """Class describing a triaxial Ellipsoid with rotation and translation.

    The implicit equation for an unrotated ellipsoid in the center is:

    .. math::
       :label: shape-ellipsoid-simple

       \\frac{x}{a^2} + \\frac{y}{b^2} + \\frac{z}{c^2} - 1 = 0

    To rotate the ellipsoid, we need to transform the :math:`xyz` coordinates to the new :math:`x'y'z'` system.
    Three rotations must be applied in the following order:

      - A rotation :math:`\\boldsymbol{R_x}(\\gamma)` about the ellipsoid's x-axis.
      - A rotation :math:`\\boldsymbol{R_y}(\\beta)` about the ellipsoid's y-axis.
      - A rotation :math:`\\boldsymbol{R_z}(\\alpha)` about the ellipsoid's z-axis.

    The combination of these rotations is an intrinsic rotation
    whose Tait–Bryan angles are :math:`\\gamma`, :math:`\\beta`, and :math:`\\alpha`.
    We can represent the complete rotation as:

    .. math::
       :label: shape-ellipsoid-rotation

       \\begin{aligned}
       \\boldsymbol{R} &= \\boldsymbol{R_z}(\\alpha)\\boldsymbol{R_y}(\\beta)\\boldsymbol{R_x}(\\gamma)\\\\[12pt]
       &=
       \\begin{bmatrix}
         \\cos(\\alpha) & -\\sin(\\alpha)  & 0 \\\\
         \\sin(\\alpha) &  \\cos(\\alpha)  & 0 \\\\
         0              & 0                & 1
       \\end{bmatrix}
       \\begin{bmatrix}
         \\cos(\\beta)  & 0 & \\sin(\\beta) \\\\
         0              & 1 & 0             \\\\
         -\\sin(\\beta) & 0 & \\cos(\\beta)
       \\end{bmatrix}
       \\begin{bmatrix}
         1 & 0              & 0               \\\\
         0 & \\cos(\\gamma) & -\\sin(\\gamma) \\\\
         0 & \\sin(\\gamma) &  \\cos(\\gamma)
       \\end{bmatrix} \\\\[12pt]
       &=
       \\begin{bmatrix}
         \\cos(\\alpha)\\cos(\\beta) & \\cos(\\alpha)\\sin(\\beta)\\sin(\\gamma)-\\sin(\\alpha)\\cos(\\gamma) & \\cos(\\alpha)\\sin(\\beta)\\cos(\\gamma)+\\sin(\\alpha)\\sin(\\gamma) \\\\
         \\sin(\\alpha)\\cos(\\beta) & \\sin(\\alpha)\\sin(\\beta)\\sin(\\gamma)+\\cos(\\alpha)\\cos(\\gamma) & \\sin(\\alpha)\\sin(\\beta)\\cos(\\gamma)-\\cos(\\alpha)\\sin(\\gamma) \\\\
         -\\sin(\\beta)      & \\cos(\\beta)\\sin(\\gamma)                    & \\cos(\\beta)\\cos(\\gamma)
       \\end{bmatrix}\\\\
       \\end{aligned}

    The main goal is to find the state of a point :math:`P(x,y,z)` with regards to the transformed ellipsoid.
    To do that, the coordinates of :math:`P` must undergo the same transformation as the ellipsoid.
    This means that first it must be translated by the vector :math:`(x_c, y_c, z_c)`,
    and then the rotation :math:`\\boldsymbol{R}` must be applied to it.
    The formula for this transformation is:

    .. math::
       :label: shape-ellipsoid-pdot-transform

       \\begin{bmatrix}x'\\\\y'\\\\z'\\end{bmatrix}
       =\\boldsymbol{R}(\\alpha, \\beta, \\gamma)\\begin{bmatrix}x-x_c\\\\y-y_c\\\\z-z_c\\end{bmatrix}

    Now that we have :math:`P'(x',y',z')`, we can rewrite Eq. :eq:`shape-ellipsoid-simple` for :math:`P'`:

    .. math::
       :label: shape-ellipsoid-pdot-eq

       \\frac{x'}{a^2} + \\frac{y'}{b^2} + \\frac{z'}{c^2} - 1 = 0

    The actual implementation is a little different.
    Using Eqs. :eq:`shape-ellipsoid-rotation` and :eq:`shape-ellipsoid-pdot-transform`,
    and MATLAB's Symbolic Math Toolbox,
    the expressions for each of :math:`x'`, :math:`y'`, and :math:`z'` are found.
    This allows us to use the transformed coordinates :math:`P'(x',y',z')`
    to evaluate Eq. :eq:`shape-ellipsoid-pdot-eq`.

    The reason for this different approach lies in the complex vectorization
    performed in :mod:`~vcams.mask.function` module.
    """

    def __init__(self, id: int, alpha: float, beta: float, gamma: float,
                 xc: float, yc: float, zc: float,
                 a: float, b: float, c: float,
                 ba: float = 0, bb: float = 0, bc: float = 0):
        """
        Args:
            id: ID of the shape which should be must be unique.
            alpha: Rotation of the ellipsoid about its z-axis. It must be in the range [0, 360] degrees.
            beta: Rotation of the ellipsoid around its y-axis. It must be in the range [0, 180] degrees.
            gamma: Rotation of the ellipsoid around its x-axis. It must be in the range [0, 360] degrees.
            xc: x-coordinate of the center of the ellipsoid where semi-axes meet.
            yc: y-coordinate of the center of the ellipsoid where semi-axes meet.
            zc: z-coordinate of the center of the ellipsoid where semi-axes meet.
            a: Semi-axis of the ellipsoid along the unrotated x-axis. It must be positive.
            b: Semi-axis of the ellipsoid along the unrotated y-axis. It must be positive.
            c: Semi-axis of the ellipsoid along the unrotated z-axis. It must be positive.
            ba: Boundary added to *a* when dispersing the shape. Defaults to 0.
            bb: Boundary added to *b* when dispersing the shape. Defaults to 0.
            bc: Boundary added to *c* when dispersing the shape. Defaults to 0.
        """
        super().__init__()
        self.id = id
        self.xc = xc
        self.yc = yc
        self.zc = zc
        self.ba = ba
        self.bb = bb
        self.bc = bc
        if a <= 0:
            raise ValueError(f'a must be positive but is {a:.6f}')
        else:
            self.a = a
        if b <= 0:
            raise ValueError(f'b must be positive but is {b:.6f}')
        else:
            self.b = b
        if c <= 0:
            raise ValueError(f'c must be positive but is {c:.6f}')
        else:
            self.c = c
        if alpha > 360 or alpha < 0:
            raise ValueError(f'alpha must be in the range [0, 360], but is {alpha:.6f}')
        else:
            self.alpha = radians(alpha)
        if beta > 180 or beta < 0:
            raise ValueError(f'beta must be in the range [0, 180], but is {beta:.6f}')
        else:
            self.beta = radians(beta)
        if gamma > 360 or gamma < 0:
            raise ValueError(f'gamma must be in the range [0, 360], but is {gamma:.6f}')
        else:
            self.gamma = radians(gamma)

    dim: str = '3D'
    """This class attribute means that shape can be used for 3D models."""

    @property
    def analytical_volume(self):
        """Volume of the ellipsoid calculated using the analytical equation
        :math:`\\frac{4}{3}\\pi a b c`,
        where :math:`a`, :math:`b`, and :math:`c` are the semi-axes.
        This should only be used as an approximation as
        it does not take into account voxelization errors and contacts with the boundary."""
        return (4 * pi * self.a * self.b * self.c) / 3

    def func(self, x: float | ndarray, y: float | ndarray, z: float | ndarray,
             boundary_on: bool = False) -> float | ndarray:
        # Apply the translation.
        xx = x - self.xc
        yy = y - self.yc
        zz = z - self.zc

        # Apply the rotation.
        xxx = (xx * cos(self.alpha) * cos(self.beta)
               - yy * (cos(self.gamma) * sin(self.alpha) - cos(self.alpha) * sin(self.gamma) * sin(self.beta))
               + zz * (sin(self.gamma) * sin(self.alpha) + cos(self.gamma) * cos(self.alpha) * sin(self.beta))
               )
        yyy = (xx * cos(self.beta) * sin(self.alpha)
               + yy * (cos(self.gamma) * cos(self.alpha) + sin(self.gamma) * sin(self.alpha) * sin(self.beta))
               - zz * (cos(self.alpha) * sin(self.gamma) - cos(self.gamma) * sin(self.alpha) * sin(self.beta))
               )
        zzz = -xx * sin(self.beta) + yy * cos(self.beta) * sin(self.gamma) + zz * cos(self.gamma) * cos(self.beta)

        # Evaluate the ellipsoid function.
        return ((xxx ** 2 / ((self.a + boundary_on * self.ba) ** 2))
                + (yyy ** 2 / ((self.b + boundary_on * self.bb) ** 2))
                + (zzz ** 2 / ((self.c + boundary_on * self.bc) ** 2)) - 1)
