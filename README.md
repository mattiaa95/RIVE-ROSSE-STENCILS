# RIVE ROSSE STENCILS

Stencils 3D paramétricos para señalizar los trails de **RIVE ROSSE**: carteles de trail, señales técnicas, flechas, niveles, ayuda y placas dobles de 190 × 80 mm.

Todo el catálogo se genera desde Python a partir de contornos vectoriales, se valida como malla cerrada y se exporta en STL a escala real en milímetros.

<p align="center">
  <img src="png/catalogo_rive_rosse.png" alt="Catálogo completo RIVE ROSSE" width="560">
</p>

<p align="center">
  <strong>33 diseños estándar · 44 placas estrechas · 43 placas dobles · 120 STL · 20 G-code</strong>
</p>

---

## Contenido

- [Qué incluye](#qué-incluye)
- [Especificaciones](#especificaciones)
- [Catálogo](#catálogo)
- [G-code listo para imprimir](#g-code-listo-para-imprimir)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Generar los STL](#generar-los-stl)
- [Impresión](#impresión)
- [Scripts](#scripts)
- [Validación](#validación)
- [Fuentes y créditos](#fuentes-y-créditos)
- [Licencia](#licencia)

---

## Qué incluye

| Familia | Formato | Diseños | STL |
|---|---:|---:|---:|
| Carteles de trail y especiales | 190 × 190 × 0,5 mm | 17 | 17 |
| Señales técnicas, flechas, ayuda y niveles | 190 × 190 × 0,5 mm | 16 | 16 |
| Carteles estrechos | 190 × 80 × 0,5 mm | 11 + 1 flecha especial | 12 |
| Placas dobles de carteles estrechos | 190 × 164 × 0,5 mm | 11 | 11 |
| Señales compactas | 190 × 80 × 0,5 mm | 16 | 16 |
| Placas dobles de señales compactas | 190 × 164 × 0,5 mm | 16 | 16 |
| Trails 2 | 190 × 80 × 0,5 mm | 16 | 16 |
| Placas dobles de Trails 2 | 190 × 164 × 0,5 mm | 16 | 16 |
| **Total** | | | **120** |

Además:

- **20 G-code** prelaminados en `gcode/`, con nombres compactos tipo `miniVariantSassEZT`.
- **29 PNG** de catálogo y previsualización en `png/`.
- Scripts reproducibles en `script/`.
- Fuentes stencil incluidas en `font/`.

---

## Especificaciones

- **Unidades:** milímetros reales.
- **Grosor:** 0,5 mm.
- **Formato estándar:** 190 × 190 mm.
- **Formato estrecho:** 190 × 80 mm.
- **Placa doble:** 190 × 164 mm, con 4 mm de separación entre placas.
- **Márgenes:** 7–8 mm.
- **Puentes:** integrados en el diseño, 2,2–2,4 mm.
- **Malla:** cerrada, una sola pieza, sin triángulos degenerados.
- **Texto:** vectorizado desde TTF; no depende de la fuente en el laminador.
- **Previsualizaciones:** modo `spray` (naranja sobre beige) y modo `stencil` (blanco sobre negro).

> Cada STL es una **placa sólida con los huecos del stencil**, no un relieve. La placa se apoya en el suelo y se usa como plantilla para spray.

---

## Catálogo

### Catálogo completo 190 × 190 mm

| Spray | Stencil |
|---|---|
| <img src="png/catalogo_rive_rosse.png" width="420"> | <img src="png/catalogo_rive_rosse_stencil.png" width="420"> |

### Carteles estrechos 190 × 80 mm

| Spray | Stencil |
|---|---|
| <img src="png/cartelli_stretti/catalogo_cartelli_stretti_spray.png" width="420"> | <img src="png/cartelli_stretti/catalogo_cartelli_stretti_stencil.png" width="420"> |

### Señales compactas 190 × 80 mm

| Spray | Stencil |
|---|---|
| <img src="png/segnali_stretti/catalogo_segnali_stretti_spray.png" width="420"> | <img src="png/segnali_stretti/catalogo_segnali_stretti_stencil.png" width="420"> |

### Trails 2

| Spray | Stencil |
|---|---|
| <img src="png/trails_2/catalogo_trails_2_spray.png" width="420"> | <img src="png/trails_2/catalogo_trails_2_stencil.png" width="420"> |

### Placas dobles

| Carteles | Señales | Trails 2 |
|---|---|---|
| <img src="png/cartelli_stretti/piastra_doppia_spray.png" width="260"> | <img src="png/segnali_stretti/piastra_doppia_segnali_spray.png" width="260"> | <img src="png/trails_2/piastra_doppia_trails_2_spray.png" width="260"> |

---

## G-code listo para imprimir

La carpeta `gcode/` contiene **20 archivos prelaminados** con Cura 5.2.2. Los nombres siguen el esquema compacto:

```text
mini + nombre normalizado en CamelCase + .gcode
```

Ejemplo: `miniVariantSassEZT.gcode`.

<details>
<summary>Ver los 20 G-code</summary>

```text
miniCPMDS.gcode
miniCiaoCoolma.gcode
miniDropIndietro.gcode
miniErnestoFactor.gcode
miniFlamingoRocco.gcode
miniFrecciaDritto.gcode
miniFrecciaMTB.gcode
miniGaleottoCapri.gcode
miniGhiandaMagma.gcode
miniLivello1e2.gcode
miniLivello3e4.gcode
miniM33TdP.gcode
miniM41eBis.gcode
miniMoiaCaracse.gcode
miniNYPinolo.gcode
miniPignVerg.gcode
miniPisacravaSpeedy.gcode
miniRipidoSalto.gcode
miniTASV.gcode
miniVariantSassEZT.gcode
```

</details>

El script `script/renombrar_gcode.py` contiene el mapeo completo y permite volver atrás:

```bash
python3 script/renombrar_gcode.py --dry-run
python3 script/renombrar_gcode.py
python3 script/renombrar_gcode.py --revert
```

> Los G-code están preparados para la impresora con la que se generaron. Si cambias de máquina, de boquilla o de material, regenera desde los STL.

---

## Estructura del repositorio

```text
RIVE_ROSSE_STENCILS/
├── font/                     Fuentes stencil incluidas
├── gcode/                    20 G-code prelaminados
├── png/                      Catálogos y previews
│   ├── cartelli/             17 carteles 190 × 190
│   ├── cartelli_stretti/     Carteles estrechos
│   ├── segnali/              Señales 190 × 190
│   ├── segnali_stretti/      Señales compactas
│   └── trails_2/             Trails 2
├── script/                   Generadores y utilidades
├── stl/                      Mallas listas para laminar
│   ├── cartelli/             17 carteles 190 × 190
│   ├── cartelli_stretti/     11 singulares + 11 dobles + 1 flecha
│   ├── segnali/              16 señales 190 × 190
│   ├── segnali_stretti/      16 singulares + 16 dobles
│   └── trails_2/             16 singulares + 16 dobles
├── README.md
└── requirements.txt
```

---

## Generar los STL

### Requisitos

- Python 3.10 o superior.
- `pip`.
- macOS, Linux o Windows.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Generar el catálogo estándar 190 × 190

```bash
python3 script/generare_cartelli.py
python3 script/generare_segnali.py
python3 script/generare_segnali_aiuto.py
python3 script/generare_catalogo.py
```

### Generar el catálogo estrecho 190 × 80

```bash
python3 script/generare_cartelli_stretti.py
python3 script/generare_segnali_stretti.py
python3 script/generare_trails_2.py
```

Los scripts escriben directamente en `stl/` y `png/`, crean las carpetas que faltan y validan cada archivo antes de terminar.

`script/generare_stencil.py` es el módulo base: carga la fuente, convierte texto a polígonos, hace las operaciones booleanas, añade puentes y valida las mallas. No hace falta ejecutarlo para generar el catálogo actual.

---

## Impresión

Ajustes de referencia para placas de 0,5 mm:

| Ajuste | Valor |
|---|---|
| Escala | 100 % |
| Altura de capa | 0,20 mm |
| Capas sólidas arriba/abajo | 3 |
| Perímetros | 2–3 |
| Relleno | 100 % o equivalente sólido |
| Soportes | No |
| Material | PLA / PETG |
| Orientación | Plana, con la cara del stencil hacia arriba |

Recomendaciones:

- Revisa la primera capa: la placa es fina y necesita buena adherencia.
- No escales el STL en el laminador salvo que quieras cambiar el tamaño real.
- Comprueba que los puentes interiores siguen abiertos después de laminar.
- Para pintar en el suelo, usa spray de baja presión y retira la plantilla con cuidado.

---

## Scripts

| Script | Función |
|---|---|
| `generare_stencil.py` | Motor común: fuente, polígonos, booleanas, puentes, extrusión y validación. |
| `generare_segnali.py` | Señales técnicas 190 × 190: DROP, SALTO, RIPIDO. |
| `generare_segnali_aiuto.py` | Flechas, ayuda, niveles y señales de orientación. |
| `generare_cartelli.py` | Carteles de trail y carteles especiales 190 × 190. |
| `generare_catalogo.py` | Catálogo PNG completo y catálogo de carteles. |
| `generare_cartelli_stretti.py` | Carteles estrechos, placas dobles y flecha MTB. |
| `generare_segnali_stretti.py` | Señales compactas 190 × 80 y sus placas dobles. |
| `generare_trails_2.py` | Los 16 carteles de Trails 2. |
| `renombrar_gcode.py` | Renombrado compacto y reversible de los G-code. |

---

## Validación

Cada STL se comprueba automáticamente antes de exportarse:

- dimensiones exactas en milímetros;
- malla cerrada y orientada;
- una sola pieza;
- sin triángulos degenerados;
- área abierta coherente con el diseño;
- puentes y separación entre elementos.

Los catálogos PNG se generan desde la misma geometría que los STL, así que la previsualización y la pieza impresa comparten contornos.

---

## Fuentes y créditos

- **Saira Stencil One** — fuente principal incluida en `font/SairaStencilOne-Regular.ttf`.
- **Allerta Stencil** — alternativa incluida en `font/AllertaStencil-Regular.ttf`.
- Geometría y generación: Python + `fonttools`, `shapely`, `trimesh`, `manifold3d`, `numpy` y `matplotlib`.
- Diseños y nombres de trail: **RIVE ROSSE**.

Las fuentes se distribuyen bajo **SIL Open Font License 1.1**. Consulta la licencia original de cada familia antes de redistribuirlas por separado.

---

## Licencia

Proyecto privado. Los diseños, nombres y marcas de RIVE ROSSE pertenecen a sus autores. No se concede permiso de uso comercial ni de redistribución pública sin autorización.
