"""Script for Example C-11: Dispersion of Shapes based on Volume Fraction"""

from vcams.mask.shape import Circle, EllipseFromAspectRatio
from vcams.mask.shape_dispersion import ShapeDispersionArray, RandomDispersion, TruncatedNormalDistributionDispersion
from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(200, 200), base_material=1, voxel_size=(0.005, 0.005),
                 name='Ex C-11 Dispersion Shapes VF',
                 description='A 2D square 200*200 part created with '
                             'a volume fraction of shapes randomly dispersed in it.', log_debug=True)

# Set the number of boundary pixels and calculate the respective length.
num_bound_pixels = 2
bound_length = num_bound_pixels * part.voxel_size[0]

# Set the minimum value for radius used for truncating the random distributions.
min_valid_r = 4 * part.voxel_size[0]

# Create a ShapeArray based on the VoxelPart object.
shape_disp_array_obj = ShapeDispersionArray(dim='2D', part=part,
                                            num_bound_pixels=0, wrap_mask=True, short_msg=True)

# Request the circles.
# Note that the boundary for RandomDispersion instances
# is only set to bound_length because we do not have any values
# for the radius so there is no maximum radius to be added to it.
# This means that some circles may touch the boundary.
circle_r = TruncatedNormalDistributionDispersion(target_mean=0.05, target_std=0.02, bound_a=min_valid_r)
circle_xc = RandomDispersion(0, part.real_size[0], bound_length)
circle_yc = RandomDispersion(0, part.real_size[1], bound_length)
shape_disp_array_obj.add_shape_request(num_shapes=None, cls=Circle,
                                       xc=circle_xc, yc=circle_yc, r=circle_r, br=bound_length)

# Request the ellipses.
ellipse_a = TruncatedNormalDistributionDispersion(target_mean=0.06, target_std=0.03, bound_a=min_valid_r)
ellipse_aspect_ratio = TruncatedNormalDistributionDispersion(target_mean=1, target_std=0.25, bound_a=0.1)
ellipse_xc = RandomDispersion(0, part.real_size[0])
ellipse_yc = RandomDispersion(0, part.real_size[1])
ellipse_alpha = RandomDispersion(low=0, high=180)
shape_disp_array_obj.add_shape_request(num_shapes=None, cls=EllipseFromAspectRatio,
                                       xc=ellipse_xc, yc=ellipse_yc, alpha=ellipse_alpha,
                                       a=ellipse_a, aspect_ratio=ellipse_aspect_ratio,
                                       ba=bound_length, bb=bound_length)

# Disperse the shapes in shape_disp_array_obj with the desired target_vf.
shape_disp_array_obj.disperse_shapes_vf(target_vf=0.30, vf_tolerance=0.03,
                                        min_num_shapes=5, max_num_shapes=20,
                                        max_attempts=100, max_trials=1000, max_generations=100)

# Apply the Boolean mask to the part.
part.apply_mask(mask=shape_disp_array_obj.mask, value=2)

# # Output the part.
part.output_abaqus_inp(file_name='ex_c11_shape_dispersion_vf',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
