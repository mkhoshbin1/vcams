"""In this example, a complete part with a shape of 50*50 voxels is created.
The part is then output to abaqus with a uniform scale of 0.02 in all directions."""

import vcams

# Create a part.
part = vcams.voxelpart.VoxelPart(size=(50, 100), base_material=1,
                                 voxel_size=(0.02, 0.02),
                                 name='Filled 2D Part',
                                 description='A square 50*50 part filled with elements.',
                                 log_debug=True)

# Output the part.
part.output_abaqus_inp(file_name='complete_part_2d',
                       elem_type='CPE4R', dim='2D',
                       material_elem_sets='All', custom_elem_sets=True)
