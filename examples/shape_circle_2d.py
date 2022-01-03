"""In this example, a full part with a shape of 50*50 voxels is created.
Then, a number of circles are used to create a mask.
Afterwards, the mask is used to determine where material values must be equal to two.
Finally, the part is output to abaqus with a uniform scale of 0.02 in all directions.
The result is a cubic part where the center is a sphere with a material code of 2,
while the rest of the cube has a material code of 1."""

import vcams
from vcams.mask.shape import ShapeArray, Circle

results_path = 'path\\to\\results\\directory'

# Create a part.
part = vcams.voxelpart.VoxelPart(size=(50, 50), base_material=1,
                                 voxel_size=(0.02, 0.02),
                                 name='Shape Circle 2D Part',
                                 description='A square 50*50 part created using a circle mask.')

# Create a mask with the same shape and voxel_size as the part.
t = part.data.shape[0] * part.voxel_size[0] / 2

shape_array = ShapeArray(dim='2D', part_shape=part.data.shape,
                         voxel_size=part.voxel_size, is_mask_calculation_lazy=True)
shape_array.add_shape(Circle, a=0, b=0, r=0.1)
shape_array.add_shape(Circle, a=0.4, b=0.2, r=0.15)
shape_array.add_shape(Circle, a=0.7, b=0.5, r=0.15)

# Apply the mask to the part.
part.apply_mask(mask=shape_array.mask, value=2)

# Output the part.
part.output_abaqus_inp(file_name='shape_circle_2d',
                       elem_type='CPE4R', dim='2D',
                       material_elem_sets='All', custom_elem_sets=True)
