"""Masks created from images to be used for manipulating VoxelPart objects."""

from skimage.filters import threshold_otsu
from skimage.io import imread
from skimage.restoration import denoise_bilateral
from skimage.transform import rescale
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


def mask_from_image(image_path, scale=1.0, denoise=True, show_image=True):
    """Create a boolean mask from an image.
    # TODO
    Returns:

    """

    # Open the image and convert it to grayscale.
    gray_image = imread(fname=image_path, as_gray=True)

    # Denoise the image using a bilateral filer.
    if denoise:
        gray_image = denoise_bilateral(gray_image)

    # Apply Otsu’s method to make a binary image.
    thresh = threshold_otsu(gray_image)
    binary_image = gray_image > thresh

    # Apply the scale. # TODO: doc that the rescale method is used.
    gray_image = rescale(gray_image, scale, anti_aliasing=False)

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
    return binary_image




# https://scikit-image.org/docs/dev/api/skimage.io.html#imread-collection