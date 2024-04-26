"""Script for Example C-4: Shape Array."""
from vcams.voxelpart import VoxelPart
from vcams.mask.shape import Circle, Ellipse, EllipseFromAspectRatio
from vcams.mask.shape_dispersion import ShapeDispersionArray, RandomDispersion, NormalDistributionDispersion, \
    ManualListDispersion, TruncatedNormalDistributionDispersion

import numpy as np
from scipy import optimize
from scipy.optimize import milp

# Create the part.
part = VoxelPart(size=(250, 250), base_material=1,
                 voxel_size=(0.008, 0.008),
                 name='Ex C-12 Shape Dispersion Volume',
                 description='A 2D square 250*250 part created with shapes dispersed in it.',
                 log_debug=True)

# Create a ShapeArray based on the VoxelPart object.
num_bound_pixels = 2
bound = num_bound_pixels * part.voxel_size[0]
shape_disp_array_obj = ShapeDispersionArray(dim='2D', part=part,
                                            num_bound_pixels=num_bound_pixels,
                                            short_msg=True)

min_valid_r = 4 * part.voxel_size[0]
num_shapes = 7
# Request circles.
circle_r = TruncatedNormalDistributionDispersion(target_mean=0.10, target_std=0.03, bound_a=min_valid_r)
circle_xc = RandomDispersion(0, part.real_size[0], bound)
circle_yc = RandomDispersion(0, part.real_size[1], bound)
shape_disp_array_obj.add_shape_request(num_shapes=None, cls=Circle,
                                       xc=circle_xc, yc=circle_yc, r=circle_r, br=bound)

# Request ellipses.
ellipse_a = TruncatedNormalDistributionDispersion(target_mean=0.10, target_std=0.03, bound_a=min_valid_r)
ellipse_aspect_ratio = TruncatedNormalDistributionDispersion(target_mean=1.5, target_std=0.5, bound_a=min_valid_r)
ellipse_xc = RandomDispersion(0, part.real_size[0])
ellipse_yc = RandomDispersion(0, part.real_size[1])
ellipse_alpha = RandomDispersion(low=0, high=360)
shape_disp_array_obj.add_shape_request(num_shapes=None, cls=EllipseFromAspectRatio,
                                       xc=ellipse_xc, yc=ellipse_yc, alpha=ellipse_alpha,
                                       a=ellipse_a, aspect_ratio=ellipse_aspect_ratio,
                                       ba=bound, bb=bound)
shape_disp_array_obj.disperse_shapes_vf(target_vf=0.20, vf_tolerance=0.01,
                                        max_attempts=100, max_trials=100,
                                        max_generations=100)


# Apply the Boolean mask to the part.
part.apply_mask(mask=shape_disp_array_obj.mask, value=2)
#
# len(part.data[part.data==2]) / part.data.size
#
part.add_bc(bc_type='Periodic')

# # Output the part.
part.output_abaqus_inp(file_name='ex_c12_shape_dispersion_volume',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
