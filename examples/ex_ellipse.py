"""Script for Example C-3: Single Shape."""
import matplotlib.pyplot as plt

from vcams import mask
from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(250, 250), base_material=0, voxel_size=(.2, .2), name='Ex C-3 Single Shape',
                 description='A 2D square 50*50 part created using a single circular shape.', log_debug=True)
from numpy import pi
# Create an instance of the vcams.mask.shape.Circle class.
# All properties are defined when the object is created.
t = part.real_size[0] / 2
ellipse_obj = mask.shape.Ellipse(id=0, xc=20, yc=20, a=2, b=10, alpha=10)

# Create a Boolean mask based on the VoxelPart object.
# For the mask function use circle_obj.func. No other parameters are necessary.
circle_mask = mask.function.mask_from_function(part=part, func=ellipse_obj.func)

# Apply the Boolean mask to the part.
part.apply_mask(mask=circle_mask, value=2)

# Output the part.
part.output_abaqus_inp(file_name='ex_c3_single_shape',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
