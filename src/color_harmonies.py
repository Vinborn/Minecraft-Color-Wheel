# TODO: make some experimentation on modifying values for more accurate results, using Canva.color_wheel.com as ref
from .models import Oklch

def monochromatic(base: Oklch, delta_L:float = 0.19) -> tuple[Oklch, Oklch, Oklch]:
    """
    Generates Oklch monochromatic palette: (Base, Shade, Tint)
    """
    shade = Oklch(max(base.L - delta_L, 0.05), base.C * 0.85, base.h)
    tint = Oklch(min(base.L + delta_L, 0.95), base.C * 0.85, base.h)
    return base, shade, tint

def complementary(base: Oklch) -> tuple[Oklch, Oklch]:
    """
    Generates Oklch complementary palette: (Base, Complementary)
    """
    complement = Oklch(base.L, base.C, (base.h + 180.0) % 360.0)
    return base, complement

def analogous(base: Oklch, angle: float = 30.0) -> tuple[tuple, tuple, tuple]:
    """
    Generates Oklch analogous palette: (Base, Analog1, Analog2)
    """
    analog_1 = Oklch(base.L, base.C, (base.h + angle) % 360.0)
    analog_2 = Oklch(base.L, base.C, (base.h - angle) % 360.0)
    return base, analog_1, analog_2


def triadic(base: Oklch) -> tuple[tuple, tuple, tuple]:
    """
    Generates Oklch triadic palette: (Base, Triad1, Triad2)
    """
    triad_1 = Oklch(base.L, base.C, (base.h + 120.0) % 360.0)
    triad_2 = Oklch(base.L, base.C, (base.h + 240.0) % 360.0)
    return base, triad_1, triad_2