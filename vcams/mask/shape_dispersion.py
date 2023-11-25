"""Classes used for dispersing shapes inside a :class:`~vcams.voxelpart.VoxelPart`."""

import logging
from itertools import count
from numpy import squeeze, logical_or, full, copy, logical_and, var, std, mean, random, any

logger = logging.getLogger(__name__)


# TODO: document all functions.


def plot_dispersion_object(dispersion_obj, num_bins):
    """Plot a histogram of the dispersion object."""
    import matplotlib.pyplot as plt
    plt.hist(dispersion_obj, num_bins, density=True)
    plt.show()


class DispersionList(list):
    """A Dispersion list defined using a list.
    This is simply a list and is only created to have a uniform naming.
    """

    def __call__(self):
        return self.pop()

    def __repr__(self):
        return f"""{self.__class__}
        Number of Values: {len(self)}
        Actual SD:        {mean(self)}
        Actual SD:        {std(self)}
        Actual Variance:  {var(self)}
        """


class DispersionNormalDistribution:
    """A Dispersion list defined using mean and standard deviation.
    Iterating over the object is equivalent to iterating over the object's *values* attribute."""

    def __init__(self, target_mean: float, target_sd: float, num_values: int):
        self.target_mean = target_mean
        self.target_sd = target_sd
        self.values = random.default_rng().normal(loc=target_mean, scale=target_sd, size=num_values)
        self.actual_mean = mean(self.values)
        self.actual_sd = std(self.values)
        self.actual_variance = var(self.values)

    def __iter__(self):
        return self.values.__iter__()

    def __getitem__(self, index):
        return self.values[index]

    def __len__(self):
        return len(self.values)

    def __mul__(self, other):
        return DispersionList(self.values * other)

    def __repr__(self):
        return f"""{self.__class__}
        Number of Values: {len(self.values)}
        Target Mean:      {self.target_mean}
        Actual Mean:      {self.actual_mean}
        Target SD:        {self.target_sd}
        Actual SD:        {self.actual_sd}
        Actual Variance:  {self.actual_variance}
        """


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


class ShapeDispersionArray:
    """TODO: doc
    TODO: if part is specified, it's used as background."""

    def __init__(self, dim: str, part=None,
                 mask_shape: tuple[int, int, int] = None,
                 voxel_size: tuple[float, float, float] = None,
                 num_bound_pixels: int = 0,
                 max_attempts: int = 5000, max_trials: int = 100,
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
            max_attempts: The maximum number of attempts for placement of a shape.
                          If exceeded, the trial ends and the process is restarted.
            max_trials:   The maximum number of trials. If exceeded, an error is raised.
            short_msg: A boolean specifying whether the placement message should be printed
                       as a single updating line or in many lines with extensive details.
                       Passed to :func:`.print_placement_message` Defaults to *True*.
        """
        if dim.upper() not in ['2D', '3D']:
            raise ValueError("dim can only be one of '2D' or '3D'.")
        self.dim = dim.upper()
        """The boolean mask representing the union (logical OR) of the shapes in ShapeArray."""
        # TODO: for 2d, voxel_size should be OK with (x,y) but it isn't.


        if max_attempts < 1:
            raise ValueError("max_attempts should be >= 1.")
        self.max_attempts = max_attempts
        """See :meth:`.__init__`."""

        if max_trials < 1:
            raise ValueError("max_trials should be >= 1.")
        self.max_trials = max_trials
        """See :meth:`.__init__`."""

        self.short_msg = short_msg
        """See :meth:`.__init__`."""

        if part:
            self.part_name = part.name
            self.mask_shape = part.size
            self.voxel_size = part.voxel_size
            self.base_mask = (part.data != 0)
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
        """TODO"""

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

    def place_shapes(self, cls, **kwargs):
        """  """
        list_kwargs = dict()
        other_kwargs = dict()
        for k, v in kwargs.items():
            if isinstance(v, (DispersionList, DispersionNormalDistribution)):
                list_kwargs[k] = v
            else:  # It should be passed to the placement function.
                other_kwargs[k] = v

        # All the list kwargs must have the same length.
        list_values_len_set = set(len(x) for x in list_kwargs.values())
        if len(list_values_len_set) != 1:
            raise ValueError(f'Keyword arguments {*list_kwargs.keys(),} are not of the same length.')

        # Loop through the list kwargs.
        for i in range(list(list_values_len_set)[0]):
            selected_list_kwargs = dict()
            for k, v in list_kwargs.items():
                selected_list_kwargs[k] = v[i]
            self.place_shape_randomly(cls=cls, shape_number=i + 1, **selected_list_kwargs, **other_kwargs)

    def place_shape_randomly(self, cls, shape_number: int, **kwargs):
        """Place a shape in a random position.

        Args:
            cls: The shape class that should be placed. Arguments are passed as *kwargs*.
            shape_number: The number of this shape. Used for printing the progress messages.
            kwargs:       A dictionary containing *DispersionRandom* objects
                          for the placement arguments and scalars for the rest of the arguments.
        """

        # Separate random and scalar kwargs.
        scalar_dict = dict()
        random_object_dict = dict()
        for k, v in kwargs.items():
            if isinstance(v, DispersionRandom):
                random_object_dict[k] = v
            else:  # Assume it's a scalar.
                scalar_dict[k] = v

        # Try to run the process max_trials times.
        for trial_number in range(1, self.max_trials + 1):
            # Try to place randomly max_attempts times.
            for attempt_number in range(1, self.max_attempts + 1):
                random_value_dict = dict()
                for k, v in random_object_dict.items():
                    random_value_dict[k] = v()
                self.print_placement_message(cls, attempt_number, shape_number, scalar_dict,
                                             random_value_dict, trial_number=1)
                # Try to add a shape to the ShapeArray and return True if successful.
                shape_status = self.add_shape(cls, **scalar_dict, **random_value_dict)
                if self.short_msg:
                    print('\r', end='')
                    if shape_status:
                        return
                else:
                    if shape_status:
                        print('Success!')  # TODO: use debug log for this and add an info log when done.
                        return
                    else:
                        print('Failed!')
            #FIXME : somehow revert to the beggining of the trial.
        #TODO: if sucessful, replace line with a final message.
        raise RuntimeError(f'Exceeded maximum number of trials {self.max_trials}.')


    def print_placement_message(self, cls, attempt_number, shape_number, scalar_dict, random_value_dict,
                                trial_number=None):
        """Print the placement message. TODO"""
        if trial_number is None:
            trial_str = ''
        else:
            trial_str = f'Trial {trial_number: 4d}, '
        if self.part_name is None:
            name_str = ''
        else:
            name_str = f"Part '{self.part_name}': "
        if self.short_msg:
            print(f'{name_str}{trial_str}Shape {shape_number: 4d}, Attempt {attempt_number:4d}, Type {cls.__name__} ',
                  end='')
        else:
            s_k_str = ', '.join(scalar_dict.keys())
            s_v_str = ', '.join(f'{x:2.4f}' for x in scalar_dict.values())
            r_k_str = ', '.join(random_value_dict.keys())
            r_v_str = ', '.join(f'{x:2.4f}' for x in random_value_dict.values())
            print(f'Shape {shape_number: 4d}, Attempt {attempt_number:4d}: '
                  f'Trying to place {cls.__name__} with ({s_k_str})=({s_v_str}) '
                  f'at ({r_k_str})=({r_v_str}) ... ', end='')

