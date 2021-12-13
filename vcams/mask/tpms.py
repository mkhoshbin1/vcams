"""Functions that describe triply periodic minimal surfaces which
can be used to create boolean masks."""

from abc import ABC, abstractmethod
from numpy import cos, pi, sin


class BaseTpms(ABC):
    """#TODO"""

    @property
    @abstractmethod
    def tpms_id(self):
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def formula(self):
        pass

    @staticmethod
    @abstractmethod
    def func(*args):
        pass


class TpmsSchwarzP(BaseTpms):
    """#TODO"""
    tpms_id = 0
    name = 'Schwarz Primitive (P)'
    formula = r'$\Phi = cos(\frac{2\pi}{l} x) + cos(\frac{2\pi}{l} y) + cos(\frac{2\pi}{l} z) - c$'

    @staticmethod
    def func(x, y, z, l, c):
        p = 2 * pi / l  # Period.
        return cos(p * x) + cos(p * y) + cos(p * z) - c


class TpmsSchwarzD(BaseTpms):
    """#TODO"""
    tpms_id = 1
    name = 'Schwarz Diamond (D)'
    formula = (r'$\Phi = sin(\frac{2\pi}{l} x) sin(\frac{2\pi}{l} y) sin(\frac{2\pi}{l} z)$'
               r'$+ sin(\frac{2\pi}{l} x) cos(\frac{2\pi}{l} y) cos(\frac{2\pi}{l} z)$' '\n'
               r'$+ cos(\frac{2\pi}{l} x) sin(\frac{2\pi}{l} y) cos(\frac{2\pi}{l} z)$'
               r'$+ cos(\frac{2\pi}{l} x) cos(\frac{2\pi}{l} y) sin(\frac{2\pi}{l} z) - c$')

    @staticmethod
    def func(x, y, z, l, c):
        p = 2 * pi / l  # Period.
        return (sin(p * x) * sin(p * y) * sin(p * z) +
                sin(p * x) * cos(p * y) * cos(p * z) +
                cos(p * x) * sin(p * y) * cos(p * z) +
                cos(p * x) * cos(p * y) * sin(p * z) - c)


class TpmsSchwarzG(BaseTpms):
    """#TODO"""
    tpms_id = 2
    name = 'Schwarz Gyroid (G)'
    formula = (r'$\Phi = sin(\frac{2\pi}{l} x) cos(\frac{2\pi}{l} y)$'
               r'$+ sin(\frac{2\pi}{l} y) cos(\frac{2\pi}{l} z)$'
               r'$+ sin(\frac{2\pi}{l} z) cos(\frac{2\pi}{l} x) - c$')

    @staticmethod
    def func(x, y, z, l, c):
        p = 2 * pi / l  # Period.
        return (sin(p * x) * cos(p * y) +
                sin(p * y) * cos(p * z) +
                sin(p * z) * cos(p * x) - c)


def schwarz_p(x, y, z, l, c):
    """Function describing a Schwarz Primitive (P) triply periodic minimal surface.
    See TODO for information regarding usage.
    TODO: add equation.

    Args:
        x (numpy.ndarray): A numpy 1D array of x-coordinates.
        y (numpy.ndarray): A numpy 1D array of y-coordinates.
        z (numpy.ndarray): A numpy 1D array of z-coordinates.
        l (float): Length of the unit cell in all directions.
        c (float): Constant C in the equation.

    Returns: numpy.ndarray
        An array of values which may be negative, zero, or positive.
        If scalar values are passed, a scalar is returned instead of an array.
        See TODO for interpretation of the results.
    """
    p = 2 * pi / l  # Period.
    return cos(p * x) + cos(p * y) + cos(p * z) - c


def schwarz_d(x, y, z, l, c):
    """Function describing a Schwarz Diamond (D) triply periodic minimal surface.
    See TODO for information regarding usage.
    TODO: add equation.

    Args:
        x (numpy.ndarray): A numpy 1D array of x-coordinates.
        y (numpy.ndarray): A numpy 1D array of y-coordinates.
        z (numpy.ndarray): A numpy 1D array of z-coordinates.
        l (float): Length of the unit cell in all directions.
        c (float): Constant C in the equation.

    Returns: numpy.ndarray
        An array of values which may be negative, zero, or positive.
        If scalar values are passed, a scalar is returned instead of an array.
        See TODO for interpretation of the results.
    """
    p = 2 * pi / l  # Period.
    return (sin(p * x) * sin(p * y) * sin(p * z) +
            sin(p * x) * cos(p * y) * cos(p * z) +
            cos(p * x) * sin(p * y) * cos(p * z) +
            cos(p * x) * cos(p * y) * sin(p * z) - c)


def schwarz_g(x, y, z, l, c):
    """Function describing a Schwarz Gyroid (G) triply periodic minimal surface.
    See TODO for information regarding usage.
    TODO: add equation.

    Args:
        x (numpy.ndarray): A numpy 1D array of x-coordinates.
        y (numpy.ndarray): A numpy 1D array of y-coordinates.
        z (numpy.ndarray): A numpy 1D array of z-coordinates.
        l (float): Length of the unit cell in all directions.
        c (float): Constant C in the equation.

    Returns: numpy.ndarray
        An array of values which may be negative, zero, or positive.
        If scalar values are passed, a scalar is returned instead of an array.
        See TODO for interpretation of the results.
    """
    p = 2 * pi / l  # Period.
    return (sin(p * x) * cos(p * y) +
            sin(p * y) * cos(p * z) +
            sin(p * z) * cos(p * x) - c)


# Construct a dictionary of tpms ids and their respective classes.
tpms_dict = dict()
for cls in (TpmsSchwarzP, TpmsSchwarzD, TpmsSchwarzG):
    if cls.tpms_id in tpms_dict.keys():
        raise RuntimeError(('Class %s has a non-unique tpms_id. ' % cls.__name__) +
                           'All ids for the TPMS classes must be rechecked. If you are not the '
                           'developer, contact him. If you have added a new TPMS class, '
                           'check your tpms_id.')
    tpms_dict[cls.tpms_id] = cls
