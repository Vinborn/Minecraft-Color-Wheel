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

class BlockData(NamedTuple):
    """A data structure containing information about the color of a Minecraft block."""
    hex: str
    oklab: Oklab
    oklch: Oklch