"""Script for Example A-7: Manipulation of the Structure Using Masks (II)."""

from numpy import random
from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(50, 75, 100), base_material=0, voxel_size=(0.02, 0.02, 0.02), name='Ex A-7 Mask Manipulation 2',
                 description='Example A-7: A 50*75*100 part created using a random boolean mask.', log_debug=True)

# Create a random mask with the same shape as part.data.
random_mask = random.choice((True, False), size=part.data.shape)

# Apply the mask to the part.
part.apply_mask(mask=random_mask, value=1)

# Output the part.
part.output_abaqus_inp(file_name='ex_a7_mask_manipulation_2',
                       elem_code='C3D8R', dim='3D',
                       material_elem_sets='Non-Empty')
