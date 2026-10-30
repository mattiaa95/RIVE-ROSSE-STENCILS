#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera segnali-stencil de 190 x 190 x 0,5 mm para passaggi tecnici:
DROP, SALTO y RIPIDO. Usa la misma fuente stencil que los stencils de trail.

Salida en stl/segnali/passaggi_tecnici:
    drop.stl
    salto.stl
    ripido.stl
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Sequence, Tuple

import trimesh
import generare_stencil as base
from shapely import affinity
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

ANCHO = 190.0
ALTO = 190.0
GROSOR = 0.5
MARGEN = 8.0
ANCHO_PUENTE = 2.4
REFORZAR_PUENTES = False

base.ANCHO = ANCHO
base.ALTO = ALTO
base.GROSOR = GROSOR
base.MARGEN = MARGEN

MARCA = "RIVE ROSSE"
Y_MARCA = 174.0
ALTO_MARCA = 11.0

Y_SUBRAYADO = 163.0
ANCHO_SUBRAYADO = 96.0
GROSOR_SUBRAYADO = 2.8

Y_PALABRA = 128.0
ALTO_PALABRA = 44.0
ANCHO_PALABRA = 164.0

Y_PIE = 37.0
ALTO_PIE = 9.0
ANCHO_PIE = 150.0

Y_SLASH = 21.0
LARGO_SLASH = 14.0
GROSOR_SLASH = 4.0
SEPARACION_SLASH = 20.0
ANGULO_SLASH = math.radians(60.0)


@dataclass
class Senal:
    palabra: str
    pie: str
    archivo: str
    icono: Callable[[], Polygon]


def _trazo(puntos: Sequence[Tuple[float, float]], ancho: float) -> Polygon:
    linea = LineString(puntos)
    return base._solo_poligonos(
        linea.buffer(ancho * 0.5, cap_style="round", join_style="round")
    )


def _flecha(puntos: Sequence[Tuple[float, float]], ancho: float,
            largo_punta: float, ancho_punta: float) -> Polygon:
    punta = puntos[-1]
    anterior = puntos[-2]
    dx = punta[0] - anterior[0]
    dy = punta[1] - anterior[1]
    norma = math.hypot(dx, dy)
    if norma < 1.0e-9:
        raise base.ErrorStencil("La flecha tiene longitud cero.")

    ux, uy = dx / norma, dy / norma
    bx = punta[0] - ux * largo_punta
    by = punta[1] - uy * largo_punta
    px, py = -uy, ux

    cabeza = Polygon([
        punta,
        (bx + px * ancho_punta * 0.5, by + py * ancho_punta * 0.5),
        (bx - px * ancho_punta * 0.5, by - py * ancho_punta * 0.5),
    ])
    cuerpo = _trazo(list(puntos[:-1]) + [(bx, by)], ancho)
    return base._solo_poligonos(unary_union([cuerpo, cabeza]))


def _bezier(p0, p1, p2, p3, pasos: int = 64) -> List[Tuple[float, float]]:
    puntos: List[Tuple[float, float]] = []
    for i in range(pasos + 1):
        t = i / pasos
        u = 1.0 - t
        x = (u ** 3) * p0[0] + 3 * (u ** 2) * t * p1[0] + 3 * u * (t ** 2) * p2[0] + (t ** 3) * p3[0]
        y = (u ** 3) * p0[1] + 3 * (u ** 2) * t * p1[1] + 3 * u * (t ** 2) * p2[1] + (t ** 3) * p3[1]
        puntos.append((x, y))
    return puntos


def _icono_drop() -> Polygon:
    repisa = _trazo([(54.0, 96.0), (136.0, 96.0)], 6.0)
    flecha = _flecha([(95.0, 96.0), (95.0, 57.0)], 7.0, 11.0, 26.0)
    suelo = _trazo([(78.0, 50.5), (112.0, 50.5)], 4.0)
    veloces = unary_union([
        _trazo([(66.0, 80.0), (58.0, 72.0)], 4.0),
        _trazo([(124.0, 80.0), (132.0, 72.0)], 4.0),
    ])
    return base._solo_poligonos(unary_union([repisa, flecha, suelo, veloces]))


def _icono_salto() -> Polygon:
    arco = _bezier(
        (52.0, 64.0),
        (64.0, 110.0),
        (126.0, 110.0),
        (138.0, 60.0),
    )
    flecha = _flecha(arco, 6.5, 11.0, 24.0)
    suelo_izq = _trazo([(44.0, 50.5), (58.0, 50.5)], 4.0)
    suelo_der = _trazo([(132.0, 50.5), (146.0, 50.5)], 4.0)
    return base._solo_poligonos(unary_union([flecha, suelo_izq, suelo_der]))


def _icono_ripido() -> Polygon:
    flecha = _flecha([(64.0, 98.0), (104.0, 66.0), (112.0, 58.0)],
                     7.0, 11.0, 24.0)
    suelo = _trazo([(106.0, 48.5), (140.0, 48.5)], 4.0)
    veloces = unary_union([
        _trazo([(62.0, 86.0), (86.0, 72.0)], 4.5),
        _trazo([(86.0, 94.0), (110.0, 80.0)], 4.5),
    ])
    return base._solo_poligonos(unary_union([flecha, suelo, veloces]))


SENALES = [
    Senal("DROP", "PERICOLO", "drop.stl", _icono_drop),
    Senal("SALTO", "ATTENZIONE", "salto.stl", _icono_salto),
    Senal("RIPIDO", "TRATTO TECNICO", "ripido.stl", _icono_ripido),
]


def _texto(texto: str, alto_objetivo: float, ancho_maximo: float,
           centro: Tuple[float, float], font, glyphSet, hmtx,
           unidades_por_em: float) -> Tuple[Polygon, float]:
    poligono = base._texto_a_poligono(texto, font, glyphSet, hmtx)
    minx, miny, maxx, maxy = poligono.bounds
    ancho = maxx - minx
    alto = maxy - miny
    factor = min(alto_objetivo / alto, ancho_maximo / ancho)
    poligono = affinity.scale(poligono, xfact=factor, yfact=factor, origin=(0.0, 0.0))
    minx, miny, maxx, maxy = poligono.bounds
    poligono = affinity.translate(
        poligono,
        xoff=centro[0] - (minx + maxx) * 0.5,
        yoff=centro[1] - (miny + maxy) * 0.5,
    )
    return poligono, factor * unidades_por_em


def _slashes() -> Polygon:
    piezas = []
    for i in (-1, 0, 1):
        cx = ANCHO * 0.5 + i * SEPARACION_SLASH
        dx = math.cos(ANGULO_SLASH) * LARGO_SLASH * 0.5
        dy = math.sin(ANGULO_SLASH) * LARGO_SLASH * 0.5
        piezas.append(_trazo([(cx - dx, Y_SLASH - dy), (cx + dx, Y_SLASH + dy)],
                             GROSOR_SLASH))
    return base._solo_poligonos(unary_union(piezas))


def _subrayado() -> Polygon:
    return _trazo([
        (ANCHO * 0.5 - ANCHO_SUBRAYADO * 0.5, Y_SUBRAYADO),
        (ANCHO * 0.5 + ANCHO_SUBRAYADO * 0.5, Y_SUBRAYADO),
    ], GROSOR_SUBRAYADO)


def construir_diseno(senal: Senal, font, glyphSet, hmtx,
                     unidades_por_em: float):
    marca, _ = _texto(MARCA, ALTO_MARCA, 120.0, (ANCHO * 0.5, Y_MARCA),
                      font, glyphSet, hmtx, unidades_por_em)
    palabra, tamano_palabra = _texto(
        senal.palabra, ALTO_PALABRA, ANCHO_PALABRA,
        (ANCHO * 0.5, Y_PALABRA), font, glyphSet, hmtx, unidades_por_em
    )
    pie, _ = _texto(senal.pie, ALTO_PIE, ANCHO_PIE,
                    (ANCHO * 0.5, Y_PIE), font, glyphSet, hmtx, unidades_por_em)

    huecos = unary_union([
        marca,
        _subrayado(),
        palabra,
        senal.icono(),
        pie,
        _slashes(),
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
    if REFORZAR_PUENTES:
        solido, refuerzos = base._reforzar_puentes(solido, ANCHO_PUENTE)
        puentes += refuerzos

    return solido, huecos, puentes, tamano_palabra, b


def _crear_malla(solido: Polygon):
    try:
        malla = trimesh.creation.extrude_polygon(
            solido, height=GROSOR, engine="triangle"
        )
    except Exception as exc:
        raise base.ErrorStencil(f"No se pudo extruir la placa: {exc}")

    if malla.volume < 0:
        malla.invert()

    malla.apply_translation([0.0, 0.0, -float(malla.bounds[0][2])])
    if not malla.is_winding_consistent:
        malla.fix_normals()
    return malla


def _generar(senal: Senal, salida: Path, font, glyphSet, hmtx,
             unidades_por_em: float) -> None:
    solido, huecos, puentes, tamano_palabra, caja = construir_diseno(
        senal, font, glyphSet, hmtx, unidades_por_em
    )

    print()
    print("=" * 68)
    print(f"Segnale: {MARCA} / {senal.palabra} / {senal.pie}")
    print(f"Tamano de palabra: {tamano_palabra:.3f} mm")
    print(f"Caja del diseno: {caja[2]-caja[0]:.3f} x {caja[3]-caja[1]:.3f} mm")
    print(f"Margenes: izq {caja[0]:.3f}, der {ANCHO-caja[2]:.3f}, "
          f"abajo {caja[1]:.3f}, arriba {ALTO-caja[3]:.3f} mm")
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
        print("  Puentes anadidos: 0 (los puentes troquelados ya vienen en la fuente)")
    else:
        print(f"  Puentes/refuerzos anadidos: {puentes} (ancho {ANCHO_PUENTE:.2f} mm)")
    print("  Malla: estanca, una sola pieza, sin triangulos degenerados")


def main() -> int:
    try:
        if ANCHO <= 2 * MARGEN or ALTO <= 2 * MARGEN:
            raise base.ErrorStencil("ANCHO/ALTO deben ser mayores que 2*MARGEN.")

        ruta_fuente, familia = base._resolver_fuente(base.FUENTE)
        print(f"Fuente: {ruta_fuente}")
        print(f"Familia: {familia}")

        font = base._abrir_fuente(ruta_fuente, familia)
        fallos = []
        try:
            if "head" not in font or "hmtx" not in font:
                raise base.ErrorStencil("La fuente no tiene metricas tipograficas validas.")
            unidades_por_em = float(font["head"].unitsPerEm)
            glyphSet = font.getGlyphSet()
            hmtx = font["hmtx"]

            base_dir = Path(__file__).resolve().parent.parent / "stl" / "segnali" / "passaggi_tecnici"
            base_dir.mkdir(parents=True, exist_ok=True)
            for senal in SENALES:
                salida = base_dir / senal.archivo
                try:
                    _generar(senal, salida, font, glyphSet, hmtx, unidades_por_em)
                except base.ErrorStencil as exc:
                    print()
                    print(f"ERROR en {senal.archivo}: {exc}")
                    fallos.append((senal.archivo, str(exc)))
        finally:
            font.close()

        print()
        if fallos:
            print(f"Terminato con {len(fallos)} errore/i su {len(SENALES)} segnali.")
            for archivo, mensaje in fallos:
                print(f"  - {archivo}: {mensaje}")
            return 1

        print(f"Pronto: {len(SENALES)} segnali generati in {base_dir}")
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
