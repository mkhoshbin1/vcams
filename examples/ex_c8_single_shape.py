"""Script for Example C-8: Single Shape"""

from vcams import mask
from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(50, 50), base_material=1,
                 voxel_size=(0.02, 0.02),
                 name='Ex C-8 Single Shape',
                 description='A 2D square 50*50 part including a single circular inclusion.',
                 log_debug=True)

# Create an instance of the vcams.mask.shape.Circle class.
# All properties are defined when the object is created.
t = part.real_size[0] / 2
circle_obj = mask.shape.Circle(id=0, xc=t, yc=t, r=t)

# Create a Boolean mask based on the VoxelPart object.
# For the mask function use circle_obj.func. No other parameters are necessary.
circle_mask = mask.function.mask_from_function(part=part, func=circle_obj.func)

# Apply the Boolean mask to the part.
part.apply_mask(mask=circle_mask, value=2)

# Output the part.
part.output_abaqus_inp(file_name='ex_c8_single_shape',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
