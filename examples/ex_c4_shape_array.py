"""Script for Example C-4: Shape Array."""

from vcams.voxelpart import VoxelPart
from vcams.mask.shape import ShapeArray, Circle, Ellipse

# Create the part.
part = VoxelPart(size=(50, 50), base_material=1,
                 voxel_size=(0.02, 0.02),
                 name='Ex C-4 Shape Array',
                 description='A 2D square 50*50 part created using an array of circular shapes.',
                 log_debug=True)

# Create a ShapeArray based on the VoxelPart object.
shape_array_obj = ShapeArray(dim='2D', part=part)

# Add shapes to shape_array_obj.
# Note that the class object is passed as the first argument.
shape_array_obj.add_shape(Circle, xc=0, yc=0, r=0.1)
shape_array_obj.add_shape(Circle, xc=0.4, yc=0.2, r=0.15)
shape_array_obj.add_shape(Circle, xc=0.7, yc=0.5, r=0.1)
shape_array_obj.add_shape(Ellipse, a=0.15, b=0.30, xc=0.30, yc=0.65, alpha=20)
# Apply the Boolean mask to the part.
part.apply_mask(mask=shape_array_obj.mask, value=2)

# Output the part.
part.output_abaqus_inp(file_name='ex_c4_shape_array',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
