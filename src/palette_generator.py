from typing import NamedTuple
from .models import Oklch
from .database import BlockDatabase
from . import color_harmonies


class HarmonyPalette(NamedTuple):
    """Immutable structure representing generated block harmonies."""
    base_block: str
    complementary: tuple[str, ...]
    monochromatic: tuple[str, ...]
    analogous: tuple[str, ...]
    triadic: tuple[str, ...]


class PaletteGenerator:
    """Calculates Oklch harmonies for a given block and maps them to nearest textures."""

    def __init__(self, database: BlockDatabase) -> None:
        self.db = database

    def _map_color_2_block(self, target_color: Oklch, exclude: set[str]) -> tuple[str, ...]:
        block_name = self.db.find_closest_mc_texture(target_oklch=target_color, exclude_names=exclude)
        exclude.add(block_name)
        return block_name

    def generate_harmonies(self, block_name: str, base_color: Oklch) -> HarmonyPalette:
        """Generates harmonies for a block, ensuring there are no duplicates within a single palette."""
        complementary = color_harmonies.complementary(base_color)
        monochromatic = color_harmonies.monochromatic(base_color)
        analogous = color_harmonies.analogous(base_color)
        triadic = color_harmonies.triadic(base_color)

        return HarmonyPalette(
            base_block=block_name,
            complementary=self._map_color_2_block(complementary, block_name),
            monochromatic=self._map_color_2_block(monochromatic, block_name),
            analogous=self._map_color_2_block(analogous, block_name),
            triadic=self._map_color_2_block(triadic, block_name),
        )
