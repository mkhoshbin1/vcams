"""Case Study 1"""

from vcams.voxelpart import VoxelPart

num_voxels_list = (
    (50, 50, 50),
    (100, 50, 50),
    (100, 100, 50),
    (100, 100, 100),
    (500, 100, 100),
    (500, 500, 100),
    (500, 500, 500),
)

# Run once without Periodic BC and another time with it.
for pbc_flag in (False, True):
    # Name of the part is different for each case.
    if pbc_flag:
        name_str = 'Case1-%i-%i-%i-pbc'
    else:
        name_str = 'Case1-%i-%i-%i-nobc'

    # Create parts with different sizes based on num_voxels_list.
    for num_voxels in num_voxels_list:
        # Create the part.
        part = VoxelPart(size=num_voxels, base_material=1, voxel_size=(1.0, 1.0, 1.0), name=(name_str % num_voxels),
                         log_debug=False)

        if pbc_flag:
            # Request a Periodic BC for the model.
            part.add_bc(bc_type='Periodic')

        # Output the part.
        part.output_abaqus_inp(file_name=part.name,
                               elem_code='C3D8R', dim='3D',
                               material_elem_sets='Non-Empty')
        # Delete the part to free memory and release the log file.
        del part
