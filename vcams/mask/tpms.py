"""Functions that describe triply periodic minimal surfaces which
can be used to create boolean masks."""

from numpy import cos, pi, sin


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
    return (sin(p * x) * cos(p * y)+
            sin(p * y) * cos(p * z) +
            sin(p * z) * cos(p * x) - c)

