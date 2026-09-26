from pathlib import Path

from src.pipeline import analysis_textures, generate_harmonies_for_block
from src.visualization import render_texture_and_oklab_mean, render_harmony

def main():
    BASE_DIR = Path(__file__).resolve().parent
    CONFIG_PATH = BASE_DIR / "config/filters.json"

    textures_dir = BASE_DIR / "textures"
    textures_side = BASE_DIR / "textures_side"
    output_dir = BASE_DIR / "output"

    MC_VERSION = "1.21.4"
    db_name = "block_color_palette_side"  # default: "block_color_palette"

    db_path = output_dir / f"{MC_VERSION}_{db_name}.json"
    target_block_name = textures_side / "amethyst_block.png"

    db = analysis_textures(version=MC_VERSION, textures_dir=textures_side, db_path=db_path, overwrite=False,
                           remove_texture=False)

    harmony_palettes = generate_harmonies_for_block(target_block_name=target_block_name.stem, db=db)

    for palette in harmony_palettes:
        print(f"{palette}")

if __name__ == "__main__":
    main()
