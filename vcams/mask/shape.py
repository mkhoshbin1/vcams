"""Functions that define geometrical shapes which can be used to create boolean masks.
They must be in the form of TODO."""
import itertools
from abc import ABC, abstractmethod


# TODO: doc all using https://realpython.com/documenting-python-code/#class-docstrings

class Shape(ABC):
    """Abstract base class describing a shape. All shapes must inherit from this class."""

    @property
    @abstractmethod
    def dim(self):
        pass

    @abstractmethod
    def func(self, x, y, z):
        pass


class ShapeArray:
    id_iter = itertools.count()

    def __init__(self, dim):
        """Initialize the shape array.
        Args:
            dim (str): Dimensionality of the shape array which determines the shapes that
                       can be added to the shape array. Valid values are '2D' and '3D'.
        """
        if dim.upper() not in ['2D', '3D']:
            raise ValueError("dim can only be one of '2D' or '3D'.")
        self.dim = dim.upper()
        self.shapes = dict()

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

    def add_shape(self, cls, **kwargs):
        self.check_shape(cls)
        self.add_shape_obj(shape_obj=cls(id=-1, **kwargs))


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
