import json
from cmath import inf
from collections.abc import Container

import numpy as np
from pathlib import Path

from .models import BlockData, Oklab, Oklch, ColorCluster
from .color_spaces import oklch_2_oklab


class BlockDatabase:
    """A repository for the Minecraft block color database"""

    def __init__(self, filepath: Path, k_clusters: int = 3):
        self.filepath = filepath
        self.version: str = ""
        self.blocks: dict[str, BlockData] = {}

        # Cache for Accelerating Vector Searches
        self._names_list: list[str] = []
        self._matrix_oklab: np.ndarray | None = None

        # Math mapping
        self.k_clusters: int = k_clusters

        if filepath.exists():
            self.load()

    def load(self) -> None:
        """Loads a database from JSON and creates NumPy matrices for O(1) lookups."""
        with open(self.filepath, "r", encoding="utf-8") as json_file:
            raw_data: dict = json.load(json_file)

        # Removes key 'minecraft' from .json database and return version value
        self.version = raw_data.pop("minecraft", "unknown")
        # Converts raw data to NamedTuple as BlockData
        for name, data in raw_data.items():
            # Unpack the cluster array back into strict domain models
            parsed_clusters = tuple(
                ColorCluster(
                    oklab=Oklab(*cluster["oklab"]),
                    oklch=Oklch(*cluster["oklch"]),
                    hex=cluster["hex"],
                    weight=cluster["weight"]
                ) for cluster in data["clusters"]
            )

            self.blocks[name] = BlockData(
                dominant_oklab=Oklab(*data["dominant_oklab"]),
                dominant_oklch=Oklch(*data["dominant_oklch"]),
                dominant_hex=data["dominant_hex"],
                clusters=parsed_clusters
            )

        self._build_vector_cache()

    def save(self, version: str, blocks_data: dict[str, BlockData]) -> None:
        """Saves models into JSON scheme"""
        if not blocks_data:
            print("[!] Blocks data is empty!")
            return
        self.version = version
        self.blocks = blocks_data

        payload = {"minecraft":version}
        for name, block in blocks_data.items():
            payload[name] = {
                "dominant_oklab": block.dominant_oklab,
                "dominant_oklch": block.dominant_oklch,
                "dominant_hex": block.dominant_hex,
                # _asdict() automatically converts NamedTuple into dictionary with keys
                "clusters": [cluster._asdict() for cluster in block.clusters]
            }

        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, indent=4)

        print(f"[✓] Database has been successfully saved: {self.filepath}")
        self._build_vector_cache()

    def _build_vector_cache(self) -> None:
        """
        Creates an [N * K, 3] (3 = L, a, b) matrix of all Oklab vectors for instant search.
        Uses pure math (index // K) for block identification instead of hash map
        """
        self._names_list = list(self.blocks.keys()) # e.g. 'acacia_log', 'diorite', 'lapis_ore'
        n_blocks = len(self._names_list)

        # Pre-allocate contiguous memory block for max performance
        self._matrix_oklab = np.zeros((n_blocks * self.k_clusters, 3), dtype=np.float32)

        for block_idx, name in enumerate(self._names_list):
            block = self.blocks[name]

            # Checks that there are exactly K clusters
            if len(block.clusters) != self.k_clusters:
                raise ValueError(f"Block {name} has {len(block.clusters)} clusters,"
                                 f" but database is waiting for {self.k_clusters}!")

            for cluster_idx, cluster in enumerate(block.clusters):
                # Inversed formula from index // K
                flat_idx = block_idx * self.k_clusters + cluster_idx
                self._matrix_oklab[flat_idx] = cluster.oklab

    def find_closest_mc_texture(self, target_oklch: Oklch, exclude_names: Container[str] | str | None = None) -> str:
        """
        Vector search for the nearest block based on the minimum Euclidean distance (ΔE) in Oklab.
        Returns the block name that contains the matched cluster.
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
        if exclude_names and exclude_names in self._names_list:
            block_idx = self._names_list.index(exclude_names)
            # Calculating slice in flatten matrix [N*K]
            start_idx = block_idx * self.k_clusters
            end_idx = start_idx + self.k_clusters
            distances[start_idx:end_idx] = inf

        # Find index of min distance in flatten array [N * K]
        closest_flat_idx = int(np.argmin(distances))

        # Restoring index via math
        closest_block_idx = closest_flat_idx // self.k_clusters

        return self._names_list[closest_block_idx]

    def texture_index(self, target_name: str) -> int:
        """Return the index of the texture corresponding to target_name"""
        if target_name not in self._names_list or len(self._names_list) == 0:
            return None

        return self._names_list.index(target_name)
