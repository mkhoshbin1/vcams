"""In this example, a complete part with a shape of 50*50*50 voxels is created.
Then, a random distribution of materials is assigned to it.
Finally, the part is output to abaqus with a uniform scale of 0.02 in all directions."""

import numpy as np
import vcams.voxelpart

results_path = 'path\\to\\results\\directory'

# Create a part.
part = vcams.voxelpart.VoxelPart(size=(50, 50, 50), fill_value=1,
                                 name='Random 3D Part',
                                 description='A cubic 50*50*50 part filled with elements.',
                                 logger_path=results_path)

# Assign a random distribution of materials 1, 2, and 3 to the part.
rng = np.random.default_rng()
part.data = rng.integers(low=1, high=3, size=part.data.shape,
                         dtype=part.data.dtype, endpoint=True)

# Output the part.
part.output_abaqus_inp(file_name='random_part_3d', folder_path=results_path,
                       elem_type='C3D8R', dim='3D',
                       scale=(0.02, 0.02),
                       material_elem_sets=(1, 2, 3), custom_elem_sets=True)
