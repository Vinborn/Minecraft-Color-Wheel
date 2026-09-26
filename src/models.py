from typing import NamedTuple

# immutable domain models
class Oklab(NamedTuple):
    """Color representation in the Oklab space."""
    L: float    # Brightness (0.0 – 1.0)
    a: float    # Green (-) / Red (+)
    b: float    # Blue (-) / Yellow (+)

class Oklch(NamedTuple):
    """Color representation in the Oklch space."""
    L: float    # Brightness (0.0–1.0)
    C: float    # Saturation / Chroma (0.0 - ~0.37)
    h: float    # Hue (0.0 – 360.0°)

class ColorCluster(NamedTuple):
    """A data about the color cluster of Minecraft texture."""
    oklab: Oklab
    oklch: Oklch
    hex: str        # Useful for render palettes
    weight: float   # Coverage percentage (from 0.0 to 1.0)

class BlockData(NamedTuple):
    """A data structure containing information about the color of a Minecraft block."""
    # Saving dominant color for simple harmonies
    dominant_hex: str
    dominant_oklab: Oklab
    dominant_oklch: Oklch

    # K-mean++ data
    clusters: tuple[ColorCluster, ...]
