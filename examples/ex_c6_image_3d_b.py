"""Second Script for Example C-6: Part from Image Series (3D)"""

from vcams.voxelpart import voxelpart_from_image

# Create the part from the image stack.
# The image stack is taken from https://doi.org/10.6084/m9.figshare.c.3795019.v1
# Which is from the article in https://doi.org/10.1038/sdata.2018.100.
# Note that size of voxels in the unscaled image is 5.06278 micrometers.
part = voxelpart_from_image(image_dim='3D',
                            image_path=r'D:\MicroCT of mouse tibiae-oim4\28Oim__rec0???.bmp',
                            scale=0.5, denoise=True,
                            background_material=0, foreground_material=1,
                            voxel_size=(0.01012, 0.01012, 0.01012),
                            name='Ex C-6 Part from Image Series 3D - B',
                            description='A 3D part created based on a series of 2D images.',
                            log_debug=True)

# Output the part.
part.output_abaqus_inp(file_name='ex_c6_image_3d_b',
                       elem_code='C3D8R', dim='3D',
                       material_elem_sets='Non-Empty')
