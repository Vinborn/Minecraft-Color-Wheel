import numpy as np

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from PIL import Image

from pathlib import Path
from typing import Mapping, Sequence
import logging

from .color_spaces import oklab_2_srgb

logger = logging.getLogger(__name__)

def render_texture_and_oklab_mean(base_block_path: Path, oklab_mean: np.ndarray):
    """Renders original texture alongside its perceptual Oklab mean converted to sRGB."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10,5)) # 10x5 inches = 960x480 px

    # --- Left side ---
    # base block texture forced conversion of PIL to RGBA
    if base_block_path.exists():
        with Image.open(base_block_path) as original_texture:
            texture_rgba = original_texture.convert('RGBA')
            ax1.imshow(texture_rgba, interpolation='nearest')

    ax1.set_title(f"Original: {base_block_path.name.replace('_', " ")}", fontsize=14, fontweight='bold')
    ax1.axis('off')
    # + aspect ratio locking
    ax1.set_aspect(aspect="equal")

    # --- Right side ---
    # Fix gray color distortions (when gray renders as red)
    srgb_mean_float = oklab_2_srgb(oklab_mean, is_float=True)
    swatch = np.tile(srgb_mean_float, (16, 16, 1))

    ax2.imshow(swatch, interpolation='nearest')
    ax2.set_title("Perceptual Oklab Mean (SRGB)", fontsize=14, fontweight='bold')
    ax2.axis('off')
    ax2.set_aspect(aspect="equal")

    plt.tight_layout()
    plt.show()

def render_solid_harmony_color(base_color, harmony_color):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
    ax1.imshow(np.tile(base_color, (10, 10, 1)), interpolation='nearest')
    ax1.set_title("Base Color")
    ax1.axis('off')

    ax2.imshow(np.tile(harmony_color, (10, 10, 1)), interpolation='nearest')
    ax2.set_title("Complementary Color")
    ax2.axis('off')

    plt.tight_layout()
    plt.show()


def render_harmony(
        base_block_path: Path,
        texture_folder: Path,
        harmony_palettes: Mapping[str, Sequence[str]]
) -> None:
    """Dynamically renders block harmonies with O(1) access to texture files."""
    if not texture_folder.is_dir():
        logger.error(f"[!] Texture directory does not exist: {texture_folder}")
        raise NotADirectoryError(f"Missing texture folder: {texture_folder}")

    if not harmony_palettes:
        logger.warning("[!] Palette is empty!")

    def _load_texture(path: Path) -> Image.Image | None:
        try:
            with Image.open(path) as img:
                rgba = img.convert('RGBA')
                return rgba if rgba.height == 16 else rgba.crop((0, 0, 16, 16))
        except Exception as e:
            logger.error(f"[!] Failed to read file {path.name}: {e}")
            return None

    width_multiplier = 2.2
    height_multiplier = 1.7

    # Create a texture hash map in advance to prevent a recursive disk search inside the loop
    texture_map = {texture.stem: texture for texture in texture_folder.glob("*.png")}

    rows = len(harmony_palettes)
    max_cols_in_row = max(len(blocks) for blocks in harmony_palettes.values())
    # total columns: 2 for base color, 1 for harmony names
    total_cols = 3 + max_cols_in_row

    # dynamic window size
    fig = plt.figure(figsize=(width_multiplier * total_cols, height_multiplier * rows))
    grid = gridspec.GridSpec(nrows=rows, ncols=total_cols, figure=fig)

    # --- left side: base block texture ---
    ax_base = fig.add_subplot(grid[:, :2])
    if base_block_path.exists():
        base_img = _load_texture(base_block_path)
        if base_img:
            ax_base.imshow(base_img, interpolation='nearest')

    ax_base.set_title(
        f"Base:\n{base_block_path.stem.replace('_', ' ').title()}",
        fontsize=15,
        fontweight='bold',
        pad=10
    )
    ax_base.axis('off')
    ax_base.set_aspect('equal')

    # --- right side: harmony palettes ---
    for row_idx, (harmony_name, palette) in enumerate(harmony_palettes.items()):
        # Allocate an entire cell in the GridSpec for the text
        ax_text = fig.add_subplot(grid[row_idx, 2])
        ax_text.text(
            0.5, 0.5,
            harmony_name.capitalize(),
            va='center', ha='center',
            fontsize=14, fontweight='bold'
        )
        ax_text.axis('off')

        for col_idx, block_name in enumerate(palette):
            col_pos = 3 + col_idx
            ax_swatch = fig.add_subplot(grid[row_idx, col_pos])

            block_path = texture_map.get(block_name)
            if block_path:
                swatch_img = _load_texture(block_path)
                if swatch_img:
                    ax_swatch.imshow(swatch_img, interpolation='nearest')
            else:
                logger.debug(f"Texture for {block_name} was not found in map.")

            ax_swatch.set_title(block_name.replace('_', ' ').title(), fontsize=10, pad=5)
            ax_swatch.axis('off')
            ax_swatch.set_aspect('equal')

    plt.suptitle("Minecraft Palette Harmonies", fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.show()


def render_clusters(clusters: list, seed: int):
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 6))

    cluster0 = oklab_2_srgb(clusters[0], is_float=True)
    cluster1 = oklab_2_srgb(clusters[1], is_float=True)
    cluster2 = oklab_2_srgb(clusters[2], is_float=True)

    ax1.imshow(np.tile(cluster0, (16, 16, 1)), interpolation='nearest')
    ax1.axis('off')
    ax1.set_aspect(aspect="equal")

    ax2.imshow(np.tile(cluster1, (16, 16, 1)), interpolation='nearest')
    ax2.axis('off')
    ax2.set_aspect(aspect="equal")

    ax3.imshow(np.tile(cluster2, (16, 16, 1)), interpolation='nearest')
    ax3.axis('off')
    ax3.set_aspect(aspect="equal")

    plt.suptitle(f"Seed: {seed}", fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.show()
