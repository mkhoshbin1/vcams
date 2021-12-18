"""In this example, a porous structure is created
based on the Schwarz Primitive (P) triply periodic minimal surface (TPMS).

First, an empty part is created, and then a mask is created using the equation
for the surface. This mask is then applied to the part to determine the elements
which should have a material value of 1. Finally, the part is output to abaqus."""

import vcams
from vcams.mask.tpms import TpmsSchwarzP

results_path = 'path\\to\\results\\directory'

# Create a part.
part = vcams.voxelpart.VoxelPart(size=(50, 50, 50), base_material=0,
                                 voxel_size=(0.02, 0.02, 0.02),
                                 name='TPMS Schwarz P Part',
                                 description='A 50*50*50 porous part based on the Schwarz P TPMS.')

# Create a mask with the same shape and voxel_size as the part and apply it to the part.
t = part.data.shape[0] * part.voxel_size[0] / 2
boolean_mask = vcams.mask.function.mask_from_function(mask_shape=part.data.shape,
                                                      func=TpmsSchwarzP,
                                                      voxel_size=part.voxel_size,
                                                      l=t, c=0)
part.apply_mask(mask=boolean_mask, value=1)

part.add_default_node_sets(dim='3D')

# Output the part.
part.output_abaqus_inp(file_name='tpms_schwarz_p_part',
                       elem_type='C3D8R', dim='3D',
                       material_elem_sets='Non-Empty', custom_elem_sets=True)
