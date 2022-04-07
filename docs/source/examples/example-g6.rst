Example G-6: Planar Composite (Circular Inclusions) II
======================================================
In this example, the graphical user interface (GUI) is used to create
a filled 2D part in which circular shapes of a different material are present.
The final structure can be a 2D model of a composite.
This example is similar to :doc:`Example G-5 <example-g5>`,
except that the shapes are of different materials.

The structure is two dimensional with a shape of 50×100 voxels and
has a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, four circles are defined in the *Model Manipulations* tab.
The necessary parameters are the center points and radius of each circle
and the material to be assigned to it.
In the case of this example each circle has a unique material code,
one of which is 0 which signifies empty space.

The part is then exported to an Abaqus™ input file in *2D* mode with *CPE4R* elements.
The *Non-Empty* elements are requested to be exported.

The following figures show the various tabs of the GUI in this example:

.. figure:: /g-examples/ex_g6_shape_array_2d_2_1.png
   :align: center
   :width: 75%

   The GUI's "Basic Model Information" tab for Example G-6.

.. figure:: /g-examples/ex_g6_shape_array_2d_2_2.png
   :align: center
   :width: 75%

   The GUI's "Model Manipulations" tab for Example G-6.

.. figure:: /g-examples/ex_g6_shape_array_2d_2_3.png
   :align: center
   :width: 75%

   The GUI's "Boundary Conditions" tab for Example G-6.

.. figure:: /g-examples/ex_g6_shape_array_2d_2_4.png
   :align: center
   :width: 75%

   The GUI's "Output" tab for Example G-6.

After filling the form, the model can be created by pressing the *"Create Model"* button.
The screen automatically switches to the *Run* tab and will show the program log.

At the end of the process, a dialog box announces the completion
and gives the path to the output file.

Also, the program log and a summary of model information will be shown
in the *Process Log* section of the *Run* tab. It will also be written
to a *.log* file in the output folder.

Finally, a configuration file based on the examples will be written to the output folder
and can be used to import the model in the future.
:download:`It will look like this. </g-examples/ex_g6_shape_array_2d_2.vcams>`

The final model looks like :numref:`ex_g6_shape_array_2d_2_0`.
Note that the stepping visible in the part is due to the low resolution of the model.
A bigger model will result in a better shape.

.. figure:: /g-examples/ex_g6_shape_array_2d_2_0.png
   :name: ex_g6_shape_array_2d_2_0
   :align: center
   :alt: Final model of Example G-6. Different materials are shown in different colors
         and the empty space is shown in white.

   Final model of Example G-6. Different materials are shown in different colors
   and the empty space is shown in white.