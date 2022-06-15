"""Script for Example B-3: Periodic BC."""

from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(50, 100), base_material=1,
                 voxel_size=(0.02, 0.02),
                 name='Ex B-3 Periodic BC',
                 description='Example B-3: A 2D part on which a Periodic BC is applied.',
                 log_debug=True)

# Request a Periodic BC for the model.
part.add_bc(bc_type='Periodic')

# Output the part.
part.output_abaqus_inp(file_name='ex_b3_pbc',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
