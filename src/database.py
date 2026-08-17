import json
from cmath import inf
from collections.abc import Container

import numpy as np
from pathlib import Path

from .models import BlockData, Oklab, Oklch
from .color_spaces import oklch_2_oklab


class BlockDatabase:
    """A repository for the Minecraft block color database"""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.version: str = ""
        self.blocks: dict[str, BlockData] = {}

        # Cache for Accelerating Vector Searches
        self._names_list: list[str] = []
        self._names_2_idx: dict[str, int] = {} # O(1) hashmap for string-to-index lookup
        self._matrix_oklab: np.ndarray | None = None

        if filepath.exists():
            self.load()

    def load(self) -> None:
        """Loads a database from JSON and creates NumPy matrices for O(1) lookups."""
        with open(self.filepath, "r", encoding="utf-8") as json_file:
            raw_data: dict = json.load(json_file)

        # Removes key 'minecraft' from .json database and return version value
        self.version = raw_data.pop("minecraft", "unknown")
        # Converts raw data to NamedTuple as BlockData
        self.blocks = {
            name: BlockData(
                hex=data["hex_color"],
                oklab=Oklab(*data["oklab"]),
                oklch=Oklch(*data["oklch"])
            )
            for name, data in raw_data.items()
        }
        # Debug print
        #print("Database loaded!")

        self._build_vector_cache()

    def save(self, version: str, blocks_data: dict[str, BlockData]) -> None:
        """Saves in JSON scheme"""
        self.version = version
        self.blocks = blocks_data

        payload = {"minecraft":version}
        for name, block in blocks_data.items():
            payload[name] = {
                "oklab": block.oklab,
                "oklch": block.oklch,
                "hex_color": block.hex
            }
        #
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        #
        with open(self.filepath, "w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, indent=4)

        self._build_vector_cache()

    def _build_vector_cache(self) -> None:
        """Creates an [N, 3] (3 = L, a, b) matrix of all Oklab vectors for instant search"""
        self._names_list = list(self.blocks.keys()) # e.g. 'acacia_log', 'diorite', 'lapis_ore'
        # Fast string lookup index mapping
        self._names_2_idx = {name: idx for idx, name in enumerate(self._names_list)}

        oklab_vectors = []
        for name in self._names_list:
            oklab_vectors.append(self.blocks[name].oklab)
        self._matrix_oklab = np.array(oklab_vectors, dtype=np.float32)

        # Debug print
        # print(f"Cache built! Amount of blocks: {len(self._names_list)}")

    def find_closest_mc_texture(self, target_oklch: Oklch, exclude_names: Container[str] | str | None = None) -> str:
        """
        Vector search for the nearest block based on the minimum Euclidean distance (ΔE) in Oklab.
        Supports O(1) exclusion filtering via internal index mapping
        """
        if self._matrix_oklab is None or len(self._names_list) == 0:
            raise ValueError("Database is empty!")

        target_vector_oklab = np.array(oklch_2_oklab(*target_oklch), dtype=np.float32)
        # Calculate all distances at once using vector math
        distances = np.linalg.norm(self._matrix_oklab - target_vector_oklab, axis=1)

        # Normalize single string input to tuple for unified set-like evaluation
        if isinstance(exclude_names, str):
            exclude_names = (exclude_names,)

        # Make distance inf for excluded block names
        # Vectorized infinity assignment using O(1) dict lookups
        if exclude_names:
            exclude_indices = [
                self._names_2_idx[name]
                for name in exclude_names
                if name in self._names_2_idx
            ]
            # Debug print
            # print(exclude_indices)
            if exclude_indices:
                distances[exclude_indices] = inf

        closest_idx = int(np.argmin(distances))
        return self._names_list[closest_idx]

    def oklab_array(self, target_name: str) -> np.ndarray:
        """Converts the Oklab vector to a numpy array"""
        if target_name not in self._names_list or len(self._names_list) == 0:
            return None

        return np.array(self.blocks[target_name].oklab)