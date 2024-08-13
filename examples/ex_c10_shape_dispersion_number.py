"""Script for Example C-10: Dispersion of Specified Number of Shapes"""

from vcams.mask.shape import Circle, EllipseFromAspectRatio
from vcams.mask.shape_dispersion import ShapeDispersionArray, RandomDispersion, TruncatedNormalDistributionDispersion
from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(200, 200), base_material=1, voxel_size=(0.005, 0.005),
                 name='Ex C-10 Dispersion of a Specified Number of Shapes',
                 description='A 2D square 200*200 part created with '
                             'a specified number of shapes randomly dispersed in it.', log_debug=True)

# Set the number of boundary pixels and calculate the respective length.
num_bound_pixels = 2
bound_length = num_bound_pixels * part.voxel_size[0]

# Set the minimum value for radius used for truncating the random distributions.
min_valid_r = 4 * part.voxel_size[0]

# Create a ShapeArray based on the VoxelPart object.
shape_disp_array_obj = ShapeDispersionArray(dim='2D', part=part,
                                            num_bound_pixels=num_bound_pixels,
                                            short_msg=True)

# Request the circles.
num_circle = 10
circle_r = TruncatedNormalDistributionDispersion(num_values=num_circle,
                                                 target_mean=0.06, target_std=0.03, bound_a=min_valid_r)
circle_xc = RandomDispersion(0, part.real_size[0], max(circle_r) + bound_length)
circle_yc = RandomDispersion(0, part.real_size[1], max(circle_r) + bound_length)
shape_disp_array_obj.add_shape_request(num_shapes=num_circle, cls=Circle,
                                       xc=circle_xc, yc=circle_yc, r=circle_r, br=bound_length)

# Request the ellipses.
num_ellipse = 10
ellipse_a = TruncatedNormalDistributionDispersion(num_values=num_ellipse,
                                                  target_mean=0.06, target_std=0.03, bound_a=min_valid_r)
ellipse_aspect_ratio = TruncatedNormalDistributionDispersion(num_values=num_ellipse,
                                                             target_mean=0.75, target_std=0.75, bound_a=0.1)
ellipse_xc = RandomDispersion(0, part.real_size[0])
ellipse_yc = RandomDispersion(0, part.real_size[1])
ellipse_alpha = RandomDispersion(low=0, high=360)
shape_disp_array_obj.add_shape_request(num_shapes=num_ellipse, cls=EllipseFromAspectRatio,
                                       xc=ellipse_xc, yc=ellipse_yc, alpha=ellipse_alpha,
                                       a=ellipse_a, aspect_ratio=ellipse_aspect_ratio,
                                       ba=bound_length, bb=bound_length)

# Disperse the shapes in shape_disp_array_obj.
shape_disp_array_obj.disperse_shapes()

# Apply the Boolean mask to the part.
part.apply_mask(mask=shape_disp_array_obj.mask, value=2)

# Output the part.
part.output_abaqus_inp(file_name='ex_c10_shape_dispersion_number',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
