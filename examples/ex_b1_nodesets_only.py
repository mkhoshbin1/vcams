"""Script for Example B-1: Node Sets Only."""

from vcams.voxelpart import VoxelPart

# Create the part.
part = VoxelPart(size=(50, 75, 100), base_material=1, voxel_size=(0.02, 0.02, 0.02), name='Ex B-1 Node Sets Only',
                 description='Example B-1: A 3D part for which all node sets are defined.', log_debug=True)

# Ask for all node sets to be created for the model.
part.add_bc(bc_type='Nodeset Only',
            vertices_nodeset=True, edges_nodeset=True, faces_nodeset=True,
            explicit_nodeset=True, simple_nodeset=True)

# Output the part.
part.output_abaqus_inp(file_name='ex_b1_nodesets_only',
                       elem_code='C3D8R', dim='3D',
                       material_elem_sets='Non-Empty')
