Example C-8: Single Shape
=========================
In this example, a pre-defined structure is used to create a Boolean mask
and then use that mask to manipulate the part.
The shape is a circle, which means that the result will be identical
to that of :doc:`Example C-1 <example-c1>`, but the procedure is more straightforward.

This example paves the way for introducing shape arrays
which is done in :doc:`Example C-9 <example-c9>`.

First, a 2D part with a shape of 50×50 voxels is created
with a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, an instance of the :class:`~vcams.mask.shape.Circle` class is created.
The value of *id* is not important for single shapes,
and the other parameters are all set to half of the real model size::

    t = part.real_size[0] / 2
    circle_obj = mask.shape.Circle(id=0, a=t, b=t, r=t)

Then, a mask is created using the instance's ``func()`` method.
Unlike :doc:`Example C-1 <example-c1>`, no additional parameters are necessary::

    circle_mask = mask.function.mask_from_function(part=part, func=circle_obj.func)

Afterwards, the Boolean mask is applied to the part with a value of 2.
This means that the values of the elements selected by the mask are set to 2::

    part.apply_mask(mask=circle_mask, value=2)

Finally, The part is exported to an Abaqus™ input file in *2D* mode with *CPE4R* elements.
The *Non-Empty* elements (which happens to be the whole model), are requested to be exported.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex_c8_single_shape.py

The final model looks like :numref:`ex_c8_single_shape`.
Note that elements in different sets are shown in different colors.

.. figure:: /images/ex_c8_single_shape.png
   :name: ex_c8_single_shape
   :align: center
   :alt: Final model of Example C-8.
         Element sets corresponding to MAT-1 and MAT-2 are shown in green and red, respectively.

   Final model of Example C-8.
   Element sets corresponding to MAT-1 and MAT-2 are shown in green and red, respectively.