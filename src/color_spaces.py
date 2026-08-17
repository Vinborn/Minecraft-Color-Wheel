import numpy as np

"""
More information: https://bottosson.github.io/posts/oklab/
"""
# OkLab matrices
# Matrix M1 maps light coordinates to human retinal cone stimulation
M1 = np.array(
    [
        [0.8189330101, 0.3618667424, -0.1288597137],
        [0.0329845436, 0.9293118715, 0.0361456387],
        [0.0482003018, 0.2643662691, 0.6338517070],
    ],
    dtype=np.float32,
)
# Matrix M2 isolates lightness from the red/green and yellow/blue nerve paths
M2 = np.array([
    [0.2104542553, 0.7936177850, -0.0040720468],
    [1.9779984951, -2.4285922050, 0.4505937099],
    [0.0259040371, 0.7827717662, -0.8086757660],
], dtype=np.float32)

# Inverse matrices for backward conversion
M1_inv = np.array([
    [ 4.0767416621, -3.3077115913,  0.2309699292],
    [-1.2684380046,  2.6097574011, -0.3413193965],
    [-0.0041960863, -0.7034186147,  1.7076147010]
], dtype=np.float32)

M2_inv = np.array([
    [1.0,  0.3963377774,  0.2158017574],
    [1.0, -0.1055613458, -0.0638541728],
    [1.0, -0.0894841775, -1.2914855480]
], dtype=np.float32)

# Matrix sRGB (D65) -> XYZ
SRGB_TO_XYZ = np.array([
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041]
], dtype=np.float32)

def srgb_2_hex(srgb_value: np.ndarray | list[int]) -> str:
    """Converts RGB (0–255) to a HEX string"""
    r = srgb_value[0]
    g = srgb_value[1]
    b = srgb_value[2]
    return f"#{r:02x}{g:02x}{b:02x}"

def srgb_2_oklab(srgb_input: np.ndarray) -> np.ndarray:
    """
    Converts an [N, 3] array of sRGB pixels to Oklab [N, 3].
    Performs gamma decoding without using skimage.
    """
    # Standardize input to a floating-point NumPy array
    srgb_norm = np.array(srgb_input, dtype=np.float32)
    if np.any(srgb_norm > 1.0): srgb_norm /= 255.0

    # Gamma linearization sRGB
    linear = np.where(
        srgb_norm <= 0.04045,
        srgb_norm / 12.92,
        ((srgb_norm + 0.055) / 1.055) ** 2.4
    )

    # OkLAB convert process: XYZ -> LMS -> Compression -> Oklab
    # Convert sRGB to CIE XYZ space (D65 white point reference)
    xyz = linear @ SRGB_TO_XYZ.T

    # Transform XYZ to LMS (Large, Medium, Small) Cone Response Space
    # Perform matrix multiplication across the last axis
    lms = xyz @ M1.T

    # Apply cube root compression
    # Using np.cbrt handles negative values safely if any out-of-gamut data occurs
    lms_compressed = np.cbrt(lms)

    # Transform compressed LMS space to final Lab channels
    oklab = lms_compressed @ M2.T
    return oklab

def oklab_2_srgb(oklab_input: np.ndarray | tuple | list, is_float:bool = False) -> np.ndarray:
    """
    Converts OkLab values to the sRGB color space.
    """
    oklab_arr = np.array(oklab_input, dtype=np.float32)

    # Oklab back to LMS
    lms_compressed = oklab_arr @ M2_inv.T

    # Undo compression (Cube it)
    lms = lms_compressed ** 3

    # LMS back to Linear RGB
    linear = lms @ M1_inv.T

    # Re-apply Gamma Curve (Gamma encoding)
    srgb_gamma = np.where(linear <= 0.0031308, linear * 12.92, 1.055 * (linear ** (1.0/2.4)) - 0.055)

    # Clip out-of-gamut values safely to 0-1
    srgb_float = np.clip(srgb_gamma, 0, 1).astype(np.float32)

    if not is_float:
        # then scale to 0-255
        return (srgb_float * 255.0).round().astype(np.uint8)
    return srgb_float

def oklab_2_oklch(L: float, a:float, b:float) -> tuple[float, float, float]:
    """
    Converts OkLab values to the OkLCh values.
    :return: coordinates in (L, C, h) where:
      - L: Perceptual Lightness (0.0 to 1.0)
      - C: Saturation / Chroma (0.0 to 1.0)
      - h: Hue (0 to 360)
    """
    # Calculate Chroma (distance from center)
    C = float(np.sqrt(a**2 + b**2))
    h = float(np.degrees(np.arctan2(b, a))) % 360

    return float(L), C, h

def oklch_2_oklab(L: float, C:float, h:float) ->  tuple[float, float, float]:
    """
    Converts OkLCh values to the OkLab values.
    """
    h_radian = np.radians(h)
    # Reconstruct grid coordinates
    a = float(C * np.cos(h_radian))
    b = float(C * np.sin(h_radian))
    return float(L), a, b