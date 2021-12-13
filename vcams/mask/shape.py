"""Functions that define geometrical shapes which can be used to create boolean masks.
They must be in the form of TODO."""
import itertools
from abc import ABC, abstractmethod

# TODO: doc all using https://realpython.com/documenting-python-code/#class-docstrings
from numpy import logical_or

from vcams.mask.function import mask_from_function


class Shape(ABC):
    """Abstract base class describing a shape. All shapes must inherit from this class."""

    # TODO: implement buffer zone.

    @property
    @abstractmethod
    def dim(self):
        pass

    @abstractmethod
    def func(self, x, y, z):
        pass

    def calculate_mask(self, part_shape, voxel_size):
        return mask_from_function(mask_shape=part_shape, func=self.func, voxel_size=voxel_size)


class ShapeArray:
    id_iter = itertools.count()

    def __init__(self, dim, part_shape, voxel_size, is_mask_calculation_lazy=True):
        """Initialize the shape array.
        Args:
            dim (str): Dimensionality of the shape array which determines the shapes that
                       can be added to the shape array. Valid values are '2D' and '3D'.
            is_mask_calculation_lazy (bool): # TODO.
        """
        if dim.upper() not in ['2D', '3D']:
            raise ValueError("dim can only be one of '2D' or '3D'.")
        self.dim = dim.upper()
        self.part_shape = part_shape  # TODO: add voxelpart_obj as arg.
        self.voxel_size = voxel_size
        self.is_mask_calculation_lazy = is_mask_calculation_lazy
        self._ignored_masks = []
        self._mask = None
        self.shapes = dict()

    def __len__(self):
        return len(self.shapes)

    @property
    def mask(self):
        if self._ignored_masks or (self._mask is None):
            self.calculate_mask(shape_id=self._ignored_masks)
        return self._mask

    def check_shape(self, shape):
        """Check the given shape class or instance to make sure its dim matches the shape array."""
        if shape.dim != self.dim:
            raise ValueError(
                'The specified shape is %s, but the shape array has been defined for %s shapes.'
                % (shape.dim, self.dim))

    def add_shape_obj(self, shape_obj):
        self.check_shape(shape_obj)
        id = next(self.id_iter)
        shape_obj.id = id
        self.shapes[id] = shape_obj
        if not self.is_mask_calculation_lazy:
            self.calculate_mask(shape_id=id)
        else:
            self._ignored_masks.append(id)

    def add_shape(self, cls, **kwargs):
        self.check_shape(cls)
        self.add_shape_obj(shape_obj=cls(id=-1, **kwargs))

    def calculate_mask(self, shape_id=None):
        if (self._mask is None) or (shape_id is None):
            if len(self) == 0:
                raise ValueError('The boolean mask cannot be calculated because the shape array '
                                 'is empty.')
            # All masks need to be calculated.
            self._mask = self.shapes[0].calculate_mask(self.part_shape, self.voxel_size)
            if len(self) > 1:
                id_list = list(self.shapes.keys())
                id_list.remove(0)
                for i in id_list:
                    self._mask = logical_or(self._mask,
                                            self.shapes[i].calculate_mask(
                                               self.part_shape, self.voxel_size))
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
                                           self.part_shape, self.voxel_size))
                self._ignored_masks.remove(i)


class Circle(Shape):
    """Class describing a 2D Circle."""
    dim = '2D'

    def __init__(self, id, a, b, r):
        """Initialize the circle.
        Args:
            id: ID of the shape which must be unique.
            a (float): x-coordinate of the center of the circle.
            b (float): y-coordinate of the center of the circle.
            r (float): Radius of the circle.
        """
        self.id = id
        self.a = a
        self.b = b
        self.r = r

    def func(self, x, y, z):
        """Function returning the value of the circle equation for a point (x,y,z).
        Args:
            x (float | numpy.ndarray): A float or numpy 1D array of x-coordinates.
            y (float | numpy.ndarray): A float or numpy 1D array of y-coordinates.
            z (float | numpy.ndarray): A float or numpy 1D array of z-coordinates
                                       which must be passed but is not used.
        Returns:
            float | numpy.ndarray : An array of values which may be negative, zero, or positive.
                                    If scalar values are passed, a float is returned instead of
                                    an array. See TODO for interpretation of the results.
        """
        return (x - self.a) ** 2 + (y - self.b) ** 2 - self.r ** 2


class Sphere(Shape):
    """Class describing a 3D sphere."""
    dim = '3D'

    def __init__(self, id, a, b, c, r):
        """Initialize the sphere.
        Args:
            id: ID of the shape which must be unique.
            a (float): x-coordinate of the center of the sphere.
            b (float): y-coordinate of the center of the sphere.
            c (float): z-coordinate of the center of the sphere.
            r (float): Radius of the sphere.
        """
        self.id = id
        self.a = a
        self.b = b
        self.c = c
        self.r = r

    def func(self, x, y, z):
        """Function returning the value of the sphere equation for a point (x,y,z).
        Args:
            x (float | numpy.ndarray): A float or numpy 1D array of x-coordinates.
            y (float | numpy.ndarray): A float or numpy 1D array of y-coordinates.
            z (float | numpy.ndarray): A float or numpy 1D array of z-coordinates
        Returns:
            float | numpy.ndarray : An array of values which may be negative, zero, or positive.
                                    If scalar values are passed, a float is returned instead of
                                    an array. See TODO for interpretation of the results.
        """
        return (x - self.a) ** 2 + (y - self.b) ** 2 + (z - self.c) ** 2 - self.r ** 2
