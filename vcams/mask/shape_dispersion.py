"""Classes used for dispersing shapes inside a :class:`~vcams.voxelpart.VoxelPart`."""

import logging
import time
from abc import ABC
from copy import deepcopy
from numpy import var, std, mean, random, max, abs, isscalar, sum
from .shape import ShapeArray

logger = logging.getLogger(__name__)


# TODO: document all functions.


def plot_dispersion_object(dispersion_obj, num_bins):
    """Plot a histogram of the dispersion object."""
    import matplotlib.pyplot as plt
    plt.hist(dispersion_obj, num_bins, density=True)
    plt.show()


class TooManyDispersionAttemptsError(Exception):
    pass


class TooManyDispersionTrialsError(Exception):
    pass


class BaseDispersion(ABC):
    """Abstract base class for a dispersion list.
    Subclasses are used for defining various dispersion.
    """

    def plot(self, num_bins):
        """Plot a histogram of the dispersion object."""
        # noinspection PyUnresolvedReferences
        if self.__len__() < 1:
            raise ValueError('The object is empty. Has it been initialized?')
        import matplotlib.pyplot as plt
        plt.hist(self, num_bins, density=True)  # FIXME
        plt.xlabel('Value')
        plt.ylabel('Frequency')
        plt.show()


class DispersionList(BaseDispersion, list):
    """A Dispersion list defined using a list.
    This is simply a list and is only created to have a uniform naming.
    """

    def __repr__(self):
        max_whole_length = len(str(int(max(abs((mean(self), std(self), var(self))))))) + 1
        max_whole_length += 4  # Number of decimal places is set to 4.
        return f"""{self.__class__}
        Number of Values: {len(self)}
        Actual Mean:      {mean(self):{max_whole_length}.4f}
        Actual SD:        {std(self):{max_whole_length}.4f}
        Actual Variance:  {var(self):{max_whole_length}.4f}
        """


class DispersionNormalDistribution(BaseDispersion):
    """A Dispersion list defined using mean and standard deviation.
    The list is created randomly based on a random generator when the object is created
    and iterating over it is equivalent to iterating over it's *values* attribute.

    Alternatively, generation of the list can be deferred
    and done using the :meth:`generate_values` method."""

    # FIXME: sometimes the values are negative. Fix this or inherit a class.
    # FIXME: change name to gaussian

    def __init__(self, target_mean: float, target_sd: float, num_values: int = None):
        """

        Args:
            target_mean: Target mean for the randomly generated values.
                         Actual mean will be stored in *actual_mean*.
            target_sd: Target standard deviation for the randomly generated values.
                       Actual standard deviation will be stored in *actual_mean*.
            num_values: Number of values to be generated and stored in the *values* property.
                        Defaults to *None* which requires a call to :meth:`generate_values`
                        to generate the values.
        """
        self.target_mean = target_mean
        self.target_sd = target_sd

        if num_values is not None:
            self.generate_values(num_values)
        else:
            self.values = []
            self.actual_mean = None
            self.actual_sd = None
            self.actual_variance = None

    def __iter__(self):
        return self.values.__iter__()

    def __getitem__(self, index):
        return self.values[index]

    def __len__(self):
        return len(self.values)

    def __mul__(self, other):
        return DispersionList(self.values * other)

    def __repr__(self):  # FIXME: add conditional for empty list.
        max_whole_length = len(str(int(max(abs((self.target_mean, self.actual_mean,
                                                self.target_sd, self.actual_sd,
                                                self.actual_variance)))))) + 1
        max_whole_length += 4  # Number of decimal places is set to 4.
        mean_pct_error = 100 * (self.actual_mean - self.target_mean) / self.target_mean
        sd_pct_error = 100 * (self.actual_sd - self.target_sd) / self.target_sd
        return f"""{self.__class__}
        Number of Values: {len(self.values)}
        Target Mean:      {self.target_mean:{max_whole_length}.4f}
        Actual Mean:      {self.actual_mean:{max_whole_length}.4f} ({mean_pct_error:+.4f}%)
        Target SD:        {self.target_sd:{max_whole_length}.4f}
        Actual SD:        {self.actual_sd:{max_whole_length}.4f} ({sd_pct_error:+.4f}%)
        Actual Variance:  {self.actual_variance:{max_whole_length}.4f}
        """

    def generate_values(self, num_values: int):
        """Generate values randomly with the given mean and standard deviation.

        Args:
            num_values: Number of values to be generated and stored in the *values* property.
        """
        self.values = random.default_rng().normal(loc=self.target_mean, scale=self.target_sd, size=num_values)
        self.actual_mean = mean(self.values)
        self.actual_sd = std(self.values)
        self.actual_variance = var(self.values)


class DispersionRandom:
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

    def plot(self, num_bins):
        raise RuntimeError('This function is not available for the DispersionRandom class '
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
                          Coordinate arguments should be passes as :class:`DispersionRandom` instances.
                          These are then called to generate a random value for each attempt.

        Raises:
            TooManyDispersionAttemptsError: Too many attempts were made for this shape.
        """

        # Separate random and scalar kwargs.
        # Note that scalars may have come from an iterable object, but they are scalars now.
        scalar_dict = dict()
        random_object_dict = dict()
        for k, v in kwargs.items():
            if isinstance(v, DispersionRandom):
                random_object_dict[k] = v
            else:  # Assume it's a scalar.
                scalar_dict[k] = v

        # Try to place randomly max_attempts times.
        # Return if successful. Otherwise, raise an error in the end.
        for attempt_number in range(1, max_attempts + 1):
            random_value_dict = dict()
            for k, v in random_object_dict.items():
                random_value_dict[k] = v()  # Note that v (being a DispersionRandom) is *called* here.
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
            if isinstance(v, DispersionNormalDistribution) and (len(v) == 0):
                v.generate_values(1)
            iter0_dict_temp[k] = v[0]
        for (k, v) in scalar_kwargs.items():
            if isinstance(v, DispersionRandom):
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
            if isinstance(v, (DispersionList, DispersionNormalDistribution)):  # are iterables.
                if len(v) == 0:  # It has not been initiated yet.
                    if isinstance(v, DispersionNormalDistribution):
                        v.generate_values(num_shapes)
                        iterable_kwargs[k] = v
                    else:
                        raise ValueError(f'{k} is empty but should have {num_shapes} elements.')
                elif len(v) == num_shapes:
                    iterable_kwargs[k] = v
                else:
                    raise ValueError(f'{k} has {len(v)} elements but num_shapes={num_shapes}.')
            elif isscalar(v) or isinstance(v, DispersionRandom):
                scalar_kwargs[k] = v
            else:
                raise ValueError(f'{k} is neither a scalar nor a valid subclass of BaseDispersion.')

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
    #         if isinstance(v, DispersionList):
    #             raise ValueError(f'{k} is a DispersionList which is not allowed '
    #                              'for the add_shape_request_no_nums() function.')
    #         elif isinstance(v, DispersionNormalDistribution):
    #             iterable_kwargs[k] = v
    #         elif isscalar(v) or isinstance(v, DispersionRandom):
    #             scalar_kwargs[k] = v
    #         else:
    #             raise ValueError(f'{k} is neither a scalar nor a valid subclass of BaseDispersion.')
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
            if isinstance(v, DispersionList):
                if num_shapes is None:
                    raise ValueError(f'{k} is a DispersionList which is not allowed '
                                     'when num_shapes is None.')
                elif len(v) != num_shapes:
                    raise ValueError(f'{k} is a DispersionList with {len(v)} elements '
                                     f'but num_shapes is {num_shapes}. They should be equal.')
                else:
                    iterable_kwargs[k] = v
            elif isinstance(v, DispersionNormalDistribution):
                if (len(v) == 0) and (num_shapes is not None):
                    raise ValueError(f'{k} is an uninitialized DispersionNormalDistribution. '
                                     f'Specify num_shapes when defining it.')
                # If len(v)==0 and num_shapes is None, it's OK.
                iterable_kwargs[k] = v
            elif isscalar(v) or isinstance(v, DispersionRandom):
                scalar_kwargs[k] = v
            else:
                raise ValueError(f'{k} is neither a scalar nor a valid subclass of BaseDispersion.')

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

    def find_suitable_num_shapes(self, start_num_shapes: int = 1):
        """Brute force"""

        num_shapes_list = [sr[1] for sr in self.shape_requests]
        if None not in num_shapes_list:
            raise ValueError(f'Some of the num_shapes in shape_requests are *not* None.'
                             f'If you want to find suitable num_shapes, they should all start as None.'
                             f'The list is: {num_shapes_list}')

        for num_shapes in range(start_num_shapes, start_num_shapes + 1000):
            shape_list = []  # Note that this is a simple list and not a ShapeArray instance.
            for req in self.shape_requests:
                (cls, _, iterable_kwargs, scalar_kwargs) = req
                # Regenerate the DispersionList instances with num_shapes values.
                for k, v in iterable_kwargs.items():
                    if isinstance(v, DispersionList):
                        raise ValueError(f'{k} is a DispersionList which is not allowed '
                                         'when finding num_shapes.')
                    v.generate_values(num_shapes)

                for i in range(num_shapes):
                    # Put the shape's iterable_kwargs into a single dict to be passed as scalars.
                    shape_list_kwargs = dict()
                    for k, v in iterable_kwargs.items():
                        shape_list_kwargs[k] = v[i]
                    # Try to place the shape. Raises TooManyDispersionAttempts if unsuccessful.
                    shape_list.append(cls(id=i + 1, **shape_list_kwargs, **scalar_kwargs))

                print(f'num_shapes={num_shapes:4d}, total_vol={sum(i.analytical_volume for i in shape_list):.6f}')

        # We now have all the shapes. Find their volume.
        # Test up to here. Does it make the shapes?
        pass

        # find num_shapes
        # regenerate normal distribution

        #  self.shape_requests.append([cls, num_shapes, iterable_kwargs, scalar_kwargs])
        #  (cls, num_shapes, list_kwargs, other_kwargs) = req
        pass

    # FIXME: add knapsack here.
    # It should use the analytical volume for finding the optimal numner of shapes.
    # then use that to disperse and apply the knapsack algorithm to find a good list of shapes.
