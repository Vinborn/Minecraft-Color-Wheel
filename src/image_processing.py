import numpy as np
from PIL import Image
from pathlib import Path

# TODO: crop images (like respawn_anchor_top.png) to 16x16 pixels
def texture_2_srgb(image_path: Path, ignore_transparent:bool=True, alpha_threshold:int=128) -> np.ndarray:
    """
    Loads a PNG texture and returns a single list of sRGB values [R, G, B].
    :param alpha_threshold: min alpha value to not ignore transparency
    :param ignore_transparent: ignore transparent pixels
    :param image_path: path to PNG texture
    :return: single list of sRGB values
    """
    with Image.open(image_path)as img:
        # RGBA mode - rgb channel and Alpha channel
        img_rgba = img.convert('RGBA')
        # Flatten 2D grid of 16x16 4-element pixels into a single long list of 256 4-element pixels
        pixel_data = np.array(img_rgba).reshape(-1,4)

    img.close()

    # Filter
    if ignore_transparent:
        # Keep only pixels where the Alpha channel is above our threshold
        visible_mask = pixel_data[:, 3] >= alpha_threshold
        return pixel_data[visible_mask][:, :3]

    return pixel_data[:, :3]

def perceptual_mean(oklab_pixels: np.ndarray) -> np.ndarray:
    """Calculates the arithmetic mean in Oklab space (a vector of length 3)"""
    return np.mean(oklab_pixels, axis=0)