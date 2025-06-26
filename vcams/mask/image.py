"""Functions used for creating a Boolean mask from one or a sequence of images.

The resulting masks can then be used
for manipulating a :class:`~vcams.voxelpart.VoxelPart` instance
using its :meth:`~vcams.voxelpart.VoxelPart.apply_mask` method.
See the :ref:`predefined-image` section for a complete explanation
of the basic concepts.
"""

from logging import getLogger
from warnings import warn

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from numpy import moveaxis, unique, ndarray, where, rot90
from numpy.core.numeric import array_equal
from skimage.filters.thresholding import threshold_otsu
from skimage.io import imread, ImageCollection
from skimage.restoration import denoise_bilateral
from skimage.transform import rescale

logger = getLogger(__name__)

# A list of available thresholding modes used in the GUI.
image_thresh_mode_list = ('none', 'manual', 'otsu')


def mask_from_image(image_path: str, scale: float = 1.0,
                    denoise: bool = True, show_image: bool = False,
                    thresh_mode: str = 'otsu', thresh_value: float = None,
                    verbose_log: bool = True, final_log: bool = True) -> ndarray:
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
        thresh_mode: The kind of threshold to be applied to the image.
                     Valid values are 'none', 'manual', and 'otsu'. Defaults to 'otsu'.
        thresh_value: If *thresh_mode* is set to 'manual', should be a float in the range (0, 1)
                      Which is used as a threshold for binarizing the image.
                      Defaults to *None* which raises an error when used.
        show_image: If set to True, the opened image and the final binary image
                    will be shown side by side in a figure.
                    The program may be paused while the window is open.
        verbose_log: If set to True, logs will be verbose, otherwise only one entry will be made.
        final_log: If set to True, the final log entry will be made.

    Returns:
        The binary mask derived from the image.
    """
    if scale <= 0.0:
        raise ValueError('scale must be positive.')
    if scale > 1.0:
        warn('scale is greater than 1.0 which introduces fake precision.')

    valid_thresh_modes = ('none', 'manual', 'otsu')
    if thresh_mode.lower() not in ('manual', 'otsu'):
        raise ValueError(f"Invalid thresh_mode. Valid values are: {', '.join(valid_thresh_modes)}.")

    if (thresh_mode.lower() == 'manual') and ((thresh_value >= 1) or (thresh_value <= 0)):
        raise ValueError(f'For manual thresholding, thresh_value must be in the range (0, 1), '
                         f'but it is {thresh_value:.3f}.')

    # Open the image and convert it to grayscale.
    gray_image = imread(fname=image_path, as_gray=True)  # Note gray_image has a dtype of float, i.e. [0, 1].
    if verbose_log:
        logger.debug(f"Opened image '{image_path}'.")

    # Apply the scale.
    gray_image = resize_image(gray_image, scale, verbose_log)

    # The image must be rotated -90 degrees to account for the
    # difference between the XY directions in Abaqus and the picture.
    gray_image = rot90(gray_image, -1)
    if verbose_log:
        logger.debug('Rotated the image -90 degrees to account for '
                     'the difference between the XY directions in Abaqus and the picture.')

    # Denoise the image using a Bilateral filer.
    if denoise:
        gray_image = denoise_bilateral(gray_image)
        if verbose_log:
            logger.debug('Denoised the image using a Bilateral filer.')

    if thresh_mode.lower() == 'none':
        binary_image = gray_image
        if verbose_log:
            logger.debug('No thresholding applied to the image.')
    else:
        # Apply Otsu’s method to make a binary image.
        if thresh_mode == 'manual':
            pass  # thresh_value is assumed to be correct.
        elif thresh_mode == 'otsu':
            thresh_value = threshold_otsu(gray_image)
        else:
            raise ValueError(f"Invalid thresh_mode. Valid values are: {', '.join(valid_thresh_modes)}. "
                             f"This should have been caught earlier.")
        # Threshold the image based on the thresh_value value
        binary_image = gray_image > thresh_value
        if verbose_log:
            logger.debug(f'Applied a {thresh_mode} threshold to the image with a value of {thresh_value:.3f}.')

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
        num_dark_px = len(where(binary_image == 0)[0]) / binary_image.size
        num_light_px = len(where(binary_image == 1)[0]) / binary_image.size
        ax[1].annotate(f'Light Pixels = {100 * num_light_px:3.2f}%, Dark Pixels = {100 * num_dark_px:3.2f}%',
                       xy=(0.5, -0.05), xycoords='axes fraction', ha='center')
        plt.show(block=True)

    # Return the binary mask.
    final_log_msg = f"Created a binary mask from the image at '{image_path}' with a scale of {scale:.2f}."
    if final_log:
        logger.info(final_log_msg)
    else:
        if verbose_log:
            logger.debug(final_log_msg)
    return binary_image


def mask_from_image_sequence(load_pattern: str, scale: float = 1.0,
                             denoise: bool = True,
                             thresh_mode: str = 'otsu', thresh_value: float = None):
    """Return a boolean mask by opening and thresholding an image sequence.

    This function opens all images using the :func:`mask_from_image` function,
    applies the scale, and returns the final 3D binary mask.

    This function opens the images with a scale of 1.0 and then resizes them,
    meaning that a lot of RAM may be required.

    Args:
        load_pattern: A pattern describing the path of all images in the sequence.
                      Use the *?* symbol as a placeholder for a single character.
        scale: Scale to be applied to the images. Note that a scale greater than 1.0
               will introduce fake precision by interpolating the data and issues a warning.
        thresh_mode: The kind of threshold to be applied to the image.
                     Valid values are 'none', 'manual', and 'otsu'. Defaults to 'otsu'.
        thresh_value: If *thresh_mode* is set to 'manual', should be a float in the range (0, 1)
                      Which is used as a threshold for binarizing the image.
                      Defaults to *None* which raises an error when used.
        denoise: If set to True, the image will be denoised using a Bilateral filter.

    Returns:
        The binary mask derived from the image sequence.
    """
    if scale <= 0.0:
        raise ValueError('scale must be positive.')
    if scale > 1.0:
        warn('scale is greater than 1.0 which introduces fake precision.')

    valid_thresh_modes = ('none', 'manual', 'otsu')
    if thresh_mode.lower() not in ('manual', 'otsu'):
        raise ValueError(f"Invalid thresh_mode. Valid values are: {', '.join(valid_thresh_modes)}.")

    if (thresh_mode.lower() == 'manual') and ((thresh_value >= 1) or (thresh_value <= 0)):
        raise ValueError(f'For manual thresholding, thresh_value must be in the range (0, 1), '
                         f'but it is {thresh_value:.3f}.')

    # Create an ImageCollection function which loads the images using
    # the mask_from_image() function. No scaling is applied and denoising is done if requested.
    image_coll = ImageCollection(load_pattern=load_pattern, conserve_memory=False,
                                 load_func=mask_from_image,
                                 scale=1.0, denoise=denoise,
                                 thresh_mode=thresh_mode, thresh_value=thresh_value,
                                 show_image=False, verbose_log=False, final_log=False)

    # Make sure the collection has an appropriate number of images.
    if len(image_coll) == 0:
        raise ValueError('The image collection is empty. '
                         'The most likely reason is an incorrect load_pattern.')
    elif len(image_coll) == 1:
        RuntimeWarning('Only one image has been loaded into the image collection. This may indicate misuse '
                       'or an incorrect load_pattern.')
    else:
        logger.info(f'Loaded {len(image_coll)} images in the image collection')

    full_image = moveaxis(image_coll.concatenate(), 0, -1)
    # Apply the scale.
    full_image = resize_image(full_image, scale, verbose_log=True)
    return full_image


def resize_image(image: ndarray, scale: float, verbose_log: bool = True) -> ndarray:
    """Resize an image. This function is not intended for standalone use.

    Args:
        image: The image to be resized.
               If the input image is a boolean mask, nearest-neighbor interpolation
               will be used without antialiasing and the output will be cast to a boolean mask.
               Otherwise, a simple resizing operation with the default parameters
               of ``skimage.transform.rescale()`` will be attempted.
        scale: The scale to be applied. If equal to 1.0, the function logs the call and returns.
        verbose_log: If set to True, logs will be verbose, otherwise no entry will be made.

    Returns:
        The resized image which is of the same *dtype* as the input.
    """
    if scale == 1.0:
        if verbose_log:
            logger.debug('Scale was equal to 1.0. No resizing was performed.')
        return image

    if image.dtype == bool:
        # For boolean images, interpolation order must be 0, which means that
        # the nearest-neighbor interpolation method will be used.
        # Also, antialiasing must be turned off.
        # See https://github.com/scikit-image/scikit-image/issues/4292
        # and https://github.com/scikit-image/scikit-image/issues/4998.
        image = rescale(image, scale, order=0, anti_aliasing=False)

        # Rescale returns a float array which needs to be converted to bool.
        if image.dtype == float:
            if array_equal(unique(image), [0.0, 1.0]):
                image = image.astype(bool)
            else:
                raise RuntimeError('It is expected that skimage.transform.rescale '
                                   'returns a float array with only 0.0 and 1.0 values, '
                                   'which was not the case.')
    else:
        # Image is not a boolean.
        image = rescale(image, scale, anti_aliasing=True)

    if verbose_log:
        logger.debug('Applied a scale of %.2f.', scale)
    return image
