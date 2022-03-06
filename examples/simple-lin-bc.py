"""Script for TODO"""

from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(50, 100), base_material=1,
                 voxel_size=(0.02, 0.02),
                 name='Ex A-1 Simple 2D Part',
                 description='Example A-1: A simple 50*100 2D part filled with elements.',
                 log_debug=True)

part.add_bc(bc_type='Linear Displacement')

# Output the part.
part.output_abaqus_inp(file_name='simple-lin-bc',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
