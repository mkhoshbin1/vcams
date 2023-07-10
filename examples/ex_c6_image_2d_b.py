"""Second Script for Example C-6: Part from Image (2D)."""
from numpy import rot90

from vcams.voxelpart import voxelpart_from_image

# Create a Boolean mask based on an image.
# The image is taken from https://en.wikipedia.org/wiki/File:Dual_Phase_Steel.jpg
# and is under the CC BY-SA 4.0 license.
part = voxelpart_from_image(image_dim='2D',
                            image_path='ex_c6_image_2d_input.jpg',
                            scale=1.0, denoise=True,
                            background_material=1, foreground_material=2,
                            voxel_size=(0.02, 0.02),
                            name='Ex C-6 Part from Image 2D - B',
                            description='A 2D part created based on a 2D image.',
                            log_debug=True)

# Output the part.
part.output_abaqus_inp(file_name='ex_c6_image_2d_b',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
