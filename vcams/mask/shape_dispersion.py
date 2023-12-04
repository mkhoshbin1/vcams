"""Classes used for dispersing shapes inside a :class:`~vcams.voxelpart.VoxelPart`."""

import logging
import time
from abc import ABC
from copy import deepcopy
from itertools import count
from numpy import squeeze, full, copy, logical_or, logical_and, var, std, mean, random, any, ndarray, max, abs, isscalar

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
        plt.hist(self, num_bins, density=True)
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

    def __repr__(self):
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


class ShapeDispersionArray:
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
        if dim.upper() not in ['2D', '3D']:
            raise ValueError("dim can only be one of '2D' or '3D'.")
        self.dim = dim.upper()
        """The boolean mask representing the union (logical OR) of the shapes in ShapeArray."""
        # TODO: for 2d, voxel_size should be OK with (x,y) but it isn't.

        self.short_msg = short_msg
        """See :meth:`.__init__`."""

        if part:
            self.part_name = part.name
            self.mask_shape = part.size
            self.voxel_size = tuple(part.voxel_size)
            self.base_mask = (part.data == 0)  # TODO: check this with a TPMS.
            # TODO: document that this only works for empty space.
        else:
            self.part_name = None
            """Name of the part for which the ShapeDispersionArray is created.
            If a pert is not passed, it is set to *None* and it is not used."""
            self.mask_shape = mask_shape
            """See :meth:`.__init__`."""
            self.voxel_size = voxel_size
            """See :meth:`.__init__`."""
            self.base_mask = full(mask_shape, False, dtype=bool)
            """A mask for the part which contains the background where the shapes are dispersed.
            If a VoxelPart instance is passed, its nonzero elements are considered occupied,
            otherwise a blank part is used.
            Also boundary pixels, as determined by the *num_bound_pixels*
            variable, are considered occupied."""

        self._mask = full(mask_shape, False, dtype=bool)  # Private attribute for the mask property.
        self.shapes = dict()
        """A dictionary containing the shapes in the :class:`ShapeDispersionArray` object.
        Keys are integer shape IDs, and values are subclasses of :class:`.shape.BaseShape`."""

        self.shape_requests = []
        """A list of shapes shape classes and related parameters that should be dispersed.
        This list is emptied after a successful dispersion."""

        self._num_requested_shapes = 0
        """Total number of shapes requested in :meth:`shape_requests`."""

        self._backup_dict = dict()
        """A dictionary containing the state of the ShapeDispersionArray object
        which is used by :meth:`_backup_state` and :meth:`_restore_state`."""

        # Add boundary to the base mask so the shapes don't touch the outside.
        if num_bound_pixels:
            self.base_mask[:, :num_bound_pixels] = True
            self.base_mask[:, -num_bound_pixels:] = True
            self.base_mask[:num_bound_pixels, :] = True
            self.base_mask[-num_bound_pixels:, :] = True

        self._full_mask = copy(self.base_mask)  # full mask is base_mask + _mask. #TODO: doc this.
        """A mask containing both the background and current dispersed shapes.
        It is a logical_or of the ShapeArray's *base_mask* and *mask*
        and is stored to reduce repetitive computations."""

    def __len__(self):
        return len(self.shapes)

    id_iter: iter = count()
    """An iterable keeping track of the number of shapes in the ShapeArray."""

    @property
    def mask(self):
        """The boolean mask representing the union (logical OR) of the shapes in ShapeArray.
        This is guaranteed to be up-to-date and does not include the ShapeArray's *base_mask*."""
        if len(self) > 0:
            return self._mask
        else:
            raise ValueError('The array is empty.')

    def _backup_state(self):
        """Backup the state of the ShapeDispersionArray object for use before dispersion trials."""
        self._backup_dict = dict()
        self._backup_dict['id_iter'] = deepcopy(self.id_iter)
        self._backup_dict['base_mask'] = ndarray.copy(self.base_mask)
        self._backup_dict['_mask'] = ndarray.copy(self._mask)
        self._backup_dict['_full_mask'] = ndarray.copy(self._full_mask)
        self._backup_dict['shapes'] = deepcopy(self.shapes)
        self._backup_dict['shape_requests'] = deepcopy(self.shape_requests)

    def _restore_state(self):
        """Backup the state of the ShapeDispersionArray object for use after a failed dispersion trial."""
        if not self._backup_dict:
            raise RuntimeError("The object's _backup_dict property is empty."
                               "Has _backup_state() been run? This may also happen after"
                               "a successful run of disperse_shapes().")
        self.id_iter = deepcopy(self._backup_dict['id_iter'])
        self.base_mask = ndarray.copy(self._backup_dict['base_mask'])
        self._mask = ndarray.copy(self._backup_dict['_mask'])
        self._full_mask = ndarray.copy(self._backup_dict['_full_mask'])
        self.shapes = deepcopy(self._backup_dict['shapes'])
        self.shape_requests = deepcopy(self._backup_dict['shape_requests'])

    def _add_to_mask(self, new_mask):
        """Add *new_mask* to that of the current array."""
        new_mask = squeeze(new_mask)
        self._mask = logical_or(self._mask, new_mask)
        self._full_mask = logical_or(self._mask, self.base_mask)

    def _check_shape(self, shape):
        """Check the given shape class or instance to make sure its dim matches the shape array."""
        if shape.dim != self.dim:
            raise ValueError(
                'The specified shape is %s, but the shape array has been defined for %s shapes.'
                % (shape.dim, self.dim))

    def add_shape(self, cls, **kwargs) -> bool:
        """*Try* to add a shape to the ShapeArray using its class.
        If the shape intersects with the mask, it is discarded
        and False is returned to signify an unsuccessful operation.
        Otherwise, True is returned, the shape is added to the array,
        and the mask is recalculated."""

        # Make sure the class cls matches the ShapeArray object.
        self._check_shape(cls)
        # Create the new shape and calculate its mask.
        new_shape_obj = cls(id=-1, **kwargs)
        new_shape_mask = new_shape_obj.calculate_mask(self.mask_shape, self.voxel_size, boundary_on=True)

        # Check if the new shape intersects with the ShapeDispersionArray's current mask.
        if any(logical_and(self._full_mask, new_shape_mask)):
            # If they intersect, return False for an unsuccessful operation.
            # The shape is discarded.
            return False
        else:
            # If they don't intersect, return True for a successful operation,
            # add the shape to the array, and recalculate the mask.
            idd = next(self.id_iter)
            new_shape_obj.id = idd
            self.shapes[idd] = new_shape_obj
            self._add_to_mask(
                new_mask=new_shape_obj.calculate_mask(self.mask_shape, self.voxel_size, boundary_on=False))
            return True

    def remove_shape(self, id_list):
        """Remove shapes from the :class:`ShapeDispersionArray` instance and update the masks.

        Args:
            id_list: ID(s) of the shapes to be removed. Can be a single ID or an iterable.
        """

        # Validate id_list.
        if isscalar(id_list):
            id_list = (id_list,)
        for id in id_list:
            if id not in self.shapes.keys():
                raise ValueError(f'{id} is not a valid shape ID.')

        # Delete all shapes from id_list from the shapes dictionary.
        for id in id_list:
            del self.shapes[id]


        # Update the masks.


        pass

    def add_shape_request(self, cls, num_shapes: int = 1, **kwargs):
        """Add a request for a one or more shapes of a class to be added
        to the :class:`ShapeDispersionArray` instance.

        Args:
            cls: The shape class that should be placed. Arguments are passed as *kwargs*.
            num_shapes: Number of shapes that are requested.
            **kwargs: A dictionary where the keys are the arguments for the shape class
                      and the values are either dispersion objects or scalars.
        """

        # check if cls is compatible

        # Split the kwargs dictionary into two groups,
        # each mapping the argument's name to its value.
        # These are then passed to the placement function.
        list_kwargs = dict()  # The dictionary value will be a list of scalars.
        other_kwargs = dict()  # The dictionary value will be a single scalar.
        for k, v in kwargs.items():
            if isinstance(v, (DispersionList, DispersionNormalDistribution)):  # Act as lists.
                if len(v) == 0:  # It has not been initiated yet.
                    v.generate_values(num_shapes)
                    list_kwargs[k] = v
                elif len(v) == num_shapes:
                    list_kwargs[k] = v
                else:
                    raise ValueError(f'{k} has {len(v)} elements but num_shapes={num_shapes}.')
            else:  # Act as scalars.
                other_kwargs[k] = v

            # TODO: maybe here we can test one of the shapes to make sure kwargs is OK.

        self.shape_requests.append([cls, num_shapes, list_kwargs, other_kwargs])
        self._num_requested_shapes += num_shapes

    def place_shape_randomly(self, cls, shape_number: int, max_attempts: int,
                             trial_number: int = None, **kwargs):
        """Place a shape in a random position.

        Args:
            cls: The shape class that should be placed. Arguments are passed as *kwargs*.
            shape_number: The number of this shape.
                          This number keeps track of the shapes that are dispersed
                          and is used for printing the progress messages.
                          it is *not* the shape's eventual ID.
            max_attempts: The maximum number of attempts for placement of a shape.
                          If exceeded, TooManyDispersionAttemptsError is raised.
            trial_number: The number of this trial. Used for printing the progress messages.
            **kwargs:     A dictionary containing *DispersionRandom* objects
                          for the placement arguments and scalars for the rest of the arguments.
        """

        # Separate random and scalar kwargs.
        scalar_dict = dict()
        random_object_dict = dict()
        for k, v in kwargs.items():
            if isinstance(v, DispersionRandom):  # TODO: does it work with subclasses?
                random_object_dict[k] = v
            else:  # Assume it's a scalar.  #TODO: is it actually a scalar? I don't think so.
                scalar_dict[k] = v

        # Try to run the process max_trials times.
        # for trial_number in range(1, self.max_trials + 1):
        # Try to place randomly max_attempts times.
        for attempt_number in range(1, max_attempts + 1):
            random_value_dict = dict()
            for k, v in random_object_dict.items():
                random_value_dict[k] = v()  # Note that the dispersion object is *called* here.
            self.print_placement_message(cls, attempt_number, shape_number, scalar_dict,
                                         random_value_dict, trial_number)
            # Try to add a shape to the ShapeArray. shape_status is True if successful.
            shape_status = self.add_shape(cls, **scalar_dict, **random_value_dict)
            if self.short_msg:
                print('\r', end='')
            else:
                if shape_status:
                    print('Success!')
                else:
                    print('Failed!')
            if shape_status:
                return
        raise TooManyDispersionAttemptsError(f'Too many dispersion attempts for {shape_number}')

    def print_placement_message(self, cls, attempt_number, shape_number, scalar_dict,
                                random_value_dict, trial_number=None):
        """Print the placement message. TODO"""
        if trial_number is None:
            trial_str = ''
        else:
            trial_str = f'Trial {trial_number: 4d}, '
        if self.part_name is None:
            name_str = ''
        else:
            name_str = f"Part '{self.part_name}': "

        shape_num_str = f'Shape {shape_number: {len(str(self._num_requested_shapes))}d}/{self._num_requested_shapes}'
        if self.short_msg:
            print(f'{name_str}{trial_str}{shape_num_str}, Attempt {attempt_number:4d}, Type {cls.__name__} ',
                  end='')
        else:
            s_k_str = ', '.join(scalar_dict.keys())
            s_v_str = ', '.join(f'{x:2.4f}' for x in scalar_dict.values())
            r_k_str = ', '.join(random_value_dict.keys())
            r_v_str = ', '.join(f'{x:2.4f}' for x in random_value_dict.values())
            print(f'{name_str}{trial_str}{shape_num_str}, Attempt {attempt_number:4d}: '
                  f'Trying to place {cls.__name__} with ({s_k_str})=({s_v_str}) '
                  f'at ({r_k_str})=({r_v_str}) ... ', end='')

    def disperse_shapes(self, max_attempts: int = 5000, max_trials: int = 100, ):
        """

        Args:
            max_attempts: The maximum number of attempts for placement of a shape.
                          If exceeded, the trial ends and the process is restarted.
            max_trials:   The maximum number of trials. If exceeded, an error is raised.
        """

        # Define a number to be used for all shapes.  TODO
        # This number keeps track of the shapes that are dispersed
        # and is not the shape's eventual ID.

        if max_attempts < 1:
            raise ValueError('max_attempts should be >= 1.')
        if max_trials < 1:
            raise ValueError('max_trials should be >= 1.')

        # Backup the state of the ShapeDispersionArray object.
        begin_time = time.perf_counter()
        self._backup_state()
        dispersion_success = False
        for trial_number in range(1, max_trials + 1):
            try:  # Try to run a trial.
                dispersion_success = False  # This isn't strictly necessary.
                shape_number = 0
                for req in self.shape_requests:
                    (cls, num_shapes, list_kwargs, other_kwargs) = req
                    # Loop through the list kwargs.
                    for i in range(num_shapes):
                        shape_number += 1
                        # Put the shape's list_kwargs into a single dict to be passed as scalars.
                        shape_list_kwargs = dict()
                        for k, v in list_kwargs.items():
                            shape_list_kwargs[k] = v[i]
                        # Try to place the shape. Raises TooManyDispersionAttempts if unsuccessful.
                        self.place_shape_randomly(cls, shape_number, max_attempts, trial_number,
                                                  **shape_list_kwargs, **other_kwargs)
                # Both loops have run out and dispersion is successful.
                dispersion_success = True
                break
            except TooManyDispersionAttemptsError:
                # Too many attempts were made.
                # Restore the state of the ShapeDispersionArray object and retry.
                self._restore_state()
        # Either the trial loop has been broken which indicates success,
        # or it has ended which means we have run out of trials without success.
        if dispersion_success:
            elapsed_time = time.perf_counter() - begin_time
            print(f"\nPart '{self.part_name}': {self._num_requested_shapes} shapes dispersed "
                  f"successfully in {elapsed_time:.2f} seconds.")
            self.shape_requests = []
            self._num_requested_shapes = 0
            self._backup_dict = dict()
        else:
            raise TooManyDispersionTrialsError(f'Dispersion has been unsuccessful after {max_trials} trials.')

        # TODO: raise if unsuccessful
        # TODO: Empty the shape_requests list.
        #

    # def place_shapes(self, cls, **kwargs):
    #     """  """
    #     list_kwargs = dict()
    #     other_kwargs = dict()
    #     for k, v in kwargs.items():
    #         if isinstance(v, (DispersionList, DispersionNormalDistribution)):
    #             list_kwargs[k] = v
    #         else:  # It should be passed to the placement function.
    #             other_kwargs[k] = v
    #
    #     # All the list kwargs must have the same length.
    #     list_values_len_set = set(len(x) for x in list_kwargs.values())
    #     if len(list_values_len_set) != 1:
    #         raise ValueError(f'Keyword arguments {*list_kwargs.keys(),} are not of the same length.')
    #
    #     # Loop through the list kwargs.
    #     for i in range(list(list_values_len_set)[0]):
    #         selected_list_kwargs = dict()
    #         for k, v in list_kwargs.items():
    #             selected_list_kwargs[k] = v[i]
    #         self.place_shape_randomly(cls=cls, shape_number=i + 1, max_attempts=max_attempts,
    #                                   **selected_list_kwargs, **other_kwargs)
