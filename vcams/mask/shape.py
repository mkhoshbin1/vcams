"""Functions that define geometrical shapes which can be used to create boolean masks.
They must be in the form of TODO."""


def circle(x, y, z, a, b, r):
    """Function describing a circle. See TODO for information regarding usage.
    TODO: add equation.

    Args:
        x (numpy.ndarray): A numpy 1D array of x-coordinates.
        y (numpy.ndarray): A numpy 1D array of y-coordinates.
        z (numpy.ndarray): A numpy 1D array of z-coordinates.
                           This is not used, but must be passed to the function.
        a (float): x-coordinate of the center of the circle.
        b (float): y-coordinate of the center of the circle.
        r (float): Radius of the circle.

    Returns: numpy.ndarray
        An array of values which may be negative, zero, or positive.
        If scalar values are passed, a scalar is returned instead of an array.
        See TODO for interpretation of the results.
    """
    return (x - a) ** 2 + (y - b) ** 2 - r ** 2


def sphere(x, y, z, a, b, c, r):
    """Function describing a sphere. See TODO for information regarding usage.
    TODO: add equation.

    Args:
        x (numpy.ndarray): A numpy 1D array of x-coordinates.
        y (numpy.ndarray): A numpy 1D array of y-coordinates.
        z (numpy.ndarray): A numpy 1D array of z-coordinates.
        a (float): x-coordinate of the center of the sphere.
        b (float): y-coordinate of the center of the sphere.
        c (float): z-coordinate of the center of the sphere.
        r (float): Radius of the sphere.

    Returns: numpy.ndarray
        An array of values which may be negative, zero, or positive.
        If scalar values are passed, a scalar is returned instead of an array.
        See TODO for interpretation of the results.
    """
    return (x - a) ** 2 + (y - b) ** 2 + (z - c) ** 2 - r ** 2