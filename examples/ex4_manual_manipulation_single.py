"""Script for Example 4: Manual Manipulation of the Structure (Single Elements)"""

from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(5, 5), base_material=1,
                 voxel_size=(0.02, 0.02),
                 name='Ex4 Manual Manipulation Single',
                 description='Example 4: A 5*5 2D part filled with elements with two elements changed manually.',
                 log_debug=True)

# Manually change some elements. Note that NumPy uses zero-based indexing.
# Change the value of elements in positions (1,5) and (3,2) to MAT-2.
part.data[0, 4] = 2
part.data[2, 1] = 2

# Change the value of the element in position (4,3) to MAT-0 which is empty space.
part.data[3, 2] = 0

# Output the part.
part.output_abaqus_inp(file_name='ex4_manual_manipulation_single',
                       elem_type='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty')
