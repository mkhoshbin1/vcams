.. _predefined-image:

Image-Based Structures
======================
It is often necessary to create a structure based on images.
These can be a singular such as a microscopy image,
or a sequence such as a stack forming a of Computerized Tomography (CT) Scan.

VCAMS offers two functions that create Boolean masks based on images.
These can then be used for manipulating VoxelPart objects
as described in the :ref:`relevant section <boolean-masks>` of the documentation.

It should be noted that these functions offer a very specific set of features.
Real images are rarely perfect and some trial and error
with different image processing algorithms and parameters may be necessary.

The author's experience with 2D microscopy images suggests a combination of the following:

  + Creating a special algorithm based on these functions.
    You can then apply the final binary mask to an empty part of an appropriate size.

  + Performing the image processing (particularly thresholding and denoising)
    in a software such as Adobe Photoshop™, GIMP, or ImageJ/FIJI
    These software include a large number of filters and their GUIs
    facilitate thresholding. The final binary image can then be input as a binary mask.

  + Manually retouching the image to make features more distinguishable.
    This may be unavoidable for microscopy images of very poor quality,
    but the retouching *must* be limited to fixing glares and obvious noises.
    Utmost care must be taken to preserve the image's integrity,
    especially for edges of objects or phases.
    Furthermore, some simulations are more sensitive to these kinds of changes.
    If you think you shouldn't do this for your simulation, you probably shouldn't.

The two functions used for singular images and image sequences are
:func:`~vcams.mask.image.mask_from_image`
and :func:`~vcams.mask.image.mask_from_image_sequence`, respectively.
Users are advised to thoroughly read the documentation and even the source code
to familiarize themselves with the specific set of procedures done in these functions.
Finally, users should not be discouraged by bad results because
oftentimes a great deal of trial and error is necessary.

Examples :doc:`C-6 </examples/example-c6>` and :doc:`C-7 </examples/example-c7>`
demonstrate the use of these functions.