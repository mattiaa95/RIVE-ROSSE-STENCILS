#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera cartelli stretti 190 x 80 x 0,5 mm:
RIVE ROSSE arriba, linea debajo y nombre grande.

Salida:
    stl/cartelli_stretti/singoli/*.stl
    stl/cartelli_stretti/doppi/*_2x.stl
    stl/cartelli_stretti/speciali/freccia_rive_rosse_mtb.stl
    png/cartelli_stretti/*.png
"""

import math
from pathlib import Path
from typing import List, Sequence, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MplPath
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

import generare_cartelli as car
import generare_segnali as sen
import generare_stencil as base

ANCHO = 190.0
ALTO = 80.0
GROSOR = 0.5
MARGEN = 7.0
ANCHO_PUENTE = 2.2

base.ANCHO = ANCHO
base.ALTO = ALTO
base.GROSOR = GROSOR
base.MARGEN = MARGEN

MARCA = "RIVE ROSSE"
Y_MARCA = 68.0
ALTO_MARCA = 10.0
ANCHO_MARCA = 115.0

Y_SUBRAYADO = 59.5
ANCHO_SUBRAYADO = 62.0
GROSOR_SUBRAYADO = 2.6

Y_NOMBRE = 31.5
ANCHO_NOMBRE = 176.0
ALTO_NOMBRE_UNA_LINEA = 42.0
ALTO_NOMBRE_DOS_LINEAS = 22.75
HUECO_LINEAS = 3.5

HUECO_PLACA_DOBLE = 4.0
ALTO_PLACA_DOBLE = ALTO * 2.0 + HUECO_PLACA_DOBLE

DISENOS = [c for c in car.CARTELES if c.categoria == "CARTELLI TRAIL"]


def _subrayado() -> Polygon:
    return sen._trazo([
        (ANCHO * 0.5 - ANCHO_SUBRAYADO * 0.5, Y_SUBRAYADO),
        (ANCHO * 0.5 + ANCHO_SUBRAYADO * 0.5, Y_SUBRAYADO),
    ], GROSOR_SUBRAYADO)


def _texto_una_linea(nombre: str, font, glyphSet, hmtx,
                     unidades_por_em: float) -> Tuple[Polygon, float]:
    poligono, _ = sen._texto(
        nombre, ALTO_NOMBRE_UNA_LINEA, ANCHO_NOMBRE,
        (ANCHO * 0.5, Y_NOMBRE), font, glyphSet, hmtx, unidades_por_em
    )
    return poligono, poligono.bounds[3] - poligono.bounds[1]


def _texto_dos_lineas(lineas: Sequence[str], font, glyphSet, hmtx,
                      unidades_por_em: float) -> Tuple[Polygon, float]:
    if len(lineas) != 2:
        raise base.ErrorStencil("El bloque de dos lineas necesita dos textos.")

    naturales = []
    for linea in lineas:
        poligono = base._texto_a_poligono(linea, font, glyphSet, hmtx)
        b = poligono.bounds
        ancho = b[2] - b[0]
        alto = b[3] - b[1]
        naturales.append((poligono, ancho / alto))

    alto_letra = min(
        ALTO_NOMBRE_DOS_LINEAS,
        ANCHO_NOMBRE / naturales[0][1],
        ANCHO_NOMBRE / naturales[1][1],
    )
    if alto_letra <= 0:
        raise base.ErrorStencil("No se ha podido calcular el tamano del bloque.")

    bloque_alto = 2.0 * alto_letra + HUECO_LINEAS
    arriba = Y_NOMBRE + bloque_alto * 0.5
    piezas = []
    for i, (linea, _) in enumerate(zip(lineas, naturales)):
        centro_y = arriba - alto_letra * 0.5 - i * (alto_letra + HUECO_LINEAS)
        poligono, _ = sen._texto(
            linea, alto_letra, ANCHO_NOMBRE, (ANCHO * 0.5, centro_y),
            font, glyphSet, hmtx, unidades_por_em
        )
        piezas.append(poligono)

    resultado = base._solo_poligonos(unary_union(piezas))
    if resultado is None:
        raise base.ErrorStencil("El bloque de dos lineas ha quedado vacio.")
    return resultado, alto_letra


def _texto_nombre(cartel: car.Cartel, font, glyphSet, hmtx,
                  unidades_por_em: float) -> Tuple[Polygon, float]:
    if len(cartel.lineas) == 1:
        return _texto_una_linea(
            cartel.lineas[0], font, glyphSet, hmtx, unidades_por_em
        )
    return _texto_dos_lineas(
        cartel.lineas, font, glyphSet, hmtx, unidades_por_em
    )


def _comprobar_separacion(a: Polygon, b: Polygon, nombre: str) -> None:
    if a.intersection(b).area > base.EPS:
        raise base.ErrorStencil(f"{nombre} toca otra parte del diseno.")


def construir_cartello(cartel: car.Cartel, font, glyphSet, hmtx,
                       unidades_por_em: float):
    marca, _ = sen._texto(
        MARCA, ALTO_MARCA, ANCHO_MARCA, (ANCHO * 0.5, Y_MARCA),
        font, glyphSet, hmtx, unidades_por_em
    )
    linea = _subrayado()
    nombre, alto_letra = _texto_nombre(
        cartel, font, glyphSet, hmtx, unidades_por_em
    )

    _comprobar_separacion(marca, linea, "La marca y el subrayado")
    _comprobar_separacion(linea, nombre, "El subrayado y el nombre")

    huecos = base._solo_poligonos(unary_union([marca, linea, nombre]).buffer(0))
    if huecos is None:
        raise base.ErrorStencil("El cartel no ha generado geometria.")

    b = huecos.bounds
    if b[0] < MARGEN - base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("El cartel invade el margen izquierdo.")
    if b[1] < MARGEN - base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("El cartel invade el margen inferior.")
    if b[2] > ANCHO - MARGEN + base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("El cartel invade el margen derecho.")
    if b[3] > ALTO - MARGEN + base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("El cartel invade el margen superior.")

    placa = Polygon([(0, 0), (ANCHO, 0), (ANCHO, ALTO), (0, ALTO)])
    solido = base._solo_poligonos(placa.difference(huecos))
    if solido is None:
        raise base.ErrorStencil("La resta del cartel ha dejado una placa vacia.")

    solido, puentes = base._conectar_islas(solido, ANCHO_PUENTE)
    return solido, huecos, puentes, alto_letra, b


def _contorno_flecha() -> Polygon:
    puntos = [
        (14.0, 54.0),
        (145.0, 54.0),
        (145.0, 68.0),
        (179.0, 40.0),
        (145.0, 12.0),
        (145.0, 26.0),
        (14.0, 26.0),
    ]
    return sen._trazo(puntos, 7.0)


def construir_freccia(font, glyphSet, hmtx, unidades_por_em: float):
    flecha = _contorno_flecha()
    texto, _ = sen._texto(
        "RIVE ROSSE MTB", 13.0, 115.0, (80.0, 40.0),
        font, glyphSet, hmtx, unidades_por_em
    )

    _comprobar_separacion(flecha, texto, "La flecha y el texto")

    huecos = base._solo_poligonos(unary_union([flecha, texto]).buffer(0))
    if huecos is None:
        raise base.ErrorStencil("La flecha no ha generado geometria.")

    b = huecos.bounds
    if b[0] < MARGEN - base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("La flecha invade el margen izquierdo.")
    if b[1] < MARGEN - base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("La flecha invade el margen inferior.")
    if b[2] > ANCHO - MARGEN + base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("La flecha invade el margen derecho.")
    if b[3] > ALTO - MARGEN + base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("La flecha invade el margen superior.")

    placa = Polygon([(0, 0), (ANCHO, 0), (ANCHO, ALTO), (0, ALTO)])
    solido = base._solo_poligonos(placa.difference(huecos))
    if solido is None:
        raise base.ErrorStencil("La resta de la flecha ha dejado una placa vacia.")

    solido, puentes = base._conectar_islas(solido, ANCHO_PUENTE)
    return solido, huecos, puentes, b


def _validar_placa_doble(malla, volumen_esperado: float) -> None:
    if not np.allclose(malla.extents, [ANCHO, ALTO_PLACA_DOBLE, GROSOR],
                       atol=1.0e-3, rtol=0.0):
        raise base.ErrorStencil(
            "Dimensiones incorrectas en la placa doble: "
            f"{malla.extents[0]:.4f} x {malla.extents[1]:.4f} x "
            f"{malla.extents[2]:.4f} mm."
        )
    if not malla.is_watertight:
        raise base.ErrorStencil("La placa doble no es estanca.")
    if not malla.is_winding_consistent:
        raise base.ErrorStencil("La placa doble tiene normales incoherentes.")
    if malla.volume <= 0:
        raise base.ErrorStencil("La placa doble tiene volumen no positivo.")

    partes = malla.split(only_watertight=False)
    if len(partes) != 2:
        raise base.ErrorStencil(
            f"La placa doble contiene {len(partes)} piezas; deben ser 2."
        )
    for parte in partes:
        if not parte.is_watertight or parte.volume <= 0:
            raise base.ErrorStencil("Una de las dos piezas de la placa no es valida.")

    if not math.isclose(malla.volume, volumen_esperado,
                        rel_tol=1.0e-4, abs_tol=1.0e-4):
        raise base.ErrorStencil(
            "El volumen de la placa doble no coincide con las dos piezas."
        )
    if malla.bounds[0][2] < -1.0e-6 or malla.bounds[1][2] > GROSOR + 1.0e-6:
        raise base.ErrorStencil("La placa doble no esta entre z=0 y z=GROSOR.")


def _recargar_y_validar_placa_doble(ruta: Path, volumen_esperado: float) -> None:
    malla = trimesh.load(str(ruta), force="mesh")
    _validar_placa_doble(malla, volumen_esperado)


def _crear_placa_doble(solido: Polygon):
    malla_1 = sen._crear_malla(solido)
    malla_2 = malla_1.copy()
    malla_2.apply_translation([0.0, ALTO + HUECO_PLACA_DOBLE, 0.0])
    return trimesh.util.concatenate([malla_1, malla_2])


def _a_path(geometria) -> MplPath:
    vertices = []
    codigos = []
    for poligono in base._partes_poligonales(geometria):
        anillos: Sequence = [poligono.exterior, *poligono.interiors]
        for anillo in anillos:
            coords = list(anillo.coords)
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            vertices.extend(coords)
            codigos.extend(
                [MplPath.MOVETO]
                + [MplPath.LINETO] * (len(coords) - 2)
                + [MplPath.CLOSEPOLY]
            )
    return MplPath(vertices, codigos)


def _preview(items, salida: Path, spray: bool, titulo: str) -> None:
    columnas = min(3, len(items))
    filas = math.ceil(len(items) / columnas)
    fig, ejes = plt.subplots(filas, columnas,
                             figsize=(4.5 * columnas, 2.4 * filas))
    ejes = list(ejes.flat) if hasattr(ejes, "flat") else [ejes]

    fondo_placa = "#e9e2d4" if spray else "#111111"
    color_hueco = "#c7441e" if spray else "#ffffff"
    fondo_pagina = "#f5f1e8"
    fig.patch.set_facecolor(fondo_pagina)

    for eje, (etiqueta, hueco) in zip(ejes, items):
        eje.set_facecolor(fondo_pagina)
        eje.add_patch(Rectangle((0, 0), ANCHO, ALTO,
                                facecolor=fondo_placa,
                                edgecolor="#d5cdbd" if spray else "#111111",
                                linewidth=0.6))
        eje.add_patch(PathPatch(_a_path(hueco), facecolor=color_hueco,
                                edgecolor="none", antialiased=True))
        eje.set_xlim(0, ANCHO)
        eje.set_ylim(0, ALTO)
        eje.set_aspect("equal")
        eje.axis("off")
        eje.set_title(etiqueta, fontsize=9.0, fontweight="bold", pad=5)

    for eje in ejes[len(items):]:
        eje.axis("off")

    modo = "spray" if spray else "stencil"
    fig.suptitle(
        f"{titulo} / {modo}\n"
        "cartelli 190 x 80 x 0,5 mm",
        fontsize=13, fontweight="bold", y=0.995
    )
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    fig.savefig(salida, dpi=160, bbox_inches="tight", facecolor=fondo_pagina)
    plt.close(fig)


def _preview_placa_doble(hueco: Polygon, salida: Path, spray: bool) -> None:
    fig, eje = plt.subplots(figsize=(5.2, 4.8))
    fondo_placa = "#e9e2d4" if spray else "#111111"
    color_hueco = "#c7441e" if spray else "#ffffff"
    fondo_pagina = "#f5f1e8"
    fig.patch.set_facecolor(fondo_pagina)
    eje.set_facecolor(fondo_pagina)

    eje.add_patch(Rectangle((0, 0), ANCHO, ALTO_PLACA_DOBLE,
                            facecolor=fondo_placa,
                            edgecolor="#d5cdbd" if spray else "#111111",
                            linewidth=0.6))
    for desplazamiento in (0.0, ALTO + HUECO_PLACA_DOBLE):
        eje.add_patch(PathPatch(
            _a_path(affinity.translate(hueco, yoff=desplazamiento)),
            facecolor=color_hueco, edgecolor="none", antialiased=True
        ))

    eje.set_xlim(0, ANCHO)
    eje.set_ylim(0, ALTO_PLACA_DOBLE)
    eje.set_aspect("equal")
    eje.axis("off")
    eje.set_title("Placca doppia 190 x 164 mm / 2 x 190 x 80 mm",
                  fontsize=11, fontweight="bold", pad=8)
    fig.tight_layout()
    fig.savefig(salida, dpi=160, bbox_inches="tight", facecolor=fondo_pagina)
    plt.close(fig)


def _generar_singolo(nombre: str, solido: Polygon, huecos: Polygon,
                     puentes: int, alto_letra: float, caja,
                     salida: Path) -> None:
    print()
    print("=" * 68)
    print(f"Cartello stretto: {MARCA} / {nombre}")
    print(f"Alto de letra: {alto_letra:.3f} mm")
    print(f"Caja del diseno: {caja[2] - caja[0]:.3f} x {caja[3] - caja[1]:.3f} mm")
    print(f"Area abierta: {100.0 * huecos.area / (ANCHO * ALTO):.2f} %")

    malla = sen._crear_malla(solido)
    base._validar_malla(malla, solido.area)

    salida = salida.expanduser()
    malla.export(str(salida), file_type="stl")
    base._recargar_y_validar_stl(salida)

    print("VALIDACION CORRECTA")
    print(f"  Archivo: {salida}")
    print(f"  Dimensiones: {malla.extents[0]:.3f} x {malla.extents[1]:.3f} x "
          f"{malla.extents[2]:.3f} mm")
    print(f"  Puentes anadidos: {puentes} (ancho {ANCHO_PUENTE:.2f} mm)")
    print("  Malla: estanca, una sola pieza, sin triangulos degenerados")


def _generar_placas_dobles(carteles, solidos, salida_dir: Path) -> None:
    print()
    print("=" * 68)
    print("PLACAS DOBLES APILADAS")
    for cartel, solido in zip(carteles, solidos):
        malla = _crear_placa_doble(solido)
        volumen_esperado = solido.area * GROSOR * 2.0
        _validar_placa_doble(malla, volumen_esperado)

        salida = salida_dir / f"{Path(cartel.archivo).stem}_2x.stl"
        malla.export(str(salida), file_type="stl")
        _recargar_y_validar_placa_doble(salida, volumen_esperado)
        print(f"  OK: {salida.name} -> {malla.extents[0]:.1f} x "
              f"{malla.extents[1]:.1f} x {malla.extents[2]:.1f} mm")


def main() -> int:
    try:
        if not DISENOS:
            raise base.ErrorStencil("No hay carteles de trail para generar.")

        ruta_fuente, familia = base._resolver_fuente(base.FUENTE)
        print(f"Fuente: {ruta_fuente}")
        print(f"Familia: {familia}")

        font = base._abrir_fuente(ruta_fuente, familia)
        fallos = []
        carteles_ok = []
        solidos_ok = []
        huecos_ok = []
        dobles_huecos = []
        try:
            unidades_por_em = float(font["head"].unitsPerEm)
            glyphSet = font.getGlyphSet()
            hmtx = font["hmtx"]

            raiz = Path(__file__).resolve().parent.parent
            dir_singoli = raiz / "stl" / "cartelli_stretti" / "singoli"
            dir_dobles = raiz / "stl" / "cartelli_stretti" / "doppi"
            dir_especiales = raiz / "stl" / "cartelli_stretti" / "speciali"
            dir_png = raiz / "png" / "cartelli_stretti"
            for carpeta in (dir_singoli, dir_dobles, dir_especiales, dir_png):
                carpeta.mkdir(parents=True, exist_ok=True)

            for cartel in DISENOS:
                salida = dir_singoli / cartel.archivo
                try:
                    solido, huecos, puentes, alto_letra, caja = construir_cartello(
                        cartel, font, glyphSet, hmtx, unidades_por_em
                    )
                    _generar_singolo(
                        cartel.nombre, solido, huecos, puentes, alto_letra, caja,
                        salida
                    )
                    carteles_ok.append(cartel)
                    solidos_ok.append(solido)
                    huecos_ok.append((cartel.nombre, huecos))
                except base.ErrorStencil as exc:
                    print()
                    print(f"ERROR en {cartel.archivo}: {exc}")
                    fallos.append((cartel.archivo, str(exc)))

            try:
                solido, huecos, puentes, caja = construir_freccia(
                    font, glyphSet, hmtx, unidades_por_em
                )
                _generar_singolo(
                    "FRECCIA / RIVE ROSSE MTB", solido, huecos, puentes,
                    caja[3] - caja[1], caja,
                    dir_especiales / "freccia_rive_rosse_mtb.stl"
                )
                huecos_ok.append(("FRECCIA / RIVE ROSSE MTB", huecos))
            except base.ErrorStencil as exc:
                print()
                print(f"ERROR en freccia_rive_rosse_mtb.stl: {exc}")
                fallos.append(("freccia_rive_rosse_mtb.stl", str(exc)))

            if carteles_ok:
                _generar_placas_dobles(carteles_ok, solidos_ok, dir_dobles)

            if huecos_ok:
                _preview(
                    huecos_ok, dir_png / "catalogo_cartelli_stretti_spray.png",
                    True, "RIVE ROSSE / cartelli stretti"
                )
                _preview(
                    huecos_ok, dir_png / "catalogo_cartelli_stretti_stencil.png",
                    False, "RIVE ROSSE / cartelli stretti"
                )

            if carteles_ok:
                _preview_placa_doble(
                    huecos_ok[0][1], dir_png / "piastra_doppia_spray.png", True
                )
                _preview_placa_doble(
                    huecos_ok[0][1], dir_png / "piastra_doppia_stencil.png", False
                )

            if len(huecos_ok) > len(carteles_ok):
                _preview(
                    [huecos_ok[-1]],
                    dir_png / "freccia_rive_rosse_mtb_spray.png",
                    True, "RIVE ROSSE / freccia speciale"
                )
                _preview(
                    [huecos_ok[-1]],
                    dir_png / "freccia_rive_rosse_mtb_stencil.png",
                    False, "RIVE ROSSE / freccia speciale"
                )
        finally:
            font.close()

        print()
        if fallos:
            print(f"Terminato con {len(fallos)} errore/i.")
            for archivo, mensaje in fallos:
                print(f"  - {archivo}: {mensaje}")
            return 1

        print(f"Pronto: {len(carteles_ok)} cartelli singoli, "
              f"{len(carteles_ok)} piastre doppie e 1 freccia speciale.")
        return 0

    except base.ErrorStencil as exc:
        print()
        print("ERROR: " + str(exc))
        return 1
    except KeyboardInterrupt:
        print("\nCancelado.")
        return 130
    except Exception as exc:
        print()
        print(f"ERROR inesperado: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
