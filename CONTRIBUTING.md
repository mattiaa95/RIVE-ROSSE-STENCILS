# Contributing

Thanks for helping improve the RIVE ROSSE stencil catalog. Issues, corrections
and new trail designs are welcome.

## Development setup

```bash
make install   # creates .venv and installs requirements.txt
make all       # regenerates every STL and PNG
make check     # validates the 120 STL files
```

You can also run the generators directly:

```bash
python3 script/generare_cartelli.py
python3 script/generare_catalogo.py
```

## Adding or changing a design

1. Edit the design list of the corresponding generator:

   | Catalog | File |
   |---|---|
   | Trail signs, 190 x 190 | `script/generare_cartelli.py` |
   | Technical signs, 190 x 190 | `script/generare_segnali.py` |
   | Arrows, help and levels | `script/generare_segnali_aiuto.py` |
   | Narrow signs, 190 x 80 | `script/generare_cartelli_stretti.py` |
   | Compact signs and Trails 2 | `script/generare_segnali_stretti.py`, `script/generare_trails_2.py` |

2. Keep names uppercase. Every character must exist in the included stencil
   font; the generator stops with a clear error if a glyph is missing.
3. Prefer short lines. Long names are scaled down to fit the margins, so they
   end up thinner.
4. Run the affected generator and `make check`.
5. Commit the script change together with the regenerated STL and PNG files.

## Design rules

- Plates are solid masks with cut-outs, not reliefs.
- Thickness is 0.5 mm, margins 7-8 mm, bridges 2.2-2.4 mm.
- Every mesh must be watertight, a single piece (two for double plates), and
  free of degenerate triangles.
- Do not change plate size, thickness or bridge width without re-tuning the
  bridge logic in `script/generare_stencil.py`.
- Do not add G-code. Slicing depends on the printer, nozzle and material; every
  user must slice the STL files with their own profile.

## Licensing of contributions

- Code, scripts and documentation: MIT License.
- Designs, STL files and preview images: CC BY-NC-SA 4.0.
- Do not submit third-party trademarks, logos or designs you cannot license.

## Pull request checklist

- [ ] `make check` passes.
- [ ] Regenerated STL and PNG files are included.
- [ ] README counts are updated if the number of designs changes.
- [ ] New designs do not use third-party trademarks.
