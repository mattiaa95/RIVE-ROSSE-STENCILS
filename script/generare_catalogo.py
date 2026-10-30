#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera un catalogo PNG unico con tutti gli stencil RIVE ROSSE, separati
per sezioni e con i nomi dei file.

Uscita in png:
    catalogo_rive_rosse.png
    catalogo_rive_rosse_stencil.png
    cartelli/spray.png
    cartelli/stencil.png
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MplPath
from shapely.geometry import Polygon

import generare_cartelli as cart
import generare_segnali as sen
import generare_segnali_aiuto as ayuda
import generare_stencil as base

ANCHO = sen.ANCHO
ALTO = sen.ALTO
FONDO = "#f5f1e8"
VERDE = "#c7441e"

SECCIONES = [
    "CARTELLI TRAIL",
    "CARTELLI SPECIALI",
    "FRECCE",
    "AIUTO",
    "LIVELLI",
    "PASSAGGI TECNICI",
]


@dataclass
class Item:
    seccion: str
    titulo: str
    subtitulo: str
    archivo: str
    hueco: Polygon


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


def _recolectar(font, glyphSet, hmtx, unidades_por_em: float) -> List[Item]:
    items: List[Item] = []

    for cartel in cart.CARTELES:
        _, huecos, _, _, _ = cart.construir_cartel(
            cartel, font, glyphSet, hmtx, unidades_por_em
        )
        subtitulo = cartel.pie if cartel.pie else "SPAZIO LIBERO"
        items.append(Item(
            cartel.categoria,
            " / ".join(cartel.lineas),
            subtitulo,
            cartel.archivo,
            huecos,
        ))

    for senal in sen.SENALES:
        _, huecos, _, _, _ = sen.construir_diseno(
            senal, font, glyphSet, hmtx, unidades_por_em
        )
        items.append(Item(
            "PASSAGGI TECNICI",
            senal.palabra,
            senal.pie,
            senal.archivo,
            huecos,
        ))

    for diseno in ayuda.DISENOS:
        _, huecos, _, _, _ = ayuda.construir_diseno(
            diseno, font, glyphSet, hmtx, unidades_por_em
        )
        seccion = {
            "frecce": "FRECCE",
            "aiuto": "AIUTO",
            "livelli": "LIVELLI",
        }[diseno.categoria]
        items.append(Item(
            seccion,
            diseno.palabra,
            diseno.pie,
            diseno.archivo,
            huecos,
        ))

    return items


def _dibujar_item(eje, item: Item, spray: bool) -> None:
    fondo_placa = "#e9e2d4" if spray else "#111111"
    color_hueco = VERDE if spray else "#ffffff"
    borde = "#d5cdbd" if spray else "#111111"

    eje.set_facecolor(FONDO)
    eje.add_patch(Rectangle(
        (0, 0), ANCHO, ALTO,
        facecolor=fondo_placa,
        edgecolor=borde,
        linewidth=0.6,
    ))
    eje.add_patch(PathPatch(
        _a_path(item.hueco),
        facecolor=color_hueco,
        edgecolor="none",
        antialiased=True,
    ))
    eje.set_xlim(0, ANCHO)
    eje.set_ylim(0, ALTO)
    eje.set_aspect("equal")
    eje.axis("off")
    eje.set_title(
        f"{item.titulo}\n{item.subtitulo} / {item.archivo}",
        fontsize=8.2,
        fontweight="bold",
        pad=4,
    )


def _render(items: List[Item], salida: Path, spray: bool,
            columnas: int = 6) -> None:
    secciones = []
    for nombre in SECCIONES:
        grupo = [item for item in items if item.seccion == nombre]
        if grupo:
            secciones.append((nombre, grupo))

    filas_items = sum(math.ceil(len(grupo) / columnas) for _, grupo in secciones)
    alto = 3.25 * filas_items + 0.7 * len(secciones) + 1.2
    fig = plt.figure(figsize=(3.1 * columnas, alto))
    fig.patch.set_facecolor(FONDO)

    ratios = []
    for _, grupo in secciones:
        ratios.append(0.28)
        ratios.extend([1.0] * math.ceil(len(grupo) / columnas))

    gs = fig.add_gridspec(
        len(ratios), columnas,
        height_ratios=ratios,
        hspace=0.28,
        wspace=0.12,
    )

    fila = 0
    for nombre, grupo in secciones:
        eje = fig.add_subplot(gs[fila, :])
        eje.axis("off")
        eje.text(
            0.01, 0.56, nombre,
            transform=eje.transAxes,
            fontsize=12.5,
            fontweight="bold",
            color=VERDE if spray else "#111111",
            va="center",
        )
        eje.plot(
            [0.0, 1.0], [0.05, 0.05],
            transform=eje.transAxes,
            color="#d5cdbd" if spray else "#777777",
            linewidth=0.8,
        )
        fila += 1

        for indice, item in enumerate(grupo):
            r = fila + indice // columnas
            c = indice % columnas
            _dibujar_item(fig.add_subplot(gs[r, c]), item, spray)

        fila += math.ceil(len(grupo) / columnas)

    modo = "SPRAY" if spray else "STENCIL"
    fig.suptitle(
        f"RIVE ROSSE / CATALOGO COMPLETO / {modo}\n"
        f"{len(items)} stencil 190 x 190 x 0,5 mm",
        fontsize=17,
        fontweight="bold",
        y=0.997,
    )
    leyenda = (
        "SPRAY: arancio = vernice, beige = materiale"
        if spray else
        "STENCIL: bianco = foro, nero = materiale"
    )
    fig.text(0.01, 0.004, leyenda, fontsize=9, color="#333333")
    fig.subplots_adjust(top=0.965, bottom=0.015, left=0.01, right=0.99)
    fig.savefig(salida, dpi=160, bbox_inches="tight", facecolor=FONDO)
    plt.close(fig)


def main() -> int:
    try:
        ruta_fuente, familia = base._resolver_fuente(base.FUENTE)
        print(f"Fuente: {ruta_fuente}")
        print(f"Familia: {familia}")

        font = base._abrir_fuente(ruta_fuente, familia)
        try:
            unidades_por_em = float(font["head"].unitsPerEm)
            glyphSet = font.getGlyphSet()
            hmtx = font["hmtx"]
            items = _recolectar(font, glyphSet, hmtx, unidades_por_em)
        finally:
            font.close()

        raiz = Path(__file__).resolve().parent.parent
        png = raiz / "png"
        cartelli_png = png / "cartelli"
        cartelli_png.mkdir(parents=True, exist_ok=True)

        _render(items, png / "catalogo_rive_rosse.png", True, 6)
        _render(items, png / "catalogo_rive_rosse_stencil.png", False, 6)

        cartelli = [
            item for item in items
            if item.seccion in ("CARTELLI TRAIL", "CARTELLI SPECIALI")
        ]
        _render(cartelli, cartelli_png / "spray.png", True, 4)
        _render(cartelli, cartelli_png / "stencil.png", False, 4)

        print(f"Pronto: {len(items)} stencil nel catalogo.")
        print(f"  {png / 'catalogo_rive_rosse.png'}")
        print(f"  {png / 'catalogo_rive_rosse_stencil.png'}")
        print(f"  {cartelli_png / 'spray.png'}")
        print(f"  {cartelli_png / 'stencil.png'}")
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
