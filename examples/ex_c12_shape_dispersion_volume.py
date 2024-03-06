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
shape_disp_array_obj.add_shape_request2(num_shapes=None, cls=Circle,
                                        xc=circle_xc, yc=circle_yc, r=circle_r, br=bound)

# Request ellipses.
ellipse_a = TruncatedNormalDistributionDispersion(target_mean=0.10, target_std=0.03, bound_a=min_valid_r)
ellipse_aspect_ratio = TruncatedNormalDistributionDispersion(target_mean=1.5, target_std=0.5, bound_a=min_valid_r)
ellipse_xc = RandomDispersion(0, part.real_size[0])
ellipse_yc = RandomDispersion(0, part.real_size[1])
ellipse_alpha = RandomDispersion(low=0, high=360)
shape_disp_array_obj.add_shape_request2(num_shapes=None, cls=EllipseFromAspectRatio,
                                        xc=ellipse_xc, yc=ellipse_yc, alpha=ellipse_alpha,
                                        a=ellipse_a, aspect_ratio=ellipse_aspect_ratio,
                                        ba=bound, bb=bound)

# suitable_num_shapes = shape_disp_array_obj._find_suitable_num_shapes(target_vf=0.30, vf_tolerance=0.01,
#                                                                      print_progress=True)
# shape_disp_array_obj.disperse_shapes_knapsack(suitable_num_shapes)

shape_disp_array_obj.disperse_shapes_vf(target_vf=0.20, vf_tolerance=0.01,
                                        max_attempts=100, max_trials=100,
                                        print_progress=True)

# #
# #
# # # The offending ones can be removed from the shapes dict
# # # and there is a function for re-calculating the mask.
# #
# shape_volume_fraction_list = np.array([i.real_volume_fraction for i in shape_disp_array_obj.shapes.values()])
# # All instances of MyClass have equal value.
# shape_values = np.full_like(shape_volume_fraction_list, 1.0)
#
# print(shape_volume_fraction_list)
# print(sum(shape_volume_fraction_list))
#
# target_volume = 0.15
# pct_error = 0.005  # Acceptable error as percentage of target_area.
#
# # Set decision variable (x_i) to be between 0 and 1 and to be integers.
# # This makes them effectively Boolean, and they can be cast to bool in the end.
# integrality = np.full_like(shape_values, True)  # x_i must be integers within bounds.
# bounds = optimize.Bounds(0, 1)  # x_i must be between 0 and 1.
#
# # Calculate and set the upper and lower bounds.
# lb = (1 - pct_error) * target_volume
# ub = (1 + pct_error) * target_volume
# constraints = optimize.LinearConstraint(A=shape_volume_fraction_list, lb=lb, ub=ub)
#
# optimization_result = milp(c=-shape_values, constraints=constraints,
#                            integrality=integrality, bounds=bounds)
#
# if not optimization_result.success:
#     raise RuntimeError('The MILP optimization procedure failed!')
#
# delete_status_arr = np.invert(optimization_result.x.astype(bool))
# shape_keys_arr = np.array(list(shape_disp_array_obj.shapes))
# to_delete_idx = shape_keys_arr[delete_status_arr]
#
# print(f'Total area: {shape_volume_fraction_list[optimization_result.x.astype(bool)].sum()}')
# print(shape_volume_fraction_list[optimization_result.x.astype(bool)])
# ## TODO: couunt the number of false and raise if more than 10%
#
#
# # a.sort()
# #
# #
# Apply the Boolean mask to the part.
part.apply_mask(mask=shape_disp_array_obj.mask, value=2)
#
# len(part.data[part.data==2]) / part.data.size
#
# # Output the part.
part.output_abaqus_inp(file_name='ex_c12_shape_dispersion_volume',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
