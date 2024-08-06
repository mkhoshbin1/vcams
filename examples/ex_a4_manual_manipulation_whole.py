"""Script for Example A-4: Manual Manipulation of the Structure (Whole Array)."""

from numpy import random
from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(5, 5), base_material=1, voxel_size=(0.02, 0.02), name='Ex A4 Manual Manipulation Whole',
                 description='Example A-4: A 5*5 2D part filled with all elements replaced with a random array.',
                 log_debug=True)

# Prepare the random number generator.
rng = random.default_rng()
# Create an array of random integers with the same size and dtype as part.data
# and set the min and max values to 1 and 3, respectively.
random_array = rng.integers(low=1, high=3, size=part.size,
                            dtype=part.data.dtype, endpoint=True)
# Assign random_array to part.data, which replaces its contents.
part.data = random_array

# Output the part.
part.output_abaqus_inp(file_name='ex_a4_manual_manipulation_whole',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
