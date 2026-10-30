#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Sequence, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MplPath
from shapely.geometry import Polygon
from shapely.ops import unary_union

import generare_segnali as sen
import generare_stencil as base

ANCHO = sen.ANCHO
ALTO = sen.ALTO
MARGEN = sen.MARGEN
ANCHO_PUENTE = sen.ANCHO_PUENTE
GROSOR = sen.GROSOR

Icono = Callable[[object, object, object, float], Polygon]


@dataclass
class Diseno:
    palabra: str
    pie: str
    archivo: str
    categoria: str
    icono: Icono


def _circulo(centro: Tuple[float, float], radio: float, pasos: int = 40) -> Polygon:
    cx, cy = centro
    puntos = [
        (cx + radio * math.cos(2.0 * math.pi * i / pasos),
         cy + radio * math.sin(2.0 * math.pi * i / pasos))
        for i in range(pasos)
    ]
    return Polygon(puntos)


def _icono_flecha_arriba(*_) -> Polygon:
    return sen._flecha([(95.0, 56.0), (95.0, 102.0)], 15.0, 28.0, 50.0)


def _icono_flecha_sinistra(*_) -> Polygon:
    return sen._flecha([(148.0, 76.0), (52.0, 76.0)], 15.0, 30.0, 50.0)


def _icono_flecha_derecha(*_) -> Polygon:
    return sen._flecha([(42.0, 76.0), (138.0, 76.0)], 15.0, 30.0, 50.0)


def _icono_flecha_abajo(*_) -> Polygon:
    return sen._flecha([(95.0, 100.0), (95.0, 52.0)], 15.0, 30.0, 50.0)


def _icono_croce(*_) -> Polygon:
    vertical = sen._trazo([(95.0, 52.0), (95.0, 98.0)], 17.0)
    horizontal = sen._trazo([(69.0, 75.0), (121.0, 75.0)], 17.0)
    return base._solo_poligonos(unary_union([vertical, horizontal]))


def _icono_gota(*_) -> Polygon:
    cuerpo = _circulo((95.0, 72.0), 17.0)
    punta = Polygon([(95.0, 101.0), (78.0, 72.0), (112.0, 72.0)])
    return base._solo_poligonos(unary_union([cuerpo, punta]))


def _icono_rifugio(*_) -> Polygon:
    tejado = Polygon([(51.0, 78.0), (95.0, 104.0), (139.0, 78.0)])
    cuerpo = Polygon([(63.0, 50.0), (127.0, 50.0), (127.0, 79.0), (63.0, 79.0)])
    return base._solo_poligonos(unary_union([tejado, cuerpo]))


def _icono_barreira(*_) -> Polygon:
    postes = [
        sen._trazo([(58.0, 50.0), (58.0, 96.0)], 6.0),
        sen._trazo([(95.0, 50.0), (95.0, 96.0)], 6.0),
        sen._trazo([(132.0, 50.0), (132.0, 96.0)], 6.0),
    ]
    barras = [
        sen._trazo([(48.0, 62.0), (142.0, 62.0)], 7.0),
        sen._trazo([(48.0, 84.0), (142.0, 84.0)], 7.0),
    ]
    return base._solo_poligonos(unary_union(postes + barras))


def _icono_ruta(*_) -> Polygon:
    ruta = sen._flecha([(50.0, 56.0), (76.0, 86.0), (108.0, 66.0), (140.0, 94.0)],
                       6.5, 12.0, 25.0)
    inicio = _circulo((50.0, 56.0), 4.5)
    return base._solo_poligonos(unary_union([ruta, inicio]))


def _icono_numero(numero: str) -> Icono:
    def icono(font, glyphSet, hmtx, unidades_por_em: float) -> Polygon:
        poligono, _ = sen._texto(
            numero, 54.0, 90.0, (ANCHO * 0.5, 73.0),
            font, glyphSet, hmtx, unidades_por_em
        )
        return poligono
    return icono


DISENOS: List[Diseno] = [
    Diseno("DRITTO", "SEGUI LA FRECCIA", "freccia_dritto.stl", "frecce",
           _icono_flecha_arriba),
    Diseno("SINISTRA", "SEGUI LA FRECCIA", "freccia_sinistra.stl", "frecce",
           _icono_flecha_sinistra),
    Diseno("DESTRA", "SEGUI LA FRECCIA", "freccia_destra.stl", "frecce",
           _icono_flecha_derecha),
    Diseno("INDIETRO", "SEGUI LA FRECCIA", "freccia_indietro.stl", "frecce",
           _icono_flecha_abajo),
    Diseno("AIUTO", "CHIAMA IL 112", "aiuto_112.stl", "aiuto",
           _icono_croce),
    Diseno("ACQUA", "FONTE POTABILE", "aiuto_acqua.stl", "aiuto",
           _icono_gota),
    Diseno("RIFUGIO", "RIPARO", "aiuto_rifugio.stl", "aiuto",
           _icono_rifugio),
    Diseno("CHIUSO", "SENTIERO CHIUSO", "aiuto_chiuso.stl", "aiuto",
           _icono_barreira),
    Diseno("SEGUI", "LE FRECCE", "aiuto_orientamento.stl", "aiuto",
           _icono_ruta),
    Diseno("FACILE", "LIVELLO VERDE", "livello_facile.stl", "livelli",
           _icono_numero("1")),
    Diseno("MEDIO", "LIVELLO BLU", "livello_medio.stl", "livelli",
           _icono_numero("2")),
    Diseno("DIFFICILE", "LIVELLO ROSSO", "livello_difficile.stl", "livelli",
           _icono_numero("3")),
    Diseno("ESTREMO", "LIVELLO NERO", "livello_estremo.stl", "livelli",
           _icono_numero("4")),
]


def construir_diseno(diseno: Diseno, font, glyphSet, hmtx,
                     unidades_por_em: float):
    marca, _ = sen._texto(
        sen.MARCA, sen.ALTO_MARCA, 120.0, (ANCHO * 0.5, sen.Y_MARCA),
        font, glyphSet, hmtx, unidades_por_em
    )
    palabra, alto_palabra = sen._texto(
        diseno.palabra, sen.ALTO_PALABRA, sen.ANCHO_PALABRA,
        (ANCHO * 0.5, sen.Y_PALABRA), font, glyphSet, hmtx, unidades_por_em
    )
    pie, _ = sen._texto(
        diseno.pie, sen.ALTO_PIE, sen.ANCHO_PIE,
        (ANCHO * 0.5, sen.Y_PIE), font, glyphSet, hmtx, unidades_por_em
    )
    icono = diseno.icono(font, glyphSet, hmtx, unidades_por_em)

    if icono is None or icono.is_empty:
        raise base.ErrorStencil("El icono ha quedado vacio.")
    if icono.bounds[3] > palabra.bounds[1] - 1.0:
        raise base.ErrorStencil("El icono toca la palabra principal.")
    if icono.bounds[1] < pie.bounds[3] + 1.0:
        raise base.ErrorStencil("El icono toca el pie.")

    huecos = unary_union([
        marca,
        sen._subrayado(),
        palabra,
        icono,
        pie,
        sen._slashes(),
    ])
    huecos = base._solo_poligonos(huecos.buffer(0))
    if huecos is None:
        raise base.ErrorStencil("El diseno no ha generado geometria.")

    b = huecos.bounds
    if b[0] < MARGEN - base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("El diseno invade el margen izquierdo.")
    if b[1] < MARGEN - base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("El diseno invade el margen inferior.")
    if b[2] > ANCHO - MARGEN + base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("El diseno invade el margen derecho.")
    if b[3] > ALTO - MARGEN + base.TOLERANCIA_VALIDACION:
        raise base.ErrorStencil("El diseno invade el margen superior.")

    placa = Polygon([(0, 0), (ANCHO, 0), (ANCHO, ALTO), (0, ALTO)])
    solido = base._solo_poligonos(placa.difference(huecos))
    if solido is None:
        raise base.ErrorStencil("La resta del diseno ha dejado una placa vacia.")

    solido, puentes = base._conectar_islas(solido, ANCHO_PUENTE)
    return solido, huecos, puentes, alto_palabra, b


def _crear_malla(solido: Polygon):
    return sen._crear_malla(solido)


def _generar(diseno: Diseno, salida: Path, font, glyphSet, hmtx,
             unidades_por_em: float):
    solido, huecos, puentes, alto_palabra, caja = construir_diseno(
        diseno, font, glyphSet, hmtx, unidades_por_em
    )

    print()
    print("=" * 68)
    print(f"Segnale: {sen.MARCA} / {diseno.palabra} / {diseno.pie}")
    print(f"Alto de palabra: {alto_palabra:.3f} mm")
    print(f"Caja del diseno: {caja[2]-caja[0]:.3f} x {caja[3]-caja[1]:.3f} mm")
    print(f"Area abierta: {100.0 * huecos.area / (ANCHO * ALTO):.2f} %")

    malla = _crear_malla(solido)
    base._validar_malla(malla, solido.area)

    salida = salida.expanduser()
    malla.export(str(salida), file_type="stl")
    base._recargar_y_validar_stl(salida)

    print("VALIDACION CORRECTA")
    print(f"  Archivo: {salida}")
    print(f"  Dimensiones: {malla.extents[0]:.3f} x {malla.extents[1]:.3f} x "
          f"{malla.extents[2]:.3f} mm")
    if puentes == 0:
        print("  Puentes anadidos: 0 (los puentes ya vienen en la fuente)")
    else:
        print(f"  Puentes anadidos: {puentes} (ancho {ANCHO_PUENTE:.2f} mm)")
    print("  Malla: estanca, una sola pieza, sin triangulos degenerados")


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


def _preview(disenos: List[Diseno], huecos: List[Polygon], salida: Path,
             spray: bool) -> None:
    columnas = 4
    filas = math.ceil(len(disenos) / columnas)
    fig, ejes = plt.subplots(filas, columnas, figsize=(4.0 * columnas, 4.25 * filas))
    ejes = list(ejes.flat) if hasattr(ejes, "flat") else [ejes]

    fondo_placa = "#111111" if not spray else "#e9e2d4"
    color_hueco = "#ffffff" if not spray else "#c7441e"
    fondo_pagina = "#f5f1e8" if not spray else "#f5f1e8"
    fig.patch.set_facecolor(fondo_pagina)

    for eje, diseno, hueco in zip(ejes, disenos, huecos):
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
        eje.set_title(f"{diseno.palabra} / {diseno.pie}",
                      fontsize=8.5, fontweight="bold", pad=5)

    for eje in ejes[len(disenos):]:
        eje.axis("off")

    modo = "spray" if spray else "stencil"
    fig.suptitle(
        f"RIVE ROSSE / frecce, aiuto e livelli / {modo}\n"
        f"{len(disenos)} segnali 190 x 190 x 0,5 mm",
        fontsize=13, fontweight="bold", y=0.995
    )
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    fig.savefig(salida, dpi=160, bbox_inches="tight", facecolor=fondo_pagina)
    plt.close(fig)


def main() -> int:
    try:
        if ANCHO <= 2 * MARGEN or ALTO <= 2 * MARGEN:
            raise base.ErrorStencil("ANCHO/ALTO deben ser mayores que 2*MARGEN.")
        if not DISENOS:
            raise base.ErrorStencil("DISENOS esta vacio.")

        archivos = [d.archivo for d in DISENOS]
        if len(set(archivos)) != len(archivos):
            raise base.ErrorStencil("Hay nombres de archivo repetidos.")

        ruta_fuente, familia = base._resolver_fuente(base.FUENTE)
        print(f"Fuente: {ruta_fuente}")
        print(f"Familia: {familia}")

        font = base._abrir_fuente(ruta_fuente, familia)
        fallos = []
        huecos_ok: List[Polygon] = []
        disenos_ok: List[Diseno] = []
        try:
            unidades_por_em = float(font["head"].unitsPerEm)
            glyphSet = font.getGlyphSet()
            hmtx = font["hmtx"]

            raiz = Path(__file__).resolve().parent.parent
            for diseno in DISENOS:
                carpeta = raiz / "stl" / "segnali" / diseno.categoria
                carpeta.mkdir(parents=True, exist_ok=True)
                salida = carpeta / diseno.archivo
                try:
                    solido, huecos, _, _, _ = construir_diseno(
                        diseno, font, glyphSet, hmtx, unidades_por_em
                    )
                    malla = _crear_malla(solido)
                    base._validar_malla(malla, solido.area)
                    malla.export(str(salida), file_type="stl")
                    base._recargar_y_validar_stl(salida)

                    print()
                    print("=" * 68)
                    print(f"Segnale: {sen.MARCA} / {diseno.palabra} / {diseno.pie}")
                    print("VALIDACION CORRECTA")
                    print(f"  Archivo: {salida}")
                    print(f"  Dimensiones: {malla.extents[0]:.3f} x {malla.extents[1]:.3f} x "
                          f"{malla.extents[2]:.3f} mm")

                    disenos_ok.append(diseno)
                    huecos_ok.append(huecos)
                except base.ErrorStencil as exc:
                    print()
                    print(f"ERROR en {diseno.archivo}: {exc}")
                    fallos.append((diseno.archivo, str(exc)))
        finally:
            font.close()

        print()
        if fallos:
            print(f"Terminato con {len(fallos)} errore/i su {len(DISENOS)} segnali.")
            for archivo, mensaje in fallos:
                print(f"  - {archivo}: {mensaje}")
            return 1

        raiz = Path(__file__).resolve().parent.parent
        png_dir = raiz / "png" / "segnali"
        png_dir.mkdir(parents=True, exist_ok=True)
        _preview(disenos_ok, huecos_ok, png_dir / "aiuto_livelli_spray.png", True)
        _preview(disenos_ok, huecos_ok, png_dir / "aiuto_livelli_stencil.png", False)

        print(f"Pronto: {len(DISENOS)} segnali generati in {raiz}")
        print("Previews: png/segnali/aiuto_livelli_spray.png y aiuto_livelli_stencil.png")
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
