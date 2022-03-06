"""Script for Example A-6: Manipulation of the Structure Using Masks (I)"""

from numpy import array, rot90
from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(5, 5), base_material=0,
                 voxel_size=(0.02, 0.02),
                 name='Ex A6 Mask Manipulation 1',
                 description='Example A-6: A 5*5 2D part create using three boolean masks.',
                 log_debug=True)

# Create the three masks according to the images.
mask1 = array(((1, 1, 1, 1, 1),
               (1, 0, 0, 0, 0),
               (0, 0, 0, 1, 0),
               (0, 1, 0, 1, 0),
               (0, 1, 0, 1, 0)),
              dtype=bool)
mask2 = array(((0, 0, 0, 0, 0),
               (0, 1, 0, 1, 0),
               (0, 0, 0, 0, 0),
               (1, 0, 1, 0, 1),
               (1, 0, 1, 0, 0)),
              dtype=bool)
mask3 = array(((0, 0, 0, 0, 0),
               (0, 0, 1, 0, 0),
               (1, 0, 0, 0, 0),
               (0, 0, 0, 0, 0),
               (0, 0, 0, 0, 1)),
              dtype=bool)

# Apply the masks with their respective material codes.
# The masks must be rotated -90 degrees to account for the
# Different between Abaqus's XY direction and the defined array.
part.apply_mask(mask=rot90(mask1, -1), value=1)
part.apply_mask(mask=rot90(mask2, -1), value=2)
part.apply_mask(mask=rot90(mask3, -1), value=3)

# Output the part.
part.output_abaqus_inp(file_name='ex_a6_mask_manipulation_1',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
