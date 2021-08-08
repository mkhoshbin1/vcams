"""In this example, an empty part with a shape of 50*50 voxels is created.
Then, a random mask is applied and used to determine where material values must be equal to one.
Finally, the part is output to abaqus with a uniform scale of 0.02 in all directions."""

import numpy as np
import vcams

results_path = 'path\\to\\results\\directory'

# Create a part.
part = vcams.voxelpart.VoxelPart(size=(50, 50), fill_value=0,
                                 name='Random Mask 2D Part',
                                 description='A square 50*50 part created using a random mask.',
                                 logger_path=results_path)

# Create a random mask with the same shape as part.data.
random_mask = np.random.choice((True, False), size=part.data.shape)

# Apply the mask to the part.
part.apply_mask(mask=random_mask, value=1)

# Output the part.
part.output_abaqus_inp(file_name='mask_part_2d', folder_path=results_path,
                       elem_type='CPE4R', dim='2D',
                       scale=(0.02, 0.02),
                       material_elem_sets=(1,), custom_elem_sets=True)
