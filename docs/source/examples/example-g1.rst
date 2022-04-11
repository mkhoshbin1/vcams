Example G-1: Simple Filled 2D Part
==================================
In this example, the graphical user interface (GUI) is used to create a filled 2D part.
This example mirrors :doc:`Example A-1 <example-a1>`.

The structure is two  dimensional with a shape of 50×100 voxels and
has a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

The part is then exported to an Abaqus™ input file in *2D* mode with *CPE4R* elements.
The *Non-Empty* elements (which happens to be the whole model), are requested to be exported.

The following figures show the various tabs of the GUI in this example:

.. figure:: /g-examples/ex_g1_simple_part_2d_1.png
   :align: center
   :width: 75%

   The GUI's "Basic Model Information" tab for Example G-1.

.. figure:: /g-examples/ex_g1_simple_part_2d_2.png
   :align: center
   :width: 75%

   The GUI's "Model Manipulations" tab for Example G-1.

.. figure:: /g-examples/ex_g1_simple_part_2d_3.png
   :align: center
   :width: 75%

   The GUI's "Boundary Conditions" tab for Example G-1.

.. figure:: /g-examples/ex_g1_simple_part_2d_4.png
   :align: center
   :width: 75%

   The GUI's "Output" tab for Example G-1.

.. figure:: /g-examples/ex_g1_simple_part_2d_5.png
   :align: center
   :width: 75%

   The GUI's "Run" tab for Example G-1.

After filling the form, the model can be created by pressing the *"Create Model"* button.
The screen automatically switches to the *Run* tab and will show the program log.

At the end of the process, the dialog box shown
in :numref:`ex_g1_simple_part_2d_6` announces the completion.
Note that the path to the output file will be different
depending on the input parameters and the machine.

.. figure:: /g-examples/ex_g1_simple_part_2d_6.png
   :name: ex_g1_simple_part_2d_6
   :align: center
   :width: 50%

   The GUI's "Done!" dialog box that is shown after creation of the model in Example G-1.

Also, the program log and a summary of model information will be shown
in the *Process Log* section of the *Run* tab. It will also be written
to a *.log* file in the output folder.

Finally, a configuration file based on the examples will be written to the output folder
and can be used to import the model in the future.
:download:`It will look like this. </g-examples/ex_g1_simple_part_2d.vcams>`