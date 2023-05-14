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


def print_placement_message(cls, try_number, shape_number, scalar_dict, random_value_dict):
    """Print the placement message."""
    s_k_str = ', '.join(scalar_dict.keys())
    s_v_str = ', '.join(f'{x:2.4f}' for x in scalar_dict.values())
    r_k_str = ', '.join(random_value_dict.keys())
    r_v_str = ', '.join(f'{x:2.4f}' for x in random_value_dict.values())
    print(f'Shape {shape_number: 4d}, Attempt {try_number:4d}: '
          f'Trying to place {cls.__name__} with ({s_k_str})=({s_v_str}) '
          f'at ({r_k_str})=({r_v_str}) ... ', end='')


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
    def __init__(self, low, high, boundary):
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
                 voxel_size: tuple[float, float, float] = None):
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
        """
        if dim.upper() not in ['2D', '3D']:
            raise ValueError("dim can only be one of '2D' or '3D'.")
        self.dim = dim.upper()
        """The boolean mask representing the union (logical OR) of the shapes in ShapeArray."""
        # TODO: for 2d, voxel_size should be OK with (x,y) but it isn't.
        if part:
            self.mask_shape = part.size
            self.voxel_size = part.voxel_size
            self.base_mask = (part.data != 0)
            self._full_mask = copy(self.base_mask)
        else:
            self.mask_shape = mask_shape
            self.voxel_size = voxel_size
            self.base_mask = None
            self._full_mask = full(mask_shape, False, dtype=bool)
        self._mask = full(mask_shape, False, dtype=bool)
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
        if len(self) > 0:
            return self._mask
        else:
            raise ValueError('The array is empty.')

    def _add_to_mask(self, new_mask):
        """Add the mask to that of the current array."""
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
        and the mask is recalculated.
        """
        self._check_shape(cls)
        # Create the new shape and calculate its mask.
        new_shape_obj = cls(id=-1, **kwargs)
        new_shape_mask = new_shape_obj.calculate_mask(self.mask_shape, self.voxel_size)

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
            self._add_to_mask(new_mask=new_shape_mask)
            return True

    def place_shape_randomly(self, cls, shape_number: int, max_tries: int = 5000, **kwargs):
        """Place a shape in a random position.

        Args:
            cls: The shape class that should be placed. Arguments are passed as *kwargs*.
            shape_number: The number of this shape. Used for printing the progress messages.
            max_tries: The maximum number of tries for placement of a shape. An error is raised if it is exceeded.
            kwargs: A dictionary containing *DispersionRandom* objects
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

        # Try to place randomly.
        for i in range(1, max_tries + 1):
            random_value_dict = dict()
            for k, v in random_object_dict.items():
                random_value_dict[k] = v()
            print_placement_message(cls, i, shape_number, scalar_dict, random_value_dict)
            shape_status = self.add_shape(cls, **scalar_dict, **random_value_dict)
            if shape_status:
                print('Success!')  # TODO: use debug log for this and add an info log when done.
                return
            else:
                print('Failed!')
        raise RuntimeError(f'Exceeded maximum number of tries {max_tries}.')

    def place_shapes(self, cls, max_tries=5000, **kwargs):
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
            self.place_shape_randomly(cls=cls, shape_number=i + 1, max_tries=max_tries,
                                      **selected_list_kwargs, **other_kwargs)
