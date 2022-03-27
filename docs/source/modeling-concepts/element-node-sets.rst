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
the :ref:`boundary-conditions` section describes these sets in detail.

Manual Creation of Sets
-----------------------
Both node and element sets can be created manually.
It should be noted that names of element and node sets must be valid
according to the documentation for the :func:`.helper.is_name_valid` function.
which is based on the *Input Syntax Rules* of the Abaqus™ software.

In order to create element sets,
the :meth:`~.voxelpart.VoxelPart.add_custom_elem_set` method is used.
It is supplied with a name and a list of element IDs and these are then stored
in the *VoxelPart* object and written to output if the appropriate flag is enabled
when exporting the part, which is the default behavior.

Similarly, node sets are created using
the :meth:`~.voxelpart.VoxelPart.add_node_set` method with similar parameters.
For node sets, care should be taken not to use the names used in BCs,
as the manually defined sets will be overwritten by the program.

The procedure for creating custom element and node sets
is demonstrated in :doc:`Example A-8 </examples/example-a8>`.