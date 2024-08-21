Example G-5: 2D Part with a Randomly Distributed Second Phase
=============================================================
In this example, the graphical user interface (GUI) is used to create
a 2D part in which in which a second phase is randomly distributed in the background.
This example mirrors :doc:`Example C-3 <example-c3>`.

The structure is 2D with a shape of 100×100 voxels and
has a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, the parameters for the second phase are entered in the *Model Manipulations* tab.
The necessary parameters are *Second Phase Fraction* which is set to 0.42 which means 42%,
and *Second Phase Material Code* which is set to 2 resulting in the second phase having a material code of 2.

The part is then exported to an Abaqus™ input file in *3D* mode with *C3D8R* elements.
The *Non-Empty* elements (which happens to be the whole model), are requested to be exported.

The following figures show the various tabs of the GUI in this example:

.. figure:: /g-examples/ex_g5_random_2d_part_1.png
   :align: center
   :width: 75%

   The GUI's "Basic Model Information" tab for Example G-4.

.. figure:: /g-examples/ex_g5_random_2d_part_2.png
   :align: center
   :width: 75%

   The GUI's "Model Manipulations" tab for Example G-4.

.. figure:: /g-examples/ex_g5_random_2d_part_3.png
   :align: center
   :width: 75%

   The GUI's "Boundary Conditions" tab for Example G-4.

.. figure:: /g-examples/ex_g5_random_2d_part_4.png
   :align: center
   :width: 75%

   The GUI's "Output" tab for Example G-4.

After filling the form, the model can be created by pressing the *"Create Model"* button.
The screen automatically switches to the *Run* tab and will show the program log.

At the end of the process, a dialog box announces the completion
and gives the path to the output file.

Also, the program log and a summary of model information will be shown
in the *Process Log* section of the *Run* tab. It will also be written
to a *.log* file in the output folder.

Finally, a configuration file based on the examples will be written to the output folder
and can be used to import the model in the future.
:download:`It will look like this. </g-examples/ex_g5_random_2d_part.vcams>`