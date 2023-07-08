"""First Script for Example C-6: Part from Image (2D)."""
from numpy import rot90

from vcams.mask.image import mask_from_image
from vcams.voxelpart import VoxelPart

# Create a Boolean mask based on an image.
# The image is taken from https://en.wikipedia.org/wiki/File:Dual_Phase_Steel.jpg
# and is under the CC BY-SA 4.0 license.
image_mask = mask_from_image(image_path='ex_c6_image_2d_input.jpg',
                             scale=1.0, denoise=True)

# The mask must be rotated -90 degrees to account for the
# difference between the XY directions in Abaqus and the picture.
image_mask = rot90(image_mask, -1)

# Create the part based on the size of image_mask.
part = VoxelPart(size=image_mask.shape, base_material=1,
                 voxel_size=(0.02, 0.02),
                 name='Ex C-6 Part from Image 2D - A',
                 description='A 2D part created based on a 2D image.',
                 log_debug=True)

# Apply the Boolean mask to the part.
# The elements selected by the mask will be set to 2,
# while the rest will be 1.
part.apply_mask(mask=image_mask, value=2)

# Output the part.
part.output_abaqus_inp(file_name='ex_c6_image_2d_a',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
