Example G-7: The Gyroid TPMS
============================
In this example, the graphical user interface (GUI) is used to create
a 3D part based on the Gyroid
`TPMS <https://en.wikipedia.org/wiki/Triply_periodic_minimal_surface>`__.
This example mirrors :doc:`Example C-5 <example-c5>`.

The structure is two dimensional with a shape of 50×50×50 voxels and
has a base material of 0 (empty space) and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, the parameters for the Gyroid TPMS are entered in the *Model Manipulations* tab.
The necessary parameters are *Unit Cell Length*, the *Formula Constant*,
and the material to be assigned to the structure which will be set to 1.

The part is then exported to an Abaqus™ input file in *3D* mode with *C3D8R* elements.
The *Non-Empty* elements are requested to be exported.

The following figures show the various tabs of the GUI in this example:

.. figure:: /g-examples/ex_g7_tpms_gyroid_1.png
   :align: center
   :width: 75%

   The GUI's "Basic Model Information" tab for Example G-7.

.. figure:: /g-examples/ex_g7_tpms_gyroid_2.png
   :align: center
   :width: 75%

   The GUI's "Model Manipulations" tab for Example G-7.

.. figure:: /g-examples/ex_g7_tpms_gyroid_3.png
   :align: center
   :width: 75%

   The GUI's "Boundary Conditions" tab for Example G-7.

.. figure:: /g-examples/ex_g7_tpms_gyroid_4.png
   :align: center
   :width: 75%

   The GUI's "Output" tab for Example G-7.

After filling the form, the model can be created by pressing the *"Create Model"* button.
The screen automatically switches to the *Run* tab and will show the program log.

At the end of the process, a dialog box announces the completion
and gives the path to the output file.

Also, the program log and a summary of model information will be shown
in the *Process Log* section of the *Run* tab. It will also be written
to a *.log* file in the output folder.

Finally, a configuration file based on the examples will be written to the output folder
and can be used to import the model in the future.
:download:`It will look like this. </g-examples/ex_g7_tpms_gyroid.vcams>`

The final model looks like :numref:`ex_g7_tpms_gyroid_0`.
Note that the stepping visible in the part is due to the low resolution of the model.
A bigger model will result in a better shape.

.. figure:: /g-examples/ex_g7_tpms_gyroid_0.png
   :name: ex_g7_tpms_gyroid_0
   :align: center
   :alt: Final model of Example G-7.

   Final model of Example G-7.