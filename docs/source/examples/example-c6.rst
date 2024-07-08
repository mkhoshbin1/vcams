Example C-6: Part from Image Series (3D)
========================================
In this example, a 3D part is created based on a sequence of images.
Two methods are presented, with the first using
the :func:`~vcams.mask.image.mask_from_image_sequence` function
which binarizes the image using the default Otsu's Threshold
and returns a 3D Boolean mask, which is then applied to the part.
The second method uses the :func:`~vcams.voxelpart.voxelpart_from_image` function
that does all of this automatically.

The image set used in this example is a micro-CT scan of the tibia of a mouse.
It has been made available by the authors of
`this data paper <https://doi.org/10.1038/sdata.2018.100>`__ [1]_
and its corresponding `figshare collection <https://doi.org/10.6084/m9.figshare.c.3795019.v1>`__.
The dataset is large and has not been included here, but it can be downloaded from the aforementioned links.

In the collection, the micro-CT scan used is named *MicroCT of mouse tibiae-oim4*
and consists of 991 images (which will be in the z-direction of the model),
each being 784×784 pixels. Each voxel is reported to be 5.06 micrometers.
The model is scaled at 50%, which means that voxel size must doubled.

The First Method
----------------
First, the image sequence is converted to a mask without being re-scaled.
The *load_pattern* parameter is set to a path which describes all of the
images in the sequence. They will be automatically be loaded in alphabetical order::

    image_mask = mask_from_image_sequence(load_pattern=r'D:\MicroCT of mouse tibiae-oim4\28Oim__rec0???.bmp',
                                          scale=1.0, denoise=True)

Then, a 3D part with the same shape as the mask is created
with a base material of 0 (empty space) and a voxel size of 0.01012 units in all directions.
The parameter *log_debug* is set to *True* for demonstration purposes.

Afterwards, the Boolean mask is applied to the part with a value of 1.
This means that the values of the elements selected by the mask are set to 1,
making them the only non-empty elements in the model.
And finally, the part is then exported to an Abaqus™ input file in *3D* mode with *C3D8R* elements.
The *Non-Empty* elements are requested to be exported.

The code can be found in the *examples* folder of the main repository. It is also included below:

.. literalinclude:: /../../examples/ex_c6_image_3d_a.py

The Second Method
-----------------
This method uses the :func:`~vcams.voxelpart.voxelpart_from_image` function
which automatically does all of the steps used in the first method.
it is more convenient, but allows for less customization.

.. literalinclude:: /../../examples/ex_c6_image_3d_b.py

Results
-------
The initial image and the final model are shown in :numref:`ex_c6_image_3d`.
It should be noted that the method used here is very crude.
Realistically, the images must be further processed
to reduce noise (note the specks on the image),
improve binarization, and remove the support structure.
Also, even the scaled model is very big (3.9M elements) and
may not be feasible for finite element analysis.

.. figure:: /images/ex_c6_image_3d.png
   :name: ex_c6_image_3d
   :align: center
   :alt: Isotropic image and two cross-sections of the model for Example C-6.

   Isotropic image and two cross-sections of the model for Example C-6.


.. [1] Ranzoni, A. M., Corcelli, M., Arnett, T. R. & Guillot, P. V. (2018).
       Micro-computed tomography reconstructions of tibiae of stem cell
       transplanted osteogenesis imperfecta mice.
       Sci. Data 5:180100.
       `<https://doi.org/10.1038/sdata.2018.100>`__