from pathlib import Path

from src.pipeline import analysis_textures, generate_harmonies_for_block
from src.visualization import render_harmony, render_texture_and_oklab_mean

def main():
    BASE_DIR = Path(__file__).resolve().parent
    CONFIG_PATH = BASE_DIR / "config/filters.json"

    textures_dir = BASE_DIR / "textures"
    output_dir = BASE_DIR / "output"

    MC_VERSION = "1.21.4"
    db_name = "block_color_palette2" # default: "block_color_palette"

    db_path = output_dir / f"{MC_VERSION}_{db_name}.json"
    target_block_name = textures_dir / "orange_glazed_terracotta.png"

    db = analysis_textures(MC_VERSION, textures_dir, db_path)

    target_block_mean = db.oklab_array(target_name=target_block_name.stem)

    render_texture_and_oklab_mean(base_block_path=target_block_name, oklab_mean=target_block_mean)

    harmony_palettes = generate_harmonies_for_block(target_block_name=target_block_name.stem, db=db, global_exclusion=False)

    for name, palette in harmony_palettes.items():
      print(f"----{name.capitalize()}----\n{palette}")

    render_harmony(base_block_path=target_block_name, texture_folder=textures_dir, harmony_palettes=harmony_palettes)

if __name__ == "__main__":
    main()
