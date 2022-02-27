"""Script for Example 1: Simple Filled 2D Part"""

from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(50, 100), base_material=1,
                 voxel_size=(0.02, 0.02),
                 name='Ex1 Simple 2D Part',
                 description='Example 1: A simple 50*100 2D part filled with elements.',
                 log_debug=True)

# Output the part.
part.output_abaqus_inp(file_name='ex1_simple_part_2d',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
