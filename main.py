from pathlib import Path

from src.pipeline import analysis_textures, generate_harmonies_for_block, clustering
from src.visualization import render_texture_and_oklab_mean, render_harmony, render_clusters

def main():
    BASE_DIR = Path(__file__).resolve().parent
    CONFIG_PATH = BASE_DIR / "config/filters.json"

    textures_dir = BASE_DIR / "textures"
    output_dir = BASE_DIR / "output"

    MC_VERSION = "1.21.4"
    db_name = "block_color_palette_top"  # default: "block_color_palette"

    db_path = output_dir / f"{MC_VERSION}_{db_name}.json"
    target_block_name = textures_dir / "black_glazed_terracotta.png"

    db = analysis_textures(version=MC_VERSION, textures_dir=textures_dir, db_path=db_path, overwrite=False,
                           remove_texture=False)

    target_block_mean = db.oklab_array(target_name=target_block_name.stem)

    render_texture_and_oklab_mean(base_block_path=target_block_name, oklab_mean=target_block_mean)

    cluster_dict: dict[int, tuple[list, list]] = clustering(target_block_name=target_block_name.stem,
                                                            textures_dir=textures_dir, db=db)

    for seed, cluster_data in cluster_dict.items():
        render_clusters(seed=seed, clusters=cluster_data[0])

    # harmony_palettes = generate_harmonies_for_block(target_block_name=target_block_name.stem, db=db, global_exclusion=True)
    #
    # for name, palette in harmony_palettes.items():
    #   print(f"----{name.capitalize()}----\n{palette}")
    #
    # render_harmony(base_block_path=target_block_name, texture_folder=textures_dir, harmony_palettes=harmony_palettes)

if __name__ == "__main__":
    main()
