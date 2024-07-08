"""Script for Example C-4: Randomly Distributed Second Phase (3D)"""
from vcams.voxelpart import VoxelPart
from vcams.mask.random import random_binary_mask

# Create the part.
part = VoxelPart(size=(100, 100, 100), base_material=1,
                 voxel_size=(0.02, 0.02, 0.02),
                 name='Ex C-4 Random Mask 3D Part',
                 description='Example C-4: A two-phase 100*100*100 part with a random distribution of elements.',
                 log_debug=True)

# Create a Boolean mask based on a random distribution of elements.
random_mask = random_binary_mask(part=part, true_fraction=0.42)

# Apply the Boolean mask to the part as material 2.
part.apply_mask(mask=random_mask, value=2)

# Output the part.
part.output_abaqus_inp(file_name='ex_c4_random_mask_3d',
                       elem_code='C3D8R', dim='3D',
                       material_elem_sets='Non-Empty')
