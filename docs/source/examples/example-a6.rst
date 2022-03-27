Example A-6: Manipulation of the Structure Using Masks (I)
==========================================================
In this example, a 2D part is created based on the *data* variable
described in the :ref:`materials` section.
That *data* variable is the result of applying multiple Boolean masks
as described in the :ref:`boolean-masks` section and shown in :numref:`mask-combine-to-mesh`.
The procedure is followed in this example.

First, a 2D part with a shape of 5×5 voxels is created
with a base material of 0 (empty space) and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, numpy is imported and three boolean arrays are created based on Fig TODO::

    from numpy import array, rot90

    mask1 = array(((1, 1, 1, 1, 1),
                   (1, 0, 0, 0, 0),
                   (0, 0, 0, 1, 0),
                   (0, 1, 0, 1, 0),
                   (0, 1, 0, 1, 0)),
                  dtype=bool)
    mask2 = array(((0, 0, 0, 0, 0),
                   (0, 1, 0, 1, 0),
                   (0, 0, 0, 0, 0),
                   (1, 0, 1, 0, 1),
                   (1, 0, 1, 0, 0)),
                  dtype=bool)
    mask3 = array(((0, 0, 0, 0, 0),
                   (0, 0, 1, 0, 0),
                   (1, 0, 0, 0, 0),
                   (0, 0, 0, 0, 0),
                   (0, 0, 0, 0, 1)),
                  dtype=bool)

They are then applied to the model. However, because of the difference
in the definition of XY in the above array and the XY system in Abaqus,
we have to rotate the arrays -90 degrees.
If this is not done, the model needs to be rotated inside Abaqus.
Application of the masks is done as follows::

    part.apply_mask(mask=rot90(mask1, -1), value=1)
    part.apply_mask(mask=rot90(mask2, -1), value=2)
    part.apply_mask(mask=rot90(mask3, -1), value=3)

Finally, The part is exported to an Abaqus™ input file in *2D* mode with *CPE4R* elements.
The *Non-Empty* elements are requested to be exported.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex_a6_mask_manipulation_1.py

The final model looks like :numref:`ex_a6_mask_manipulation_1`.
The elements sets are shown in the same color as the :ref:`materials` section.

.. figure:: /images/ex_a6_mask_manipulation_1.png
   :name: ex_a6_mask_manipulation_1
   :align: center
   :alt: Final model of Example A-6.
         Element sets corresponding to MAT-1, MAT-2 and MAT-3 are shown in blue, green, and orange, respectively.

   Final model of Example A-6.
   Element sets corresponding to MAT-1, MAT-2 and MAT-3 are shown in blue, green, and orange, respectively.