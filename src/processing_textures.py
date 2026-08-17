# NOTE: this is my first scheme or, more likely, a draft
# It does not use in any file, but it just a reminder how 'bad code' could be

import json
from pathlib import Path

import color_spaces
import color_harmonies
from image_processing import perceptual_mean

def block_database_decoder(self, dct: dict):
    """
    Called automatically on every JSON object `{}` decoded.
    """
    # If the dictionary has our color keys, parse it into BlockData
    if "hex_color" in dct and "oklab" in dct:
        return ... #BlockData(
        #         hex=dct["hex_color"],
        #         oklab=Oklab(*dct["oklab"]),
        #         oklch=Oklch(*dct["oklch"])
        # )

    # Otherwise, return dict as-is
    return dct

def has_json_data(path: Path) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Evaluates False if data is {}, [], "", None, or 0
            return bool(data)
    except (json.JSONDecodeError, FileNotFoundError):
        return False

def run_texture_analysis(version: str, textures_dir: str, output_dir: str, database_name:str, display_results: bool=False):
    """Get all textures, calculate perceptual mean for each one, save data to database.
    :param version: version of minecraft textures
    :param textures_dir: where textures are stored
    :param output_dir: where to store the results
    :param database_name: name of the database to store the results (without file extension)
    :param display_results: display results with plot or not
    """
    textures_folder = Path(textures_dir)
    output_folder = Path(output_dir)
    database_path = output_folder / Path(version+"_"+database_name+".json")

    # Check if we have any textures to process
    if not textures_folder.exists() or not any(textures_folder.glob("*.png")):
        print(f"ERROR: textures folder does not exist: {textures_folder}")
        return None
    elif has_json_data(database_path):
        print(f"There are some data in path: {database_path}.")
        return database_path

    output_folder.mkdir(parents=True, exist_ok=True)

    # This dictionary will store our final structured dataset
    color_database = {
        "minecraft_ver": version,
    }

    # Get a list of all PNG files in the texture cache directory
    png_files = list(textures_folder.glob("*.png"))
    total_files = len(png_files)
    processed_count = 0

    for file_path in png_files:
        texture_name = file_path.stem # e.g., 'lapis_ore' from 'lapis_ore.png'

        try:
            # Load the texture and extract visible sRGB pixels
            srgb_pixels = color_spaces.texture_2_srgb(file_path, ignore_transparent=True, alpha_threshold=128)

            # Skip this file entirely, if full or half transparent
            # 768 = 256(texture size) * 3 (RGB channels) for full block
            if srgb_pixels.size == 0 or srgb_pixels.size < 768:
                print(f"'{file_path}' has been skipped. Reason: not full block")
                continue

            # Convert raw sRGB pixel arrays to perceptual Oklab space
            oklab_pixels = color_spaces.srgb_2_oklab(srgb_pixels)

            # Calculate the perceptual arithmetic mean inside Oklab space
            perceptual_oklab = perceptual_mean(oklab_pixels)

            L = perceptual_oklab[0]
            a = perceptual_oklab[1]
            b = perceptual_oklab[2]

            # Convert oklab to oklch color space for future modifications
            L, C, h = color_spaces.oklab_2_oklch(L, a, b)

            oklab_list = [float(L), float(a), float(b)]
            oklch_list = [float(L), float(C), float(h)]

            # Convert the resulting sRGB average into a Hexadecimal string
            perceptual_srgb = color_spaces.oklab_2_srgb(perceptual_oklab)
            hex_color = color_spaces.srgb_2_hex(perceptual_srgb)

            if display_results:
                try:
                    data_display.render_texture_and_oklab_mean(srgb_pixels, perceptual_srgb)
                except Exception as e:
                    print("Warning: Failed to display results. Reason: ", e)

            color_database[texture_name] = {
                "oklab": oklab_list,
                "oklch": oklch_list,
                "hex_color": f"{hex_color}",
            }

            processed_count += 1

            # Print a neat console progress bar
            if processed_count % 25 == 0 or processed_count == total_files:
                progress = (processed_count / total_files) * 100
                print(f"Progress: [{processed_count}/{total_files}] ({progress:.1f}%) processed.")

        except Exception as e:
            print(f"Warning: Failed to process '{file_path}'. Reason: {e}")

    with open(database_path, "w", encoding="utf-8") as json_file:
        # Use indent=4 for a great formatted, human-readable JSON output
        json.dump(color_database, json_file, indent=2)

    return database_path

def find_texture(texture_name: str, textures_dir: str):
    textures_folder = Path(textures_dir)

    # Check if we have any textures to process
    if not textures_folder.exists() or not any(textures_folder.glob("*.png")):
        print(f"ERROR: textures folder does not exist: {textures_folder}")
        return None

    png_files = list(textures_folder.glob("*.png"))

    srgb_pixels = ...
    return srgb_pixels

def texture_amount(json_path: str):
    json_file = open(json_path, "r", encoding="utf-8")
    json_data = json.loads(json_file.read())

    total_textures = len(json_data)
    print(total_textures)

def run_harmony_analysis(database_path: str, target_block_path: str) -> dict:
    """
    Loads the database, calculates all computational harmonies for a given block,
    and maps theoretical color coordinates back to real Minecraft block names.
    :return resolved_palettes: computational palette with block names
    """
    # Load the database file with object_hook
    with open(database_path, "r", encoding="utf-8") as json_file:
        database: dict[str, BlockData] = json.load(json_file, object_hook=block_database_decoder)

    block_name = Path(target_block_path).stem
    base_block = database[block_name]

    #closest_match = find_closest_mc_texture(base_block.oklch, database)
    # Calculates color harmonies for base color
    harmonies = {
        "complementary": color_harmonies.complementary(base_block.oklch.L, base_block.oklch.C, base_block.oklch.h),
        "monochromatic": color_harmonies.monochromatic(base_block.oklch.L, base_block.oklch.C, base_block.oklch.h),
        "analogous": color_harmonies.analogous(base_block.oklch.L, base_block.oklch.C, base_block.oklch.h),
        "triadic": color_harmonies.triadic(base_block.oklch.L, base_block.oklch.C, base_block.oklch.h)
    }

    resolved_palettes = {}
    # Converting to srgb color space every palette
    for harmony_name, harmony_coords in harmonies.items():
        # Keep all colors except base color
        harmony_coords_without_base = list(harmony_coords[1:])
        matched_blocks = []
        # print(f"----{harmony_name.capitalize()}----\n{harmony_coords_without_base}") # Print basic data for comparing with final results
        for harmony_coord in harmony_coords_without_base:
            closest_match = find_closest_mc_texture(target_oklch=Oklch(*harmony_coord), database=database)
            matched_blocks.append(closest_match)

        resolved_palettes[harmony_name] = matched_blocks
        # Change oklch values into srgb
        #harmonies[harmony_name] = tuple(harmony_coords_without_base)

    return resolved_palettes