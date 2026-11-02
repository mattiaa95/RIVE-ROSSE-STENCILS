#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera plantillas de grafiti (stencil) de 190 x 190 x 0,5 mm con los nombres
de trail en dos lineas: TRAIL arriba y el nombre del trail abajo.

Salida:
    stencil_trail_m41.stl
    stencil_trail_m41_bis.stl
    stencil_trail_la_pignola.stl
    stencil_trail_vergnago.stl
    stencil_trail_m33.stl       (mallas cerradas, listas para laminador)

Dependencias:
    python3 -m pip install --user -r requirements.txt

Incluye Saira Stencil One (OFL), una stencil gruesa. El pie de la L se reconecta
porque esta fuente lo trae separado y parecia un punto. Tambien puedes usar la
clasica "Stencil" instalando la familia, o cambiar FUENTE por otra stencil.
Nunca se sustituye por Arial ni por una fuente normal.
"""

import os
import sys
import math
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Sequence, Set, Tuple

# ---------------------------------------------------------------------------
# PARAMETROS EDITABLES
# ---------------------------------------------------------------------------

ANCHO = 190.0          # mm
ALTO = 190.0           # mm
GROSOR = 0.5           # mm
MARGEN = 8.0          # mm, minimo en los cuatro bordes
# Stencil incluida. Alternativa mas fina: "../font/AllertaStencil-Regular.ttf".
FUENTE = str(Path(__file__).resolve().parent.parent / "font" / "SairaStencilOne-Regular.ttf")

# Un diseno por linea: (texto superior, texto inferior, archivo STL).
DISENOS = [
    ("TRAIL", "M41", "stencil_trail_m41.stl"),
    ("TRAIL", "M41 BIS", "stencil_trail_m41_bis.stl"),
    ("TRAIL", "LA PIGNOLA", "stencil_trail_la_pignola.stl"),
    ("TRAIL", "VERGNAGO", "stencil_trail_vergnago.stl"),
    ("TRAIL", "M33", "stencil_trail_m33.stl"),
]

SEPARACION_EM = 0.30       # separacion entre lineas, en fraccion del tamano de fuente
ANCHO_PUENTE = 2.20        # mm, ancho minimo de los puentes anadidos automaticamente
EXPANSION_TRAZO = 0.0      # mm, engorda mas los trazos si hace falta
TOLERANCIA_CURVA = 0.20    # unidades de fuente para aplanar curvas
TOLERANCIA_VALIDACION = 1.0e-4

EPS = 1.0e-7

# ---------------------------------------------------------------------------
# COMPROBACION DE DEPENDENCIAS
# ---------------------------------------------------------------------------

FALTAN = []

try:
    import numpy as np
except ImportError:
    FALTAN.append("numpy")

try:
    from fontTools.pens.basePen import BasePen
    from fontTools.ttLib import TTFont, TTCollection
except ImportError:
    FALTAN.append("fonttools")

try:
    from shapely import affinity
    from shapely.geometry import LineString, Polygon, box
    from shapely.ops import nearest_points, unary_union
except ImportError:
    FALTAN.append("shapely")

try:
    import trimesh
except ImportError:
    FALTAN.append("trimesh")

try:
    import manifold3d  # noqa: F401  (extrusion solida con agujeros)
except ImportError:
    FALTAN.append("manifold3d")

try:
    import scipy  # noqa: F401  (trimesh lo necesita para separar piezas)
except ImportError:
    FALTAN.append("scipy")

if FALTAN:
    print("ERROR: faltan dependencias de Python:")
    print("  " + ", ".join(FALTAN))
    print()
    print("Instalalas con:")
    print("  python3 -m pip install --user -r requirements.txt")
    sys.exit(1)


class ErrorStencil(Exception):
    """Error controlado con un mensaje comprensible para el usuario."""


# ---------------------------------------------------------------------------
# LOCALIZACION Y CARGA DE LA FUENTE
# ---------------------------------------------------------------------------

def _agregar_nombres(font: TTFont, nombres: Set[str]) -> None:
    """Anade a 'nombres' las familias y nombres completos de una fuente."""
    if "name" not in font:
        return
    for registro in font["name"].names:
        if registro.nameID not in (1, 4, 6, 16):
            continue
        try:
            texto = registro.toUnicode().strip()
        except Exception:
            continue
        if texto:
            nombres.add(texto)


def _nombres_de_fuente(ruta: Path) -> Set[str]:
    """Lee los nombres de todos los tipos de letra de un archivo .ttf/.otf/.ttc."""
    nombres: Set[str] = set()
    sufijo = ruta.suffix.lower()

    if sufijo in (".ttc", ".otc"):
        coleccion = TTCollection(str(ruta), lazy=True)
        try:
            for font in coleccion.fonts:
                _agregar_nombres(font, nombres)
        finally:
            for font in coleccion.fonts:
                try:
                    font.close()
                except Exception:
                    pass
    else:
        font = TTFont(str(ruta), lazy=True)
        try:
            _agregar_nombres(font, nombres)
        finally:
            font.close()

    return nombres


def _directorios_de_fuentes() -> List[Path]:
    """Devuelve los directorios habituales de fuentes del sistema."""
    casa = Path.home()
    directorios = [
        casa / "Library" / "Fonts",
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts"),
        Path("/System/Library/Fonts/Supplemental"),
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        casa / ".fonts",
        casa / ".local" / "share" / "fonts",
    ]

    if sys.platform.startswith("win"):
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        directorios += [windir / "Fonts", casa / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts"]

    vistos = set()
    resultado = []
    for directorio in directorios:
        try:
            clave = str(directorio.resolve())
        except Exception:
            continue
        if directorio.is_dir() and clave not in vistos:
            vistos.add(clave)
            resultado.append(directorio)
    return resultado


def _archivos_de_fuentes() -> List[Path]:
    archivos: List[Path] = []
    vistos = set()
    extensiones = ("*.ttf", "*.otf", "*.ttc", "*.otc")
    for directorio in _directorios_de_fuentes():
        for extension in extensiones:
            for ruta in directorio.rglob(extension):
                try:
                    clave = str(ruta.resolve())
                except Exception:
                    continue
                if ruta.is_file() and clave not in vistos:
                    vistos.add(clave)
                    archivos.append(ruta)
    return archivos


def _buscar_por_fontconfig(nombre_familia: str) -> Optional[Path]:
    """Consulta fontconfig y solo acepta una coincidencia real de familia."""
    ejecutable = shutil.which("fc-match")
    if not ejecutable:
        return None

    try:
        resultado = subprocess.run(
            [ejecutable, "-f", "%{file}\n", nombre_familia],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except Exception:
        return None

    objetivo = nombre_familia.casefold()
    for linea in resultado.stdout.splitlines():
        ruta = Path(linea.strip())
        if not ruta.is_file():
            continue
        try:
            nombres = {n.casefold() for n in _nombres_de_fuente(ruta)}
        except Exception:
            continue
        if objetivo in nombres:
            return ruta
    return None


def _resolver_fuente(valor: str) -> Tuple[Path, str]:
    """
    Devuelve (ruta, familia real). Si 'valor' es una ruta, se usa esa ruta.
    Si es una familia, se exige que la familia exista realmente; no se acepta
    el sustituto que fontconfig devuelve cuando no encuentra la fuente.
    """
    texto = str(valor).strip().strip('"').strip("'")
    if not texto:
        raise ErrorStencil("El parametro FUENTE esta vacio.")

    ruta_directa = Path(texto).expanduser()
    if not ruta_directa.is_absolute() and not ruta_directa.is_file():
        junto_al_script = Path(__file__).resolve().parent / ruta_directa
        if junto_al_script.is_file():
            ruta_directa = junto_al_script

    if ruta_directa.is_file():
        nombres = _nombres_de_fuente(ruta_directa)
        familias = " ".join(nombres).casefold()
        if "stencil" not in familias and "stencil" not in ruta_directa.name.casefold():
            raise ErrorStencil(
                "La ruta indicada en FUENTE no parece una fuente stencil:\n"
                f"  {ruta_directa}\n"
                "Indica un .ttf/.otf/.ttc stencil autentico."
            )
        familia = sorted(nombres)[0] if nombres else ruta_directa.name
        return ruta_directa, familia

    if any(separador in texto for separador in ("/", "\\")):
        raise ErrorStencil(f"No existe el archivo indicado en FUENTE:\n  {ruta_directa}")

    objetivo = texto.casefold()
    ruta = _buscar_por_fontconfig(texto)
    if ruta is not None:
        nombres = _nombres_de_fuente(ruta)
        for nombre in nombres:
            if nombre.casefold() == objetivo:
                return ruta, nombre

    archivos = _archivos_de_fuentes()
    archivos.sort(key=lambda p: (0 if "stencil" in p.name.casefold() else 1, str(p)))

    familias_stencil: Set[str] = set()
    for ruta in archivos:
        try:
            nombres = _nombres_de_fuente(ruta)
        except Exception:
            continue
        for nombre in nombres:
            if "stencil" in nombre.casefold():
                if not nombre.startswith("."):
                    familias_stencil.add(nombre)
            if nombre.casefold() == objetivo:
                return ruta, nombre

    pistas = ""
    if familias_stencil:
        pistas = (
            "\n\nFuentes stencil encontradas en el sistema:\n  "
            + "\n  ".join(sorted(familias_stencil))
            + "\nPuedes usar una de ellas cambiando FUENTE o pasar su ruta completa."
        )

    raise ErrorStencil(
        f"No se ha encontrado la fuente stencil '{texto}'.\n\n"
        "Opciones:\n"
        "  1. Instala una fuente stencil autentica con esa familia.\n"
        "     En macOS: doble clic en el .ttf y pulsa 'Instalar fuente'.\n"
        "     En Windows: clic derecho > Instalar.\n"
        "     En Linux: copiala a ~/.local/share/fonts y ejecuta fc-cache -f.\n"
        "  2. Cambia FUENTE por la ruta completa al archivo .ttf/.otf/.ttc, por ejemplo:\n"
        '     FUENTE = "/ruta/a/Stencil.ttf"\n'
        "  3. O cambia FUENTE por otra familia stencil ya instalada.\n"
        "No se usara Arial ni ninguna fuente convencional en silencio." + pistas
    )


def _abrir_fuente(ruta: Path, familia_buscada: Optional[str] = None) -> TTFont:
    """Abre una fuente; si es una coleccion .ttc elige la cara stencil adecuada."""
    sufijo = ruta.suffix.lower()
    if sufijo not in (".ttc", ".otc"):
        return TTFont(str(ruta), lazy=False)

    coleccion = TTCollection(str(ruta), lazy=True)
    indice = 0
    objetivo = (familia_buscada or "").casefold()
    face_names: Set[str] = set()
    try:
        for i, font in enumerate(coleccion.fonts):
            nombres = set()
            _agregar_nombres(font, nombres)
            minusculas = {n.casefold() for n in nombres}
            if objetivo and objetivo in minusculas:
                indice = i
                break
            if any("stencil" in n.casefold() for n in minusculas):
                indice = i
                break
        _agregar_nombres(coleccion.fonts[indice], face_names)
    finally:
        for font in coleccion.fonts:
            try:
                font.close()
            except Exception:
                pass

    if not face_names:
        face_names = {familia_buscada or ruta.name}
    return TTFont(str(ruta), fontNumber=indice, lazy=False)


# ---------------------------------------------------------------------------
# VECTORIZACION DEL TEXTO
# ---------------------------------------------------------------------------

class _PlumaContornos(BasePen):
    """Convierte los contornos de un glifo en listas de puntos aplanados."""

    def __init__(self, glyphSet, tolerancia: float):
        super().__init__(glyphSet)
        self.tolerancia = tolerancia
        self.contornos: List[List[Tuple[float, float]]] = []
        self.actual: List[Tuple[float, float]] = []

    def _punto(self, p) -> Tuple[float, float]:
        return (float(p[0]), float(p[1]))

    def _terminar_contorno(self) -> None:
        if len(self.actual) >= 3:
            puntos = self.actual
            if puntos[0] == puntos[-1]:
                puntos = puntos[:-1]
            if len(puntos) >= 3:
                self.contornos.append(puntos)
        self.actual = []

    def _moveTo(self, p) -> None:
        self._terminar_contorno()
        self.actual = [self._punto(p)]

    def _lineTo(self, p) -> None:
        punto = self._punto(p)
        if punto != self.actual[-1]:
            self.actual.append(punto)

    def _curva_plana(self, p0, p1, p2, p3) -> bool:
        x0, y0 = p0
        x3, y3 = p3
        dx = x3 - x0
        dy = y3 - y0
        longitud = math.hypot(dx, dy)
        if longitud < EPS:
            return max(math.hypot(p1[0] - x0, p1[1] - y0),
                       math.hypot(p2[0] - x0, p2[1] - y0)) <= self.tolerancia
        d1 = abs((p1[0] - x0) * dy - (p1[1] - y0) * dx) / longitud
        d2 = abs((p2[0] - x0) * dy - (p2[1] - y0) * dx) / longitud
        return max(d1, d2) <= self.tolerancia

    @staticmethod
    def _medio(a, b):
        return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5)

    def _aplanar_cubica(self, p0, p1, p2, p3, profundidad: int) -> None:
        if profundidad >= 14 or self._curva_plana(p0, p1, p2, p3):
            self.actual.append(p3)
            return

        p01 = self._medio(p0, p1)
        p12 = self._medio(p1, p2)
        p23 = self._medio(p2, p3)
        p012 = self._medio(p01, p12)
        p123 = self._medio(p12, p23)
        p0123 = self._medio(p012, p123)

        self._aplanar_cubica(p0, p01, p012, p0123, profundidad + 1)
        self._aplanar_cubica(p0123, p123, p23, p3, profundidad + 1)

    def _curveToOne(self, p1, p2, p3) -> None:
        p0 = self.actual[-1]
        self._aplanar_cubica(p0, self._punto(p1), self._punto(p2),
                             self._punto(p3), 0)

    def _closePath(self) -> None:
        self._terminar_contorno()

    def _endPath(self) -> None:
        self._terminar_contorno()


def _solo_poligonos(geometria):
    """Extrae la parte poligonal valida de una geometria de Shapely."""
    if geometria is None or geometria.is_empty:
        return None
    if geometria.geom_type == "Polygon":
        return geometria if geometria.area > EPS else None
    if geometria.geom_type in ("MultiPolygon", "GeometryCollection"):
        partes = [
            p for p in geometria.geoms
            if p.geom_type == "Polygon" and p.area > EPS
        ]
        if not partes:
            return None
        resultado = unary_union(partes)
        return resultado if not resultado.is_empty else None
    return None


def _contorno_a_poligono(puntos: Sequence[Tuple[float, float]]):
    if len(puntos) < 3:
        return None
    try:
        poligono = Polygon(puntos)
        if not poligono.is_valid:
            poligono = poligono.buffer(0)
    except Exception:
        return None
    return _solo_poligonos(poligono)


def _poligono_de_glifo(glifo, glyphSet) -> Optional[Polygon]:
    """Obtiene el contorno relleno de un glifo usando la regla par-impar."""
    pluma = _PlumaContornos(glyphSet, TOLERANCIA_CURVA)
    glifo.draw(pluma)

    resultado = None
    for contorno in pluma.contornos:
        poligono = _contorno_a_poligono(contorno)
        if poligono is None:
            continue
        if resultado is None:
            resultado = poligono
        else:
            resultado = resultado.symmetric_difference(poligono)
            resultado = _solo_poligonos(resultado)
            if resultado is None:
                return None
    return _solo_poligonos(resultado)


def _reconectar_pie_de_L(poligono: Polygon) -> Polygon:
    """
    Algunas stencil (por ejemplo Saira Stencil One) separan el pie de la L
    con un corte tan grande que la letra parece 'L.' en el stencil. Si se
    detectan dos piezas con forma de pie y tallo, se rellena solo ese corte.
    """
    partes = sorted(_partes_poligonales(poligono),
                    key=lambda p: p.area, reverse=True)
    if len(partes) != 2:
        return poligono

    a, b = partes
    alto_a = a.bounds[3] - a.bounds[1]
    alto_b = b.bounds[3] - b.bounds[1]
    tallo, pie = (a, b) if alto_a >= alto_b else (b, a)
    alto_tallo = tallo.bounds[3] - tallo.bounds[1]
    alto_pie = pie.bounds[3] - pie.bounds[1]

    if alto_pie <= 0 or alto_tallo <= 0:
        return poligono
    if alto_pie >= alto_tallo * 0.5:
        return poligono
    if pie.bounds[0] <= tallo.bounds[2]:
        return poligono
    if abs(pie.bounds[1] - tallo.bounds[1]) > alto_tallo * 0.02:
        return poligono

    hueco = pie.bounds[0] - tallo.bounds[2]
    if hueco <= 0 or hueco > alto_tallo * 0.15:
        return poligono

    solape = max(hueco * 0.25, alto_tallo * 0.01)
    relleno = box(
        tallo.bounds[2] - solape,
        min(tallo.bounds[1], pie.bounds[1]),
        pie.bounds[0] + solape,
        pie.bounds[3] + solape,
    )
    unido = _solo_poligonos(unary_union([poligono, relleno]))
    return unido if unido is not None else poligono


def _texto_a_poligono(texto: str, font: TTFont, glyphSet, hmtx) -> Polygon:
    """Compone una linea de texto como un unico poligono (puede tener varias partes)."""
    if not texto or not texto.strip():
        raise ErrorStencil("Una de las lineas de texto esta vacia.")
    if "\n" in texto or "\r" in texto:
        raise ErrorStencil("Cada linea debe ir en su propio parametro, sin saltos de linea.")

    cmap = font.getBestCmap()
    if not cmap:
        raise ErrorStencil("La fuente no tiene una tabla cmap utilizable.")

    faltantes = sorted({c for c in texto if not c.isspace() and ord(c) not in cmap})
    if faltantes:
        raise ErrorStencil(
            "La fuente no contiene estos caracteres: " + " ".join(faltantes)
        )

    x = 0.0
    piezas = []
    for caracter in texto:
        nombre_glifo = cmap.get(ord(caracter))
        if nombre_glifo is None:
            if caracter.isspace():
                continue
            raise ErrorStencil(f"Caracter no disponible en la fuente: {caracter!r}")

        avance = float(hmtx[nombre_glifo][0])
        if not caracter.isspace():
            try:
                glifo = glyphSet[nombre_glifo]
            except KeyError:
                raise ErrorStencil(f"Glifo no encontrado en la fuente: {nombre_glifo}")
            poligono = _poligono_de_glifo(glifo, glyphSet)
            if poligono is not None:
                if caracter == "L":
                    poligono = _reconectar_pie_de_L(poligono)
                piezas.append(affinity.translate(poligono, xoff=x))
        x += avance

    if not piezas:
        raise ErrorStencil(f"El texto {texto!r} no ha generado geometria.")

    resultado = _solo_poligonos(unary_union(piezas))
    if resultado is None:
        raise ErrorStencil(f"El texto {texto!r} ha generado geometria vacia.")
    return resultado


# ---------------------------------------------------------------------------
# DISPOSICION, PLACA Y PUENTES
# ---------------------------------------------------------------------------

@dataclass
class Disposicion:
    linea_1: Polygon
    linea_2: Polygon
    tamano_fuente_mm: float
    separacion_mm: float
    alto_bloque_mm: float
    caja: Tuple[float, float, float, float]


def _disponer_texto(linea_1: Polygon, linea_2: Polygon,
                    unidades_por_em: float,
                    expansion: float = 0.0) -> Disposicion:
    """Escala y centra las dos lineas respetando los margenes."""
    b1 = linea_1.bounds
    b2 = linea_2.bounds
    ancho_1, alto_1 = b1[2] - b1[0], b1[3] - b1[1]
    ancho_2, alto_2 = b2[2] - b2[0], b2[3] - b2[1]

    ancho_util = ANCHO - 2.0 * MARGEN - 2.0 * expansion - EPS
    alto_util = ALTO - 2.0 * MARGEN - 2.0 * expansion - EPS
    if ancho_util <= 0 or alto_util <= 0:
        raise ErrorStencil("Los margenes no dejan espacio util en la placa.")

    separacion_unidades = SEPARACION_EM * unidades_por_em
    factor_ancho = ancho_util / max(ancho_1, ancho_2)
    factor_alto = alto_util / (alto_1 + alto_2 + separacion_unidades)
    factor = min(factor_ancho, factor_alto)
    if factor <= 0:
        raise ErrorStencil("No se ha podido calcular un tamano de fuente positivo.")

    tamano_fuente = factor * unidades_por_em
    separacion = separacion_unidades * factor
    alto_bloque = (alto_1 + alto_2) * factor + separacion

    if alto_bloque > alto_util + TOLERANCIA_VALIDACION:
        raise ErrorStencil("El bloque de texto no cabe en el alto disponible.")

    arriba = (ALTO + alto_bloque) * 0.5
    abajo = arriba - alto_bloque

    def transformar(poligono: Polygon, bbox, y_superior: float) -> Polygon:
        left = (ANCHO - (bbox[2] - bbox[0]) * factor) * 0.5
        xoff = left - bbox[0] * factor
        yoff = y_superior - bbox[3] * factor
        escalado = affinity.scale(poligono, xfact=factor, yfact=factor,
                                  origin=(0.0, 0.0))
        return affinity.translate(escalado, xoff=xoff, yoff=yoff)

    linea_1_final = transformar(linea_1, b1, arriba)
    linea_2_final = transformar(linea_2, b2, arriba - alto_1 * factor - separacion)

    caja_final = unary_union([linea_1_final, linea_2_final]).bounds
    return Disposicion(
        linea_1=linea_1_final,
        linea_2=linea_2_final,
        tamano_fuente_mm=tamano_fuente,
        separacion_mm=separacion,
        alto_bloque_mm=alto_bloque,
        caja=caja_final,
    )


def _partes_poligonales(geometria) -> List[Polygon]:
    if geometria is None or geometria.is_empty:
        return []
    if geometria.geom_type == "Polygon":
        return [geometria]
    if geometria.geom_type in ("MultiPolygon", "GeometryCollection"):
        return [p for p in geometria.geoms if p.geom_type == "Polygon" and p.area > EPS]
    return []


def _barra_entre(punto_a, punto_b, ancho: float) -> Polygon:
    """Rectangulo de material que une dos puntos, con extremos ensanchados."""
    linea = LineString([punto_a, punto_b])
    barra = linea.buffer(ancho * 0.5, cap_style="square", join_style="mitre")
    return _solo_poligonos(barra)


def _conectar_islas(solido, ancho_puente: float) -> Tuple[Polygon, int]:
    """
    Si la placa menos el texto deja islas sueltas (por ejemplo, los huecos
    interiores de A o D), anade barras de material que las unen a la placa.
    Devuelve el solido conectado y el numero de puentes anadidos.
    """
    solido = _solo_poligonos(solido)
    if solido is None:
        raise ErrorStencil("La resta del texto ha dejado una placa vacia.")

    partes = sorted(_partes_poligonales(solido), key=lambda p: p.area, reverse=True)
    if len(partes) <= 1:
        return solido, 0

    principal = partes[0]
    islas = partes[1:]
    puentes = 0

    for isla in islas:
        interseccion = principal.intersection(isla)
        if not interseccion.is_empty and interseccion.area > EPS:
            principal = _solo_poligonos(unary_union([principal, isla]))
            if principal is None:
                raise ErrorStencil("No se pudo unir una isla a la placa.")
            continue

        punto_isla, punto_principal = nearest_points(isla, principal)
        barra = _barra_entre(punto_isla, punto_principal, ancho_puente)
        if barra is None:
            raise ErrorStencil("No se pudo crear un puente para una isla interior.")

        unido = _solo_poligonos(unary_union([principal, isla, barra]).buffer(0))
        if unido is None:
            raise ErrorStencil("El puente creado no ha producido geometria valida.")
        principal = unido
        puentes += 1

    if len(_partes_poligonales(principal)) != 1:
        raise ErrorStencil(
            "Quedan islas sueltas despues de anadir los puentes. "
            "Prueba una fuente stencil con puentes mas anchos o aumenta ANCHO_PUENTE."
        )

    return principal, puentes


def _reforzar_puentes(solido: Polygon, ancho_puente: float) -> Tuple[Polygon, int]:
    """
    Refuerza los puentes finos que ya trae la fuente. Para localizarlos se
    erosiona ligeramente la placa: los contrapunzones (interiores de A, D, etc.)
    que solo estaban sujetos por un puente demasiado fino quedan como islas.
    Despues se une cada una a la placa con una barra de ancho conocido.
    """
    radio_deteccion = ancho_puente * 0.50
    erosionado = solido.buffer(-radio_deteccion, join_style="mitre")
    partes = sorted(_partes_poligonales(erosionado), key=lambda p: p.area, reverse=True)

    if len(partes) <= 1:
        return solido, 0

    principal = partes[0]
    islas = partes[1:]
    refuerzos = 0
    resultado = solido

    for isla in islas:
        if isla.area <= EPS:
            continue
        try:
            punto_isla, punto_principal = nearest_points(isla, principal)
        except Exception:
            continue

        barra = _barra_entre(punto_isla, punto_principal, ancho_puente)
        if barra is None:
            continue

        unido = _solo_poligonos(unary_union([resultado, barra]).buffer(0))
        if unido is None:
            raise ErrorStencil("No se pudo reforzar un puente fino.")
        resultado = unido
        refuerzos += 1

    if len(_partes_poligonales(resultado)) != 1:
        raise ErrorStencil(
            "El refuerzo de puentes ha dejado piezas separadas. "
            "Aumenta ANCHO_PUENTE o usa una variante mas gruesa de la fuente."
        )

    return resultado, refuerzos


# ---------------------------------------------------------------------------
# CREACION Y VALIDACION DEL STL
# ---------------------------------------------------------------------------

def _contornos_manifold(solido: Polygon) -> List[np.ndarray]:
    """Convierte el solido en contornos cerrados con la orientacion correcta."""
    contornos: List[np.ndarray] = []
    for poligono in _partes_poligonales(solido):
        exterior = np.asarray(poligono.exterior.coords)[:-1]
        if not poligono.exterior.is_ccw:
            exterior = exterior[::-1]
        contornos.append(exterior)
        for interior in poligono.interiors:
            hueco = np.asarray(interior.coords)[:-1]
            if interior.is_ccw:
                hueco = hueco[::-1]
            contornos.append(hueco)
    return contornos


def _crear_malla(solido: Polygon):
    try:
        seccion = manifold3d.CrossSection(_contornos_manifold(solido))
        cuerpo = manifold3d.Manifold.extrude(seccion, float(GROSOR))
        # Elimina triangulos de area cero en bordes rectos alineados.
        cuerpo = cuerpo.simplify(1.0e-9)
        malla_manifold = cuerpo.to_mesh()
        malla = trimesh.Trimesh(
            vertices=np.asarray(malla_manifold.vert_properties)[:, :3],
            faces=np.asarray(malla_manifold.tri_verts),
            process=False,
        )
    except Exception as exc:
        raise ErrorStencil(f"No se pudo extruir la placa: {exc}")

    if malla.volume < 0:
        malla.invert()

    malla.apply_translation([0.0, 0.0, -float(malla.bounds[0][2])])
    if not malla.is_winding_consistent:
        malla.fix_normals()
    return malla


def _validar_2d(disp: Disposicion, solido: Polygon, texto: Polygon) -> None:
    tol = TOLERANCIA_VALIDACION + 1.0e-6

    minx, miny, maxx, maxy = texto.bounds
    if minx < MARGEN - tol or miny < MARGEN - tol:
        raise ErrorStencil("El texto invade el margen inferior/izquierdo.")
    if maxx > ANCHO - MARGEN + tol or maxy > ALTO - MARGEN + tol:
        raise ErrorStencil("El texto invade el margen superior/derecho.")
    if abs((minx + maxx) * 0.5 - ANCHO * 0.5) > tol:
        raise ErrorStencil("El texto no esta centrado horizontalmente.")
    if abs((miny + maxy) * 0.5 - ALTO * 0.5) > tol:
        raise ErrorStencil("El bloque de dos lineas no esta centrado verticalmente.")

    if disp.linea_1.bounds[1] <= disp.linea_2.bounds[3]:
        raise ErrorStencil("Las lineas se solapan o no estan en el orden correcto.")

    if texto.area <= 0:
        raise ErrorStencil("El texto no tiene area.")

    placa = Polygon([(0, 0), (ANCHO, 0), (ANCHO, ALTO), (0, ALTO)])
    if not placa.buffer(-tol).covers(texto):
        raise ErrorStencil("El texto no esta completamente dentro de la placa.")

    if solido is None or solido.is_empty:
        raise ErrorStencil("La placa resultante esta vacia.")


def _validar_malla(malla, area_solido: float) -> None:
    ext = malla.extents
    esperado = np.array([ANCHO, ALTO, GROSOR], dtype=float)
    if not np.allclose(ext, esperado, atol=1.0e-3, rtol=0.0):
        raise ErrorStencil(
            "Dimensiones incorrectas: "
            f"{ext[0]:.4f} x {ext[1]:.4f} x {ext[2]:.4f} mm "
            f"(esperado {ANCHO:.1f} x {ALTO:.1f} x {GROSOR:.1f})."
        )

    if len(malla.faces) == 0 or len(malla.vertices) == 0:
        raise ErrorStencil("La malla esta vacia.")
    if not malla.is_watertight:
        raise ErrorStencil("La malla no es estanca (watertight).")
    if not malla.is_winding_consistent:
        raise ErrorStencil("La malla tiene normales incoherentes.")
    if malla.volume <= 0:
        raise ErrorStencil("La malla tiene volumen no positivo.")
    if np.any(malla.area_faces <= 1.0e-10):
        raise ErrorStencil("La malla contiene triangulos degenerados.")

    partes = malla.split(only_watertight=False)
    if len(partes) != 1:
        raise ErrorStencil(
            f"La malla contiene {len(partes)} piezas separadas; debe ser una sola."
        )

    volumen_esperado = area_solido * GROSOR
    if not math.isclose(malla.volume, volumen_esperado,
                        rel_tol=1.0e-4, abs_tol=1.0e-4):
        raise ErrorStencil(
            "El volumen de la malla no coincide con la placa extruida "
            f"({malla.volume:.6f} vs {volumen_esperado:.6f} mm3)."
        )

    if malla.bounds[0][2] < -1.0e-6 or malla.bounds[1][2] > GROSOR + 1.0e-6:
        raise ErrorStencil("La extrusion no esta entre z=0 y z=GROSOR.")


def _recargar_y_validar_stl(ruta: Path) -> None:
    try:
        malla = trimesh.load(str(ruta), force="mesh")
    except Exception as exc:
        raise ErrorStencil(f"El STL exportado no se puede volver a leer: {exc}")

    if not malla.is_watertight or malla.volume <= 0:
        raise ErrorStencil("El STL exportado no es una malla cerrada valida.")
    if len(malla.split(only_watertight=False)) != 1:
        raise ErrorStencil("El STL exportado contiene piezas separadas.")
    if not np.allclose(malla.extents, [ANCHO, ALTO, GROSOR],
                       atol=1.0e-3, rtol=0.0):
        raise ErrorStencil("El STL exportado no conserva las dimensiones.")


# ---------------------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------------------------

def _generar_diseno(texto_1: str, texto_2: str, salida: Path,
                    font: TTFont, glyphSet, hmtx,
                    unidades_por_em: float) -> None:
    texto_1 = texto_1.strip()
    texto_2 = texto_2.strip()
    if not texto_1 or not texto_2:
        raise ErrorStencil("Las dos lineas deben tener texto.")

    linea_1_unidades = _texto_a_poligono(texto_1, font, glyphSet, hmtx)
    linea_2_unidades = _texto_a_poligono(texto_2, font, glyphSet, hmtx)
    disp = _disponer_texto(linea_1_unidades, linea_2_unidades,
                           unidades_por_em, EXPANSION_TRAZO)

    texto = unary_union([disp.linea_1, disp.linea_2])
    if EXPANSION_TRAZO > 0:
        texto = texto.buffer(EXPANSION_TRAZO, join_style="round")
        texto = _solo_poligonos(texto.buffer(0))
        if texto is None:
            raise ErrorStencil("El engrosado del texto no ha producido geometria valida.")

    # El buffer redondeado puede dejar un descentrado de milesimas de mm.
    bx0, by0, bx1, by1 = texto.bounds
    texto = affinity.translate(
        texto,
        xoff=ANCHO * 0.5 - (bx0 + bx1) * 0.5,
        yoff=ALTO * 0.5 - (by0 + by1) * 0.5,
    )

    print()
    print("=" * 68)
    print(f"Diseno: {texto_1} / {texto_2}")
    print(f"Tamano de fuente: {disp.tamano_fuente_mm:.3f} mm")
    print(f"Separacion entre lineas: {disp.separacion_mm:.3f} mm")
    print(f"Engrosado de trazo: {EXPANSION_TRAZO:.3f} mm")
    print(f"Caja del texto: {texto.bounds[2]-texto.bounds[0]:.3f} x "
          f"{texto.bounds[3]-texto.bounds[1]:.3f} mm")

    placa = Polygon([(0, 0), (ANCHO, 0), (ANCHO, ALTO), (0, ALTO)])
    solido = _solo_poligonos(placa.difference(texto.buffer(0)))
    if solido is None:
        raise ErrorStencil("La resta del texto ha dejado una placa vacia.")

    solido, puentes = _conectar_islas(solido, ANCHO_PUENTE)
    solido, refuerzos = _reforzar_puentes(solido, ANCHO_PUENTE)
    puentes += refuerzos

    _validar_2d(disp, solido, texto)

    # Margenes reales, solo informativos.
    minx, miny, maxx, maxy = texto.bounds
    print(f"Margenes: izq {minx:.3f}, der {ANCHO-maxx:.3f}, "
          f"abajo {miny:.3f}, arriba {ALTO-maxy:.3f} mm")

    malla = _crear_malla(solido)
    _validar_malla(malla, solido.area)

    salida = salida.expanduser()
    malla.export(str(salida), file_type="stl")
    _recargar_y_validar_stl(salida)

    print()
    print("VALIDACION CORRECTA")
    print(f"  Archivo: {salida}")
    print(f"  Dimensiones: {malla.extents[0]:.3f} x {malla.extents[1]:.3f} x "
          f"{malla.extents[2]:.3f} mm")
    print(f"  Lineas: {texto_1} / {texto_2}")
    print("  Texto: dos lineas centradas y dentro de los margenes")
    print("  Recorte: completo, de z=0 a z=GROSOR")
    detalle_puentes = (
        "la fuente ya traia puentes suficientemente anchos"
        if puentes == 0 else
        f"ancho de puente {ANCHO_PUENTE:.2f} mm"
    )
    print(f"  Puentes/refuerzos anadidos: {puentes} ({detalle_puentes})")
    print("  Malla: estanca, una sola pieza, sin triangulos degenerados")
    print("  STL: lectura de comprobacion correcta")


def main() -> int:
    try:
        if ANCHO <= 2 * MARGEN or ALTO <= 2 * MARGEN:
            raise ErrorStencil("ANCHO/ALTO deben ser mayores que 2*MARGEN.")
        if GROSOR <= 0:
            raise ErrorStencil("GROSOR debe ser positivo.")
        if SEPARACION_EM < 0:
            raise ErrorStencil("SEPARACION_EM no puede ser negativa.")
        if ANCHO_PUENTE <= 0:
            raise ErrorStencil("ANCHO_PUENTE debe ser positivo.")
        if EXPANSION_TRAZO < 0:
            raise ErrorStencil("EXPANSION_TRAZO no puede ser negativa.")
        if not DISENOS:
            raise ErrorStencil("DISENOS esta vacio.")
        archivos = [archivo for _, _, archivo in DISENOS]
        if len(set(archivos)) != len(archivos):
            raise ErrorStencil("Hay nombres de archivo repetidos en DISENOS.")

        ruta_fuente, familia = _resolver_fuente(FUENTE)
        print(f"Fuente: {ruta_fuente}")
        print(f"Familia: {familia}")

        font = _abrir_fuente(ruta_fuente, familia)
        fallos = []
        try:
            if "head" not in font or "hmtx" not in font:
                raise ErrorStencil("La fuente no tiene metricas tipograficas validas.")

            unidades_por_em = float(font["head"].unitsPerEm)
            glyphSet = font.getGlyphSet()
            hmtx = font["hmtx"]

            base = Path(__file__).resolve().parent.parent / "stl" / "archivio"
            base.mkdir(parents=True, exist_ok=True)
            for texto_1, texto_2, archivo in DISENOS:
                salida = base / archivo
                try:
                    _generar_diseno(texto_1, texto_2, salida,
                                    font, glyphSet, hmtx, unidades_por_em)
                except ErrorStencil as exc:
                    print()
                    print(f"ERROR en {archivo}: {exc}")
                    fallos.append((archivo, str(exc)))
        finally:
            font.close()

        print()
        if fallos:
            print(f"Terminado con {len(fallos)} error(es) de {len(DISENOS)} disenos.")
            for archivo, mensaje in fallos:
                print(f"  - {archivo}: {mensaje}")
            return 1

        print(f"Listo: {len(DISENOS)} stencils generados en {base}")
        print("Abre los STL con OrcaSlicer, Cura o PrusaSlicer.")
        return 0

    except ErrorStencil as exc:
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
    sys.exit(main())
