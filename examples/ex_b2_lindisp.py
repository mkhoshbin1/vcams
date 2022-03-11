"""Script for Example B-2: Linear Displacement BC."""

from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(50, 100), base_material=1,
                 voxel_size=(0.02, 0.02),
                 name='Ex B-2 Linear Displacement BC',
                 description='Example B-2: A 2D part on which a linear displacement BC is applied.',
                 log_debug=True)

# Ask for a linear displacement BC to be applied to the model.
part.add_bc(bc_type='Linear Displacement')

# Output the part.
part.output_abaqus_inp(file_name='ex_b2_lindisp',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
