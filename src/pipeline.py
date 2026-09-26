from pathlib import Path

from . import color_spaces
from . import image_processing

from .models import Oklab, Oklch, ColorCluster, BlockData
from .database import BlockDatabase
from .palette_generator import PaletteGenerator, HarmonyPalette


def analysis_textures(version: str, textures_dir: Path, db_path: Path,
                      overwrite: bool = False,remove_texture: bool = False) -> BlockDatabase:
    """
    Get all textures, calculate clusters using kmeans++ for each one, save data to database.
    """
    db = BlockDatabase(db_path)
    if db.blocks and not overwrite:
        print(f"[+] The existing database has been loaded: {db_path.name}")
        return db

    png_files = list(textures_dir.glob("*.png"))
    total_files = len(png_files)
    result_data: dict[str, BlockData] = {}

    for idx, file_path in enumerate(png_files):
        try:
            srgb_pixels = image_processing.texture_2_srgb(file_path)
            # Skip or remove not full/transparent block textures
            if srgb_pixels.shape[0] < 256:
                if remove_texture:
                    remove_textures_from_folder(file_path=file_path)
                print(f"[!] {file_path} is skipped. Shape is {srgb_pixels.shape}, less than 256 pixels!")
                continue

            oklab_pixels = color_spaces.srgb_2_oklab(srgb_pixels)

            oklab_centroids, weights = image_processing.kmean_oklab(oklab_pixels=oklab_pixels)

            cluster_obj = []
            # Parallel iteration using 'zip' without indices
            for centroid, weight in zip(oklab_centroids, weights):
                # Cast to native `float` for safe JSON serialization
                c_L, c_a, c_b = float(centroid[0]), float(centroid[1]), float(centroid[2])

                c_oklch = color_spaces.oklab_2_oklch(c_L, c_a, c_b)
                c_hex = color_spaces.srgb_2_hex(color_spaces.oklab_2_srgb(centroid))

                cluster_obj.append(ColorCluster(
                    oklab=Oklab(c_L, c_a, c_b),
                    oklch=Oklch(*c_oklch),
                    hex=c_hex,
                    weight=float(weight),
                ))

            # Extract dominant color for simple harmonies
            dominant_id = image_processing.extract_dominant_cluster_index(weights=weights)
            dominant_cluster: ColorCluster = cluster_obj[dominant_id]

            result_data[file_path.stem] = BlockData(
                dominant_hex=dominant_cluster.hex,
                dominant_oklab=dominant_cluster.oklab,
                dominant_oklch=dominant_cluster.oklch,
                clusters=tuple(cluster_obj),
            )

            if idx % 25 == 0 or idx == total_files:
                progress = (idx / total_files) * 100
                print(f"Progress: [{idx}/{total_files}] ({progress:.1f}%) processed.")

        except Exception as e:
            print(f"[!] Failed to process {file_path.name}. Reason: {e}")

    db.save(version, result_data)
    return db

def generate_harmonies_for_block(target_block_name: str, db: BlockDatabase) -> HarmonyPalette:
    """
    Loads the database, calculates all computational harmonies for a given block,
    and maps theoretical color coordinates back to real Minecraft block names.
    :param target_block_name: anchor block texture name etc. "lapis_ore", "acacia_planks"
    :param db: Preloaded BlockDatabase instance
    """
    if target_block_name not in db.blocks:
        raise ValueError(f"[!] Block {target_block_name} not found in database!")

    base_block = db.blocks[target_block_name]
    base_oklch = base_block.dominant_oklch

    palettes = PaletteGenerator(database=db)
    harmonies = palettes.generate_harmonies(block_name=target_block_name, base_color=base_oklch)
    return harmonies

def remove_textures_from_folder(file_path: Path):
    try:
        file_path.unlink()
        # Debug print
        print(f"[*] The texture {file_path.name} has been removed!")
    except FileNotFoundError:
        print("[!] The file does not exist!")
