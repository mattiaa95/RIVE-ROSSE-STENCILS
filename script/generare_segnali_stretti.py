#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera segnali compatti 190 x 80 x 0,5 mm:
RIVE ROSSE arriba, linea, icono a la izquierda y palabra + pie a la derecha.

Salida:
    stl/segnali_stretti/singoli/<categoria>/*.stl
    stl/segnali_stretti/doppi/<categoria>/*_2x.stl
    png/segnali_stretti/*.png
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, Rectangle
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

import generare_cartelli_stretti as mini
import generare_segnali as sen
import generare_segnali_aiuto as ayuda
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
ANCHO_MARCA = 120.0

Y_SUBRAYADO = 59.5
ANCHO_SUBRAYADO = 62.0
GROSOR_SUBRAYADO = 2.6

X_ICONO = 8.0
ANCHO_ICONO = 56.0
Y_ICONO = 32.0
ALTO_ICONO = 46.0

X_TEXTO = 70.0
ANCHO_TEXTO = 112.0
CENTRO_TEXTO = X_TEXTO + ANCHO_TEXTO * 0.5

Y_PALABRA = 36.0
ALTO_PALABRA = 32.0
Y_PIE = 13.5
ALTO_PIE = 8.0

Icono = Callable[..., Polygon]


@dataclass
class SenalCompacta:
    palabra: str
    pie: str
    archivo: str
    categoria: str
    icono: Icono


SENALES: List[SenalCompacta] = [
    SenalCompacta(
        s.palabra, s.pie, s.archivo, "passaggi_tecnici",
        (lambda *_args, _senal=s: _senal.icono()),
    )
    for s in sen.SENALES
]
SENALES += [
    SenalCompacta(d.palabra, d.pie, d.archivo, d.categoria, d.icono)
    for d in ayuda.DISENOS
]


def _subrayado() -> Polygon:
    return sen._trazo([
        (ANCHO * 0.5 - ANCHO_SUBRAYADO * 0.5, Y_SUBRAYADO),
        (ANCHO * 0.5 + ANCHO_SUBRAYADO * 0.5, Y_SUBRAYADO),
    ], GROSOR_SUBRAYADO)


def _ajustar_icono(icono: Polygon, font, glyphSet, hmtx,
                   unidades_por_em: float) -> Polygon:
    if icono is None or icono.is_empty:
        raise base.ErrorStencil("El icono ha quedado vacio.")

    b = icono.bounds
    ancho = b[2] - b[0]
    alto = b[3] - b[1]
    if ancho <= base.EPS or alto <= base.EPS:
        raise base.ErrorStencil("El icono no tiene dimensiones validas.")

    factor = min(ANCHO_ICONO / ancho, ALTO_ICONO / alto)
    ajustado = affinity.scale(icono, xfact=factor, yfact=factor, origin=(0.0, 0.0))
    b = ajustado.bounds
    centro_x = X_ICONO + ANCHO_ICONO * 0.5
    ajustado = affinity.translate(
        ajustado,
        xoff=centro_x - (b[0] + b[2]) * 0.5,
        yoff=Y_ICONO - (b[1] + b[3]) * 0.5,
    )
    return base._solo_poligonos(ajustado.buffer(0))


def _comprobar_separacion(a: Polygon, b: Polygon, nombre: str) -> None:
    if a.intersection(b).area > base.EPS:
        raise base.ErrorStencil(f"{nombre} toca otra parte del diseno.")


def construir_segnale(diseno: SenalCompacta, font, glyphSet, hmtx,
                      unidades_por_em: float):
    marca, _ = sen._texto(
        MARCA, ALTO_MARCA, ANCHO_MARCA, (ANCHO * 0.5, Y_MARCA),
        font, glyphSet, hmtx, unidades_por_em
    )
    linea = _subrayado()
    palabra, alto_palabra = sen._texto(
        diseno.palabra, ALTO_PALABRA, ANCHO_TEXTO,
        (CENTRO_TEXTO, Y_PALABRA), font, glyphSet, hmtx, unidades_por_em
    )
    pie, _ = sen._texto(
        diseno.pie, ALTO_PIE, ANCHO_TEXTO,
        (CENTRO_TEXTO, Y_PIE), font, glyphSet, hmtx, unidades_por_em
    )
    icono = _ajustar_icono(
        diseno.icono(font, glyphSet, hmtx, unidades_por_em),
        font, glyphSet, hmtx, unidades_por_em
    )

    piezas: Sequence[Tuple[str, Polygon]] = (
        ("La marca y el subrayado", marca, linea),
        ("El subrayado y la palabra", linea, palabra),
        ("El subrayado y el icono", linea, icono),
        ("La palabra y el pie", palabra, pie),
        ("El icono y la palabra", icono, palabra),
        ("El icono y el pie", icono, pie),
        ("La marca y el icono", marca, icono),
    )
    for nombre, a, b in piezas:
        _comprobar_separacion(a, b, nombre)

    huecos = base._solo_poligonos(
        unary_union([marca, linea, palabra, pie, icono]).buffer(0)
    )
    if huecos is None:
        raise base.ErrorStencil("El segnale no ha generado geometria.")

    b = huecos.bounds
    if b[0] < MARGEN - base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("El segnale invade el margen izquierdo.")
    if b[1] < MARGEN - base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("El segnale invade el margen inferior.")
    if b[2] > ANCHO - MARGEN + base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("El segnale invade el margen derecho.")
    if b[3] > ALTO - MARGEN + base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("El segnale invade el margen superior.")

    placa = Polygon([(0, 0), (ANCHO, 0), (ANCHO, ALTO), (0, ALTO)])
    solido = base._solo_poligonos(placa.difference(huecos))
    if solido is None:
        raise base.ErrorStencil("La resta del segnale ha dejado una placa vacia.")

    solido, puentes = base._conectar_islas(solido, ANCHO_PUENTE)
    return solido, huecos, puentes, alto_palabra, b


def _generar_singolo(diseno: SenalCompacta, solido: Polygon, huecos: Polygon,
                     puentes: int, alto_palabra: float, caja,
                     salida: Path) -> None:
    print()
    print("=" * 68)
    print(f"Segnale compatto: {MARCA} / {diseno.palabra} / {diseno.pie}")
    print(f"Alto de palabra: {alto_palabra:.3f} mm")
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


def _generar_placas_dobles(disenos: List[SenalCompacta], solidos: List[Polygon],
                           dir_doppi: Path) -> None:
    print()
    print("=" * 68)
    print("PLACAS DOBLES APILADAS / SEGNALI COMPATTI")
    for diseno, solido in zip(disenos, solidos):
        malla = mini._crear_placa_doble(solido)
        volumen_esperado = solido.area * GROSOR * 2.0
        mini._validar_placa_doble(malla, volumen_esperado)

        carpeta = dir_doppi / diseno.categoria
        carpeta.mkdir(parents=True, exist_ok=True)
        salida = carpeta / f"{Path(diseno.archivo).stem}_2x.stl"
        malla.export(str(salida), file_type="stl")
        mini._recargar_y_validar_placa_doble(salida, volumen_esperado)
        print(f"  OK: {salida.name} -> {malla.extents[0]:.1f} x "
              f"{malla.extents[1]:.1f} x {malla.extents[2]:.1f} mm")


def _preview(items, salida: Path, spray: bool, titulo: str) -> None:
    columnas = min(4, len(items))
    filas = math.ceil(len(items) / columnas)
    fig, ejes = plt.subplots(filas, columnas,
                             figsize=(4.2 * columnas, 2.4 * filas))
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
        eje.add_patch(PathPatch(mini._a_path(hueco), facecolor=color_hueco,
                                edgecolor="none", antialiased=True))
        eje.set_xlim(0, ANCHO)
        eje.set_ylim(0, ALTO)
        eje.set_aspect("equal")
        eje.axis("off")
        eje.set_title(etiqueta, fontsize=8.5, fontweight="bold", pad=5)

    for eje in ejes[len(items):]:
        eje.axis("off")

    modo = "spray" if spray else "stencil"
    fig.suptitle(
        f"{titulo} / {modo}\n"
        f"{len(items)} segnali 190 x 80 x 0,5 mm",
        fontsize=13, fontweight="bold", y=0.995
    )
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    fig.savefig(salida, dpi=160, bbox_inches="tight", facecolor=fondo_pagina)
    plt.close(fig)


def _previews(disenos: List[SenalCompacta], huecos: List[Polygon],
              dir_png: Path) -> None:
    _preview(
        [(d.palabra, h) for d, h in zip(disenos, huecos)],
        dir_png / "catalogo_segnali_stretti_spray.png", True,
        "RIVE ROSSE / segnali compatti"
    )
    _preview(
        [(d.palabra, h) for d, h in zip(disenos, huecos)],
        dir_png / "catalogo_segnali_stretti_stencil.png", False,
        "RIVE ROSSE / segnali compatti"
    )

    por_categoria: Dict[str, List[Tuple[str, Polygon]]] = {}
    for diseno, hueco in zip(disenos, huecos):
        por_categoria.setdefault(diseno.categoria, []).append(
            (diseno.palabra, hueco)
        )
    for categoria, items in por_categoria.items():
        _preview(
            items, dir_png / f"catalogo_{categoria}_stretti_spray.png", True,
            f"RIVE ROSSE / {categoria.replace('_', ' ')}"
        )
        _preview(
            items, dir_png / f"catalogo_{categoria}_stretti_stencil.png", False,
            f"RIVE ROSSE / {categoria.replace('_', ' ')}"
        )


def main() -> int:
    try:
        if not SENALES:
            raise base.ErrorStencil("No hay senales para generar.")

        archivos = [s.archivo for s in SENALES]
        if len(set(archivos)) != len(archivos):
            raise base.ErrorStencil("Hay nombres de archivo repetidos.")

        ruta_fuente, familia = base._resolver_fuente(base.FUENTE)
        print(f"Fuente: {ruta_fuente}")
        print(f"Familia: {familia}")

        font = base._abrir_fuente(ruta_fuente, familia)
        fallos = []
        disenos_ok: List[SenalCompacta] = []
        solidos_ok: List[Polygon] = []
        huecos_ok: List[Polygon] = []
        try:
            unidades_por_em = float(font["head"].unitsPerEm)
            glyphSet = font.getGlyphSet()
            hmtx = font["hmtx"]

            raiz = Path(__file__).resolve().parent.parent
            dir_singoli = raiz / "stl" / "segnali_stretti" / "singoli"
            dir_doppi = raiz / "stl" / "segnali_stretti" / "doppi"
            dir_png = raiz / "png" / "segnali_stretti"
            for carpeta in (dir_singoli, dir_doppi, dir_png):
                carpeta.mkdir(parents=True, exist_ok=True)

            for diseno in SENALES:
                carpeta = dir_singoli / diseno.categoria
                carpeta.mkdir(parents=True, exist_ok=True)
                salida = carpeta / diseno.archivo
                try:
                    solido, huecos, puentes, alto_palabra, caja = construir_segnale(
                        diseno, font, glyphSet, hmtx, unidades_por_em
                    )
                    _generar_singolo(
                        diseno, solido, huecos, puentes, alto_palabra, caja,
                        salida
                    )
                    disenos_ok.append(diseno)
                    solidos_ok.append(solido)
                    huecos_ok.append(huecos)
                except base.ErrorStencil as exc:
                    print()
                    print(f"ERROR en {diseno.archivo}: {exc}")
                    fallos.append((diseno.archivo, str(exc)))

            if disenos_ok:
                _generar_placas_dobles(disenos_ok, solidos_ok, dir_doppi)
                _previews(disenos_ok, huecos_ok, dir_png)
                mini._preview_placa_doble(
                    huecos_ok[0], dir_png / "piastra_doppia_segnali_spray.png",
                    True
                )
                mini._preview_placa_doble(
                    huecos_ok[0], dir_png / "piastra_doppia_segnali_stencil.png",
                    False
                )
        finally:
            font.close()

        print()
        if fallos:
            print(f"Terminato con {len(fallos)} errore/i.")
            for archivo, mensaje in fallos:
                print(f"  - {archivo}: {mensaje}")
            return 1

        print(f"Pronto: {len(disenos_ok)} segnali singoli e "
              f"{len(disenos_ok)} piastre doppie.")
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
