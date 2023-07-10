"""First Script for Example C-7: Part from Image Series (3D)."""

from vcams.mask.image import mask_from_image_sequence
from vcams.voxelpart import VoxelPart

# Create a Boolean mask based on the image stack.
# The image stack is taken from https://doi.org/10.6084/m9.figshare.c.3795019.v1
# Which is from the article in https://doi.org/10.1038/sdata.2018.100.
# Note that size of voxels in the unscaled image is 5.06278 micrometers.
image_mask = mask_from_image_sequence(load_pattern=r'D:\MicroCT of mouse tibiae-oim4\28Oim__rec0???.bmp',
                                      scale=0.5, denoise=True)

# Create the part based on the size of image_mask.
part = VoxelPart(size=image_mask.shape, base_material=0,
                 voxel_size=(0.01012, 0.01012, 0.01012),
                 name='Ex C-7 Part from Image Series 3D - A',
                 description='A 3D part created based on a series of 2D images.',
                 log_debug=True)

# Apply the Boolean mask to the part.
# The elements selected by the mask will be set to 1.
part.apply_mask(mask=image_mask, value=1)

# Output the part.
part.output_abaqus_inp(file_name='ex_c7_image_3d_a',
                       elem_code='C3D8R', dim='3D',
                       material_elem_sets='Non-Empty')
