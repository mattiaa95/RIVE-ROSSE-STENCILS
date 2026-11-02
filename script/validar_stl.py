#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida las mallas STL del catalogo antes de publicar o imprimir.

Comprueba, para cada familia:
    - numero de archivos esperado;
    - dimensiones exactas en milimetros;
    - malla estanca, orientada y con volumen positivo;
    - una pieza (o dos en las placas dobles);
    - ausencia de triangulos degenerados;
    - extrusion entre z=0 y z=0,5 mm.

Uso:
    python3 script/validar_stl.py
    python3 script/validar_stl.py --verbose
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import trimesh

RAIZ = Path(__file__).resolve().parent.parent
STL = RAIZ / "stl"

GROSOR = 0.5
TOLERANCIA = 1.0e-3
AREA_MINIMA = 1.0e-10

FAMILIAS: Dict[str, Tuple[Tuple[float, float, float], int, int]] = {
    "cartelli": ((190.0, 190.0, GROSOR), 1, 17),
    "segnali": ((190.0, 190.0, GROSOR), 1, 16),
    "cartelli_stretti/singoli": ((190.0, 80.0, GROSOR), 1, 11),
    "cartelli_stretti/speciali": ((190.0, 80.0, GROSOR), 1, 1),
    "cartelli_stretti/doppi": ((190.0, 164.0, GROSOR), 2, 11),
    "segnali_stretti/singoli": ((190.0, 80.0, GROSOR), 1, 16),
    "segnali_stretti/doppi": ((190.0, 164.0, GROSOR), 2, 16),
    "trails_2/singoli": ((190.0, 80.0, GROSOR), 1, 16),
    "trails_2/doppi": ((190.0, 164.0, GROSOR), 2, 16),
}


def _familia_de(ruta: Path) -> str:
    partes = ruta.relative_to(STL).parts
    if len(partes) >= 3 and partes[1] in ("singoli", "doppi", "speciali"):
        return f"{partes[0]}/{partes[1]}"
    return partes[0]


def _validar_malla(ruta: Path, esperado: Tuple[float, float, float],
                   piezas: int) -> List[str]:
    errores: List[str] = []
    try:
        malla = trimesh.load(str(ruta), force="mesh")
    except Exception as exc:
        return [f"no se puede leer: {exc}"]

    if len(malla.faces) == 0 or len(malla.vertices) == 0:
        return ["malla vacia"]
    if not np.allclose(malla.extents, esperado, atol=TOLERANCIA, rtol=0.0):
        errores.append(
            "dimensiones "
            f"{malla.extents[0]:.3f} x {malla.extents[1]:.3f} x "
            f"{malla.extents[2]:.3f} mm, esperado "
            f"{esperado[0]:.1f} x {esperado[1]:.1f} x {esperado[2]:.1f}"
        )
    if not malla.is_watertight:
        errores.append("malla no estanca")
    if not malla.is_winding_consistent:
        errores.append("normales incoherentes")
    if malla.volume <= 0:
        errores.append("volumen no positivo")
    if np.any(malla.area_faces <= AREA_MINIMA):
        errores.append("triangulos degenerados")

    partes = malla.split(only_watertight=False)
    if len(partes) != piezas:
        errores.append(f"{len(partes)} piezas, esperado {piezas}")
    for indice, parte in enumerate(partes, start=1):
        if not parte.is_watertight or parte.volume <= 0:
            errores.append(f"pieza {indice} no valida")

    if malla.bounds[0][2] < -1.0e-6 or malla.bounds[1][2] > GROSOR + 1.0e-6:
        errores.append("la extrusion no esta entre z=0 y z=GROSOR")

    return errores


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true",
                        help="muestra tambien los archivos correctos")
    args = parser.parse_args()

    if not STL.is_dir():
        print(f"ERROR: no existe la carpeta {STL}")
        return 1

    archivos = sorted(STL.rglob("*.stl"))
    if not archivos:
        print(f"ERROR: no hay STL en {STL}")
        return 1

    agrupados: Dict[str, List[Path]] = {}
    for ruta in archivos:
        agrupados.setdefault(_familia_de(ruta), []).append(ruta)

    desconocidas = sorted(set(agrupados) - set(FAMILIAS))
    if desconocidas:
        print("ERROR: familias no reconocidas: " + ", ".join(desconocidas))
        return 1

    total_ok = 0
    total_errores = 0
    for familia, (esperado, piezas, cantidad) in FAMILIAS.items():
        rutas = agrupados.get(familia, [])
        print(f"\n{familia}: {len(rutas)}/{cantidad} archivos")
        if len(rutas) != cantidad:
            print(f"  ERROR: se esperaban {cantidad} archivos")
            total_errores += 1

        for ruta in rutas:
            errores = _validar_malla(ruta, esperado, piezas)
            nombre = ruta.relative_to(STL)
            if errores:
                total_errores += 1
                print(f"  ERROR {nombre}: " + "; ".join(errores))
            else:
                total_ok += 1
                if args.verbose:
                    print(f"  OK    {nombre}")

    print(f"\nResultado: {total_ok} STL validos, {total_errores} errores.")
    return 0 if total_errores == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
