.. _export:

Exporting the Model
===================
Using this program, a structure can be created using a variety of techniques
and it can be changed many times to obtain a complex structure.
In the end, it must be exported to a FEA software so it can be analyzed.

This section discusses the process for exporting a model.


Output to Abaqus™
-----------------------
How to Export the Model
+++++++++++++++++++++++
There are two methods for exporting the model.

In the scripts, after a *VoxelPart* is created and all manipulations have been done,
it can be exported using its :meth:`~.voxelpart.VoxelPart.output_abaqus_inp` method.
contains a complete list and explanation of its parameters, but some of them are explained below.

When using the graphical user interface (GUI), exporting the model is part of the workflow.
This is explained in :ref:`the relevant section <gui-output>` of the GUI's documentation.


.. _export_abq_elem_code:

Choosing an Element Code
++++++++++++++++++++++++
Abaqus™ has a large element library.
This program only supports output to linear elements with a shape compatible with a voxel or pixel.
This means that in 2D, only 4-node quadrilateral (square-shaped) elements can be used
and for 3D models, only 8-node hexahedral (brick) elements are valid.
Furthermore, the element code is applied to all elements in the model.

Because of the large number of elements, the program accepts the element code as a string,
such as *'CPE4R'* or *'C3D8R'* and does not validate it any further.
The user is responsible for selecting an appropriate element code.
If the dimensionality or type of element is inappropriate, Abaqus™ rejects the input file.

If more complex behavior is desired the user can use Abaqus' Python Scripting Interface
to apply the element codes to any of the defined and custom element sets.

Selecting the Materials for Export
++++++++++++++++++++++++++++++++++
As explained in the :ref:`materials` section,
the model consists one or more materials, each of which have a *material code*.
When exporting the model, a list of materials may be selected
and only elements with that material code will be exported.
There are also two special values that can be used:
*'All'* which refers to all materials in the model,
and *'Non-Empty'* which refers to all except the material code of zero
which, by convention, refers to empty space.

For every material code, a set will also be created.
Its name will be the material code prepended by *'MAT-'*.
These sets can be used for applying material properties in the CAE or using the Python Scripting Interface.

Custom Element Sets
+++++++++++++++++++
The material sets described above will always be exported.
There are also custom element sets that are defined using
the :meth:`~.voxelpart.VoxelPart.add_custom_elem_set` method,
and their export can be suppressed.
See the documentation for :meth:`~.voxelpart.VoxelPart.output_abaqus_inp`
for more information.

The :ref:`element-node-sets` section has a
complete discussion of node and element sets.

Boundary Conditions
+++++++++++++++++++
The boundary conditions defined as per the :ref:`boundary-conditions`
section will be added to the model automatically.
