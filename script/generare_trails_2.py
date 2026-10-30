#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera los carteles de trail que faltan en formato estrecho 190 x 80 x 0,5 mm.

Salida:
    stl/trails_2/singoli/*.stl
    stl/trails_2/doppi/*_2x.stl
    png/trails_2/*.png
"""

from pathlib import Path

import generare_cartelli as car
import generare_cartelli_stretti as est
import generare_stencil as base

DISENOS = [
    car.Cartel("CIAOROBY", ["CIAOROBY"], "ciaoroby.stl"),
    car.Cartel("COOLMA DH", ["COOLMA DH"], "coolma_dh.stl"),
    car.Cartel("ERNESTO SPARALESTO", ["ERNESTO", "SPARALESTO"],
               "ernesto_sparalesto.stl"),
    car.Cartel("FACTORY", ["FACTORY"], "factory.stl"),
    car.Cartel("FLAMINGO", ["FLAMINGO"], "flamingo.stl"),
    car.Cartel("FLY TO ROCCO", ["FLY TO", "ROCCO"], "fly_to_rocco.stl"),
    car.Cartel("GALEOTTO BOB", ["GALEOTTO", "BOB"], "galeotto_bob.stl"),
    car.Cartel("LA CAPRI", ["LA CAPRI"], "la_capri.stl"),
    car.Cartel("LA GHIANDA", ["LA GHIANDA"], "la_ghianda.stl"),
    car.Cartel("MAGMA DEL VULCANO", ["MAGMA", "DEL VULCANO"],
               "magma_del_vulcano.stl"),
    car.Cartel("NUOVA YORK", ["NUOVA", "YORK"], "nuova_york.stl"),
    car.Cartel("PINOLO", ["PINOLO"], "pinolo.stl"),
    car.Cartel("PISACRAVA", ["PISACRAVA"], "pisacrava.stl"),
    car.Cartel("SPEEDYPENNY", ["SPEEDY", "PENNY"], "speedypenny.stl"),
    car.Cartel("VARIANTE DEL SASSONE", ["VARIANTE", "DEL SASSONE"],
               "variante_del_sassone.stl"),
    car.Cartel("ZOTTO CHITARRA", ["ZOTTO", "CHITARRA"],
               "zotto_chitarra.stl"),
]

TITULO = "RIVE ROSSE / trails 2"


def main() -> int:
    try:
        if not DISENOS:
            raise base.ErrorStencil("No hay trails para generar.")

        archivos = [c.archivo for c in DISENOS]
        if len(set(archivos)) != len(archivos):
            raise base.ErrorStencil("Hay nombres de archivo repetidos.")

        ruta_fuente, familia = base._resolver_fuente(base.FUENTE)
        print(f"Fuente: {ruta_fuente}")
        print(f"Familia: {familia}")

        font = base._abrir_fuente(ruta_fuente, familia)
        fallos = []
        carteles_ok = []
        solidos_ok = []
        huecos_ok = []
        try:
            unidades_por_em = float(font["head"].unitsPerEm)
            glyphSet = font.getGlyphSet()
            hmtx = font["hmtx"]

            raiz = Path(__file__).resolve().parent.parent
            dir_singoli = raiz / "stl" / "trails_2" / "singoli"
            dir_dobles = raiz / "stl" / "trails_2" / "doppi"
            dir_png = raiz / "png" / "trails_2"
            for carpeta in (dir_singoli, dir_dobles, dir_png):
                carpeta.mkdir(parents=True, exist_ok=True)

            for cartel in DISENOS:
                salida = dir_singoli / cartel.archivo
                try:
                    solido, huecos, puentes, alto_letra, caja = (
                        est.construir_cartello(
                            cartel, font, glyphSet, hmtx, unidades_por_em
                        )
                    )
                    est._generar_singolo(
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

            if carteles_ok:
                est._generar_placas_dobles(carteles_ok, solidos_ok, dir_dobles)

            if huecos_ok:
                est._preview(
                    huecos_ok, dir_png / "catalogo_trails_2_spray.png",
                    True, TITULO
                )
                est._preview(
                    huecos_ok, dir_png / "catalogo_trails_2_stencil.png",
                    False, TITULO
                )
                est._preview_placa_doble(
                    huecos_ok[0][1], dir_png / "piastra_doppia_trails_2_spray.png",
                    True
                )
                est._preview_placa_doble(
                    huecos_ok[0][1],
                    dir_png / "piastra_doppia_trails_2_stencil.png", False
                )
        finally:
            font.close()

        print()
        if fallos:
            print(f"Terminato con {len(fallos)} errore/i.")
            for archivo, mensaje in fallos:
                print(f"  - {archivo}: {mensaje}")
            return 1

        print(f"Pronto: {len(carteles_ok)} cartelli singoli e "
              f"{len(carteles_ok)} piastre doppie in stl/trails_2.")
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
