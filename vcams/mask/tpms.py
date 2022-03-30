"""Classes defining Triply Periodic Minimal Surfaces (TPMS)
which can be used to create boolean masks.

These resulting mask can then be used
for manipulating :class:`~vcams.voxelpart.VoxelPart` object
using its :meth:`~vcams.voxelpart.VoxelPart.apply_mask` method.
See the :ref:`predefined-tpms` section for a complete explanation
of the basic concepts.
"""
from abc import ABC, abstractmethod
from numpy import cos, pi, sin, ndarray


class BaseTpms(ABC):
    """Abstract base class describing a Triply Periodic Minimal Surface (TPMS).
    Note that the subclasses will be static.

    All TPMS classes must inherit from this class.
    Subclasses define the level set function *func* describing the shape in 3D space,
    and the three attributes *name*, *tpms_id*, and *formula* which are used by PyQt
    for the GUI.
    """
    @property
    @abstractmethod
    def name(self):
        """Name of the TPMS which is used in the GUI."""
        pass

    @property
    @abstractmethod
    def tpms_id(self):
        """An integer id that is unique to this TPMS class and is used in the GUI."""
        pass

    @property
    @abstractmethod
    def formula(self):
        """Formula of the TPMS which must be an inline latex math
        compatible with PyQt and is used in the GUI."""
        pass

    @staticmethod
    @abstractmethod
    def func(*args):
        """The level set function *func* describing the surface in 3D space.
        It must be compatible with :func:`vcams.mask.function.mask_from_function`.
        """
        pass


class TpmsSchwarzP(BaseTpms):
    """Static class describing a Schwarz Primitive (P) triply periodic minimal surface
    with the following equation:

    .. math::
       \\Phi = cos(\\frac{2\pi}{l}x) + cos(\\frac{2\pi}{l}y) + cos(\\frac{2\pi}{l}z) - c = 0
    """
    @staticmethod
    def func(x: ndarray, y: ndarray, z: ndarray, l: float, c: float) -> ndarray:  # noqa: E741
        """Function describing a Schwarz Primitive (P) triply periodic minimal surface.

        Args:
            x: A numpy 1D array of x-coordinates.
            y: A numpy 1D array of y-coordinates.
            z: A numpy 1D array of z-coordinates.
            l: Length of the unit cell in all directions.
            c: Constant C in the equation.

        Returns:
            An array of floats which may be negative, zero, or positive.
            If scalar values are passed, a float is returned instead of an array.
            See TODO for interpretation of the results.
        """
        p = 2 * pi / l  # Period.
        return cos(p * x) + cos(p * y) + cos(p * z) - c

    tpms_id: int = 0
    name: str = 'Schwarz Primitive (P)'
    formula: str = r'$\Phi = cos(\frac{2\pi}{l} x) + cos(\frac{2\pi}{l} y) + cos(\frac{2\pi}{l} z) - c$'


class TpmsSchwarzD(BaseTpms):
    """Static class describing a Schwarz Diamond (D) triply periodic minimal surface
    with the following equation:

    .. math::
       \\Phi = \\enspace &sin(\\frac{2\pi}{l}x) \\ sin(\\frac{2\pi}{l}y) \\ sin(\\frac{2\pi}{l}z)\\\\
                     +\\ &sin(\\frac{2\pi}{l}x) \\ cos(\\frac{2\pi}{l}y) \\ cos(\\frac{2\pi}{l}z)\\\\
                     +\\ &cos(\\frac{2\pi}{l}x) \\ sin(\\frac{2\pi}{l}y) \\ cos(\\frac{2\pi}{l}z)\\\\
                     +\\ &cos(\\frac{2\pi}{l}x) \\ cos(\\frac{2\pi}{l}y) \\ sin(\\frac{2\pi}{l}z) - c = 0
    """
    @staticmethod
    def func(x, y, z, l, c):  # noqa: E741
        """Function describing a Schwarz Diamond (D) triply periodic minimal surface.

        Args:
            x: A numpy 1D array of x-coordinates.
            y: A numpy 1D array of y-coordinates.
            z: A numpy 1D array of z-coordinates.
            l: Length of the unit cell in all directions.
            c: Constant C in the equation.

        Returns:
            An array of floats which may be negative, zero, or positive.
            If scalar values are passed, a float is returned instead of an array.
            See TODO for interpretation of the results.
        """
        p = 2 * pi / l  # Period.
        return (sin(p * x) * sin(p * y) * sin(p * z) +
                sin(p * x) * cos(p * y) * cos(p * z) +
                cos(p * x) * sin(p * y) * cos(p * z) +
                cos(p * x) * cos(p * y) * sin(p * z) - c)

    tpms_id: int = 1
    name: str = 'Schwarz Diamond (D)'
    formula: str = (r'$\Phi = sin(\frac{2\pi}{l} x) sin(\frac{2\pi}{l} y) sin(\frac{2\pi}{l} z)$' '\n'
                    r'$+ sin(\frac{2\pi}{l} x) cos(\frac{2\pi}{l} y) cos(\frac{2\pi}{l} z)$' '\n'
                    r'$+ cos(\frac{2\pi}{l} x) sin(\frac{2\pi}{l} y) cos(\frac{2\pi}{l} z)$' '\n'
                    r'$+ cos(\frac{2\pi}{l} x) cos(\frac{2\pi}{l} y) sin(\frac{2\pi}{l} z) - c$')


class TpmsSchwarzG(BaseTpms):
    """Static class describing a Schwarz Gyroid (G) triply periodic minimal surface
    with the following equation:

    .. math::
       \\Phi = \\enspace &sin(\\frac{2\pi}{l}x) \\ cos(\\frac{2\pi}{l}y)\\\\
                     +\\ &sin(\\frac{2\pi}{l}y) \\ cos(\\frac{2\pi}{l}z)\\\\
                     +\\ &sin(\\frac{2\pi}{l}z) \\ cos(\\frac{2\pi}{l}x) - c = 0
    """
    @staticmethod
    def func(x, y, z, l, c):  # noqa: E741
        """Function describing a Schwarz Gyroid (G) triply periodic minimal surface.

        Args:
            x: A numpy 1D array of x-coordinates.
            y: A numpy 1D array of y-coordinates.
            z: A numpy 1D array of z-coordinates.
            l: Length of the unit cell in all directions.
            c: Constant C in the equation.

        Returns:
            An array of floats which may be negative, zero, or positive.
            If scalar values are passed, a float is returned instead of an array.
            See TODO for interpretation of the results.
        """
        p = 2 * pi / l  # Period.
        return (sin(p * x) * cos(p * y) +
                sin(p * y) * cos(p * z) +
                sin(p * z) * cos(p * x) - c)

    tpms_id: int = 2
    name: str = 'Schwarz Gyroid (G)'
    formula: str = (r'$\Phi = sin(\frac{2\pi}{l} x) cos(\frac{2\pi}{l} y)$' '\n'
                    r'$+ sin(\frac{2\pi}{l} y) cos(\frac{2\pi}{l} z)$' '\n'
                    r'$+ sin(\frac{2\pi}{l} z) cos(\frac{2\pi}{l} x) - c$')


# Construct a dictionary of tpms ids and their respective classes.
tpms_dict: dict = dict()
"""A dictionary mapping tpms ids to their respective classes, used for the GUI."""
for cls in (TpmsSchwarzP, TpmsSchwarzD, TpmsSchwarzG):
    if cls.tpms_id in tpms_dict.keys():
        raise RuntimeError(('Class %s has a non-unique tpms_id. ' % cls.__name__) +
                           'All ids for the TPMS classes must be rechecked. If you are not the '
                           'developer, contact him. If you have added a new TPMS class, '
                           'check your tpms_id.')
    tpms_dict[cls.tpms_id] = cls
