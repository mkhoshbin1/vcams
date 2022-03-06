"""Script for Example A-2: Simple Filled 3D Part"""

from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(50, 75, 100), base_material=1,
                 voxel_size=(0.02, 0.02, 0.02),
                 name='Ex A-2 Simple 3D Part',
                 description='Example A-2: A simple 50*75*100 3D part filled with elements.',
                 log_debug=True)

# Output the part.
part.output_abaqus_inp(file_name='ex_a2_simple_part_3d',
                       elem_code='C3D8R', dim='3D',
                       material_elem_sets='Non-Empty')
