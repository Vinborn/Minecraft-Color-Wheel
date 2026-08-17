from pathlib import Path

from . import color_harmonies
from . import color_spaces
from . import image_processing

from .models import Oklab, Oklch, BlockData
from .database import BlockDatabase

def analysis_textures(version: str, textures_dir: Path, db_path: Path) -> BlockDatabase:
    """
    Get all textures, calculate perceptual mean for each one, save data to database.
    """
    db = BlockDatabase(db_path)
    if db.blocks:
        print(f"[+] The existing database has been loaded: {db_path.name}")
        return db

    png_files = list(textures_dir.glob("*.png"))
    total_files = len(png_files)
    result_data: dict[str, BlockData] = {}

    for idx, file_path in enumerate(png_files):
        try:
            srgb_pixels = image_processing.texture_2_srgb(file_path)
            # Skip not full/transparent block textures
            if srgb_pixels.shape[0] < 256:
                continue

            oklab_pixels = color_spaces.srgb_2_oklab(srgb_pixels)
            oklab_mean = image_processing.perceptual_mean(oklab_pixels)

            L, a, b = oklab_mean[0], oklab_mean[1], oklab_mean[2]
            oklch_mean = color_spaces.oklab_2_oklch(L, a, b)

            srgb_mean = color_spaces.oklab_2_srgb(oklab_mean)
            hex_code = color_spaces.srgb_2_hex(srgb_mean)

            result_data[file_path.stem] = BlockData(
                hex=hex_code,
                oklab=Oklab(float(L), float(a), float(b)),
                oklch=Oklch(*oklch_mean)
            )

            if idx % 25 == 0 or idx == total_files:
                progress = (idx / total_files) * 100
                print(f"Progress: [{idx}/{total_files}] ({progress:.1f}%) processed.")

        except Exception as e:
            print(f"[!] Failed to process {file_path.name}. Reason: {e}")

    db.save(version, result_data)
    print(f"[✓] Database has been successfully saved: {db_path}")
    return db

def generate_harmonies_for_block(target_block_name: str, db: BlockDatabase, global_exclusion: bool = False) -> dict[str, list[str]]:
    """
    Loads the database, calculates all computational harmonies for a given block,
    and maps theoretical color coordinates back to real Minecraft block names.
    :param target_block_name: anchor block texture name etc. "lapis_ore", "acacia_planks"
    :param db: Preloaded BlockDatabase instance
    :param global_exclusion: If True, prevents repeating any block across ALL harmony palettes
    """
    if target_block_name not in db.blocks:
        raise ValueError(f"[!] Block {target_block_name} not found in database!")

    base_block = db.blocks[target_block_name]
    base_oklch = base_block.oklch

    # Calculates color harmonies for base color
    harmonies = {
        "complementary": color_harmonies.complementary(base_oklch),
        "monochromatic": color_harmonies.monochromatic(base_oklch),
        "analogous": color_harmonies.analogous(base_oklch),
        "triadic": color_harmonies.triadic(base_oklch)
    }

    resolved_palettes: dict[str, list[str]] = {}
    global_exclude_names: set[str] = {target_block_name}

    for harmony_name, palette in harmonies.items():
        # Reset set of excluded block textures to make unique local harmonies
        local_exclude_names = global_exclude_names.copy() if global_exclusion else {target_block_name}
        matched_blocks: list[str] = []

        # Skip the base color (index 0) from palette
        for oklch_color in palette[1:]:
            closest_texture = db.find_closest_mc_texture(target_oklch=oklch_color, exclude_names=local_exclude_names)
            matched_blocks.append(closest_texture)

            # Update exclusion sets dynamically
            local_exclude_names.add(closest_texture)
            if global_exclusion:
                global_exclude_names.add(closest_texture)

        resolved_palettes[harmony_name] = matched_blocks
    return resolved_palettes