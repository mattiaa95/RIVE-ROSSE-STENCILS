#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera cartelli-stencil de 190 x 190 x 0,5 mm con los nombres de los trails
en el estilo RIVE ROSSE: marca arriba, nombre grande, icono de sendero,
SENTIERO y tres rayas.

Salida en stl/cartelli:
    m41.stl
    m41_bis.stl
    la_pignola.stl
    vergnago.stl
    m33.stl
    trail_academy.stl
    super_vulcano.stl
    trail_dei_pini.stl
    capitan_tuta.stl
    madonna_del_sabbione.stl
    moia_caracse.stl
    rientro.stl
    trasferimento.stl
    partenza.stl
    arrivo.stl
    navetta.stl
    parcheggio.stl
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

import generare_segnali as sen
import generare_stencil as base
from shapely.geometry import Polygon
from shapely.ops import unary_union

ANCHO = sen.ANCHO
ALTO = sen.ALTO
MARGEN = sen.MARGEN
ANCHO_PUENTE = sen.ANCHO_PUENTE

ALTO_PALABRA = sen.ALTO_PALABRA
ANCHO_PALABRA = sen.ANCHO_PALABRA
ALTO_BLOQUE_DOS_LINEAS = 55.0
HUECO_LINEAS = 5.0
MAX_ALTO_DOS_LINEAS = (ALTO_BLOQUE_DOS_LINEAS - HUECO_LINEAS) * 0.5

PIE = "SENTIERO"

PANEL_X0 = 25.0
PANEL_Y0 = 48.0
PANEL_X1 = 165.0
PANEL_Y1 = 98.0
PANEL_DASH = 8.0
PANEL_GAP = 4.0
PANEL_GROSOR = 1.4


@dataclass
class Cartel:
    nombre: str
    lineas: Sequence[str]
    archivo: str
    categoria: str = "CARTELLI TRAIL"
    pie: str = PIE
    panel_libre: bool = False


CARTELES = [
    Cartel("M41", ["M41"], "m41.stl"),
    Cartel("M41 BIS", ["M41 BIS"], "m41_bis.stl"),
    Cartel("LA PIGNOLA", ["LA PIGNOLA"], "la_pignola.stl"),
    Cartel("VERGNAGO", ["VERGNAGO"], "vergnago.stl"),
    Cartel("M33", ["M33"], "m33.stl"),
    Cartel("TRAIL ACADEMY", ["TRAIL", "ACADEMY"], "trail_academy.stl"),
    Cartel("SUPER VULCANO", ["SUPER", "VULCANO"], "super_vulcano.stl"),
    Cartel("TRAIL DEI PINI", ["TRAIL", "DEI PINI"], "trail_dei_pini.stl"),
    Cartel("CAPITAN TUTA", ["CAPITAN", "TUTA"], "capitan_tuta.stl"),
    Cartel("MADONNA DEL SABBIONE", ["MADONNA", "DEL SABBIONE"],
           "madonna_del_sabbione.stl"),
    Cartel("MOIA-CARASCÈ", ["MOIA-CARASCÈ"], "moia_caracse.stl"),
    Cartel("RIENTRO", ["RIENTRO"], "rientro.stl",
           categoria="CARTELLI SPECIALI", pie="ALLA PARTENZA"),
    Cartel("TRASFERIMENTO", ["TRASFERIMENTO", "A"], "trasferimento.stl",
           categoria="CARTELLI SPECIALI", pie="", panel_libre=True),
    Cartel("PARTENZA", ["PARTENZA"], "partenza.stl",
           categoria="CARTELLI SPECIALI", pie="INIZIO SENTIERO"),
    Cartel("ARRIVO", ["ARRIVO"], "arrivo.stl",
           categoria="CARTELLI SPECIALI", pie="FINE SENTIERO"),
    Cartel("NAVETTA", ["NAVETTA"], "navetta.stl",
           categoria="CARTELLI SPECIALI", pie="TRASFERIMENTO"),
    Cartel("PARCHEGGIO", ["PARCHEGGIO"], "parcheggio.stl",
           categoria="CARTELLI SPECIALI", pie="AUTO E BICI"),
]


def _circulo(centro: Tuple[float, float], radio: float, pasos: int = 32) -> Polygon:
    cx, cy = centro
    puntos = [
        (cx + radio * math.cos(2.0 * math.pi * i / pasos),
         cy + radio * math.sin(2.0 * math.pi * i / pasos))
        for i in range(pasos)
    ]
    return Polygon(puntos)


def icono_trail() -> Polygon:
    puntos = [(52.0, 56.0), (80.0, 88.0), (110.0, 64.0), (144.0, 94.0)]
    ruta = sen._flecha(puntos, 6.5, 11.0, 24.0)
    inicio = _circulo((52.0, 56.0), 4.5)
    return base._solo_poligonos(unary_union([ruta, inicio]))


def _panel_guia() -> Polygon:
    piezas = []

    def lado(x0: float, y0: float, x1: float, y1: float) -> None:
        largo = math.hypot(x1 - x0, y1 - y0)
        ux = (x1 - x0) / largo
        uy = (y1 - y0) / largo
        pos = 0.0
        while pos < largo:
            fin = min(pos + PANEL_DASH, largo)
            piezas.append(sen._trazo([
                (x0 + ux * pos, y0 + uy * pos),
                (x0 + ux * fin, y0 + uy * fin),
            ], PANEL_GROSOR))
            pos = fin + PANEL_GAP

    lado(PANEL_X0, PANEL_Y0, PANEL_X1, PANEL_Y0)
    lado(PANEL_X1, PANEL_Y0, PANEL_X1, PANEL_Y1)
    lado(PANEL_X1, PANEL_Y1, PANEL_X0, PANEL_Y1)
    lado(PANEL_X0, PANEL_Y1, PANEL_X0, PANEL_Y0)
    return base._solo_poligonos(unary_union(piezas))


def _texto_una_linea(nombre: str, font, glyphSet, hmtx,
                     unidades_por_em: float) -> Tuple[Polygon, float]:
    poligono, _ = sen._texto(nombre, ALTO_PALABRA, ANCHO_PALABRA,
                             (ANCHO * 0.5, sen.Y_PALABRA), font, glyphSet, hmtx,
                             unidades_por_em)
    alto_letra = poligono.bounds[3] - poligono.bounds[1]
    return poligono, alto_letra


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
        MAX_ALTO_DOS_LINEAS,
        ANCHO_PALABRA / naturales[0][1],
        ANCHO_PALABRA / naturales[1][1],
    )
    if alto_letra <= 0:
        raise base.ErrorStencil("No se ha podido calcular el tamano del bloque.")

    bloque_alto = 2.0 * alto_letra + HUECO_LINEAS
    arriba = sen.Y_PALABRA + bloque_alto * 0.5
    piezas = []
    for i, (linea, _) in enumerate(zip(lineas, naturales)):
        centro_y = arriba - alto_letra * 0.5 - i * (alto_letra + HUECO_LINEAS)
        poligono, _ = sen._texto(linea, alto_letra, ANCHO_PALABRA,
                                 (ANCHO * 0.5, centro_y), font, glyphSet, hmtx,
                                 unidades_por_em)
        piezas.append(poligono)

    resultado = base._solo_poligonos(unary_union(piezas))
    if resultado is None:
        raise base.ErrorStencil("El bloque de dos lineas ha quedado vacio.")
    return resultado, alto_letra


def construir_cartel(cartel: Cartel, font, glyphSet, hmtx,
                     unidades_por_em: float):
    marca, _ = sen._texto(sen.MARCA, sen.ALTO_MARCA, 120.0,
                          (ANCHO * 0.5, sen.Y_MARCA), font, glyphSet, hmtx,
                          unidades_por_em)
    if len(cartel.lineas) == 1:
        nombre, alto_letra = _texto_una_linea(
            cartel.lineas[0], font, glyphSet, hmtx, unidades_por_em
        )
    else:
        nombre, alto_letra = _texto_dos_lineas(
            cartel.lineas, font, glyphSet, hmtx, unidades_por_em
        )

    piezas = [marca, sen._subrayado(), nombre]
    if cartel.pie:
        pie, _ = sen._texto(cartel.pie, sen.ALTO_PIE, sen.ANCHO_PIE,
                            (ANCHO * 0.5, sen.Y_PIE), font, glyphSet, hmtx,
                            unidades_por_em)
        piezas.append(pie)
    if cartel.panel_libre:
        piezas.append(_panel_guia())
    else:
        piezas.append(icono_trail())
    piezas.append(sen._slashes())

    huecos = unary_union(piezas)
    huecos = base._solo_poligonos(huecos.buffer(0))
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


def _generar(cartel: Cartel, salida: Path, font, glyphSet, hmtx,
             unidades_por_em: float) -> None:
    solido, huecos, puentes, alto_letra, caja = construir_cartel(
        cartel, font, glyphSet, hmtx, unidades_por_em
    )

    print()
    print("=" * 68)
    print(f"Cartello: {sen.MARCA} / {cartel.nombre}")
    print(f"Lineas: {' / '.join(cartel.lineas)}")
    print(f"Alto de letra: {alto_letra:.3f} mm")
    print(f"Caja del diseno: {caja[2]-caja[0]:.3f} x {caja[3]-caja[1]:.3f} mm")
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
    if puentes == 0:
        print("  Puentes anadidos: 0 (los puentes ya vienen en la fuente)")
    else:
        print(f"  Puentes anadidos: {puentes} (ancho {ANCHO_PUENTE:.2f} mm)")
    print("  Malla: estanca, una sola pieza, sin triangulos degenerados")


def main() -> int:
    try:
        if ANCHO <= 2 * MARGEN or ALTO <= 2 * MARGEN:
            raise base.ErrorStencil("ANCHO/ALTO deben ser mayores que 2*MARGEN.")
        if not CARTELES:
            raise base.ErrorStencil("CARTELES esta vacio.")

        archivos = [c.archivo for c in CARTELES]
        if len(set(archivos)) != len(archivos):
            raise base.ErrorStencil("Hay nombres de archivo repetidos.")

        ruta_fuente, familia = base._resolver_fuente(base.FUENTE)
        print(f"Fuente: {ruta_fuente}")
        print(f"Familia: {familia}")

        font = base._abrir_fuente(ruta_fuente, familia)
        fallos = []
        try:
            unidades_por_em = float(font["head"].unitsPerEm)
            glyphSet = font.getGlyphSet()
            hmtx = font["hmtx"]

            base_dir = Path(__file__).resolve().parent.parent / "stl" / "cartelli"
            base_dir.mkdir(parents=True, exist_ok=True)
            for cartel in CARTELES:
                salida = base_dir / cartel.archivo
                try:
                    _generar(cartel, salida, font, glyphSet, hmtx, unidades_por_em)
                except base.ErrorStencil as exc:
                    print()
                    print(f"ERROR en {cartel.archivo}: {exc}")
                    fallos.append((cartel.archivo, str(exc)))
        finally:
            font.close()

        print()
        if fallos:
            print(f"Terminato con {len(fallos)} errore/i su {len(CARTELES)} cartelli.")
            for archivo, mensaje in fallos:
                print(f"  - {archivo}: {mensaje}")
            return 1

        print(f"Pronto: {len(CARTELES)} cartelli generati in {base_dir}")
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
