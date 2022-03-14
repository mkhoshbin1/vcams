"""Script for Example C-1: Custom Mask Function (2D)."""

from vcams import mask
from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(50, 50), base_material=1,
                 voxel_size=(0.02, 0.02),
                 name='Ex C-1 Custom Mask Function 2D',
                 description='A 2D square 50*50 part created using a custom mask function.',
                 log_debug=True)


# Define the function of a circle so a Boolean mask can be created from it.
# Note that the function accepts x, y, z and then the rest of the parameters.
# The function must always accept z, even if it is not used.
def circle_func(x, y, z, a, b, r):
    return (x - a) ** 2 + (y - b) ** 2 - r ** 2


# Create a Boolean mask based on the VoxelPart object.
t = part.real_size[0] / 2
circle_mask = mask.function.mask_from_function(part=part, func=circle_func,
                                               a=t, b=t, r=t)

# Apply the Boolean mask to the part.
part.apply_mask(mask=circle_mask, value=2)

# Output the part.
part.output_abaqus_inp(file_name='ex_c1_custom_function_2d',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
