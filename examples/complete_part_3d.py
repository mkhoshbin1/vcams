"""In this example, a complete part with a shape of 50*50*50 voxels is created.
The part is then output to abaqus with a uniform scale of 0.02 in all directions."""

import vcams

# Create a part.
part = vcams.voxelpart.VoxelPart(size=(50, 75, 100), fill_value=1,
                                 voxel_size=(0.02, 0.02, 0.02),
                                 name='Filled 3D Part',
                                 description='A cubic 50*50*50 part filled with elements.')

# Output the part.
part.output_abaqus_inp(file_name='complete_part_3d',
                       elem_type='C3D8R', dim='3D',
                       material_elem_sets=(1,), custom_elem_sets=True)
