"""Script for Example A-5: Random 3D Model."""

from numpy import random
from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(50, 75, 100), base_material=1,
                 voxel_size=(0.02, 0.02, 0.02),
                 name='Ex A5 Random 3D Part',
                 description='Example A-5: A 50*75*100 3D part filled with random elements.',
                 log_debug=True)

# Prepare the random number generator.
rng = random.default_rng()
# Create an array of random integers with the same size and dtype as part.data
# and set the min and max values to 1 and 3, respectively.
random_array = rng.integers(low=1, high=3, size=part.data.shape,
                            dtype=part.data.dtype, endpoint=True)
# Assign random_array to part.data, which replaces its contents.
part.data = random_array

# Output the part.
part.output_abaqus_inp(file_name='ex_a5_random_3d_part',
                       elem_code='C3D8R', dim='3D',
                       material_elem_sets='Non-Empty')
