import json
import shutil
import zipfile
from pathlib import Path

def load_filters(config_path:Path) -> list[str]:
    """Loads keyword exclusions from a JSON configuration file."""
    if not config_path.exists():
        print("Error: Config File Not Found")
        return []

    with open(config_path, "r", encoding="utf-8") as config_file:
        data = json.load(config_file)
        return data.get("excluded_keywords", [])

def clean_directory(folder_path:Path):
    """Deletes the entire folder and recreates it fresh."""
    if folder_path.exists():
        shutil.rmtree(folder_path)
        print(f"Cleared old textures from: {folder_path.absolute()}")

    folder_path.mkdir(parents=True, exist_ok=True)

def jar_2_textures(jar_path:Path, texture_dir:Path, config_path:Path) -> str | None:
    # Convert string paths to modern Path objects
    jar_file = Path(jar_path)
    texture_folder = Path(texture_dir) # e.g., ../textures/1.21.4, ../textures/1.20.1

    # Check if the .jar file exists
    if not jar_file.exists():
        print("Error: Jar File Not Found")
        return None

    # Clear out all old textures
    clean_directory(texture_folder)

    # Load filter keywords from json
    keywords = load_filters(Path(config_path))

    # Debug print
    # print(f"Opening {jar_file.name}...")
    extracted_count  = 0

    # Open .jar archive
    with zipfile.ZipFile(jar_file, 'r') as jar_archive:
        # Loop through every file path inside the .jar
        for file in jar_archive.namelist():
            # Filter only PNGs
            if file.startswith("assets/minecraft/textures/block/") and file.endswith(".png"):
                texture_name = Path(file).name # Extract the actual filename (e.g., "dirt.png") from the long path

                # Filter check
                if any(word in texture_name for word in keywords): continue

                save_folder = texture_folder / texture_name # Create the final save destination

                # Read binary bytes from the jar and write them to export folder
                with jar_archive.open(file) as texture_file:
                    with open(save_folder, "wb") as save_destination:
                        save_destination.write(texture_file.read())

                extracted_count += 1
    # Debug print
    # print(f"Successfully extracted {extracted_count} block textures to '{texture_folder.absolute()}'!")
    return jar_file.stem

def texture_finder(jar_path:str, key_word:str):
    """Find all textures with the given keyword."""
    jar_file = Path(jar_path)

    # Check if the .jar file exists
    if not jar_file.exists():
        raise FileNotFoundError("Error: Jar File Not Found")

    with zipfile.ZipFile(jar_file, 'r') as jar_archive:
        # Loop through every file path inside the .jar
        for file in jar_archive.namelist():
            # Filter only PNGs
            if file.startswith("assets/minecraft/textures/block/") and file.endswith(".png") and key_word in file:
                texture_name = Path(file).name # Extract the actual filename (e.g., "dirt.png") from the long path
                print(texture_name)