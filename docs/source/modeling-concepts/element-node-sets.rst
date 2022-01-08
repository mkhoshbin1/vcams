.. _element-node-sets:

Element and Node Sets
=====================
Grouping of nodes and elements is an important step for many pre- and post-processing procedures.
This is done in two ways:

+ Automatically as part of the regular program workflow.
+ Manually at the request of the user.

Automatic Creation of Sets
--------------------------
Element sets are created automatically for all material codes.
Of course, only the requested materials (and their sets) are written to the output.
See :ref:`materials` section for more information regarding materials.

Node sets are created automatically when boundary conditions are assigned.
Section TODO describes these sets in detail.

Manual Creation of Sets
-----------------------
Both node and element sets can be created manually.
It should be noted that names of element and node sets must be valid according to TODO
which is based on the *Input Syntax Rules* of the Abaqus™ software.

In order to create element sets, the VoxelPart.add_custom_elem_set() TODO function is used.
It is supplied with a name and a list of element IDs and these are then stored in the *VoxelPart* object
and written to output if the appropriate flag is enabled in TODO.

Similarly, node sets are created using VoxelPart.add_node_set() TODO function with similar parameters.
For node sets, care should be taken not to use the names used in BCs,
as the manually defined sets will be overwritten by the program.

TODO: code block for creating manual sets. maybe example?