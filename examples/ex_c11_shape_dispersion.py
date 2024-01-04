"""Script for Example C-4: Shape Array."""
from vcams.voxelpart import VoxelPart
from vcams.mask.shape import Circle, Ellipse, EllipseFromAspectRatio
from vcams.mask.shape_dispersion import ShapeDispersionArray, RandomDispersion, NormalDistributionDispersion, \
    ManualListDispersion

# Create the part.
part = VoxelPart(size=(250, 250), base_material=1,
                 voxel_size=(0.008, 0.008),
                 name='Ex C-11 Shape Dispersion',
                 description='A 2D square 250*250 part created with shapes dispersed in it.',
                 log_debug=True)

# Create a ShapeArray based on the VoxelPart object.
num_bound_pixels = 2
bound = num_bound_pixels * part.voxel_size[0]
shape_disp_array_obj = ShapeDispersionArray(dim='2D', part=part,
                                            num_bound_pixels=num_bound_pixels,
                                            short_msg=True)

# Request circles.
num_circles = 5
circle_r = NormalDistributionDispersion(target_mean=0.10, target_sd=0.03, num_values=num_circles)
circle_xc = RandomDispersion(0, part.real_size[0], max(circle_r) + bound)
circle_yc = RandomDispersion(0, part.real_size[1], max(circle_r) + bound)
shape_disp_array_obj.add_shape_request(num_shapes=num_circles, cls=Circle,
                                       xc=circle_xc, yc=circle_yc, r=circle_r, br=bound)

# Request ellipses.
num_ellipse = 5
ellipse_a = NormalDistributionDispersion(target_mean=0.10, target_sd=0.03, num_values=num_ellipse)
ellipse_aspect_ratio = NormalDistributionDispersion(target_mean=3, target_sd=1, num_values=num_ellipse)
ellipse_xc = RandomDispersion(0, part.real_size[0])
ellipse_yc = RandomDispersion(0, part.real_size[1])
ellipse_alpha = RandomDispersion(low=0, high=360)
shape_disp_array_obj.add_shape_request(num_shapes=num_ellipse, cls=EllipseFromAspectRatio,
                                       xc=ellipse_xc, yc=ellipse_yc, alpha=ellipse_alpha,
                                       a=ellipse_a, aspect_ratio=ellipse_aspect_ratio,
                                       ba=bound, bb=bound)

shape_disp_array_obj.disperse_shapes()

# Apply the Boolean mask to the part.
part.apply_mask(mask=shape_disp_array_obj.mask, value=2)

# Output the part.
part.output_abaqus_inp(file_name='ex_c11_shape_dispersion',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
