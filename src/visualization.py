import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from PIL import Image
from pathlib import Path

from .color_spaces import oklab_2_srgb


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

def display_solid_harmony_color(base_color, harmony_color):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
    ax1.imshow(np.tile(base_color, (10, 10, 1)), interpolation='nearest')
    ax1.set_title("Base Color")
    ax1.axis('off')

    ax2.imshow(np.tile(harmony_color, (10, 10, 1)), interpolation='nearest')
    ax2.set_title("Complementary Color")
    ax2.axis('off')

    plt.tight_layout()
    plt.show()

def display_harmony_palettes(base_block_path: Path, texture_folder: Path, harmony_palettes:dict): #
    """
    Creates a single consolidated plot:
    - Left: Large base block texture image.
    - Right: 4 rows of harmony palettes with color swatches.
    """
    # Initialize a single figure with a custom GridSpec layout
    # 12x6 inches = 1152×576 px
    # 4 rows = complementary, monochromatic, analogous and triadic
    fig = plt.figure(figsize=(12,6))
    gs = gridspec.GridSpec(4, 6, figure=fig)

    # --- left side: base block texture ---
    # Span across all 4 rows and the first 2 columns (cols 0 and 1)
    ax_base = fig.add_subplot(gs[:, :2])
    try:
        # Convert single list of 256 sRGB pixels to a 16x16 shape of MC texture
        # base_texture = (texture_2_srgb(image_path=base_block_path)).reshape(16, 16, 3)
        base_texture = Image.open(base_block_path)
        ax_base.imshow(base_texture, interpolation='nearest')
        ax_base.set_title("Base Block", fontsize=15, fontweight='bold',pad=10)
    except Exception as e:
        print("ERROR. Reason: ", e)

    ax_base.axis('off')
    plt.suptitle("Harmonies", fontsize=16, fontweight='bold', y=0.95)
    # plt.tight_layout()
    # plt.show()
    # return
    #print("Base color was successfully displayed")

    # --- right side: Harmony Rows ---
    png_files = list(texture_folder.glob("*.png"))
    harmony_rows = list(harmony_palettes.keys()) # ["complementary", "monochromatic", "analogous", "triadic"]
    for row_idx, harmony_name in enumerate(harmony_rows):
        block_textures = harmony_palettes[harmony_name]

        # Create a subplot for the harmony label/row (spanning columns 2 to 5)
        # We use individual subplots or draw patches per row
        for col_idx, block_name in enumerate(block_textures):
            # Compute grid column position (offsetting by 2 columns to leave room on the left)
            col_pos = 3 + col_idx
            ax_swatch = fig.add_subplot(gs[row_idx, col_pos])

            for file_path in png_files:
                texture_name = file_path.stem
                if block_name == texture_name:
                    try:
                        harmony_texture = Image.open(file_path)
                        ax_swatch.imshow(harmony_texture, interpolation='nearest')
                    except Exception as e:
                        print("ERROR. Reason: ", e)

            # Draw a solid color patch representing the block's mean color
            #print(f"{harmony_name.capitalize()}: {color}")
            # ax_swatch.set_facecolor(block_name)
            # ax_swatch.set_xticks([])
            # ax_swatch.set_yticks([])

            # Add block name as a clean label under or inside the swatch
            ax_swatch.set_title(f"{block_name.capitalize()}", fontsize=10, pad=5)

            # Add a clean border around the swatch box
            for spine in ax_swatch.spines.values():
                spine.set_edgecolor('#333333')
                spine.set_linewidth(1.5)

        print(f"{harmony_name.capitalize()} was successfully displayed\n")

        row_y_coords = [0.87, 0.67, 0.5, 0.23] # Estimated vertical offsets for 4 rows
        fig.text(0.35, row_y_coords[row_idx], f"{harmony_name.capitalize()}", va='center', fontsize=15, fontweight='bold')

    plt.suptitle("Harmonies", fontsize=16, fontweight='bold', y=0.97)
    plt.tight_layout()
    plt.show()

def render_harmony(base_block_path: Path, texture_folder: Path, harmony_palettes: dict[str, list[str]]):
    """Renders harmonies with O(1) access to texture files."""
    # Create a texture hash map in advance to prevent a recursive disk search inside the loop
    texture_map = {texture.stem: texture for texture in texture_folder.glob("*.png")}

    # 12x6 inches = 1152×576 px
    # 4 rows = complementary, monochromatic, analogous and triadic
    fig = plt.figure(figsize=(12, 6))
    gs = gridspec.GridSpec(4, 6, figure=fig)

    # --- left side: base block texture ---
    ax_base = fig.add_subplot(gs[:, :2])
    if base_block_path.exists():
        with Image.open(base_block_path) as base_img:
            texture_rgba = base_img.convert('RGBA')
            ax_base.imshow(texture_rgba, interpolation='nearest')
    ax_base.set_title(f"Base: {base_block_path.stem.title().replace("_", " ")}", fontsize=15, fontweight='bold', pad=10)
    ax_base.axis('off')
    ax_base.set_aspect('equal')

    # --- right side: Harmony Rows ---
    row_y_coords = [0.87, 0.67, 0.5, 0.23]  # Estimated vertical offsets for 4 rows
    harmony_rows = list(harmony_palettes.keys())
    for row_idx, harmony_name in enumerate(harmony_rows):
        block_names = harmony_palettes[harmony_name]

        for col_idx, block_name in enumerate(block_names):
            col_pos = 3 + col_idx
            ax_swatch = fig.add_subplot(gs[row_idx, col_pos])

            # O(1) file search using a hash map instead of iterative scans
            if block_name in texture_map:
                with Image.open(texture_map[block_name]) as texture_img:
                    texture_rgba = texture_img.convert("RGBA")
                    ax_swatch.imshow(texture_rgba, interpolation='nearest')

            # Add a clean border around the swatch box
            for spine in ax_swatch.spines.values():
                spine.set_edgecolor('#333333')
                spine.set_linewidth(1.5)

            ax_swatch.set_title(block_name.title().replace("_", " "), fontsize=10, pad=5)

        fig.text(0.35, row_y_coords[row_idx], f"{harmony_name.capitalize()}", va='center', fontsize=14, fontweight='bold')

    plt.suptitle("Minecraft Palette Harmonies", fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.show()