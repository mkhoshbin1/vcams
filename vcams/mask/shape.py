"""Classes defining geometrical shapes which can be used to create boolean masks.

These resulting mask can then be used
for manipulating :class:`~vcams.voxelpart.VoxelPart` object
using its :meth:`~vcams.voxelpart.VoxelPart.apply_mask` method.
See the :ref:`predefined-shape` section for a complete explanation
of the basic concepts.
"""
from itertools import count
from abc import ABC, abstractmethod
from typing import Union

from numpy import logical_or, ndarray

from vcams.mask.function import mask_from_function


class BaseShape(ABC):
    """Abstract base class describing a shape.

    All shapes must inherit from this class.
    Subclasses define their dimensionality using the *dim* class attribute
    which can be either be '2D' or '3D',
    and define the level set function *func* describing the shape in 3D space.
    It must be compatible with :func:`vcams.mask.function.mask_from_function`.
    """
    # TODO: implement buffer zone.
    @property
    @abstractmethod
    def dim(self):
        """The dimensionality of the shape. Must be defined by subclasses to be '2D' or '3D'."""
        pass

    @abstractmethod
    def func(self, x: Union[float, ndarray],
             y: Union[float, ndarray], z: Union[float, ndarray]) -> Union[float, ndarray]:
        """The level set function *func* describing the shape in 3D space

        It must be compatible with :func:`vcams.mask.function.mask_from_function`.

        Args:
            x: A float or numpy 1D array of x-coordinates.
            y: A float or numpy 1D array of y-coordinates.
            z: A float or numpy 1D array of z-coordinates.

        Returns:
            An array of floats which may be negative, zero, or positive.
            If scalar values are passed, a float is returned instead of an array.
            See TODO for interpretation of the results.
        """
    pass

    def calculate_mask(self, part_shape: tuple[int, int, int],
                       voxel_size: tuple[float, float, float]) -> ndarray:
        """Calculate the boolean mask based on this shape.
        This is a wrapper for :func:`vcams.mask.function.mask_from_function`.

        Args:
            part_shape: A tuple containing three integers which determine
                        the shape of the returned boolean mask. Ignored if *part* is passed.
            voxel_size: A tuple containing three floats which determine the size of a voxel
                        in the x, y, and z directions. Ignored if *part* is passed.

        Returns:
            A numpy ndarray with a dtype of bool representing the current shape.
        """
        return mask_from_function(part=None, mask_shape=part_shape, voxel_size=voxel_size, func=self.func)


class ShapeArray:
    """Class for an array of shapes.
    The array may contain any number of shapes of any class as long as they have the same *dim* attribute.
    """
    def __init__(self, dim: str, part=None,
                 mask_shape: tuple[int, int, int] = None,
                 voxel_size: tuple[float, float, float] = None,
                 is_mask_calculation_lazy: bool = True):
        """
        Args:
            part (VoxelPart | None): The VoxelPart object (TODO) based on which the ShapeArray is created.
                                     If None, *mask_shape* and *voxel_size* must be specified.
            dim: Dimensionality of the shape array which determines the shapes that
                 can be added to the shape array. Valid values are '2D' and '3D'.
            is_mask_calculation_lazy: If True, the ShapeArray's private *_mask* property is updated
                                      only when necessary which greatly improves performance.
                                      Otherwise, it is updated everytime a shape is added to the array.
            mask_shape: A tuple containing three integers which determines
                        the shape of the returned boolean mask. Ignored if *part* is passed.
            voxel_size: A tuple containing three floats which determine the size of a voxel
                        in the x, y, and z directions. Ignored if *part* is passed.
        """
        if dim.upper() not in ['2D', '3D']:
            raise ValueError("dim can only be one of '2D' or '3D'.")
        self.dim = dim.upper()
        if part:
            self.mask_shape = part.size
            self.voxel_size = part.voxel_size
        else:
            self.mask_shape = mask_shape
            self.voxel_size = voxel_size
        self.is_mask_calculation_lazy = is_mask_calculation_lazy
        self._ignored_masks = []
        self._mask = None
        self.shapes = dict()

    def __len__(self):
        return len(self.shapes)

    id_iter: iter = count()
    """An iterable keeping track of the number of shapes in the ShapeArray."""

    @property
    def mask(self):
        """The boolean mask representing the union (logical OR) of the shapes in ShapeArray.
        This is guaranteed to be up-to-date.
        """
        if self._ignored_masks or (self._mask is None):
            self._calculate_mask(shape_id=self._ignored_masks)
        return self._mask

    def add_shape_obj(self, shape_obj):
        """Add an existing shape object to the ShapeArray."""
        self._check_shape(shape_obj)
        idd = next(self.id_iter)
        shape_obj.id = idd
        self.shapes[idd] = shape_obj
        if not self.is_mask_calculation_lazy:
            self._calculate_mask(shape_id=idd)
        else:
            self._ignored_masks.append(idd)

    def add_shape(self, cls, **kwargs):
        """Add a shape to the ShapeArray using its class.
         The arguments are passed as *\*\*kwargs* and the shape ID is set automatically.
         """
        self._check_shape(cls)
        self.add_shape_obj(shape_obj=cls(id=-1, **kwargs))

    def _calculate_mask(self, shape_id=None):
        """Calculate the mask for the entire ShapeArray or only a single shape."""
        if (self._mask is None) or (shape_id is None):
            if len(self) == 0:
                raise ValueError('The boolean mask cannot be calculated because the shape array '
                                 'is empty.')
            # All masks need to be calculated.
            self._mask = self.shapes[0].calculate_mask(self.mask_shape, self.voxel_size)
            if len(self) > 1:
                id_list = list(self.shapes.keys())
                id_list.remove(0)
                for i in id_list:
                    self._mask = logical_or(self._mask,
                                            self.shapes[i].calculate_mask(
                                               self.mask_shape, self.voxel_size))
        else:
            # Only the shape with shape_id needs to be added to the mask.
            for i in list(shape_id):
                if i not in self.shapes.keys():
                    raise ValueError('shape_id %i is not in the shape array.')
                if i not in self._ignored_masks:
                    raise ValueError('shape_id %i in not one of the ignored masks. This means '
                                     'that either it has already been accounted for or you are '
                                     'truing to recalculate the mask for that shape. Either way, '
                                     'you should do a complete recalculation of the mask.')
                self._mask = logical_or(self._mask,
                                        self.shapes[i].calculate_mask(
                                           self.mask_shape, self.voxel_size))
                self._ignored_masks.remove(i)

    def _check_shape(self, shape):
        """Check the given shape class or instance to make sure its dim matches the shape array."""
        if shape.dim != self.dim:
            raise ValueError(
                'The specified shape is %s, but the shape array has been defined for %s shapes.'
                % (shape.dim, self.dim))


class Circle(BaseShape):
    """Class describing a 2D Circle with the formula:

    .. math::
       (x-a)^2 + (y-b)^2 - r^2 = 0
    """
    def __init__(self, id: int, a: float, b: float, r: float):
        """
        Args:
            id: ID of the shape which should be must be unique.
            a: x-coordinate of the center of the circle.
            b: y-coordinate of the center of the circle.
            r: Radius of the circle.
        """
        self.id = id
        self.a = a
        self.b = b
        self.r = r

    dim: str = '2D'
    """This class attribute means that shape can be used for 2D models."""

    def func(self, x: Union[float, ndarray],
             y: Union[float, ndarray], z: Union[float, ndarray]) -> Union[float, ndarray]:
        return (x - self.a) ** 2 + (y - self.b) ** 2 - self.r ** 2


class Sphere(BaseShape):
    """Class describing a 3D Sphere with the formula:

    .. math::
       (x-a)^2 + (y-b)^2 + (z-c)^2 - r^2 = 0
    """
    def __init__(self, id, a: float, b: float, c: float, r: float):
        """
        Args:
            id: ID of the shape which should be must be unique.
            a: x-coordinate of the center of the sphere.
            b: y-coordinate of the center of the sphere.
            c: y-coordinate of the center of the sphere.
            r: Radius of the sphere.
        """
        self.id = id
        self.a = a
        self.b = b
        self.c = c
        self.r = r

    dim: str = '3D'
    """This class attribute means that shape can be used for 3D models."""

    def func(self, x: Union[float, ndarray],
             y: Union[float, ndarray], z: Union[float, ndarray]) -> Union[float, ndarray]:
        return (x - self.a) ** 2 + (y - self.b) ** 2 + (z - self.c) ** 2 - self.r ** 2
