Example G-3: Requesting Node Sets
=================================
In this example, the graphical user interface (GUI) is used to create
a filled 2D part in which the node sets on the boundary are output.
This example mirrors :doc:`Example B-1 <example-b1>`.

The structure is 3D with a shape of 50×75×100 voxels and
has a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, the node sets are requested in the *Boundary Conditions* tab.

The part is then exported to an Abaqus™ input file in *3D* mode with *C3D8R* elements.
The *Non-Empty* elements (which happens to be the whole model), are requested to be exported.

The following figures show the various tabs of the GUI in this example:

.. figure:: /g-examples/ex_g3_nodesets_only_1.png
   :align: center
   :width: 75%

   The GUI's "Basic Model Information" tab for Example G-3.

.. figure:: /g-examples/ex_g3_nodesets_only_2.png
   :align: center
   :width: 75%

   The GUI's "Model Manipulations" tab for Example G-3.

.. figure:: /g-examples/ex_g3_nodesets_only_3.png
   :align: center
   :width: 75%

   The GUI's "Boundary Conditions" tab for Example G-3.

.. figure:: /g-examples/ex_g3_nodesets_only_4.png
   :align: center
   :width: 75%

   The GUI's "Output" tab for Example G-3.

After filling the form, the model can be created by pressing the *"Create Model"* button.
The screen automatically switches to the *Run* tab and will show the program log.

At the end of the process, a dialog box announces the completion
and gives the path to the output file.

Also, the program log and a summary of model information will be shown
in the *Process Log* section of the *Run* tab. It will also be written
to a *.log* file in the output folder.

Finally, a configuration file based on the examples will be written to the output folder
and can be used to import the model in the future.
:download:`It will look like this. </g-examples/ex_g3_nodesets_only.vcams>`