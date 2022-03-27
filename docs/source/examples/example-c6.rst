Example C-6: Part from Image (2D)
=================================
In this example, a 2D part is created based on an image.
This is done using the :func:`~vcams.mask.image.mask_from_image` function
which binarizes the image and returns a Boolean mask,
which is then applied to the part.

This procedure is especially useful for grayscale images obtained from microscopy.
See :ref:`predefined-image` for more information and some important tips.
In order to avoid copyright issues, a simple image of a dual-phase steel
is taken from `Wikipedia <https://en.wikipedia.org/wiki/File:Dual_Phase_Steel.jpg>`__
(licensed under CC BY-SA 4.0) and is used for this example.

First, the image is converted to a mask without being re-scaled::

    image_mask = mask_from_image(image_path='ex_c6_image_2d_input.jpg',
                                 scale=1.0, denoise=True)

Then the image is rotated -90 degrees to account for the
difference between the XY directions in Abaqus and the picture::

    image_mask = rot90(image_mask, -1)

Afterwards, a 3D part with the same shape as the mask is created
with a base material of 1 and a voxel size of 0.02 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

The mask is then applied to the part with a value of 2.
And finally, the part is then exported to an Abaqus™ input file in *3D* mode with *C3D8R* elements.
The *Non-Empty* elements are requested to be exported.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex_c6_image_2d.py

The initial image and the final model are shown in :numref:`ex_c6_image_2d`.

.. figure:: /images/ex_c6_image_2d.png
   :name: ex_c6_image_2d
   :align: center
   :alt: Initial image (left) and final model (right) for Example C-6.

   Initial image (left) and final model (right) for Example C-6.