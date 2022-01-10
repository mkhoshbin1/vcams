Example 8: Manipulation of the Structure Using Masks (II)
=========================================================

The goal of this example is to create a 3D part with a random dispersion
of elements in an empty space.
This is achieved by creating an empty model and then applying a boolean mask to it
which will be a random array of 0 and 1.

It should be noted that this model can also be created according to :doc:`Example 6 <example6>`,
but the goal here is to create and apply a boolean mask.
This is to show that a mask can be created using *any* means and as long as its of
an appropriate size and data type, it can be applied to the part.

First, a 3D part with a shape of 50×75×100 voxels is created
with a base material of 0 (empty space) and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, numpy is imported and an array is created using its *choice* function::

    random_mask = random.choice((True, False), size=part.data.shape)

The mask is then applied to the part with a value of 1 which corresponds to *MAT-1*::

    part.apply_mask(mask=random_mask, value=1)

Finally, The part is output to abaqus in *3D* mode with *C3D8R* elements.
The *Non-Empty* elements are requested to be written to the output.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex8_mask_manipulation_2.py

The final model looks like :numref:`ex8_mask_manipulation_2`.
Note that the part has been cut at the middle of its X dimension to better show the empty space.

.. figure:: /images/ex8_mask_manipulation_2.png
   :name: ex8_mask_manipulation_2
   :align: center
   :alt: Final model of Example 8.
         The part has been cut at the middle of its X dimension to better show the empty space.

   Final model of Example 8.
   The part has been cut at the middle of its X dimension to better show the empty space.