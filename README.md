# ⛏️ Minecraft Color Wheel

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Color Space: Oklab/Oklch](https://img.shields.io/badge/Color%20Space-Oklab%2F%20Oklch-FF69B4.svg?style=flat-square)](https://bottosson.github.io/posts/oklab/)
[![Architecture: Clean Code](https://img.shields.io/badge/Architecture-Clean%20%2F%20Modular-00599C.svg?style=flat-square)](#-architecture--module-structure)


> **Minecraft Color Wheel** is a color analysis system for Minecraft textures
> using Oklab/Oklch spaces to extract perceptual color information,
> and uses color relationships to generate harmonious Minecraft block palettes.


## 📌 Current functionality
- *Asset Extraction Engine*
- *Perceptual Color Processing (Oklab space)*
- *Data Serialization*
- *Harmony Engine (OkLch Rules)*

## 📝 Planned functionality
- **The 60-30-10 Rule Palette Analyzer**
- **K-Means Clustering**

---

## 🎯 Technical Highlights

- **Direct Archive Streaming (`src/extractor.py`)**: Reads and filters block PNG textures
                                                    directly from Minecraft `.jar` archives without extracting unnecessary game assets.
- **Perceptual Color Science (`src/color_spaces.py`)**: Full sRGB gamma decoding
    $\to$ CIE XYZ (D65) $\to$ LMS Cone Response $\to$ Non-linear cube-root compression $\to$ Oklab ($L, a, b$) $\to$ Oklch ($L, C, h$).
- **Alpha-Aware Pixel Filtering (`src/image_processing.py`)**: Handles transparency gracefully by ignoring empty/alpha channels
                                                              to calculate unbiased block surface averages.
- **Vectorized Nearest-Neighbor Search (`src/database.py`)**: Utilizes NumPy matrix operations to compute Euclidean distances
                                                              ($\Delta E$) in Oklab space across hundreds of block textures in milliseconds.
- **Color Harmony Resolver (`src/color_harmonies.py`)**: Calculates exact geometric color relationships in 3D polar Oklch space 
                                                          and maps theoretical target coordinates back to existing Minecraft blocks.
- **Optimized Rendering Engine (`src/visualization.py`)**: Custom Matplotlib GridSpec layout with $O(1)$ texture hash-map lookups, 
                                                       completely eliminating disk traversal overhead during visualization.

---

## 📐 Mathematical Framework: Why Oklab / Oklch?

Standard RGB and HSV color spaces are not perceptually uniform — for instance, pure yellow appears significantly brighter to human eyes than pure blue at equal nominal value coordinates. **Oklab** (developed by Björn Ottosson) solves this by ensuring that Euclidean distance in color space corresponds directly to perceived visual distance:

$$\Delta E = \sqrt{(L_1 - L_2)^2 + (a_1 - a_2)^2 + (b_1 - b_2)^2}$$

### Conversion Pipeline

1. **sRGB Linearization (Gamma Decoding)**:
```math
   $$C_{\text{linear}} = \begin{cases} \frac{C_{\text{srgb}}}{12.92}, & C_{\text{srgb}} \le 0.04045 \\ \left(\frac{C_{\text{srgb}} + 0.055}{1.055}\right)^{2.4}, & C_{\text{srgb}} > 0.04045 \end{cases}$$
```
2. **Linear RGB to LMS Cone Stimulation Space**:
```math
   $$\begin{bmatrix} L \\ M \\ S \end{bmatrix} = M_1 \cdot M_{\text{sRGB}\to\text{XYZ}} \cdot \begin{bmatrix} R_{\text{linear}} \\ G_{\text{linear}} \\ B_{\text{linear}} \end{bmatrix}$$
```
3. **Cube-Root Non-Linearity & Oklab Projection**:
```math 
   $$L' = \sqrt[3]{L}, \quad M' = \sqrt[3]{M}, \quad S' = \sqrt[3]{S}$$
   $$\begin{bmatrix} L_{\text{oklab}} \\ a_{\text{oklab}} \\ b_{\text{oklab}} \end{bmatrix} = M_2 \cdot \begin{bmatrix} L' \\ M' \\ S' \end{bmatrix}$$
```
4. **Polar Transformation to Oklch**:
   $$C = \sqrt{a^2 + b^2}, \quad h = \text{atan2}(b, a) \pmod{360^\circ}$$

---

## 🏗️ Architecture Structure

```
minecraft-color-wheel/
├── config/
│   └── filters.json                    # Configurable keyword filter rules
├── output/
│   └── 1.2*_block_color_palette.json   # Exported perceptual color database
├── src/
│   ├── __init__.py
│   ├── models.py                       # Immutable NamedTuple domain models (Oklab, Oklch, BlockData)
│   ├── color_spaces.py                 # Transformation matrices & bidirectional color conversions
│   ├── image_processing.py             # Alpha masking, sRGB flattening, perceptual mean calculations
│   ├── color_harmonies.py              # Geometric palette algorithms (Monochromatic, Triadic, etc.)
│   ├── database.py                     # Vector cache repository & nearest-neighbor search engine
│   ├── extractor.py                    # ZIP archive stream reader & file filtering
│   ├── pipeline.py                     # End-to-end processing & palette resolution orchestrator
│   └── visualization.py                # Matplotlib GridSpec rendering engine
├── textures/
│   ├── amethyst_block.png              # Test textures 
│   ├── birch_planks.png
│   ├── black_glazed_terracotta.png
│   ├── crying_obsidian.png
│   ***
│   ├── stripped_dark_oak_log.png
│   └── stone_bricks.png
├── main.py                             # Application execution entry point
├── requirements.txt                    # Project dependencies
└── README.md                           # Technical documentation
```

### System Data Flow

```
+------------------+      +----------------+      +--------------------+
| 1.2*.jar Archive | -->  |  extractor.py  | -->  |  Raw PNG Textures  |
+------------------+      +----------------+      +--------------------+
                                                            |
                                                            v
+-----------------+     +------------------+     +---------------------+
| Block Database  | <-- | color_spaces.py  | <-- | image_processing.py |
| Cache (.json)   |     | (Oklab / Oklch)  |     | (Alpha Filter)      |
+-----------------+     +------------------+     +---------------------+
         |
         v
+------------------+     +------------------+     +--------------------+
| Target Block     | --> | color_harmonies  | --> | Matched MC Blocks  |
| Selection        |     | (Geometric Calc) |     | & Visualization    |
+------------------+     +------------------+     +--------------------+
```

---

## 🛠️ Code Conventions & Design Principles

- **Clean Architecture & SOLID**: Strict separation of concerns — IO operations (`extractor.py`), mathematical transformations (`color_spaces.py`), domain entities (`models.py`), and UI presentation (`visualization.py`) are decoupled.
- **Type Safety**: Pervasive Python type annotations (`Path`, `np.ndarray`, `Oklch`, `Oklab`).
- **Immutability**: Domain models built using `NamedTuple` to prevent state mutation side effects.

---

## 📄 License

Distributed under the [MIT License](LICENSE).