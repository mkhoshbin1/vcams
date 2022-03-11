"""Script for Example A-8: Custom Element and Node Sets."""

from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(50, 100), base_material=1,
                 voxel_size=(0.02, 0.02),
                 name='Ex A-8 Custom Sets',
                 description='Example A-8: A 2D part with custom element and node sets.',
                 log_debug=True)

# Add a node set that will always be exported.
# Note that the ids list need not be sorted.
part.add_node_set(name='custom node set', ids=(0, 10, 450, 112, 250))

# Add a custom element set
# that will be exported if custom_elem_sets = True, which is the default behavior.
# Note that here the range(10, 151) is used as the ids list,
# which is the same as the array (10, 11,..., 150).
part.add_custom_elem_set(name='custom node set', ids=range(10, 151))

# Output the part.
# Note that custom_elem_sets is set to True,
# but this is not necessary because it defaults to True.
part.output_abaqus_inp(file_name='ex_a8_custom_sets',
                       elem_code='CPE4R', dim='2D',
                       material_elem_sets='Non-Empty',
                       custom_elem_sets=True)
