"""Script for Example 2: Simple Filled 3D Part"""

from vcams.voxelpart import VoxelPart
# FIXME
# Create the part.
part = VoxelPart(size=(50, 100), base_material=1,
                 voxel_size=(0.02, 0.02),
                 name='Ex1 Simple 2D Part',
                 description='Example 1: A simple 50*100 2D part filled with elements.',
                 log_debug=True)

# Output the part.
part.output_abaqus_inp(file_name='ex2_simple_part_3d',
                       elem_type='C3D8R', dim='3D',
                       material_elem_sets='Non-Empty')
