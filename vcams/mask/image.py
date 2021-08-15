"""Masks created from images to be used for manipulating VoxelPart objects.

These functions offer a very specific set of features.
Real images are rarely perfect and some trial and error
with different image processing algorithms and parameters
may be necessary.
The author's experience with 2D microscopy images suggests a combination of the following:
  + Creating a special algorithm based on these functions.
    You can then apply the final binary mask to an empty part of an appropriate size.
  + Performing the image processing in a software such as Adobe Photoshop (TM), GIMP,
    or ImageJ/FIJI. These software include a large number of filters and their GUIs
    facilitate thresholding. The final binary image can then be input as a binary mask.
  + Manually retouching the image to make features more distinguishable.
    This may be unavoidable for microscopy images of very poor quality,
    but the retouching must be limited to fixing glares and obvious noises.
    Utmost care must be taken to preserve the images's integrity,
    especially for edges of objects or phases.
    Furthermore, some simulations are more sensitive to these kinds of changes.
    If you think you shouldn't do this for your simulation, you probably shouldn't.
"""

import logging
from warnings import warn

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from numpy import moveaxis
from skimage.filters import threshold_otsu
from skimage.io import imread, ImageCollection
from skimage.restoration import denoise_bilateral
from skimage.transform import rescale

logger = logging.getLogger(__name__)


def mask_from_image(image_path, scale=1.0, denoise=True, show_image=True):
    """Return a boolean mask by thresholding an image.

    This function does the following in the given order:
      1. Scale the image. skimage.transform.rescale() is used with anti_aliasing=True.
      2. If specified, Denoise the image using skimage.restoration.denoise_bilateral().
      3. Apply a threshold using skimage.filters.threshold_otsu().
      4. If specified, show the opened image as grayscale and the final binary image.

    Args:
        image_path (str): Full path to the image file. The image will be opened as a grayscale.

        scale (float): Scale to be applied to the image. Note that a scale greater than 1.0
                       will introduce fake precision by interpolating the data.
                       If so, a warning is raised.
                       Defaults to 1.0.

        denoise (bool): If set to :py:obj:`True`, the image will be denoised using
                        a Bilateral filter.
                        Defaults to :py:obj:`True`.

        show_image (bool): If set to :py:obj:`True`, the opened image and the final binary image
                           will be shown side by side in a figure. The program may be paused
                           while the window is open. Defaults to :py:obj:`True`.

    Returns:
        bool: The binary mask derived from the image.
    """

    if scale <= 0.0:
        raise ValueError('scale must be positive.')

    if scale > 1.0:
        warn('scale is greater than 1.0 which introduces fake precision.')  # TODO: test this.

    # Open the image and convert it to grayscale.
    gray_image = imread(fname=image_path, as_gray=True)
    logger.debug("Opened image '%s'.", image_path)

    # Apply the scale.
    if scale != 1.0:
        gray_image = rescale(gray_image, scale, anti_aliasing=True)
        logger.debug('Applied a scale of %.2f.', scale)

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
        ax = axes.ravel()
        ax[0] = plt.subplot(1, 2, 1)
        ax[1] = plt.subplot(1, 2, 2)
        ax[0].imshow(gray_image, cmap=plt.cm.gray)
        ax[0].set_title('Opened Image (Grayscale)')
        ax[0].axis('off')
        ax[1].imshow(binary_image, cmap=ListedColormap(['black', 'white']))
        ax[1].set_title('Binary Image')
        ax[1].axis('off')
        plt.show()

    # Return the binary mask.
    logger.info("Created a binary mask from the image at '%s'.", image_path)
    return binary_image


# https://scikit-image.org/docs/dev/api/skimage.io.html#imread-collection

def mask_from_image_sequence(load_pattern, scale=1.0, denoise=True):
    # TODO: add show_image.

    # Create an ImageCollection function which loads the images using
    # the mask_from_image() function. No scaling is applied and denoising is done if requested.
    image_coll = ImageCollection(load_pattern=load_pattern, conserve_memory=True,
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

    # Apply the scale.
    if scale != 1.0:
        full_image = rescale(full_image, scale, anti_aliasing=True)
        logger.debug('Applied a scale of %.2f.', scale)

    return full_image
