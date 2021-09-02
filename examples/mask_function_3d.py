"""In this example, a full part with a shape of 50*50*50 voxels is created.
Then, a function is defined which describes the surface of a sphere,
and a mask is created and applied based on that function.
Afterwards, the mask is used to determine where material values must be equal to two.
Finally, the part is output to abaqus with a uniform scale of 0.02 in all directions.
The result is a cubic part where the center is a sphere with a material code of 2,
while the rest of the cube has a material code of 1."""

import vcams

results_path = 'path\\to\\results\\directory'

# Create a part.
part = vcams.voxelpart.VoxelPart(size=(50, 50, 50), fill_value=1,
                                 voxel_size=(0.02, 0.02, 0.02),
                                 name='Function Mask 3D Part',
                                 description='A cubic 50*50*50 part created using a function mask.',
                                 logger_path=results_path)

# Create a mask with the same shape and voxel_size as as the part.
t = part.data.shape[0] * part.voxel_size[0]/2
sphere_mask = vcams.mask.function.mask_from_function(mask_shape=part.data.shape,
                                                     func=vcams.mask.shape.sphere,
                                                     voxel_size=part.voxel_size,
                                                     a=t, b=t, c=t, r=t)

# Apply the mask to the part.
part.apply_mask(mask=sphere_mask, value=2)

# Output the part.
part.output_abaqus_inp(file_name='function_part_3d', folder_path=results_path,
                       elem_type='C3D8R', dim='3D',
                       material_elem_sets=(1, 2), custom_elem_sets=True)
