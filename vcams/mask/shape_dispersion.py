"""Classes used for dispersing shapes inside a :class:`~vcams.voxelpart.VoxelPart`."""

import logging
import time
import matplotlib
import numpy as np

matplotlib.use('TkAgg')  # FIXME: https://stackoverflow.com/a/73788178/7180705
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod
from copy import deepcopy
from numpy import var, std, mean, random, max, abs, isscalar, sum, inf
from scipy.stats import truncnorm

from .shape import ShapeArray

logger = logging.getLogger(__name__)


# TODO: document all functions.


class TooManyDispersionAttemptsError(Exception):
    pass


class TooManyDispersionTrialsError(Exception):
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
        self.values = np.array([])
        """A numpy array containing the values in the instance."""

    def plot(self, num_bins, plot_actual_normal_curve=False):
        """Plot a histogram of the dispersion object."""
        if self.__len__() < 1:
            raise ValueError('The object is empty. Has it been initialized?')
        plt.plot([], [], ' ', label=f'$\\bf{{Dispersion Type: {type(self).__name__}}}$')
        plt.hist(self.values, num_bins, density=True, label='Actual Values Histogram')  # FIXME
        plt.xlabel('Value')
        plt.ylabel('Frequency')

        if plot_actual_normal_curve:
            x = np.linspace(-3 * self.actual_std + self.actual_mean, 3 * self.actual_std + self.actual_mean, 100)
            y = (np.exp(-np.power((x - self.actual_mean) / self.actual_std, 2.0) / 2)
                 / (np.sqrt(2.0 * np.pi) * self.actual_std))
            plt.plot(x, y, label='Normal Distribution (Actual Values)')

        self._set_plot_legend()
        plt.show()

    @staticmethod
    def _set_plot_legend():
        plt.gca().legend(frameon=False, prop={'family': 'monospace'},
                         fontsize=1, numpoints=1, loc='upper right')
        # TODO: see if legend can be correctly placed outside.
        # It seems that the legend should be added to bbox_extra_artists
        # which can only be done in savefig.
        # plt.legend(title='MY TITLE', frameon=False,
        #            prop={'family': 'monospace'}, fontsize=2,
        #            numpoints=1, bbox_to_anchor=(1.05, 1),
        #            loc='upper left')


class ManualListDispersion(BaseListDispersion):
    """A Dispersion list defined manually using a list.
    This is simply a list and is only created to have a uniform naming.
    """

    def __init__(self, values):
        super().__init__()
        # TODO: make sure values is an iterable and flat.
        self.values = np.array(values)

    def __repr__(self):
        return f"""{self.__class__}
        Number of Values: {len(self)}
        Actual Mean:      {self.actual_mean:{self._repr_float_length}.4f}
        Actual SD:        {self.actual_std:{self._repr_float_length}.4f}
        Actual Variance:  {self.actual_variance:{self._repr_float_length}.4f}
        """

    # noinspection PyMethodOverriding
    def plot(self, num_bins):
        """Plot a histogram of the dispersion object."""
        BaseListDispersion.plot(self, num_bins, plot_actual_normal_curve=True)
        plt.plot([], [], ' ', label=self.__repr__().split('\n', 1)[1])
        BaseListDispersion._set_plot_legend()
        plt.show()


class BaseNormalDistributionDispersion(BaseListDispersion):
    """Abstract base class for dispersion classes that generate a list of values
    with a normal (gaussian) distribution.

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
        """
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
            return (f'{self.__class__}\n'
                    f'    The instance is empty. Use generate_values(num_values) to populate it.\n'
                    f'    Target Mean:      {self.target_mean:{self._repr_float_length}.4f}\n'
                    f'    Target SD:        {self.target_std:{self._repr_float_length}.4f}')
        else:
            mean_pct_error = 100 * (self.actual_mean - self.target_mean) / self.target_mean
            sd_pct_error = 100 * (self.actual_std - self.target_std) / self.target_std
            return (f'{self.__class__}\n'
                    f'    Number of Values: {len(self.values)}\n'
                    f'    Target Mean:      {self.target_mean:{self._repr_float_length}.4f}\n'
                    f'    Actual Mean:      {self.actual_mean:{self._repr_float_length}.4f} ({mean_pct_error:+.4f}%)\n'
                    f'    Target SD:        {self.target_std:{self._repr_float_length}.4f}\n'
                    f'    Actual SD:        {self.actual_std:{self._repr_float_length}.4f} ({sd_pct_error:+.4f}%)\n'
                    f'    Actual Variance:  {self.actual_variance:{self._repr_float_length}.4f}')

    # noinspection PyMethodOverriding
    def plot(self, num_bins):
        """Plot a histogram of the dispersion object."""
        BaseListDispersion.plot(self, num_bins)
        x = np.linspace(-3 * self.target_std + self.target_mean, 3 * self.target_std + self.target_mean, 1000)
        y = (np.exp(-np.power((x - self.target_mean) / self.target_std, 2.0) / 2)
             / (np.sqrt(2.0 * np.pi) * self.target_std))
        plt.plot(x, y, label='Normal Distribution (Target)')
        plt.plot([], [], ' ', label=self.__repr__().split('\n', 1)[1])
        BaseListDispersion._set_plot_legend()
        plt.show()

    @abstractmethod
    def _generate_values_once(self, num_values: int, qc_results=True):
        """Abstract method for generating a single set of :attr:`values`
        based on the instance's attributes.
        This method can be called as many times as necessary to regenerate the instance's
        *values* list and change its *num_values*."""
        pass

    def generate_values(self, num_values: int, qc_results=True, max_attempts=1000):
        """TODO note that error is raised and attempts are made.

        Args:
            num_values: Number of values to be generated and stored in the *values* property.
            qc_results: If *True*, the values are quality controlled
                        using :meth:`BaseNormalDistributionDispersion._qc_dispersion`.
                        Defaults to *True*.
            max_attempts: The maximum number of attempts for generation of valid values.
                          If exceeded, :class:`TooManyValueGenerationAttemptsError` is raised.

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

    def _qc_dispersion(self, min_size=0, max_absolute_pct_error: int | None = None):
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
    a normal (gaussian) distribution.

    The generated distribution will be truly normal, but may include negative values.
    This will cause issues for some purposes such as geometrical features.
    Other classes will not be truly normal but not won't have this problem.

    This is a subclass of :class:`BaseNormalDistributionDispersion`.
    See its docs for other details.
    """

    def _generate_values_once(self, num_values: int, qc_results=True):
        """Generate values randomly with the given mean and standard deviation.
        This method can be called as many times as necessary to regenerate the instance's
        *values* list and change its *num_values*.

        This function uses NumPy's `random.default_rng().normal` function.

        Args:
            num_values: Number of values to be generated and stored in the *values* property.
            qc_results: If *True*, the values are quality controlled
                        using :meth:`BaseNormalDistributionDispersion._qc_dispersion`.
                        Defaults to *True*.
        """
        if num_values < 1:
            raise ValueError('num_values must be bigger than 0.')
        self.values = random.default_rng().normal(loc=self.target_mean, scale=self.target_std, size=num_values)
        if qc_results:
            self._qc_dispersion()


class TruncatedNormalDistributionDispersion(BaseNormalDistributionDispersion):
    """todo"""

    def __init__(self, target_mean: float, target_std: float,
                 bound_a: float = -inf, bound_b: float = inf, num_values: int = None):
        """
        Args:
            target_mean: Target mean for the randomly generated values.
                         Actual mean will be stored in *actual_mean*.
            target_std: Target standard deviation for the randomly generated values.
                        Actual standard deviation will be stored in *actual_mean*.
            bound_a:    The beginning of the range from which values should be drawn.
            bound_b:    The end of the range from which values should be drawn.
            num_values: Number of values to be generated and stored in the *values* property.
                        Defaults to *None* which defers value generation and
                        requires a call to :meth:`generate_values` to generate the values.
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

    def plot(self, num_bins):
        """Plot a histogram of the dispersion object."""
        BaseListDispersion.plot(self, num_bins)

        x = np.linspace(-3 * self.target_std + self.target_mean, 3 * self.target_std + self.target_mean, 1000)
        y = truncnorm.pdf(x, a=self._truncnorm_a, b=self._truncnorm_b,
                          loc=self.target_mean, scale=self.target_std)
        plt.plot(x, y, label='Truncated Normal Distribution (Target)')
        plt.plot([], [], ' ', label=self.__repr__().split('\n', 1)[1])
        BaseListDispersion._set_plot_legend()
        plt.show()

    def _generate_values_once(self, num_values: int, qc_results=True):
        """Generate values randomly based on a truncated normal distribution
        with the given mean and standard deviation.
        This method can be called as many times as necessary to regenerate the instance's
        *values* list and change its *num_values*.
        
        This function uses SciPy's `stats.truncnorm.rvs` function.
        
        Args:
            num_values: Number of values to be generated and stored in the *values* property.
            qc_results: If *True*, the values are quality controlled
                        using :meth:`BaseNormalDistributionDispersion._qc_dispersion`.
                        Defaults to *True*.
        """  # See __init__ for _truncnorm_a and _truncnorm_b.
        self.values = truncnorm.rvs(a=self._truncnorm_a, b=self._truncnorm_b,
                                    loc=self.target_mean, scale=self.target_std,
                                    size=num_values)
        if qc_results:
            self._qc_dispersion()


class RandomDispersion:  # TODO: doc
    def __init__(self, low, high, boundary=0):
        self.low = low + boundary
        self.high = high - boundary

    def __call__(self):
        return random.uniform(low=self.low, high=self.high, size=None)

    def __repr__(self):
        return f"""{self.__class__}
        Actual Low:  {self.low}
        Actual High: {self.high}
        """

    def plot(self):
        raise NotImplementedError('This function is not available for the RandomDispersion class '
                                  'because it only return a random scalar.')


class ShapeDispersionArray(ShapeArray):
    """TODO: doc
    TODO: if part is specified, it's used as background. Is this a question or a statement??"""

    def __init__(self, dim: str, part=None,
                 mask_shape: tuple[int, int, int] = None,
                 voxel_size: tuple[float, float, float] = None,
                 num_bound_pixels: int = 0,
                 short_msg: bool = True):
        """
        Args:
            part (VoxelPart | None): The VoxelPart object (TODO) based on which the ShapeArray is created.
                                     If None, *mask_shape* and *voxel_size* must be specified (%TODO: enforce).
            dim: Dimensionality of the shape array which determines the shapes that
                 can be added to the shape array. Valid values are '2D' and '3D'.
            mask_shape: A tuple containing three integers which determines
                        the shape of the returned boolean mask. Ignored if *part* is passed.
            voxel_size: A tuple containing three floats which determine the size of a voxel
                        in the x, y, and z directions. Ignored if *part* is passed.
            num_bound_pixels: An int specifying the number of pixels to add to the boundary of the base mask.
                              The boundary will become a region that the dispersed shapes cannot touch.
                              Defaults to 0.
            short_msg: A boolean specifying whether the placement message should be printed
                       as a single updating line or in many lines with extensive details.
                       Passed to :func:`.print_placement_message` Defaults to *True*.
        """

        super().__init__(dim, part, mask_shape, voxel_size, is_mask_calculation_lazy=False)
        # TODO: doc that is_mask_calculation_lazy is True

        self.short_msg = short_msg
        """See :meth:`.__init__`."""

        self.shape_requests = []
        """A list of shapes shape classes and related parameters that should be dispersed.
        This list is emptied after a successful dispersion."""  # TODO: talk about structure.

        # Add boundary to the base mask so the shapes don't touch the outside.
        if num_bound_pixels:  # FIXME: here or in ShapeArray?
            self.base_mask[:, :num_bound_pixels] = True
            self.base_mask[:, -num_bound_pixels:] = True
            self.base_mask[:num_bound_pixels, :] = True
            self.base_mask[-num_bound_pixels:, :] = True

    @property
    def num_requested_shapes(self):  # TODO: test
        """Total number of shapes requested in :meth:`shape_requests`."""
        num_shapes_list = [sr[1] for sr in self.shape_requests]
        if None in num_shapes_list:
            return '???'
        else:
            return sum(num_shapes_list)

    def _backup_state(self):
        super()._backup_state()
        self._backup_dict['shape_requests'] = deepcopy(self.shape_requests)

    def _restore_state(self):
        super()._restore_state()
        self.shape_requests = deepcopy(self._backup_dict['shape_requests'])

    def _place_shape_randomly(self, cls, shape_number: int, max_attempts: int,
                              trial_number: int = None, **kwargs):
        """Place a shape in a random position. Placement is tried *max_attempts* number of times.

        Args:
            cls: The shape class that should be placed. Arguments are passed as *kwargs*.
            shape_number: The number of this shape.
                          This number keeps track of the shapes that are dispersed
                          and is used for printing the progress messages.
                          it is *not* the shape's eventual ID.
            max_attempts: The maximum number of attempts for placement of a shape.
                          If exceeded, :class:`TooManyDispersionAttemptsError` is raised.
            trial_number: The number for this trial. Used for printing the progress messages.
            **kwargs:     A dictionary where the keys are the arguments for the shape class
                          and the values are either dispersion objects or scalars.
                          Coordinate arguments should be passes as :class:`RandomDispersion` instances.
                          These are then called to generate a random value for each attempt.

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
            self._print_placement_message(cls, attempt_number, shape_number,
                                          scalar_dict, random_value_dict, trial_number)
            # Try to add a shape to the array. shape_status will be True if successful.
            shape_status = self.add_shape(cls, intersect_ok=False, **scalar_dict, **random_value_dict)
            self._print_shape_status_message(shape_status)
            if shape_status:
                return
        raise TooManyDispersionAttemptsError(f'Too many dispersion attempts for {shape_number}')

    def _print_placement_message(self, cls, attempt_number, shape_number, scalar_dict,
                                 random_value_dict, trial_number=None):
        """Print the placement message for a shape."""
        # TODO: add logging here.
        if trial_number is None:
            trial_str = ''
        else:
            trial_str = f'Trial {trial_number:4d}, '
        if self.part_name is None:
            name_str = ''
        else:
            name_str = f"Part '{self.part_name}': "

        shape_num_str = f'Shape {shape_number:{len(str(self.num_requested_shapes))}d}/{self.num_requested_shapes}'
        attempt_num_str = f'Attempt {attempt_number:4d}'
        if self.short_msg:
            print(f'{name_str}{trial_str}{shape_num_str}, {attempt_num_str}, Type {cls.__name__} ', end='')
        else:
            s_k_str = ', '.join(scalar_dict.keys())
            s_v_str = ', '.join(f'{x:2.4f}' for x in scalar_dict.values())
            r_k_str = ', '.join(random_value_dict.keys())
            r_v_str = ', '.join(f'{x:2.4f}' for x in random_value_dict.values())
            print(f'{name_str}{trial_str}{shape_num_str}, {attempt_num_str}: '
                  f'Trying to place {cls.__name__} with ({s_k_str})=({s_v_str}) '
                  f'at ({r_k_str})=({r_v_str}) ... ', end='')

    def _print_shape_status_message(self, shape_status):
        """Print the status message after the shape's placement message."""
        # TODO: add logging here.
        if self.short_msg:
            # Return the carriage so the current placement message can be overwritten by the next.
            print('\r', end='')
        else:
            # Print status with a newline so the next placement message is written to the next line.
            if shape_status:
                print('Success!')
            else:
                print('Failed!')

    def _print_dispersion_success_message(self, elapsed_time):
        print(f"\nPart '{self.part_name}': {self.num_requested_shapes} shapes dispersed "
              f"successfully in {elapsed_time:.2f} seconds.")

    @staticmethod
    def _test_cls_kwargs(cls, iterable_kwargs, scalar_kwargs):
        """Try to create a shape with a set of iterable_kwargs and scalar_kwargs
        to make sure they are valid. It raises an error if unsuccessful and is otherwise silent."""
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

    def add_shape_request(self, cls, num_shapes: int = 1, **kwargs):
        """Add a request for a one or more shapes of a class to be added to the instance.

        Args:
            cls: The shape class that should be placed. Arguments are passed as *kwargs*.
            num_shapes: Number of shapes that are requested with the given arguments.
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
            if isinstance(v, BaseListDispersion):  # are iterables.
                if len(v) == 0:  # It has not been initiated yet.
                    if isinstance(v, BaseNormalDistributionDispersion):
                        v.generate_values(num_shapes)
                        iterable_kwargs[k] = v
                    else:
                        raise ValueError(f'{k} is empty but should have {num_shapes} elements.')
                elif len(v) == num_shapes:
                    iterable_kwargs[k] = v
                else:
                    raise ValueError(f'{k} has {len(v)} elements but num_shapes={num_shapes}.')
            elif isscalar(v) or isinstance(v, RandomDispersion):
                scalar_kwargs[k] = v
            else:
                raise ValueError(f'{k} is neither a scalar nor a valid subclass of BaseListDispersion.')

        # Try to create a shape with iterable_kwargs and scalar_kwargs to make sure they're valid.
        ShapeDispersionArray._test_cls_kwargs(cls, iterable_kwargs, scalar_kwargs)

        # Add the shape request as a tuple to the instance's shape_requests list.
        self.shape_requests.append([cls, num_shapes, iterable_kwargs, scalar_kwargs])

    # def add_shape_request_no_nums(self, cls, **kwargs):
    #     # Validate the shape class.
    #     self._check_shape_class(cls)
    #
    #     # Split the kwargs dictionary into two groups,
    #     # that will each be passed to the placement function differently.
    #     # The keys are the arguments' names.
    #     # In iterable_kwargs, the value is an iterable whose contents will be passed one by one;
    #     # and in other_kwargs, the value is a single scalar which will be passed each time.
    #     iterable_kwargs = dict()
    #     scalar_kwargs = dict()
    #     for k, v in kwargs.items():
    #         if isinstance(v, ManualListDispersion):
    #             raise ValueError(f'{k} is a ManualListDispersion which is not allowed '
    #                              'for the add_shape_request_no_nums() function.')
    #         elif isinstance(v, NormalDistributionDispersion):
    #             iterable_kwargs[k] = v
    #         elif isscalar(v) or isinstance(v, RandomDispersion):
    #             scalar_kwargs[k] = v
    #         else:
    #             raise ValueError(f'{k} is neither a scalar nor a valid subclass of BaseListDispersion.')
    #
    #     # Try to create a shape with iterable_kwargs and scalar_kwargs to make sure they're valid.
    #     ShapeDispersionArray._test_cls_kwargs(cls, iterable_kwargs, scalar_kwargs)
    #
    #     # Add the shape request as a tuple to the instance's shape_requests list.
    #     self.shape_requests.append([cls, num_shapes, iterable_kwargs, scalar_kwargs])
    #     pass

    def add_shape_request2(self, cls, num_shapes: int | None, **kwargs):
        # TODO: add doc. document possibility of num_shapes being None.
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
                if (len(v) == 0) and (num_shapes is not None):
                    raise ValueError(f'{k} is an uninitialized NormalDistributionDispersion. '
                                     f'Specify num_shapes when defining it.')
                # If len(v)==0 and num_shapes is None, it's OK.
                iterable_kwargs[k] = v
            elif isscalar(v) or isinstance(v, RandomDispersion):
                scalar_kwargs[k] = v
            else:
                raise ValueError(f'{k} is neither a scalar nor a valid subclass of BaseListDispersion.')

        # Try to create a shape with iterable_kwargs and scalar_kwargs to make sure they're valid.
        ShapeDispersionArray._test_cls_kwargs(cls, iterable_kwargs, scalar_kwargs)

        # Add the shape request as a tuple to the instance's shape_requests list.
        self.shape_requests.append([cls, num_shapes, iterable_kwargs, scalar_kwargs])

    def disperse_shapes(self, max_attempts: int = 5000, max_trials: int = 100, ):
        """Disperse shapes in the *ShapeDispersionArray* instance according to
        the shape requests. All shape requests are processed and then :attr:`shape_requests`
        is emptied.

        Args:
            max_attempts: The maximum number of attempts for placement of a shape.
                          If exceeded, the trial ends and the process is restarted.
            max_trials:   The maximum number of trials. If exceeded,
                          :class:`TooManyDispersionTrialsError` is raised.

        Raises:
            TooManyDispersionTrialsError: Too many trials were done.
                                          Note that each trials entails many attempts.
        """

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
                dispersion_success = False  # This isn't strictly necessary. TODO: try removing it.
                shape_number = 0
                for req in self.shape_requests:
                    (cls, num_shapes, iterable_kwargs, scalar_kwargs) = req
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
                # Both loops have run out and dispersion is successful.
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
            self._print_dispersion_success_message(elapsed_time)
            self.shape_requests = []
            self._backup_dict = dict()
        else:
            raise TooManyDispersionTrialsError(f'Dispersion has been unsuccessful after {max_trials} trials.')

    def find_suitable_num_shapes(self, target_vf: float, max_vf_diff: float,
                                 start_num_shapes: int = 5, max_num_shapes: int = 1000,
                                 print_progress=False) -> int:
        """Brute force TODO doc

        Args:
            target_vf: Target volume fraction.
            max_vf_diff: Maximum difference between the reached volume fraction and *target_vf*.
                         It should be a float greater than 1E-4.
            start_num_shapes: The initial value of *num_shapes* investigated by the function.
            max_num_shapes: The maximum value of *num_shapes* investigated by the function.
            print_progress: If True, the values of total volume, volume fraction, and vf_diff
                            are printed for each value of num_shapes. Defaults to False.

        Returns:
            A suitable value for *num_shapes* that can be used in conjunction with the knapsack algorithm.
        """

        # Validate input.
        if target_vf <= 0:
            raise ValueError('target_volume_fraction should be a positive number.')
        if max_vf_diff < 1E-6:
            raise ValueError('max_vf_diff should be None or a float greater than 1E-4.')
        if max_num_shapes <= start_num_shapes:
            raise ValueError('max_num_shapes should be greater than start_num_shapes.')
        # Make sure all num_shapes in the shape requests are None.
        num_shapes_list = [sr[1] for sr in self.shape_requests]
        if not all(ns is None for ns in num_shapes_list):
            raise ValueError(f'Some of the num_shapes in shape_requests are *not* None.'
                             f'If you want to find suitable num_shapes, they should *all* start as None.'
                             f'The list is: {num_shapes_list}')

        for num_shapes in range(start_num_shapes, max_num_shapes + 1):
            shape_list = []  # Note that this is a simple list and not a ShapeArray instance.
            for req in self.shape_requests:
                (cls, _, iterable_kwargs, scalar_kwargs) = req
                # Regenerate the ManualListDispersion instances with num_shapes values.
                for k, v in iterable_kwargs.items():
                    if isinstance(v, ManualListDispersion):
                        raise ValueError(f'{k} is a ManualListDispersion which is not allowed '
                                         'when finding num_shapes.')
                    v.generate_values(num_shapes)

                # Create the shapes as single independent instances in shape_list.
                for i in range(num_shapes):
                    # Put the shape's iterable_kwargs into a single dict to be passed as scalars.
                    shape_list_kwargs = dict()
                    for k, v in iterable_kwargs.items():
                        shape_list_kwargs[k] = v[i]
                    # Create the shape.
                    # Note that a shape instance is not placed anywhere and simply exists.
                    # In fact, the coordinate variable should have a RandomDispersion instance
                    # as the value which will raise an error if used.
                    # But we only need to calculate the analytical volume so this is OK.
                    shape_list.append(cls(id=i + 1, **shape_list_kwargs, **scalar_kwargs))

            # Calculate the sum of analytical volumes for the shapes in shape_list.
            total_analytical_volume = sum(i.analytical_volume for i in shape_list)
            # Calculate volume fraction and the difference between it and target_vf.
            current_vf = total_analytical_volume / self.part_volume
            vf_diff = current_vf - target_vf
            if print_progress:
                print(f'num_shapes={num_shapes:4d}, total_vol={total_analytical_volume:.6f}, '
                      f'vf={current_vf:.6f}, target_vf={target_vf:.6}, '
                      f'vf_diff={vf_diff:+.6f}, max_vf_diff={max_vf_diff:.6}.')
            # If within acceptable range, return here.
            if abs(vf_diff) < max_vf_diff:
                return num_shapes
        # If we are here, all values have been checked. Raise error.
        raise SuitableNumShapesNotFoundError(
            f'Suitable num_shapes not found in the range [{start_num_shapes},{max_num_shapes}].')

    # FIXME: add knapsack here.
    # It should use the analytical volume for finding the optimal numner of shapes.
    # then use that to disperse and apply the knapsack algorithm to find a good list of shapes.
