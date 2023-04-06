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

import numpy as np
from numpy import logical_or, ndarray, sin, cos, radians, array, diagflat, sum

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
            # TODO: add definition of level set (https://en.wikipedia.org/wiki/Level_set)
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
    """Class describing a 2D Circle with the implicit equation:

    .. math::
       (x-a)^2 + (y-b)^2 - r^2 = 0
    """

    def __init__(self, id: int, a: float, b: float, r: float):
        """
        Args:
            id: ID of the shape which should be must be unique.
            a: x-coordinate of the center of the circle. It must be positive.
            b: y-coordinate of the center of the circle. It must be positive.
            r: Radius of the circle. It must be positive.
        """
        self.id = id
        if a <= 0:
            raise ValueError(f'a must be positive but is {a:.6f}')
        else:
            self.a = a
        if b <= 0:
            raise ValueError(f'b must be positive but is {b:.6f}')
        else:
            self.b = b
        if r <= 0:
            raise ValueError(f'r must be positive but is {r:.6f}')
        else:
            self.r = r

    dim: str = '2D'
    """This class attribute means that shape can be used for 2D models."""

    def func(self, x: Union[float, ndarray],
             y: Union[float, ndarray], z: Union[float, ndarray]) -> Union[float, ndarray]:
        return (x - self.a) ** 2 + (y - self.b) ** 2 - self.r ** 2


class Sphere(BaseShape):
    """Class describing a 3D Sphere with the implicit equation:

    .. math::
       (x-a)^2 + (y-b)^2 + (z-c)^2 - r^2 = 0
    """

    def __init__(self, id, a: float, b: float, c: float, r: float):
        """
        Args:
            id: ID of the shape which should be must be unique.
            a: x-coordinate of the center of the sphere. It must be positive.
            b: y-coordinate of the center of the sphere. It must be positive.
            c: y-coordinate of the center of the sphere. It must be positive.
            r: Radius of the sphere. It must be positive.
        """
        self.id = id
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
        if r <= 0:
            raise ValueError(f'r must be positive but is {r:.6f}')
        else:
            self.r = r

    dim: str = '3D'
    """This class attribute means that shape can be used for 3D models."""

    def func(self, x: Union[float, ndarray],
             y: Union[float, ndarray], z: Union[float, ndarray]) -> Union[float, ndarray]:
        return (x - self.a) ** 2 + (y - self.b) ** 2 + (z - self.c) ** 2 - self.r ** 2


class Cylinder(BaseShape):
    """Class describing a 3D Cylinder with the axis in one of x, y, or z directions.
    """

    # TODO: add cylinder formula in a table.
    # TODO: change formula to equation in docs.
    # TODO: This can probably optimized by using multiple classes and selecting the appropriate one.
    # TODO: See if you can cylinder with general axis direction.
    # TODO: We work with right cylinders. (https://www.math.net/cylinder) document this.
    # TODO: 2D cylinder (rectangle)
    # TODO: capped cylinder (half-circle vs line vs infinite)
    # TODO: update predefined structures to add new shapes.

    def __init__(self, id, dir: str, a: float, b: Union[float, None], c: Union[float, None], r: Union[float, None]):
        """
        Args:
            id:  ID of the shape which should be must be unique.
            dir: Direction of the axis. Can be 'x', 'y', or 'z'.
            a:   x-coordinate of the center of the cylinder or *None* if it's in the direction of axis.
            b:   y-coordinate of the center of the cylinder or *None* if it's in the direction of axis.
            c:   y-coordinate of the center of the cylinder or *None* if it's in the direction of axis.
            r:   Radius of the cylinder.
        """
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

    def func(self, x: Union[float, ndarray],
             y: Union[float, ndarray], z: Union[float, ndarray]) -> Union[float, ndarray]:
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

    def __init__(self, id: int, alpha: float, xc: float, yc: float, a: float, b: float):
        """
        Args:
            id: ID of the shape which should be must be unique.
            a: semi-axis of the ellipse along the unrotated x-axis. It must be positive.
            b: semi-axis of the ellipse along the unrotated y-axis. It must be positive.
            alpha: Counterclockwise rotation of the ellipse around the z-axis. It must be in the range [0, 360] in degrees.
            xc: x-coordinate of the center of the ellipse where semi-axes meet.
            yc: y-coordinate of the center of the ellipse where semi-axes meet.
        """
        self.id = id
        self.xc = xc
        self.yc = yc
        if a <= 0:
            raise ValueError(f'a must be positive but is {a:.6f}')
        else:
            self.a = a
        if b <= 0:
            raise ValueError(f'b must be positive but is {b:.6f}')
        else:
            self.b = b
        if alpha > 360 or alpha < 0:
            raise ValueError(f'alpha must be in the range [0, 360], but is {alpha:.6f}')
        else:
            self.alpha = radians(alpha)

    dim: str = '2D'
    """This class attribute means that shape can be used for 2D models."""

    def func(self, x: Union[float, ndarray],
             y: Union[float, ndarray], z: Union[float, ndarray]) -> Union[float, ndarray]:
        return (((((x - self.xc) * cos(self.alpha) - (y - self.yc) * sin(self.alpha)) ** 2) / self.a ** 2)
                + ((((x - self.xc) * sin(self.alpha) + (y - self.yc) * cos(self.alpha)) ** 2) / self.b ** 2)
                - 1)


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

    def __init__(self, id: int, a: float, b: float, c: float,
                 xc: float, yc: float, zc: float,
                 alpha: float, beta: float, gamma: float):
        """
        Args:
            id: ID of the shape which should be must be unique.
            a: semi-axis of the ellipsoid along the unrotated x-axis. It must be positive.
            b: semi-axis of the ellipsoid along the unrotated y-axis. It must be positive.
            c: semi-axis of the ellipsoid along the unrotated z-axis. It must be positive.
            xc: x-coordinate of the center of the ellipsoid where semi-axes meet.
            yc: y-coordinate of the center of the ellipsoid where semi-axes meet.
            zc: z-coordinate of the center of the ellipsoid where semi-axes meet.
            alpha: Rotation of the ellipsoid about its z-axis. It must be in the range [0, 360] degrees.
            beta: Rotation of the ellipsoid around its y-axis. It must be in the range [0, 180] degrees.
            gamma: Rotation of the ellipsoid around its x-axis. It must be in the range [0, 360] degrees.
        """
        self.id = id
        self.xc = xc
        self.yc = yc
        self.zc = zc
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

    def func(self, x: Union[float, ndarray],
             y: Union[float, ndarray], z: Union[float, ndarray]) -> Union[float, ndarray]:
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
        return (xxx ** 2 / (self.a ** 2)) + (yyy ** 2 / (self.b ** 2)) + (zzz ** 2 / (self.c ** 2)) - 1
