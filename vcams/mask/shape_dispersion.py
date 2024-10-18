"""Classes used for dispersing shapes inside a :class:`~vcams.voxelpart.VoxelPart`."""

import logging
import time
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Iterable, Callable

import matplotlib
import matplotlib.pyplot as plt
import numpy as np  # This is intentional to simplify the formulae.
from numpy import random, max, abs, isscalar, sum, inf, ndarray
from scipy.stats import truncnorm

from .shape import ShapeArray
from ..logger_conf import setup_dispersion_logger, LogWithoutFormatContext

matplotlib.use('TkAgg')  # From https://stackoverflow.com/a/73788178/7180705
logger = logging.getLogger(__name__)


class TooManyDispersionAttemptsError(Exception):
    pass


class TooManyDispersionTrialsError(Exception):
    pass


class TooManyDispersionGenerationsError(Exception):
    pass


class TooMuchDeviationError(Exception):
    pass


class TooManyValueGenerationAttemptsError(Exception):
    pass


class SuitableNumShapesNotFoundError(Exception):
    pass


class BaseListDispersion(ABC):
    """Abstract base class for dispersions that contain a list of values.
    Subclasses are used for defining various dispersions.
    """

    @property
    def actual_mean(self):
        """Actual mean of the values in the instance."""
        return self.values.mean()

    @property
    def actual_std(self):
        """Actual standard deviation of the values in the instance."""
        return self.values.std()

    @property
    def actual_variance(self):
        """Actual variance of the values in the instance."""
        return self.values.var()

    @property
    def _repr_float_length(self):
        """The optimal number of floating point decimal places.
        Used for representing the instance in text format."""
        if len(self) == 0:
            return 0
        else:
            repr_float_length = len(str(int(max(abs((self.actual_mean, self.actual_std,
                                                     self.actual_variance)))))) + 1
        return repr_float_length + 4  # Add four decimal places.

    def __iter__(self):
        return self.values.__iter__()

    def __getitem__(self, index):
        return self.values[index]

    def __len__(self):
        return len(self.values)

    def __mul__(self, other):
        return ManualListDispersion(self.values * other)

    def __init__(self):
        """Constructor for the :class:`BaseListDispersion` abstract base class.
        It should be called by subclasses."""
        self.values = np.array([])
        """A numpy array containing the values in the instance."""

    @staticmethod
    def _set_plot_legend():
        """Set the legend for the plots created by the :meth:`BaseListDispersion.plot` method."""
        plt.gca().legend(frameon=False, prop={'family': 'monospace'},  # bbox_to_anchor=(1.04, 1),
                         fontsize=2, numpoints=1, loc='upper right')
        # plt.tight_layout()

    def plot(self, num_bins: int, plot_actual_normal_curve: bool = False):
        """Plot a histogram of the dispersion object.

        Args:
            num_bins: Number of bins for the histogram of actual values.
            plot_actual_normal_curve: Whether the actual normal distribution of the values should be plotted.
                                      Defaults to False.
        """
        if self.__len__() < 1:
            raise ValueError('The object is empty. Has it been initialized?')
        plt.plot([], [], ' ', label=f'$\\bf{{Dispersion Type: {type(self).__name__}}}$')
        plt.hist(self.values, num_bins, density=True, label='Actual Values Histogram')
        plt.xlabel('Value')
        plt.ylabel('Frequency')

        if plot_actual_normal_curve:
            x = np.linspace(-3 * self.actual_std + self.actual_mean, 3 * self.actual_std + self.actual_mean, 100)
            y = (np.exp(-np.power((x - self.actual_mean) / self.actual_std, 2.0) / 2)
                 / (np.sqrt(2.0 * np.pi) * self.actual_std))
            plt.plot(x, y, label='Normal Distribution (Actual)')

        self._set_plot_legend()
        plt.show()


class ManualListDispersion(BaseListDispersion):
    """A Dispersion list defined manually using a list.
    This is simply a list and is only created to have a uniform naming.
    """

    def __init__(self, values: Iterable | ndarray):
        """Constructor for the :class:`ManualListDispersion` class.
        It takes an iterable, creates a *NumPy* array from it, and then flattens it.
        """
        super().__init__()
        self.values = np.array(values).flatten()

    def __repr__(self):
        return (f'{self.__class__.__name__} Instance:\n'
                f'    Number of Values: {len(self.values)}\n'
                f'    Actual Mean:      {self.actual_mean:{self._repr_float_length}.4f}\n'
                f'    Actual STD:       {self.actual_std:{self._repr_float_length}.4f}\n'
                f'    Actual Variance:  {self.actual_variance:{self._repr_float_length}.4f}')

    # noinspection PyMethodOverriding
    def plot(self, num_bins: int):
        """Plot a histogram of the dispersion object.

        Args:
            num_bins: Number of bins for the histogram of actual values.
        """
        BaseListDispersion.plot(self, num_bins, plot_actual_normal_curve=True)
        plt.plot([], [], ' ', label=self.__repr__().split('\n', 1)[1])
        BaseListDispersion._set_plot_legend()
        plt.show()


class BaseNormalDistributionDispersion(BaseListDispersion):
    """Abstract base class for dispersion classes that generate a list of values
    with a `normal (Gaussian) distribution <https://en.wikipedia.org/wiki/Normal_distribution>`_.

    Instances are defined using a target mean and standard deviation.
    Afterwards, a list is created using a random number generator.
    Instances are iterable and iterating over them is the same
    as iterating over their *values* attribute.

    If the number of values in an instance is specified at creation,
    the list of values will be populated. Otherwise, generation of the list will be deferred.
    At any point, the instances :meth:`generate_values` method can be called to
    create any number of values which will replace existing values.

    This is an abstract base class and cannot be instantiated.
    Child classes define their own :meth:`generate_values` method which determines
    the details of how the list of values is generated.
    """

    def __init__(self, target_mean: float, target_std: float,
                 num_values: int = None, max_absolute_pct_error: int = 10):
        """Constructor for the :class:`BaseNormalDistributionDispersion` class.

        Args:
            target_mean: Target mean for the randomly generated values.
                         Actual mean will be stored in *actual_mean*.
            target_std: Target standard deviation for the randomly generated values.
                        Actual standard deviation will be stored in *actual_mean*.
            num_values: Number of values to be generated and stored in the *values* property.
                        Defaults to *None* which defers value generation and
                        requires a call to :meth:`generate_values` to generate the values.
            max_absolute_pct_error: See :meth:`BaseNormalDistributionDispersion._qc_dispersion`.
                                    Defaults to 10%.
        """
        super().__init__()

        self.target_mean = target_mean
        """See :meth:`__init__`'s arguments."""
        self.target_std = target_std
        """See :meth:`__init__`'s arguments."""
        self.max_absolute_pct_error = max_absolute_pct_error
        """See :meth:`__init__`'s arguments."""

        if num_values is not None:
            self.generate_values(num_values)
        else:
            self.values = []

    @property
    def _repr_float_length(self):
        """The optimal number of floating point decimal places.
        Used for representing the instance in text format."""
        # This is overridden from BaseListDispersion.
        if len(self) == 0:
            repr_float_length = len(str(int(max(abs((self.target_mean, self.target_std)))))) + 1
        else:
            repr_float_length = len(str(int(max(abs((self.target_mean, self.actual_mean,
                                                     self.target_std, self.actual_std,
                                                     self.actual_variance)))))) + 1
        return repr_float_length + 4  # Add four decimal places.

    def __repr__(self):
        if len(self) == 0:
            return (f'{self.__class__.__name__} Instance:\n'
                    f'    The instance is empty. Use generate_values(num_values) to populate it.\n'
                    f'    Target Mean:      {self.target_mean:{self._repr_float_length}.4f}\n'
                    f'    Target STD:       {self.target_std:{self._repr_float_length}.4f}')
        else:
            mean_pct_error = 100 * (self.actual_mean - self.target_mean) / self.target_mean
            std_pct_error = 100 * (self.actual_std - self.target_std) / self.target_std
            return (f'{self.__class__.__name__} Instance:\n'
                    f'    Number of Values: {len(self.values)}\n'
                    f'    Target Mean:      {self.target_mean:{self._repr_float_length}.4f}\n'
                    f'    Actual Mean:      {self.actual_mean:{self._repr_float_length}.4f} ({mean_pct_error:+.4f}%)\n'
                    f'    Target STD:       {self.target_std:{self._repr_float_length}.4f}\n'
                    f'    Actual STD:       {self.actual_std:{self._repr_float_length}.4f} ({std_pct_error:+.4f}%)\n'
                    f'    Actual Variance:  {self.actual_variance:{self._repr_float_length}.4f}')

    # noinspection PyMethodOverriding
    def plot(self, num_bins: int, plot_actual_normal_curve: bool = False):
        """Plot a histogram of the dispersion object.

        Args:
            num_bins: Number of bins for the histogram of actual values.
            plot_actual_normal_curve: Whether the actual normal distribution of the values should be plotted.
                                      Defaults to False.
        """
        BaseListDispersion.plot(self, num_bins, plot_actual_normal_curve)
        x = np.linspace(-3 * self.target_std + self.target_mean, 3 * self.target_std + self.target_mean, 1000)
        y = (np.exp(-np.power((x - self.target_mean) / self.target_std, 2.0) / 2)
             / (np.sqrt(2.0 * np.pi) * self.target_std))
        plt.plot(x, y, label='Normal Distribution (Target)')
        plt.plot([], [], ' ', label=self.__repr__().split('\n', 1)[1])
        BaseListDispersion._set_plot_legend()
        plt.show()

    @abstractmethod
    def _generate_values_once(self, num_values: int, qc_results=True):
        """Abstract method for generating a single set of random values
        based on the instance's attributes.
        This method can be called as many times as necessary to regenerate the instance's
        *values* list and change its *num_values*.

        Args:
            num_values: Number of values to be generated and stored in the *values* property.
            qc_results: If *True*, the values are quality controlled
                        using :meth:`_qc_dispersion`. Defaults to *True*.
        """
        pass

    def generate_values(self, num_values: int, qc_results=True, max_attempts=10000):
        """Generate values based on the normal dispersion's parameters.

        Args:
            num_values: Number of values to be generated and stored in the *values* property.
            qc_results: If *True*, the values are quality controlled
                        using :meth:`BaseNormalDistributionDispersion._qc_dispersion`.
                        Defaults to *True*.
            max_attempts: The maximum number of attempts for generation of valid values.
                          If exceeded, :class:`TooManyValueGenerationAttemptsError` is raised.
                          Note that some parameters require much more tries
                          because the distribution keeps getting rejected
                          by the quality control process.

        Raises:
            TooManyValueGenerationAttemptsError: Too many attempts were made for value generation.
        """
        for i in range(max_attempts):
            try:
                self._generate_values_once(num_values=num_values, qc_results=qc_results)
                return
            except TooMuchDeviationError:
                continue
        raise TooManyValueGenerationAttemptsError(f'Too many attempts ({max_attempts}) made '
                                                  f'for generating valid values.')

    def _qc_dispersion(self, min_size: int = 0, max_absolute_pct_error: int | None = None):
        """Control the quality of the dispersion using two tests:

        - The number of values in the dispersion must be more than *min_size*. Defaults to 0.
        - The absolute percent error (APE) between target and actual values of mean and standard deviation,
          defined by :math:`|\\frac{x_{actual} - x_{target}}{x_{target}}| \\times 100\\%`,
          must be equal or less than *max_absolute_pct_error*.
          Defaults to *None* which uses the instance's *max_absolute_pct_error*.

          If the instance does not pass QC, :class:`TooMuchDeviationError` is raised.
        """
        if max_absolute_pct_error is None:
            max_absolute_pct_error = self.max_absolute_pct_error

        if len(self) < min_size:
            raise ValueError(f'The dispersion instance does not pass QC '
                             f'because it is too few values ({len(self)}<{min_size}).')
        std_ape = abs((self.actual_std - self.target_std) / self.target_std) * 100
        if std_ape > max_absolute_pct_error:
            raise TooMuchDeviationError(f'The absolute percent error between actual '
                                        f'and target standard deviation is {std_ape:.2f}% '
                                        f'but should be lower than {max_absolute_pct_error}%. '
                                        f'There are {len(self)} values.')
        mean_ape = abs((self.actual_mean - self.target_mean) / self.target_mean) * 100
        if mean_ape > max_absolute_pct_error:
            raise TooMuchDeviationError(f'The absolute percent error between actual '
                                        f'and target mean is {mean_ape:.2f}% '
                                        f'but should be lower than {max_absolute_pct_error}%. '
                                        f'There are {len(self)} values.')


class NormalDistributionDispersion(BaseNormalDistributionDispersion):
    """A dispersion class that generates a list of values with
    a `normal (Gaussian) distribution <https://en.wikipedia.org/wiki/Normal_distribution>`_.

    The generated distribution will be truly normal,
    but may include values that are negative or too small.
    This will cause issues for some purposes such as geometrical features.
    The :class:`TruncatedNormalDistributionDispersion` class
    can fix this problem but its values will not be truly normal.

    This is a subclass of :class:`BaseNormalDistributionDispersion`.
    See its docs for other details.
    """

    def _generate_values_once(self, num_values: int, qc_results=True):
        """Generate a single set of random values with the given mean and standard deviation.
        This method can be called as many times as necessary to regenerate the instance's
        *values* list and change its *num_values*.

        This function uses NumPy's `random.default_rng().normal` function.

        Args:
            num_values: Number of values to be generated and stored in the *values* property.
            qc_results: If *True*, the values are quality controlled
                        using :meth:`~BaseNormalDistributionDispersion._qc_dispersion`.
                        Defaults to *True*.
        """
        if num_values < 1:
            raise ValueError('num_values must be bigger than 0.')
        self.values = random.default_rng().normal(loc=self.target_mean, scale=self.target_std, size=num_values)
        if qc_results:
            self._qc_dispersion()


class TruncatedNormalDistributionDispersion(BaseNormalDistributionDispersion):
    """A dispersion class that generates a list of values with
    a `truncated normal (Gaussian) distribution <https://en.wikipedia.org/wiki/Truncated_normal_distribution>`_.

    A regular normal distribution created by the :class:`NormalDistributionDispersion` class
    has the problem that it may include values that are negative or too small
    which will cause issues for some purposes such as geometrical features.
    This class allows for defining boundaries for the start and end of the distribution
    which solves this problem.
    However, there are two problems:

      1. The results will not be truly normal.
      2. The generated values may not pass the quality control process
         which means that many attempts may be necessary
         when calling the :meth:`~BaseNormalDistributionDispersion.generate_values` method.

    This is a subclass of :class:`BaseNormalDistributionDispersion`.
    See its docs for other details.
    """

    def __init__(self, target_mean: float, target_std: float,
                 bound_a: float = -inf, bound_b: float = inf, num_values: int = None):
        """Constructor for the :class:`TruncatedNormalDistributionDispersion` class.

        Args:
            target_mean: Target mean for the randomly generated values.
                         Actual mean will be stored in *actual_mean*.
            target_std: Target standard deviation for the randomly generated values.
                        Actual standard deviation will be stored in *actual_mean*.
            bound_a:    The beginning of the range from which values should be drawn.
            bound_b:    The end of the range from which values should be drawn.
            num_values: Number of values to be generated and stored in the *values* property.
                        Defaults to *None* which defers value generation and
                        requires a call to :meth:`~BaseNormalDistributionDispersion.generate_values`
                        to generate the values.
        """
        # target_mean and target_std are assigned in super().__init__.
        self.bound_a = bound_a
        """See :meth:`__init__`'s arguments."""
        self.bound_b = bound_b
        """See :meth:`__init__`'s arguments."""
        # Boundaries a and b are around the mean. They must be moved to the real scale.
        self._truncnorm_a = (bound_a - target_mean) / target_std
        self._truncnorm_b = (bound_b - target_mean) / target_std
        super().__init__(target_mean, target_std, num_values)

    def plot(self, num_bins: int, plot_equivalent_normal_curve: bool = True):
        """Plot a histogram of the dispersion object.

        Args:
            num_bins: Number of bins for the histogram of actual values.
            plot_equivalent_normal_curve: Whether an equivalent (untruncated) normal distribution
                                          should be plotted based on the parameters.
                                          Defaults to True.
        """
        BaseListDispersion.plot(self, num_bins)

        x = np.linspace(-3 * self.target_std + self.target_mean, 3 * self.target_std + self.target_mean, 1000)
        y = truncnorm.pdf(x, a=self._truncnorm_a, b=self._truncnorm_b,
                          loc=self.target_mean, scale=self.target_std)
        plt.plot(x, y, label='Truncated Normal Distribution (Target)')
        if plot_equivalent_normal_curve:
            y_eq_normal = (np.exp(-np.power((x - self.target_mean) / self.target_std, 2.0) / 2)
                           / (np.sqrt(2.0 * np.pi) * self.target_std))
            plt.plot(x, y_eq_normal, label='Equivalent Normal Distribution (Target)')

        plt.plot([], [], ' ', label=self.__repr__().split('\n', 1)[1])
        BaseListDispersion._set_plot_legend()
        plt.show()

    def _generate_values_once(self, num_values: int, qc_results=True):
        """Generate a single set of random values based on a truncated normal distribution
        with the given mean and standard deviation.
        This method can be called as many times as necessary to regenerate the instance's
        *values* list and change its *num_values*.

        This function uses SciPy's `stats.truncnorm.rvs` function.

        Args:
            num_values: Number of values to be generated and stored in the *values* property.
            qc_results: If *True*, the values are quality controlled
                        using the :meth:`~BaseNormalDistributionDispersion._qc_dispersion` method.
                        Defaults to *True*.
        """
        # See __init__ for _truncnorm_a and _truncnorm_b.
        self.values = truncnorm.rvs(a=self._truncnorm_a, b=self._truncnorm_b,
                                    loc=self.target_mean, scale=self.target_std,
                                    size=num_values)
        if qc_results:
            self._qc_dispersion()


class RandomDispersion:
    """A dispersion class that generates a single random float value in a half-open interval.

    The constructor (:meth:`__init__`) takes three arguments,
    which are *low*, *high*, and boundary, and then calculates
    :attr:`actual_low` and :attr:`actual_high` using the following equations:

    .. math::

       \\begin{cases}
       \\text{actual_low} &=& \\text{low} &+& \\text{boundary}\\\\
       \\text{actual_high} &=& \\text{high} &-& \\text{boundary}
       \\end{cases}

    This class uses *numpy.random.uniform()* in the half-open interval
    :math:`[\\text{actual_low}, \\text{actual_high})`.

    Instances of this class are callables, meaning that they can be called like a function.
    For example:

    .. code-block:: python

       rand_disp_ins = RandomDispersion(low=2, high=10)
       v1 = rand_disp_ins()  # A random value between 2 and 10.
       v2 = rand_disp_ins()  # Another random value between 2 and 10.

    """

    def __init__(self, low: float, high: float, boundary: float = 0):
        """Constructor for the :class:`RandomDispersion` class.

        Args:
            low: Lower boundary of the output interval.
            high: Upper boundary of the output interval.
            boundary: A boundary applied to the *low* and *high* arguments
                      to calculate :attr:`actual_low` and :attr:`actual_high`.
        """
        self.low = low
        self.high = high
        self.boundary = boundary
        self.actual_low = low + boundary
        """Actual lower boundary from which the random number is generated.
        Values will be equal or greater than this number."""
        self.actual_high = high - boundary
        """Actual upper boundary from which the random number is generated.
        Values will be less than this number."""

    def __call__(self):
        return random.uniform(low=self.actual_low, high=self.actual_high, size=None)

    def __repr__(self):
        return (f'{self.__class__.__name__} Instance:\n'
                f'    Low:         {self.low}\n'
                f'    High:        {self.high}\n'
                f'    Boundary:    {self.boundary}\n'
                f'    Actual Low:  {self.actual_low}\n'
                f'    Actual High: {self.actual_high}\n')

    def plot(self):
        """A nonfunctional method that raises a *NotImplementedError*
        because it is not applicable to the :class:`RandomDispersion` class."""
        raise NotImplementedError('This function is not available for the RandomDispersion class '
                                  'because it only return a random scalar.')


class ShapeDispersionArray(ShapeArray):
    """Class for an array of shapes that are dispersed in the workspace.
    For each shape, its xyz coordinates are randomly assigned
    and the rest of the parameters may be predefined or randomly generated.

    This is, in fact, a subclass of :class:`~.shape.ShapeArray`
    which can disperse shapes inside itself.

    The array may contain any number of shapes of any class as long as they
    are subclasses of :class:`.shape.BaseShape` and have the same *dim* attribute.

    When constructing an instance, a :class:`~vcams.voxelpart.VoxelPart` instance
    can be passed which allows for defining a *background* in the shape array.
    This means that the shapes will only be dispersed in the nonempty regions
    of the *VoxelPart* instance.
    """

    def __init__(self, dim: str, part=None,
                 part_shape: tuple[int, int, int] = None,
                 voxel_size: tuple[float, float, float] = None,
                 wrap_mask: bool = True, num_bound_pixels: int = 0,
                 short_msg: bool = True):
        """Constructor for the *ShapeDispersionArray* class.

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
            wrap_mask: If set to True, the shapes' function is wrapped around
                       the boundaries of the working space, enabling periodic structures.
                       If *wrap_mask* is True, *num_bound_pixels* must be zero.
                       Defaults to True.
            num_bound_pixels: An int specifying the number of pixels to add to the boundary of the base mask.
                              The boundary will become a region that the dispersed shapes cannot touch.
                              If *num_bound_pixels* is non-zero, *wrap_mask* must be False.
                              Defaults to 0.
            short_msg: A boolean specifying whether the placement message should be printed
                       as a single updating line or in many lines with extensive details.
                       Passed to :meth:`._log_placement` Defaults to *True*.
        """

        # Validate the relationship between wrap_mask and num_bound_pixels.
        # The rest is validated when calling super().__init__().
        if wrap_mask and num_bound_pixels != 0:
            raise ValueError('wrap_mask is True and num_bound_pixels is non-zero. This combination in invalid.')

        # Call the parent class's constructor.
        # Note that is_mask_calculation_lazy is set to True.
        super().__init__(dim, part, part_shape, voxel_size,
                         is_mask_calculation_lazy=True, wrap_mask=wrap_mask)

        self.short_msg = short_msg
        """See :meth:`.__init__`."""

        self.shape_requests = []
        """A list of shapes shape classes and related parameters that should be dispersed.
        
        Members of this list are added by the :meth:`add_shape_request` method.
        Each is a list containing the following:
        
          - **cls**: The *class* object for the shape that is requested.
            It is a subclass of :class:`.shape.BaseShape`
            and has the same *dim* attribute (2D or 3D) as the shape array.
            The last two members of the list will be keyword arguments
            that can be used to define the shape. 
          
          - **num_shapes**: Number of requested shapes. This should be an integer.
            If set to *None*, the number can be determined by the object.
            In that case, all members of the list should have *num_shapes* set to *None*.
          
          - **iterable_kwargs**: A dictionary of keyword arguments for *cls*.
            Each dictionary key will be the name of a keyword argument for *cls*,
            and the dictionary value will be the keyword argument's value.
            Here, keys are either iterables or subclasses of :class:`BaseListDispersion`,
            except for :class:`RandomDispersion` which is treated as a scalar.
            Note that the dictionary values should have the same length as *num_shapes*.
          
          - **scalar_kwargs**: A dictionary of keyword arguments for *cls*.
            Each dictionary key will be the name of a keyword argument for *cls*,
            and the dictionary value will be the keyword argument's value.
            Here, keys are either scalars or instances :class:`RandomDispersion`.
            Scalars will be used for all the shapes requested (by this member)
            and instances :class:`RandomDispersion` will be called
            by the appropriate methods to generate random values.
          
        Addition to this list should be done by the :meth:`add_shape_request` method
        and the list is emptied after a successful dispersion.
        Users should not interact with this list. This is not enforced but highly recommended.
        """

        self._dispersion_log_file_path = \
            part._log_file_path.with_stem(part._log_file_path.stem + '_dispersion_log')  # noqa: PyProtectedMember
        self.dispersion_logger = setup_dispersion_logger(part.name, log_file=self._dispersion_log_file_path,
                                                         display_log=True)

        # Add boundary to the base mask so the shapes don't touch the outside.
        if num_bound_pixels:
            self.base_mask[:, :num_bound_pixels] = True
            self.base_mask[:, -num_bound_pixels:] = True
            self.base_mask[:num_bound_pixels, :] = True
            self.base_mask[-num_bound_pixels:, :] = True

    @property
    def num_requested_shapes(self) -> int:
        """Total number of shapes requested in :attr:`shape_requests`.
        This is calculated automatically on the fly.
        If any of the *num_shapes* in *shape_requests* is set to *None*,
        the number -1 is returned."""
        num_shapes_list = [sr[1] for sr in self.shape_requests]
        if None in num_shapes_list:
            return -1
        else:
            return int(sum(num_shapes_list, axis=None))

    def _backup_state(self):
        super()._backup_state()
        self._backup_dict['shape_requests'] = deepcopy(self.shape_requests)

    def _restore_state(self, backup_dict=None):
        super()._restore_state(backup_dict)
        if backup_dict is None:
            backup_dict = self._backup_dict
        self.shape_requests = deepcopy(backup_dict['shape_requests'])

    @staticmethod
    def _test_cls_kwargs(cls, iterable_kwargs, scalar_kwargs):
        """Try to create a shape with a set of iterable_kwargs and scalar_kwargs
        to make sure they are valid. It raises an error if unsuccessful and is otherwise silent.

        This is a method function used by the :meth:`add_shape_request` method
        and should not be directly called by the users."""
        iter0_dict_temp = dict()
        scalar_dict_temp = dict()
        for (k, v) in iterable_kwargs.items():
            if isinstance(v, BaseNormalDistributionDispersion) and (len(v) == 0):
                v.generate_values(1, qc_results=False)  # QC is turned off.
            iter0_dict_temp[k] = v[0]
        for (k, v) in scalar_kwargs.items():
            if isinstance(v, RandomDispersion):
                scalar_dict_temp[k] = v()
            else:
                scalar_dict_temp[k] = v
        try:
            _ = cls(id=-1, **iter0_dict_temp, **scalar_dict_temp)
        except Exception as err:
            exception_msg = (f'The given **kwargs cannot be used with class {cls.__name__}. They are:\n'
                             f'First element of each iterable keyword argument:\n  {iter0_dict_temp}\n'
                             f'Scalar and sample random keyword arguments:\n  {scalar_dict_temp}')
            raise Exception(exception_msg).with_traceback(err.__traceback__)

    def _place_shape_randomly(self, cls, shape_number: int, max_attempts: int,
                              trial_number: int = None, **kwargs):
        """Place a shape in a random position. Placement is tried *max_attempts* number of times
        and if not successful, :class:`TooManyDispersionAttemptsError` is raised.

        This is a private method used by the :meth:`disperse_shapes` method
        and should not be directly called by the users.

        Args:
            cls: The shape class that should be placed. Arguments are passed as *kwargs*.
            shape_number: The number of this shape.
                          This number keeps track of the shapes that are dispersed
                          and is used for logging the progress. it is *not* the shape's eventual ID.
            max_attempts: The maximum number of attempts for placement of a shape.
                          If exceeded, :class:`TooManyDispersionAttemptsError` is raised.
            trial_number: The number for this trial. Used for logging the progress.
            **kwargs:     A dictionary where the keys are the arguments for the shape class
                          and the values are either dispersion objects or scalars.
                          Coordinate arguments should always be passed as :class:`RandomDispersion`
                          instances that are then called to generate a random value for each attempt.
                          This is not enforced.

        Raises:
            TooManyDispersionAttemptsError: Too many attempts were made for this shape.
        """

        # Separate random and scalar kwargs.
        # Note that scalars may have come from an iterable object, but they are scalars now.
        scalar_dict = dict()
        random_object_dict = dict()
        for k, v in kwargs.items():
            if isinstance(v, RandomDispersion):
                random_object_dict[k] = v
            else:  # Assume it's a scalar.
                scalar_dict[k] = v

        # Try to place randomly max_attempts times.
        # Return if successful. Otherwise, raise an error in the end.
        for attempt_number in range(1, max_attempts + 1):
            random_value_dict = dict()
            for k, v in random_object_dict.items():
                random_value_dict[k] = v()  # Note that v (being a RandomDispersion) is *called* here.
            self._log_placement(cls, attempt_number, shape_number, scalar_dict, random_value_dict, trial_number)
            # Try to add a shape to the array. shape_status will be True if successful.
            shape_status = self.add_shape(cls, intersect_ok=False, **scalar_dict, **random_value_dict)
            self._log_shape_placement_status(shape_status)
            if shape_status:
                return
        raise TooManyDispersionAttemptsError(f'Too many dispersion attempts for shape {shape_number}.')

    def _log_placement(self, cls, attempt_number, shape_number, scalar_dict,
                       random_value_dict, trial_number=None):
        """Log the placement of the shape.
        This is a private method used by the :meth:`_place_shape_randomly` method
        and should not be directly called by the users."""
        if trial_number is None:
            trial_str = ''
        else:
            trial_str = f'Trial {trial_number:4d}, '
        shape_num_str = f'Shape {shape_number:{len(str(self.num_requested_shapes))}d}/{self.num_requested_shapes}'
        attempt_num_str = f'Attempt {attempt_number:4d}'
        msg_str = f'{trial_str}{shape_num_str}, {attempt_num_str}'
        if self.short_msg:
            msg_str = msg_str + f', Type {cls.__name__} ... '
        else:
            scalar_items_str = ', '.join(f'{k}={v:2.4f}' for k, v in scalar_dict.items())
            random_items_str = ', '.join(f'{k}={v:2.4f}' for k, v in random_value_dict.items())
            msg_str = msg_str + f', Type {cls.__name__}({scalar_items_str}, {random_items_str}) ... '
        self.dispersion_logger.debug(msg_str)

    def _log_shape_placement_status(self, shape_status):
        """Log the placement status of shape.
        This is a private method used by the :meth:`_place_shape_randomly` method
        and should not be directly called by the users."""
        if shape_status:
            with LogWithoutFormatContext(self.dispersion_logger):
                self.dispersion_logger.debug('Success!\r')
        else:
            with LogWithoutFormatContext(self.dispersion_logger):
                self.dispersion_logger.debug(' Failed!\r')

    def add_shape_request(self, cls, num_shapes: int | None, **kwargs):
        """Add a request for a one or more shapes of a class to be added to the instance.

        Args:
            cls: The shape class that should be placed. Arguments are passed as *kwargs*.
            num_shapes: Number of shapes that are requested with the given arguments.
                        Should either be an integer or *None* so it can be determined using
                        the instance's :meth:`_find_suitable_num_shapes` method.
                        If set to *None*, all other shape requests must also have this argument
                        set to *None*. Defaults to *None*.
            **kwargs: A dictionary where the keys are the arguments for the shape class
                      and the values are either dispersion objects or scalars.
                      The function separates the dictionary into two dictionaries,
                      one containing scalars and the other containing.
                      Note that the length of the iterable dispersion objects
                      must be equal to *num_shapes*.
        """

        # Validate the shape class.
        self._check_shape_class(cls)

        # Split the kwargs dictionary into two groups,
        # that will each be passed to the placement function differently.
        # The keys are the arguments' names.
        # In iterable_kwargs, the value is an iterable whose contents will be passed one by one;
        # and in other_kwargs, the value is a single scalar which will be passed each time.
        iterable_kwargs = dict()
        scalar_kwargs = dict()
        for k, v in kwargs.items():
            if isinstance(v, ManualListDispersion):
                if num_shapes is None:
                    raise ValueError(f'{k} is a ManualListDispersion which is not allowed '
                                     'when num_shapes is None.')
                elif len(v) != num_shapes:
                    raise ValueError(f'{k} is a ManualListDispersion with {len(v)} elements '
                                     f'but num_shapes is {num_shapes}. They should be equal.')
                else:
                    iterable_kwargs[k] = v
            elif isinstance(v, BaseNormalDistributionDispersion):
                if num_shapes is None:  # Values should not be generated for v. Current values are inconsequential.
                    pass
                elif len(v) != 0:  # v is uninitialized and should have its values generated.
                    v.generate_values(num_values=num_shapes)
                else:
                    raise ValueError(f'{k} is an uninitialized subclass of '
                                     f'BaseNormalDistributionDispersion. '
                                     f'Specify num_shapes when defining it. '
                                     f'Did you mean to pass num_shapes=None to the method?')
                iterable_kwargs[k] = v
            elif isscalar(v) or isinstance(v, RandomDispersion):
                scalar_kwargs[k] = v
            else:
                raise ValueError(f'{k} is neither a scalar nor a valid subclass of BaseListDispersion.')

        # Try to create a shape with iterable_kwargs and scalar_kwargs to make sure they're valid.
        ShapeDispersionArray._test_cls_kwargs(cls, iterable_kwargs, scalar_kwargs)

        # Add the shape request as a tuple to the instance's shape_requests list.
        self.shape_requests.append([cls, num_shapes, iterable_kwargs, scalar_kwargs])
        logger.debug(f'Adding a shape request for the {cls.__name__} class.')

    def disperse_shapes(self, max_attempts: int = 5000, max_trials: int = 100, log_main: bool = True):
        """Disperse shapes in the *ShapeDispersionArray* instance according to
        the shape requests. All shape requests are processed
        and then :attr:`shape_requests` is emptied.

        It is necessary for all the members in the instance's :attr:`shape_requests`
        to have valid *num_shapes*, otherwise an error is raised.
        If you need to disperse without knowing the number of shapes
        (based on volume fraction), use the :meth:`disperse_shapes_vf` method instead.

        The function uses the :meth:`_place_shape_randomly` function to place each shape
        in a random position. Placement is tried *max_attempts* number of times
        and if the attempts run out, the *trial* ends and a new trial begins with
        a clean ShapeArray, and the same shapes will be dispersed again.
        If after the given maximum number of trials (*max_trials*) all shapes are not placed,
        :class:`TooManyDispersionTrialsError` will be raised to indicate an error.

        Args:
            max_attempts: The maximum number of attempts for placement of a shape.
                          If exceeded, the trial ends and the process is restarted.
            max_trials:   The maximum number of trials. If exceeded,
                          :class:`TooManyDispersionTrialsError` is raised.
            log_main:     Whether the start and end of dispersion should be logged by the main logger.
                          Defaults to True.

        Raises:
            TooManyDispersionTrialsError: Too many trials were done.
                                          Note that each trials entails many attempts.
        """
        begin_msg = 'Dispersing shapes in the ShapeDispersionArray.'
        self.dispersion_logger.debug(begin_msg + '\n')
        if log_main:
            logger.debug(begin_msg)
        if max_attempts < 1:
            raise ValueError('max_attempts should be >= 1.')
        if max_trials < 1:
            raise ValueError('max_trials should be >= 1.')

        num_shapes_list = [sr[1] for sr in self.shape_requests]
        if None in num_shapes_list:
            raise ValueError(f'Some of the num_shapes in shape_requests are None.'
                             f'The list is: {num_shapes_list}')

        # Backup the state of the ShapeDispersionArray object.
        begin_time = time.perf_counter()
        self._backup_state()
        dispersion_success = False
        for trial_number in range(1, max_trials + 1):
            try:  # Try to run a trial.
                dispersion_success = False
                shape_number = 0
                for sr in self.shape_requests:
                    (cls, num_shapes, iterable_kwargs, scalar_kwargs) = sr
                    # Loop through the list kwargs.
                    for i in range(num_shapes):
                        shape_number += 1
                        # Put the shape's iterable_kwargs into a single dict to be passed as scalars.
                        shape_list_kwargs = dict()
                        for k, v in iterable_kwargs.items():
                            shape_list_kwargs[k] = v[i]
                        # Try to place the shape. Raises TooManyDispersionAttempts if unsuccessful.
                        self._place_shape_randomly(cls, shape_number, max_attempts, trial_number,
                                                   **shape_list_kwargs, **scalar_kwargs)
                # Both loops have run out without error and dispersion is successful.
                dispersion_success = True
                break
            except TooManyDispersionAttemptsError:
                # Too many attempts were made in self._place_shape_randomly().
                # Restore the state of the ShapeDispersionArray object and retry.
                self._restore_state()
        # Either the trial loop has been broken which indicates success,
        # or it has ended which means we have run out of trials without success.
        if dispersion_success:
            elapsed_time = time.perf_counter() - begin_time
            self._log_dispersion_success(elapsed_time, log_main)
            self.shape_requests = []
            self._backup_dict = dict()
        else:
            raise TooManyDispersionTrialsError(f'Dispersion has been unsuccessful after {max_trials} trials.')

    def _log_dispersion_success(self, elapsed_time, log_main):
        """Log the success of the dispersion process."""
        success_msg = (f'{self.num_requested_shapes} shapes dispersed successfully '
                       f'in {elapsed_time:.2f} seconds.')
        self.dispersion_logger.debug(success_msg + '\n')
        if log_main:
            logger.info(success_msg)

    def _find_suitable_num_shapes(self, target_vf: float, vf_tolerance: float,
                                  min_num_shapes: int, max_num_shapes: int,
                                  solver_mode: str = 'BISECTION') -> int:
        """Find the suitable number of shapes for the *ShapeDispersionArray*'s requested shapes.

        This function first makes sure that all the shape requests are without *num_shapes*,
        then finds a suitable number of shapes that satisfies a *target_vf*.
        In the case of multiple requests, an equal number of shapes will be used for all of them.

        Read the documentation for the :meth:`_find_vf_for_shape_number` for more information.
        This is a private method used by the :meth:`disperse_shapes_vf` method
        and should not be directly called by the users.

        Args:
            target_vf: Target volume fraction.
            vf_tolerance: Maximum tolerable difference between the reached volume fraction and *target_vf*.
                          It should be a float greater than 1E-4.
            min_num_shapes: The initial value of *num_shapes* investigated by the function.
            max_num_shapes: The maximum value of *num_shapes* investigated by the function.
            solver_mode: The solver used for finding the suitable number of shapes.
                         If set to *'BRUTE FORCE'*, all values from *min_num_shapes* to *max_num_shapes*
                         are tested and if set to *'BISECTION'*, the bisection method
                         is used to find the suitable value.
                         Defaults to *'BISECTION'* which is faster and more reliable.

        Returns:
            A suitable value for *num_shapes*.

        Raises:
            SuitableNumShapesNotFoundError: If a suitable number of shapes is not found in the given range.
        """
        begin_log_msg = 'Trying to find a suitable number of shapes ' \
                        'for the given shape requests and target volume fraction.'
        self.dispersion_logger.debug(begin_log_msg + '\n')
        logger.info(begin_log_msg)

        # Validate input.
        if target_vf <= 0:
            raise ValueError('target_volume_fraction should be a positive number.')
        if (int(min_num_shapes) != min_num_shapes) or (min_num_shapes < 1):
            raise ValueError(f'min_num_shapes must be an integer greater than 1, but is {min_num_shapes}.')
        if (int(max_num_shapes) != max_num_shapes) or (max_num_shapes < 1):
            raise ValueError(f'max_num_shapes must be an integer greater than 2, but is {max_num_shapes}.')
        if max_num_shapes <= min_num_shapes:
            raise ValueError(f'max_num_shapes must be greater than min_num_shapes.')
        if vf_tolerance < 1E-4:
            raise ValueError('vf_tolerance should be a float greater than 1E-4.')
        if solver_mode.upper() not in ['BRUTE FORCE', 'BISECTION']:
            raise ValueError('Invalid value for solver_mode.')
        # Make sure all num_shapes in the shape requests are None.
        num_shapes_list = [sr[1] for sr in self.shape_requests]
        if not all(ns is None for ns in num_shapes_list):
            raise ValueError(f'Some of the num_shapes in shape_requests are *not* None.'
                             f'If you want to find suitable num_shapes, they should *all* start as None.'
                             f'The list is: {num_shapes_list}')

        with LogWithoutFormatContext(self.dispersion_logger):
            self.dispersion_logger.debug(f' Using the {solver_mode.title()} solver mode.\n')
        line_str = ('=' * 80) + '\n'
        if solver_mode.upper() == 'BRUTE FORCE':
            solver_function = integer_solver_brute_force
        elif solver_mode.upper() == 'BISECTION':
            solver_function = integer_solver_bisection
        else:
            raise RuntimeError('Invalid value for solver_mode. This should have been caught earlier.')

        num_shapes = solver_function(func=self._find_vf_for_shape_number,
                                     a=min_num_shapes, b=max_num_shapes, tolerance=vf_tolerance,
                                     target_vf=target_vf)
        self.dispersion_logger.debug(f'Suitable number of shapes was found '
                                     f'to be {num_shapes}x{len(self.shape_requests)}.\n' + line_str)
        return num_shapes

    def _find_vf_for_shape_number(self, num_shapes: int, target_vf: float) -> float:
        """Calculate the volume fraction (VF) for the *ShapeDispersionArray*'s requested shapes,
        given the input number of shapes and return the difference between the actual and target VF.

        This function checks if all the shape requests are without *num_shapes*,
        then creates the requested shapes in a list.
        In the case of multiple requests each one of them will be created in *equal* numbers.
        Afterwards, the analytical volume of each shape will be calculated
        using the shape's :attr:`~.BaseShape.analytical_volume` property
        and these volume will be added and converted to a total VF.
        Finally, the *target_vf* is subtracted from the actual VF and returned.

        Notes:
            - The shapes created by this function may not be necessarily
              dispersable in a ShapeDispersionArray. This function is only about the VFs.
            - The nature of shape generation is stochastic. This means that no two calls
              will have an equal output. This is generally OK as the results are expected
              within a tolerance.
            - The volume used is the analytical volume of each shape
              which is fast but inaccurate for larger voxel sizes.
            - The volume of each voxel is calculated individually.
              This means that overlapping shapes and contact with the boundary
              will cause different VFs. A different function needs to be used for those cases.

        Args:
            num_shapes: Number of shapes to be created and investigated by the function.
            target_vf: Target volume fraction.

        Returns:
            The difference between the actual VF and *target_vf*.
        """
        # This function is used many times and therefore logs nothing.
        # Validate input.
        if target_vf <= 0:
            raise ValueError('target_volume_fraction should be a positive number.')
        # Make sure all num_shapes in the shape requests are None.
        num_shapes_list = [sr[1] for sr in self.shape_requests]
        if not all(ns is None for ns in num_shapes_list):
            raise ValueError(f'Some of the num_shapes in shape_requests are *not* None.'
                             f'If you want to find suitable num_shapes, they should *all* start as None.'
                             f'The list is: {num_shapes_list}')

        shape_list = []  # Note that this is a simple list and not a ShapeArray instance.
        for sr in self.shape_requests:
            (cls, _, iterable_kwargs, scalar_kwargs) = sr
            # Regenerate the BaseNormalDistributionDispersion subclasses with num_shapes values.
            for k, v in iterable_kwargs.items():
                if isinstance(v, ManualListDispersion):
                    raise ValueError(f'{k} is a ManualListDispersion which is not allowed '
                                     'when finding num_shapes.')
                elif isinstance(v, BaseNormalDistributionDispersion):
                    v.generate_values(num_values=num_shapes)
                else:
                    raise RuntimeError(f'Unexpected type {type(v)} for {k}: {v}.')

            # Create the shapes as single independent instances in shape_list.
            for i in range(num_shapes):
                # Put the shape's kwargs into a single dict to be passed as scalars.
                shape_i_kwargs = dict()
                for k, v in iterable_kwargs.items():
                    shape_i_kwargs[k] = v[i]
                for k, v in scalar_kwargs.items():
                    if isinstance(v, RandomDispersion):
                        shape_i_kwargs[k] = v()
                    else:
                        shape_i_kwargs[k] = v

                # Create the shape.
                # Note that a shape instance is not placed anywhere and simply exists.
                # In fact, the coordinate variable should have a RandomDispersion instance
                # as the value which will raise an error if used.
                # But we only need to calculate the analytical volume so this is OK.
                shape_list.append(cls(id=i + 1, **shape_i_kwargs))

        # Calculate the sum of analytical volumes for the shapes in shape_list.
        total_analytical_volume = sum(i.analytical_volume for i in shape_list)
        # Calculate volume fraction and the difference between it and target_vf.
        current_vf = total_analytical_volume / self.part_volume
        vf_diff = current_vf - target_vf
        self.dispersion_logger.debug(
            f'Tried num_shapes={num_shapes:4d}x{len(self.shape_requests)}, '
            f'Total Vol={total_analytical_volume:10.6f}, '
            f'VF={current_vf:10.6f}, Target VF={target_vf:.6} -> '
            f'Delta VF={vf_diff:+11.6f}\n')
        return vf_diff

    def disperse_shapes_vf(self, target_vf: float, vf_tolerance: float,
                           min_num_shapes: int = 5, max_num_shapes: int = 5000,
                           solver_mode: str = 'BISECTION',
                           max_attempts: int = 5000, max_trials: int = 100,
                           max_generations: int = 100):
        """Disperse shapes in the *ShapeDispersionArray* instance to reach a target volume fraction (VF).
        All shape requests are processed and then :attr:`shape_requests` is emptied.

        Here, all shape requests should have a *num_shapes* value of *None*.
        The function uses the :meth:`_find_suitable_num_shapes` function to find
        a suitable number of shapes (for all requests).

        Then, for *max_generations* number of times, the following is performed:

          1. The random values in shape requests are regenerated.
          2. The :meth:`disperse_shapes` method is used to disperse the shapes.
             Make sure to read that function's documents for its intricacies.
             If the shapes cannot be dispersed, a new generation is started.
          3. If dispersion is successful, the final volume fraction (VF)
             is checked to make sure it is within tolerances.

        Args:
            target_vf: Target volume fraction.
            vf_tolerance: Maximum tolerable difference between the reached volume fraction and *target_vf*.
                          It should be a float greater than 1E-4.
            min_num_shapes: The initial value used to find a suitable *num_shapes*.
            max_num_shapes: The maximum value used for finding a suitable *num_shapes*.
            solver_mode: The solver used for finding the suitable number of shapes.
                         If set to *'BRUTE FORCE'*, all values from *min_num_shapes* to *max_num_shapes*
                         are tested and if set to *'BISECTION'*, the bisection method
                         is used to find the suitable value.
                         Defaults to *'BISECTION'* which is faster and more reliable.
            max_attempts: The maximum number of attempts for placement of a shape.
                          If exceeded, the trial ends and the process is restarted.
            max_trials:   The maximum number of trials for a shape generation attempt.
                          If exceeded, a new shape generation attempt will be made.
            max_generations: Maximum number of shape generation attempts.
                             If exceeded, :class:`TooManyDispersionGenerationsError` is raised.

        Raises:
            TooManyDispersionGenerationsError: Too many trials were done.
                                               Note that each generation entails many trials.
        """
        self.dispersion_logger.debug('Dispersing shapes in the ShapeDispersionArray.\n')
        logger.debug('Dispersing shapes in the ShapeDispersionArray.')
        # Try for max_generations times to find the suitable number of shapes.
        for i in range(max_generations):
            try:
                num_shapes = self._find_suitable_num_shapes(target_vf, vf_tolerance,
                                                            min_num_shapes, max_num_shapes, solver_mode)
                break
            except SuitableNumShapesNotFoundError:
                continue
        # Set num_shapes in all shape requests and regenerate subclasses of BaseNormalDistributionDispersion.
        for sr in self.shape_requests:
            # noinspection PyUnboundLocalVariable
            sr[1] = num_shapes

        self.dispersion_logger.debug(f"Trying to disperse shapes in part '{self.part_name}'.\n"
                                     f"{' ' * 11}Target volume fraction is {target_vf:.6} "
                                     f"and tolerance is {vf_tolerance}.\n"
                                     f"{' ' * 11}Shape requests will be regenerated a maximum of {10} times.\n"
                                     f"{' ' * 11}Each generation will be dispersed for {max_trials} tries,\n"
                                     f"{' ' * 11}in which {max_attempts} placement attempts "
                                     f"will be made for each shape.\n")
        logger.info(f"Trying to disperse shapes in part '{self.part_name}'. "
                    f"Target volume fraction is {target_vf:.6} and tolerance is {vf_tolerance}.")
        # Backup the shape array instance's state.
        # Note that the instance's _backup_dict will be overwritten
        # as part of the process, so we have to create a copy for this loop.
        self._backup_state()
        vf_dispersion_backup = deepcopy(self._backup_dict)
        for gen_number in range(1, max_generations + 1):
            # fix this. it doesn't loop properly.
            # Regenerate all shape requests (subclasses of BaseNormalDistributionDispersion).
            self.dispersion_logger.debug(f'** Generation {gen_number}: Regenerating shape requests ... ')
            for sr in self.shape_requests:
                iterable_kwargs = sr[2]
                for k, v in iterable_kwargs.items():
                    if isinstance(v, BaseNormalDistributionDispersion):
                        v.generate_values(num_values=sr[1])
            with LogWithoutFormatContext(self.dispersion_logger):
                self.dispersion_logger.debug('Done. **\n')

            # Try to disperse this generation of shapes in the structure.
            try:
                self.disperse_shapes(max_attempts=max_attempts, max_trials=max_trials, log_main=False)
            except TooManyDispersionTrialsError:
                self.dispersion_logger.debug(
                    f'Generation {gen_number} could not be dispersed '
                    f'after {max_trials} trials. Regenerating.\n')
                self._restore_state(backup_dict=vf_dispersion_backup)
                continue

            # Compare target VF with the instance's real voxel-based VF.
            vf_diff = abs(self.shape_array_volume_fraction - target_vf)
            if vf_diff <= vf_tolerance:
                vf_dispersion_status = True
                dispersion_status_str = '... Accepted!'
            else:
                vf_dispersion_status = False
                dispersion_status_str = '... Rejected!'

            self.dispersion_logger.debug(
                f"Generation {gen_number} dispersed. "
                f"VF={self.shape_array_volume_fraction:.6f}, "
                f"Target VF={target_vf:.6}, Delta VF={vf_diff:.6f} "
                f"{'<' if vf_dispersion_status else '>'} {vf_tolerance} "
                f"{dispersion_status_str}\n")

            if vf_dispersion_status:
                success_msg = (f'Dispersion based on volume fraction was successful '
                               f'within the given tolerance after {gen_number} generations.')
                self.dispersion_logger.debug(success_msg + '\n')
                logger.info(success_msg)
                return
            else:
                self._restore_state(backup_dict=vf_dispersion_backup)
                continue
        raise TooManyDispersionGenerationsError(f'Dispersion failed after {max_generations} generations.')


def integer_solver_validator(func: Callable, a: int, b: int, tolerance: float):
    """Validate inputs for the integer solver functions.

    Args:
        func: The continuous function :math:`F()` to be solved.
              This function only checks if it is callable.
        a: The start of the range where the search takes place. Should be an integer less than *b*.
        b: The end of the range where the search takes place. Should be an integer greater than *a*.
        tolerance: The tolerance for finding the root of the function. It should be greater than 1E-4.

    Raises:
        ValueError: If any of the input values are invalid.
    """
    if not callable(func):
        raise ValueError(f'func should be a function or a method but its type is {type(func)}')
    if (int(a) != a) or (a < 1):
        raise ValueError(f'a must be an integer greater than 1, but is {a}.')
    if (int(b) != b) or (b < 1):
        raise ValueError(f'b must be an integer greater than 1, but is {b}.')
    if b <= a:
        raise ValueError(f'b must be greater than a.')
    if tolerance < 1E-4:
        raise ValueError('tolerance should be a float greater than 1E-4.')


def integer_solver_brute_force(func: Callable, a: int, b: int, tolerance: float, **kwargs) -> int:
    """A solver for finding the root of the function :math:`F()` using a brute force approach.

    This solver checks all values between *a* and *b* for a root that satisfies the given *tolerance*.
    The main difference between this and a regular solver is that in here, everything is an integer.

    Note that since the function :math:`F()` is stochastic in nature, there will always be
    an error associated with the result. This is OK as the result is acceptable with a tolerance.

    Args:
        func: The continuous function :math:`F()` to be solved. This solver is meant for and tested with
              the :meth:`ShapeDispersionArray._find_vf_for_shape_number` function,
              but should work for other functions.
        a: The start of the range where the search takes place. Should be an integer less than *b*.
        b: The end of the range where the search takes place. Should be an integer greater than *a*.
        tolerance: The tolerance for finding the root of the function. It should be greater than 1E-4.
        kwargs: The keyword arguments to be passed to *func*.

    Returns:
        An integer root for the function :math:`F()`.

    Raises:
        SuitableNumShapesNotFoundError: If a suitable root is not found.
    """
    # Validate inputs.
    integer_solver_validator(func, a, b, tolerance)

    old_vf_diff = None
    for num_shapes in range(a, b + 1):
        vf_diff = func(num_shapes, **kwargs)
        # If within acceptable range, return here.
        if abs(vf_diff) <= tolerance:
            return num_shapes
        # If the sign of new and old vf_diff are different,
        # it means we are only getting further from a good solution
        # and the best two solutions on the boundary have already
        # been determined to be outside tolerance.
        # So we should break the loop and raise SuitableNumShapesNotFoundError.
        if np.sign(old_vf_diff) == np.sign(vf_diff):
            break
    # If we are here, all values have been checked or a solution cannot be found. Raise error.
    raise SuitableNumShapesNotFoundError(f'Suitable num_shapes not found in the range [{a},{b}].')


def integer_solver_bisection(func: Callable, a: int, b: int, tolerance: float, **kwargs) -> int:
    """A solver for finding the root of the function :math:`F()` using
    the `bisection method <https://en.wikipedia.org/wiki/Bisection_method>`_.

    The main difference between this and a regular solver is that in here, everything is an integer.
    This means that if :math:`a=b`, or if :math:`b-a<1` and :math:`F(a)` or :math:`F(b)`
    are within the tolerances, the algorithms stops.

    Note that since the function :math:`F()` is stochastic in nature, there will always be
    an error associated with the result. This is OK as the result is acceptable with a tolerance.

    Args:
        func: The continuous function :math:`F()` to be solved. This solver is meant for and tested with
              the :meth:`ShapeDispersionArray._find_vf_for_shape_number` function,
              but should work for other functions.
              Note that :math:`F(a)` and :math:`F(b)` should have opposing signs.
        a: The start of the range where the search takes place. Should be an integer less than *b*.
        b: The end of the range where the search takes place. Should be an integer greater than *a*.
        tolerance: The tolerance for finding the root of the function. It should be greater than 1E-4.
        kwargs: The keyword arguments to be passed to *func*.

    Returns:
        An integer root for the function :math:`F()`.

    Raises:
        SuitableNumShapesNotFoundError: If a suitable root is not found.
    """
    # Validate inputs.
    integer_solver_validator(func, a, b, tolerance)

    f_a = func(a, **kwargs)
    f_b = func(b, **kwargs)
    if (f_a * f_b) > 0:
        raise ValueError('func(a) and func(b) must have opposite values. Try changing a and b.')

    while True:
        if abs(b - a) <= 1:
            if a == b:
                return a
            elif abs(f_a) < tolerance:
                return a
            elif abs(f_b) < tolerance:
                return b
            else:
                raise SuitableNumShapesNotFoundError(
                    f'The solver reached F(a={a})={f_a:.6} and F(b={b})={f_b:.6}, '
                    f'but could not find a root with the given tolerance ({tolerance:.6}).')
        # Calculate the *integer* midpoint c. Note that it will not be equal to a or b because of the above check.
        c = int((a + b) / 2)
        f_c = func(c, **kwargs)
        if abs(f_c) < tolerance:  # F(c) is OK.
            return c
        elif f_a * f_c < 0:  # The root is between a and c.
            b = c
            f_b = f_c
        else:  # The root is between c and b.
            a = c
            f_a = f_c
