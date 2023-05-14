"""Script for Example C-4: Shape Array."""
from vcams.voxelpart import VoxelPart
from vcams.mask.shape import Circle, Ellipse
from vcams.mask.shape_dispersion import ShapeDispersionArray, DispersionRandom, DispersionNormalDistribution, DispersionList

# Create the part.
part = VoxelPart(size=(250, 250), base_material=1,
                 voxel_size=(0.004, 0.004),
                 name='Ex C-4 Shape Dispersion',
                 description='A 2D square 50*50 part created using an array of circular shapes.',
                 log_debug=True)

# Create a ShapeArray based on the VoxelPart object.
shape_disp_array_obj = ShapeDispersionArray(dim='2D', mask_shape=part.size, voxel_size=tuple(part.voxel_size))

# Add shapes to shape_disp_array_obj.
# Note that the class object is passed as the first argument.
# shape_disp_array_obj.add_shape(Circle, xc=0, yc=0, r=0.1)
# shape_disp_array_obj.add_shape(Circle, xc=1, yc=1, r=0.1)
# print(shape_disp_array_obj.add_shape(Circle, xc=0.4, yc=0.2, r=0.15))
# print(shape_disp_array_obj.add_shape(Circle, xc=0.7, yc=0.5, r=0.1))
#
bound = 0.015
r = DispersionNormalDistribution(target_mean=0.10, target_sd=0.03, num_values=10)
br = DispersionList(len(r) * [bound])
xc = DispersionRandom(max(r), 1-max(r), bound)
yc = DispersionRandom(max(r), 1-max(r), bound)

shape_disp_array_obj.place_shapes(Circle, xc=xc, yc=yc, r=r, br=br)

# shape_disp_array_obj.place_shape_randomly(Circle, xc=xc, yc=yc, r=0.8, shape_number=1)
#
# print(shape_disp_array_obj.add_shape(Circle,
# xc=0.4364109988301008, yc=0.7954004794280207, r=0.1))


# Apply the Boolean mask to the part.
part.apply_mask(mask=shape_disp_array_obj.mask, value=2)

# Output the part.
part.output_abaqus_inp(file_name='ex_c11_shape_dispersion',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
