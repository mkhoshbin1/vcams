"""Script for Example C-2: Custom Mask Function (3D)."""

from vcams import mask
from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(50, 50, 50), base_material=1, voxel_size=(0.02, 0.02, 0.02),
                 name='Ex C-2 Custom Mask Function 3D',
                 description='A 3D cubic 50*50*50 part created using a custom mask function.', log_debug=True)


# Define the function of a sphere so a Boolean mask can be created from it.
# Note that the function accepts x, y, z and then the rest of the parameters.
# The function must always accept z, even if it is not used.
def sphere_func(x, y, z, a, b, c, r):
    return (x - a) ** 2 + (y - b) ** 2 + (z - c) ** 2 - r ** 2


# Create a Boolean mask based on the VoxelPart object.
t = part.real_size[0] / 2
sphere_mask = mask.function.mask_from_function(part=part, func=sphere_func,
                                               a=t, b=t, c=t, r=t)

# Apply the Boolean mask to the part.
part.apply_mask(mask=sphere_mask, value=0)

# Output the part.
part.output_abaqus_inp(file_name='ex_c2_custom_function_3d',
                       elem_code='C3D8R', dim='3D',
                       material_elem_sets='Non-Empty')
