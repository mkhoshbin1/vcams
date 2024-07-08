"""Script for Example C-7: Gyroid TPMS."""

from vcams.mask.function import mask_from_function
from vcams.mask.tpms import TpmsSchwarzG
from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(50, 50, 50), base_material=0,
                 voxel_size=(0.02, 0.02, 0.02),
                 name='Ex C-7 TPMS Gyroid',
                 description='Example C-7: A 50*50*50 porous part based on the Gyroid TPMS.',
                 log_debug=True)

# Create a Boolean mask based on the VoxelPart object.
# Note that you can pass the TpmsSchwarzG class instead of TpmsSchwarzG.func().
t = part.real_size[0] / 2
tpms_mask = mask_from_function(part=part, func=TpmsSchwarzG, l=t, c=0)

# Apply the Boolean mask to the part.
part.apply_mask(mask=tpms_mask, value=1)

# Output the part.
part.output_abaqus_inp(file_name='ex_c7_tpms_gyroid',
                       elem_code='C3D8R', dim='3D',
                       material_elem_sets='Non-Empty')
