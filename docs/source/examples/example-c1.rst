Example C-1: Custom Mask Function (2D)
======================================
This example shows how to use a custom function to create a Boolean mask
and then use that mask to manipulate the part.
This example deals with a 2D part. For a 3D example, refer to :doc:`Example C-2 <example-c2>`.

First, a 2D part with a shape of 50×50 voxels is created
with a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, the ``circle_func`` function is created which describes a circle.
This function accepts *x*, *y*, *z* and then the rest of the parameters.
It should be noted that it must always accept *z*, even if it is not used
in the calculations::

    def circle_func(x, y, z, a, b, r):
        return (x - a) ** 2 + (y - b) ** 2 - r ** 2

Then, a mask is created using the ``circle_func`` function.
There are three parameters that need to be passed which are
all set to half of the real model size::

    t = part.real_size[0] / 2
    circle_mask = mask.function.mask_from_function(part=part, func=circle_func,
                                                   a=t, b=t, r=t)

Afterwards, the Boolean mask is applied to the part with a value of 2.
This means that the values of the elements selected by the mask are set to 2::

    part.apply_mask(mask=circle_mask, value=2)

Finally, The part is then exported to an Abaqus™ input file in *2D* mode with *CPE4R* elements.
The *Non-Empty* elements (which happens to be the whole model), are requested to be exported.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex_c1_custom_function_2d.py

The final model looks like :numref:`ex_c1_custom_function_2d`.
Note that elements in different sets are shown in different colors.

.. figure:: /images/ex_c1_custom_function_2d.png
   :name: ex_c1_custom_function_2d
   :align: center
   :alt: Final model of Example C-1.
         Element sets corresponding to MAT-1 and MAT-2 are shown in green and red, respectively.

   Final model of Example C-1.
   Element sets corresponding to MAT-1 and MAT-2 are shown in green and red, respectively.