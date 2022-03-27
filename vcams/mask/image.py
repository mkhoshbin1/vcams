"""Functions used for creating a boolean mask from one or a sequence of images.

These resulting mask can then be used
for manipulating a :class:`~vcams.voxelpart.VoxelPart` object
using its :meth:`~vcams.voxelpart.VoxelPart.apply_mask` method.
See the :ref:`predefined-image` section for a complete explanation
of the basic concepts.
"""

from logging import getLogger
from warnings import warn

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from numpy import moveaxis, unique, ndarray
from skimage.filters import threshold_otsu
from skimage.io import imread, ImageCollection
from skimage.restoration import denoise_bilateral
from skimage.transform import rescale

logger = getLogger(__name__)


def mask_from_image(image_path: str, scale: float = 1.0,
                    denoise: bool = True, show_image: bool = False) -> ndarray:
    """Return a boolean mask by thresholding an image.

    This function does the following in the given order:

      1. Scale the image. ``skimage.transform.rescale()`` is used with ``anti_aliasing=True``.
      2. If specified, Denoise the image using ``skimage.restoration.denoise_bilateral()``.
      3. Apply a threshold using ``skimage.filters.threshold_otsu()``.
      4. If specified, show the opened image as grayscale and the final binary image.

    Args:
        image_path: Full path to the image file. The image will be opened as grayscale.
        scale: Scale to be applied to the image. Note that a scale greater than 1.0
               will introduce fake precision by interpolating the data and issues a warning.
        denoise: If set to True, the image will be denoised using a Bilateral filter.
        show_image: If set to True, the opened image and the final binary image
                    will be shown side by side in a figure.
                    The program may be paused while the window is open.

    Returns:
        The binary mask derived from the image.
    """
    if scale <= 0.0:
        raise ValueError('scale must be positive.')

    if scale > 1.0:
        warn('scale is greater than 1.0 which introduces fake precision.')  # TODO: test this.

    # Open the image and convert it to grayscale.
    gray_image = imread(fname=image_path, as_gray=True)
    logger.debug("Opened image '%s'.", image_path)

    # Apply the scale.
    gray_image = resize_image(gray_image, scale)

    # Denoise the image using a Bilateral filer.
    if denoise:
        gray_image = denoise_bilateral(gray_image)
        logger.debug('Denoised the image using a Bilateral filer.')

    # Apply Otsu’s method to make a binary image.
    thresh = threshold_otsu(gray_image)
    binary_image = gray_image > thresh
    logger.debug("Applied the Otsu's Method to create a binary image.")

    # Show the image.
    if show_image:
        fig, axes = plt.subplots(ncols=2, figsize=(9, 4), sharey='all')
        plt.get_current_fig_manager().set_window_title('Image Preview (Close to Continue)')
        ax = axes.ravel()
        ax[0] = plt.subplot(1, 2, 1)
        ax[1] = plt.subplot(1, 2, 2)
        ax[0].imshow(gray_image, cmap=plt.cm.gray)
        ax[0].set_title('Opened Image (Grayscale)')
        ax[0].axis('off')
        ax[1].imshow(binary_image, cmap=ListedColormap(['black', 'white']))
        ax[1].set_title('Binary Image')
        ax[1].axis('off')
        plt.show(block=True)

    # Return the binary mask.
    logger.info("Created a binary mask from the image at '%s'.", image_path)
    return binary_image


# https://scikit-image.org/docs/dev/api/skimage.io.html#imread-collection

def mask_from_image_sequence(load_pattern, scale=1.0, denoise=True):
    """Return a boolean mask by opening and thresholding an image sequence.

    This function opens all images using the :func:`mask_from_image` function,
    applies the scale, and returns the final 3D binary mask.

    Note that the images are initially opened with a scale of 1.0
    meaning that this function may require a lot of RAM.

    Args:
        load_pattern: A pattern describing the path of all images in the sequence.
                      Use the *?* symbol as a placeholder for a single character.
        scale: Scale to be applied to the image. Note that a scale greater than 1.0
               will introduce fake precision by interpolating the data and issues a warning.
        denoise: If set to True, the image will be denoised using a Bilateral filter.

    Returns:
        The binary mask derived from the image sequence.
    """
    # Create an ImageCollection function which loads the images using
    # the mask_from_image() function. No scaling is applied and denoising is done if requested.
    image_coll = ImageCollection(load_pattern=load_pattern, conserve_memory=False,
                                 load_func=mask_from_image, scale=1.0, denoise=denoise,
                                 show_image=False)

    # Make sure the collection has an appropriate number of images.
    if len(image_coll) == 0:
        raise ValueError('The image collection is empty. The most likely reason is an incorrect '
                         'load_pattern.')
    elif len(image_coll) == 1:
        warn('Only one image has been loaded into the image collection. This may indicate misuse '
             'or an incorrect load_pattern.')
        # TODO: use this method of filling (space in above line) everywhere else.
    else:
        logger.debug('Loaded %u images in the image collection', len(image_coll))

    full_image = moveaxis(image_coll.concatenate(), 0, -1)
    # TODO: test input with and without move axis.
    # TODO: is scale passed? is it already done by now? either way, check for 1.0.
    # Apply the scale.
    full_image = resize_image(full_image, scale)
    return full_image


def resize_image(image: ndarray, scale: float) -> ndarray:
    """Resize an image. This function is not intended for standalone use.

    Args:
        image: The image to be resized.
               If the input image is a boolean mask, nearest-neighbor interpolation
               will be used without anti-aliasing and the output will be cast to a boolean mask.
               Otherwise, a simple resizing operation with the default parameters
               of ``skimage.transform.rescale()`` will be attempted.
        scale: The scale to be applied. If equal to 1.0, the function logs the call and returns.

    Returns:
        The resized image which is of the same *dtype* as the input.
    """
    if scale == 1.0:
        logger.debug('Scale was equal to 1.0. No resizing was performed.')
        return image

    if image.dtype == bool:
        # For boolean images, interpolation order must be 0, which means that
        # the nearest-neighbor interpolation method will be used.
        # Also, anti aliasing must be turned off.
        # See https://github.com/scikit-image/scikit-image/issues/4292
        # and https://github.com/scikit-image/scikit-image/issues/4998.
        image = rescale(image, scale, order=0, anti_aliasing=False)

        # Rescale returns a float array which needs to be converted to bool.
        if image.dtype == float:
            if all(unique(image) == [0.0, 1.0]):
                image = image.astype(bool)
            else:
                raise RuntimeError('It is expected that skimage.transform.rescale '
                                   'returns a float array with only 0.0 and 1.0 values, '
                                   'which was not the case.')
    else:
        # Image is not a boolean.
        # TODO: test data type.
        image = rescale(image, scale, anti_aliasing=True)

    logger.debug('Applied a scale of %.2f.', scale)
    return image
