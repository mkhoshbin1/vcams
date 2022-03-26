"""Script for Example C-7: Part from Image Series (3D)."""
from numpy import rot90

from vcams.mask.image import mask_from_image_sequence
from vcams.voxelpart import VoxelPart

# Create a Boolean mask based on an image.
# The image is taken from

# The image is taken from https://en.wikipedia.org/wiki/File:Dual_Phase_Steel.jpg
# and is under the CC BY-SA 4.0 license.
image_mask = mask_from_image_sequence(load_pattern=r'D:\MicroCT of mouse tibiae-oim4\28Oim__rec0???.bmp',
                                      scale=1.0, denoise=True)

# Create the part based on the size of image_mask.
part = VoxelPart(size=image_mask.shape, base_material=0,
                 voxel_size=(0.00506, 0.00506, 0.00506),
                 name='Ex C-7 Part from Image Series 3D',
                 description='A 3D part created based on a series of 2D images.',
                 log_debug=True)

# Apply the Boolean mask to the part.
# The elements selected by the mask will be set to 1.
part.apply_mask(mask=image_mask, value=1)

# Output the part.
part.output_abaqus_inp(file_name='ex_c7_image_3d',
                       elem_code='C3D8R', dim='3D',
                       material_elem_sets='Non-Empty')
