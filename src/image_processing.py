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

        if img_rgba.height > 16:
            img_rgba = img_rgba.crop((0, 0, 16, 16))

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


def k_mean_random(oklab_pixels: np.ndarray, seed: int = 85, k: int = 3) -> tuple[np.ndarray, list]:
    """
    Re-/Initialization method: pseudo-RANDO00000OM.
    :return Tuple: (centroids, weights)
    """
    # (A - B)^2 = A^2 - 2(A * B) + B^2 => fast with no square roots
    n = oklab_pixels.shape[0]

    rng = np.random.default_rng(seed=seed)

    # the IDs of the pixels used for the most recent centroid initialization/reinitialization
    pixel_ids = rng.choice(np.arange(0, n), size=k, replace=False)

    curr_centroids: np.ndarray[tuple] = np.array(
        [oklab_pixels[pixel_ids[0]],
         oklab_pixels[pixel_ids[1]],
         oklab_pixels[pixel_ids[2]]], dtype=np.float32
    )
    cluster_weights = []

    pixels_sq = np.sum(oklab_pixels ** 2, axis=1, keepdims=True)  # A^2 shape: (N, 1)

    iterations: int = 0

    while iterations < 15:
        # Assign pixels to cluster
        centroids_sq = np.sum(curr_centroids ** 2, axis=1)  # B^2 shape: (1, K)
        dot_product = np.dot(oklab_pixels, curr_centroids.T)  # A*B shape: (N, K)
        distances_sq = pixels_sq - 2 * dot_product + centroids_sq  # (A-B)^2  shape: (N, K)
        distances_sq = np.maximum(distances_sq, 0)  # correctness for negative floating-point precision

        # Vectorized assignment
        assignments = np.argmin(distances_sq, axis=1)

        # Calculating WCSS - Within-Cluster Sum of Squares
        wcss = 0.0
        for i in range(len(assignments)):
            cluster_index = assignments[i]
            wcss += distances_sq[i][cluster_index]

        # Count cluster sizes
        cluster_sizes = np.bincount(assignments, minlength=k)

        # Calculate cluster weights
        cluster_weights = [size / n for size in cluster_sizes]

        # Handle empty clusters
        zero_indices = np.where(cluster_sizes == 0)[0]
        if len(zero_indices) > 0:
            # Regenerate random centroid if cluster size was zero
            for z_idx in zero_indices:
                candidates = np.setdiff1d(np.arange(0, n), pixel_ids)
                new_pixel_index = rng.choice(candidates)

                curr_centroids[z_idx] = oklab_pixels[new_pixel_index]

                pixel_ids[z_idx] = new_pixel_index  # replace old pixel IDs
            iterations += 1
            continue

        # Calculating new centroid for each cluster
        new_centroids = np.zeros((k, 3), dtype=np.float32)
        np.add.at(new_centroids, assignments, oklab_pixels)

        # broadcasting division instead of the three manual loops
        new_centroids /= cluster_sizes[:, np.newaxis]

        # Check if the centroids are the same
        if np.allclose(a=new_centroids, b=curr_centroids):
            # Return new_centroids because they are the result of the current iteration
            return new_centroids, cluster_weights

        curr_centroids = new_centroids
        iterations += 1

    return curr_centroids, cluster_weights
