Example 4: Manual Manipulation of the Structure (Single Elements)
=================================================================

In this example, a complete 2D part with a shape of 5×5 voxels is created
with a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, the value of elements in positions (1,5) and (3,2)
of the *data* array is set to 2, which will be output as MAT-2.

Then, the value of the element in position (4,3) is set to 0,
which signifies empty space.

Finally, The part is output to abaqus in *2D* mode with *CPE4R* elements.
The *Non-Empty* elements (which happens to be MAT-1 and MAT-2),
are requested to be written to the output.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex4_manual_manipulation_single.py

The final model looks like :numref:`ex4_manual_manipulation_single`.
Note that elements in different sets are shown in different colors.

.. figure:: /images/ex4_manual_manipulation_single.png
   :name: ex4_manual_manipulation_single
   :align: center
   :alt: Final model of Example 4.
         Element sets corresponding to MAT-1 and MAT-2 are shown in green and red, respectively.

   Final model of Example 4.
   Element sets corresponding to MAT-1 and MAT-2 are shown in green and red, respectively.