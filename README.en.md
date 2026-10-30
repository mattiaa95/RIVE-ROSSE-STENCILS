# RIVE ROSSE STENCILS

**Language:** [Italiano](README.md) · [Español](README.es.md) · English

Parametric 3D stencils for marking the **RIVE ROSSE** trails: trail signs, technical signs, arrows, difficulty levels, help signs and 190 × 80 mm double plates.

The whole catalog is generated from Python using vector contours, validated as a closed mesh and exported to STL at real scale in millimetres.

<p align="center">
  <img src="png/catalogo_rive_rosse.png" alt="RIVE ROSSE complete catalog" width="560">
</p>

<p align="center">
  <strong>33 standard designs · 44 narrow plates · 43 double plates · 120 STL · 20 G-code</strong>
</p>

---

## Contents

- [What is included](#what-is-included)
- [Specifications](#specifications)
- [Catalog](#catalog)
- [Print-ready G-code](#print-ready-g-code)
- [Repository structure](#repository-structure)
- [Generate the STL files](#generate-the-stl-files)
- [Printing](#printing)
- [Scripts](#scripts)
- [Validation](#validation)
- [Fonts and credits](#fonts-and-credits)
- [License](#license)

---

## What is included

| Family | Format | Designs | STL |
|---|---:|---:|---:|
| Trail and special signs | 190 × 190 × 0.5 mm | 17 | 17 |
| Technical signs, arrows, help and levels | 190 × 190 × 0.5 mm | 16 | 16 |
| Narrow signs | 190 × 80 × 0.5 mm | 11 + 1 special arrow | 12 |
| Double plates for narrow signs | 190 × 164 × 0.5 mm | 11 | 11 |
| Compact signs | 190 × 80 × 0.5 mm | 16 | 16 |
| Double plates for compact signs | 190 × 164 × 0.5 mm | 16 | 16 |
| Trails 2 | 190 × 80 × 0.5 mm | 16 | 16 |
| Double plates for Trails 2 | 190 × 164 × 0.5 mm | 16 | 16 |
| **Total** | | | **120** |

Also included:

- **20 G-code files** pre-sliced in `gcode/`, with compact names such as `miniVariantSassEZT`.
- **29 PNG files** for catalogs and previews in `png/`.
- Reproducible scripts in `script/`.
- Stencil fonts in `font/`.

---

## Specifications

- **Units:** real millimetres.
- **Thickness:** 0.5 mm.
- **Standard format:** 190 × 190 mm.
- **Narrow format:** 190 × 80 mm.
- **Double plate:** 190 × 164 mm, with a 4 mm gap between plates.
- **Margins:** 7–8 mm.
- **Bridges:** built into the design, 2.2–2.4 mm.
- **Mesh:** closed, single piece, no degenerate triangles.
- **Text:** vectorized from TTF; no font dependency in the slicer.
- **Previews:** `spray` mode (orange on beige) and `stencil` mode (white on black).

> Each STL is a **solid plate with the stencil cut-outs**, not a relief. The plate sits on the ground and is used as a spray mask.

---

## Catalog

### Complete 190 × 190 mm catalog

| Spray | Stencil |
|---|---|
| <img src="png/catalogo_rive_rosse.png" width="420"> | <img src="png/catalogo_rive_rosse_stencil.png" width="420"> |

### Narrow signs 190 × 80 mm

| Spray | Stencil |
|---|---|
| <img src="png/cartelli_stretti/catalogo_cartelli_stretti_spray.png" width="420"> | <img src="png/cartelli_stretti/catalogo_cartelli_stretti_stencil.png" width="420"> |

### Compact signs 190 × 80 mm

| Spray | Stencil |
|---|---|
| <img src="png/segnali_stretti/catalogo_segnali_stretti_spray.png" width="420"> | <img src="png/segnali_stretti/catalogo_segnali_stretti_stencil.png" width="420"> |

### Trails 2

| Spray | Stencil |
|---|---|
| <img src="png/trails_2/catalogo_trails_2_spray.png" width="420"> | <img src="png/trails_2/catalogo_trails_2_stencil.png" width="420"> |

### Double plates

| Signs | Signals | Trails 2 |
|---|---|---|
| <img src="png/cartelli_stretti/piastra_doppia_spray.png" width="260"> | <img src="png/segnali_stretti/piastra_doppia_segnali_spray.png" width="260"> | <img src="png/trails_2/piastra_doppia_trails_2_spray.png" width="260"> |

---

## Print-ready G-code

The `gcode/` folder contains **20 pre-sliced files** made with Cura 5.2.2. Names follow the compact scheme:

```text
mini + normalized CamelCase name + .gcode
```

Example: `miniVariantSassEZT.gcode`.

<details>
<summary>Show the 20 G-code files</summary>

```text
miniCPMDS.gcode
miniCiaoCoolma.gcode
miniDropIndietro.gcode
miniErnestoFactor.gcode
miniFlamingoRocco.gcode
miniFrecciaDritto.gcode
miniFrecciaMTB.gcode
miniGaleottoCapri.gcode
miniGhiandaMagma.gcode
miniLivello1e2.gcode
miniLivello3e4.gcode
miniM33TdP.gcode
miniM41eBis.gcode
miniMoiaCaracse.gcode
miniNYPinolo.gcode
miniPignVerg.gcode
miniPisacravaSpeedy.gcode
miniRipidoSalto.gcode
miniTASV.gcode
miniVariantSassEZT.gcode
```

</details>

The `script/renombrar_gcode.py` script contains the full mapping and can revert the rename:

```bash
python3 script/renombrar_gcode.py --dry-run
python3 script/renombrar_gcode.py
python3 script/renombrar_gcode.py --revert
```

> The G-code files are prepared for the printer they were generated on. If you change machine, nozzle or material, regenerate them from the STL files.

---

## Repository structure

```text
RIVE_ROSSE_STENCILS/
├── font/                     Included stencil fonts
├── gcode/                    20 pre-sliced G-code files
├── png/                      Catalogs and previews
│   ├── cartelli/             17 signs, 190 × 190
│   ├── cartelli_stretti/     Narrow signs
│   ├── segnali/              190 × 190 signals
│   ├── segnali_stretti/      Compact signals
│   └── trails_2/             Trails 2
├── script/                   Generators and utilities
├── stl/                      Slicer-ready meshes
│   ├── cartelli/             17 signs, 190 × 190
│   ├── cartelli_stretti/     11 singles + 11 doubles + 1 arrow
│   ├── segnali/              16 signals, 190 × 190
│   ├── segnali_stretti/      16 singles + 16 doubles
│   └── trails_2/             16 singles + 16 doubles
├── README.md                 Italiano
├── README.es.md              Español
├── README.en.md              English
└── requirements.txt
```

---

## Generate the STL files

### Requirements

- Python 3.10 or newer.
- `pip`.
- macOS, Linux or Windows.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Generate the standard 190 × 190 catalog

```bash
python3 script/generare_cartelli.py
python3 script/generare_segnali.py
python3 script/generare_segnali_aiuto.py
python3 script/generare_catalogo.py
```

### Generate the narrow 190 × 80 catalog

```bash
python3 script/generare_cartelli_stretti.py
python3 script/generare_segnali_stretti.py
python3 script/generare_trails_2.py
```

The scripts write directly to `stl/` and `png/`, create missing folders and validate every file before finishing.

`script/generare_stencil.py` is the base module: it loads the font, converts text to polygons, performs boolean operations, adds bridges and validates the meshes. You do not need to run it to generate the current catalog.

---

## Printing

Reference settings for 0.5 mm plates:

| Setting | Value |
|---|---|
| Scale | 100% |
| Layer height | 0.20 mm |
| Solid top/bottom layers | 3 |
| Perimeters | 2–3 |
| Infill | 100% or solid equivalent |
| Supports | No |
| Material | PLA / PETG |
| Orientation | Flat, with the stencil face up |

Recommendations:

- Check the first layer: the plate is thin and needs good adhesion.
- Do not scale the STL in the slicer unless you want to change the real size.
- Make sure the internal bridges remain open after slicing.
- For ground painting, use low-pressure spray and remove the mask carefully.

---

## Scripts

| Script | Purpose |
|---|---|
| `generare_stencil.py` | Shared engine: fonts, polygons, boolean operations, bridges, extrusion and validation. |
| `generare_segnali.py` | 190 × 190 technical signs: DROP, SALTO, RIPIDO. |
| `generare_segnali_aiuto.py` | Arrows, help signs, levels and orientation signs. |
| `generare_cartelli.py` | Trail signs and special signs, 190 × 190. |
| `generare_catalogo.py` | Complete PNG catalog and sign catalog. |
| `generare_cartelli_stretti.py` | Narrow signs, double plates and MTB arrow. |
| `generare_segnali_stretti.py` | Compact 190 × 80 signs and their double plates. |
| `generare_trails_2.py` | The 16 Trails 2 signs. |
| `renombrar_gcode.py` | Compact and reversible G-code renaming. |

---

## Validation

Every STL is checked automatically before export:

- exact dimensions in millimetres;
- closed and correctly oriented mesh;
- single piece;
- no degenerate triangles;
- open area consistent with the design;
- bridges and spacing between elements.

PNG catalogs are generated from the same geometry as the STL files, so the preview and the printed part share the same contours.

---

## Fonts and credits

- **Saira Stencil One** — main font included in `font/SairaStencilOne-Regular.ttf`.
- **Allerta Stencil** — alternative included in `font/AllertaStencil-Regular.ttf`.
- Geometry and generation: Python + `fonttools`, `shapely`, `trimesh`, `manifold3d`, `numpy` and `matplotlib`.
- Trail designs and names: **RIVE ROSSE**.

The fonts are distributed under the **SIL Open Font License 1.1**. Check the original license for each family before redistributing them separately.

---

## License

Private project. RIVE ROSSE designs, names and trademarks belong to their respective authors. No permission is granted for commercial use or public redistribution without authorization.
