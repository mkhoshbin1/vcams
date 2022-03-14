Example C-4: Shape Array
========================
This example demonstrates the use of the :class:`~vcams.mask.shape.ShapeArray` class
for creating a Boolean mask which is then used to manipulate the part.

A :class:`~vcams.mask.shape.ShapeArray` object contains
a number of shape objects which can be of different classes,
but must all be subclasses of the :class:`~vcams.mask.shape.Shape` class
and be of the same dimensionality (2D/3D).

Here, a 2D *ShapeArray* is defined based on the *VoxelPart* object
and then a number of shapes are added to it.
Finally, the *ShapeArray* object's *mask* property is used for manipulating the part.
Compared to examples :doc:`C-1 <example-c1>`, :doc:`C-2 <example-c2>`, and :doc:`C-3 <example-c3>`,
this method is extremely straightforward and allows for a variety of scripting techniques to be used.

First, a 2D part with a shape of 50×50 voxels is created
with a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, a :class:`~vcams.mask.shape.ShapeArray` object (named ``shape_array_obj``)
is created based on the *VoxelPart* and with its dimensionality set to *2D*::

    shape_array_obj = ShapeArray(dim='2D', part=part)

Then, a number of shapes are added using
the :meth:`~vcams.mask.shape.ShapeArray.add_shape` method.
Each time, the :class:`~vcams.mask.shape.Circle` class is passed
which determines the shape to be added and also the shape's parameters are added
as keyword arguments::

    shape_array_obj.add_shape(Circle, a=0, b=0, r=0.1)
    shape_array_obj.add_shape(Circle, a=0.4, b=0.2, r=0.15)
    shape_array_obj.add_shape(Circle, a=0.7, b=0.5, r=0.1)
    shape_array_obj.add_shape(Circle, a=0.3, b=0.7, r=0.25)

When using the *ShapeArray* object we don't need to calculate a mask,
we just ask it to give us its mask using
the :attr:`~vcams.mask.shape.ShapeArray.mask` property
which, if necessary, will be updated automatically.
This Boolean mask is applied to the part with a value of 2.
This means that the values of the elements selected by the mask are set to 2::

    part.apply_mask(mask=shape_array_obj.mask, value=2)

Finally, The part is then exported to an Abaqus™ input file in *2D* mode with *CPE4R* elements.
The *Non-Empty* elements (which happens to be the whole model), are requested to be exported.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex_c4_shape_array.py

The final model looks like :numref:`ex_c4_shape_array`.
Note that elements in different sets are shown in different colors.

.. figure:: /images/ex_c4_shape_array.png
   :name: ex_c4_shape_array
   :align: center
   :alt: Final model of Example C-4.
         Element sets corresponding to MAT-1 and MAT-2 are shown in green and red, respectively.

   Final model of Example C-4.
   Element sets corresponding to MAT-1 and MAT-2 are shown in green and red, respectively.