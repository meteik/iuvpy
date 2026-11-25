# =============================================================================
# ECMWF / CAMS - PRONÓSTICO IUV
# DESCARGA + PROCESAMIENTO + MAPA
# ORGANIZACIÓN AUTOMÁTICA POR FECHA Y HORA DE CORRIDA
# =============================================================================

import os
import numpy as np
import geopandas as gpd
import xarray as xr
import matplotlib.pyplot as plt
import rasterio
import cdsapi
import zipfile

from shapely.geometry import box
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from datetime import datetime, timedelta
from matplotlib.cm import ScalarMappable


# =============================================================================
# CONFIGURACIÓN PRINCIPAL
# =============================================================================

# -----------------------------------------------------------------------------
# CARPETA PRINCIPAL
# -----------------------------------------------------------------------------

repo_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.environ.get("IUVPY_OUTPUT_DIR", os.path.join(repo_dir, "output"))


# -----------------------------------------------------------------------------
# FECHA DE LA CORRIDA
# -----------------------------------------------------------------------------

fecha = os.environ.get("RUN_DATE", datetime.utcnow().strftime("%Y%m%d"))


# -----------------------------------------------------------------------------
# HORA DE LA CORRIDA
#
# IMPORTANTE:
#
# "00" = 00 UTC
# "12" = 12 UTC
# -----------------------------------------------------------------------------

hora = os.environ.get("RUN_HOUR", "12")

# =============================================================================
# VALIDACIÓN DE HORA
# =============================================================================

if hora not in ["00", "12"]:

    raise ValueError(
        "La hora debe ser '00' o '12'."
    )


# =============================================================================
# DATETIME DE LA CORRIDA
# =============================================================================

fecha_run = datetime.strptime(

    fecha + hora,

    "%Y%m%d%H"

)


# =============================================================================
# IDENTIFICADOR DE LA CORRIDA
# =============================================================================

run_id = fecha + hora


# =============================================================================
# NOMBRE DE LA CARPETA PRINCIPAL
# =============================================================================

nombre_corrida = (
    f"ECMWF_CAMS_IUV_{hora}_{fecha}"
)


corrida_dir = os.path.join(

    base_dir,

    nombre_corrida

)


# =============================================================================
# CARPETA DATA
# =============================================================================

data_dir = os.path.join(

    corrida_dir,

    f"DATA_{run_id}"

)


# =============================================================================
# CARPETA MAPAS
# =============================================================================

mapas_dir = os.path.join(

    corrida_dir,

    f"MAPAS_{run_id}"

)


# =============================================================================
# CREAR CARPETAS
# =============================================================================

os.makedirs(

    data_dir,

    exist_ok=True

)


os.makedirs(

    mapas_dir,

    exist_ok=True

)


# =============================================================================
# ARCHIVOS AUXILIARES
# =============================================================================

shp_py = os.path.join(
    repo_dir,
    "assets",
    "Departamentos_Paraguay.shp"
)


dem_py = os.path.join(

    base_dir,

    "DEM_PY.tif"

)


logo_py = os.path.join(
    repo_dir,
    "assets",
    "NORTE.png"
)


# =============================================================================
# ARCHIVO GRIB
# =============================================================================

grib_file = os.path.join(

    data_dir,

    f"cams_uvbed_{run_id}.grib"

)


# =============================================================================
# ARCHIVO DE MAPA
# =============================================================================

salida = os.path.join(

    mapas_dir,

    f"IUV_ECMWF_{fecha}_{hora}.png"

)


# =============================================================================
# INFORMACIÓN
# =============================================================================

print()
print("=" * 80)
print("                  ECMWF / CAMS - IUV")
print("=" * 80)

print()

print(
    f"Fecha de corrida : "
    f"{fecha_run:%d/%m/%Y}"
)

print(
    f"Hora de corrida  : "
    f"{hora}Z"
)

print(
    f"Identificador    : "
    f"{run_id}"
)

print()

print(
    f"Carpeta corrida:\n"
    f"{corrida_dir}"
)

print()

print(
    f"DATA:\n"
    f"{data_dir}"
)

print()

print(
    f"MAPAS:\n"
    f"{mapas_dir}"
)

print()

print(
    f"GRIB:\n"
    f"{grib_file}"
)

print()

print(
    f"MAPA:\n"
    f"{salida}"
)

print()


# =============================================================================
# LOGO
# =============================================================================

def add_logo(
    ax,
    logo_path,
    zoom=0.065
):

    if not os.path.exists(
        logo_path
    ):

        print(
            f"⚠ No se encontró el logo:"
            f"\n{logo_path}"
        )

        return


    img = plt.imread(
        logo_path
    )


    ab = AnnotationBbox(

        OffsetImage(
            img,
            zoom=zoom
        ),

        (0.84, 0.80),

        xycoords="axes fraction",

        frameon=False

    )


    ax.add_artist(
        ab
    )


# =============================================================================
# DESCARGA CAMS
# =============================================================================

def descargar_cams(
    outfile
):

    print()
    print("=" * 80)
    print("                    DESCARGA CAMS")
    print("=" * 80)


    c = cdsapi.Client()


    request = {

        "variable": [

            "uv_biologically_effective_dose"

        ],

        "date": [

            f"{fecha[:4]}-"
            f"{fecha[4:6]}-"
            f"{fecha[6:8]}"

        ],

        "time": [

            f"{hora}:00"

        ],

        "leadtime_hour": [

            str(h)

            for h in range(
                0,
                121
            )

        ],

        "type": [

            "forecast"

        ],

        "data_format": "grib"

    }


    print()
    print("Solicitud enviada a CDS:")

    print()
    print(
        f"Fecha : {fecha}"
    )

    print(
        f"Hora  : {hora}Z"
    )

    print(
        "Leadtime: 0–120 h"
    )

    print()


    c.retrieve(

        "cams-global-atmospheric-composition-forecasts",

        request,

        outfile

    )


# =============================================================================
# COMPROBAR / DESCARGAR
# =============================================================================

if os.path.exists(
    grib_file
):

    print()
    print(
        "✓ El archivo CAMS ya existe."
    )

    print(
        grib_file
    )


else:

    print()
    print(
        "Descargando CAMS/ECMWF..."
    )

    descargar_cams(
        grib_file
    )

    print()
    print(
        "✓ Descarga finalizada."
    )


# =============================================================================
# LECTURA DEL GRIB
# =============================================================================

print()
print("=" * 80)
print("                    LECTURA CAMS")
print("=" * 80)


ds0 = xr.open_dataset(

    grib_file,

    engine="cfgrib"

)


# =============================================================================
# RENOMBRAR VARIABLE
# =============================================================================

variable_original = (

    list(
        ds0.data_vars
    )[0]

)


ds0 = ds0.rename({

    variable_original:
    "uvbed"

})


# =============================================================================
# CONVERSIÓN
# =============================================================================

uvi = (

    ds0["uvbed"]

    * 40.0

)


# =============================================================================
# IUV DIARIO - MÁXIMO EN HORARIO SOLAR
# =============================================================================

daily = []

for d in range(4):

    # Día válido
    fecha_valida = fecha_run + timedelta(days=d + 1)

    # Desde las 14 UTC hasta las 20 UTC aproximadamente
    # cubrimos el período de máxima radiación solar sobre Paraguay.
    hora_inicio = 14
    hora_fin = 20

    # Lead time respecto a la corrida
    inicio_step = int(
        (fecha_valida.replace(hour=hora_inicio) - fecha_run).total_seconds() / 3600
    )

    fin_step = int(
        (fecha_valida.replace(hour=hora_fin) - fecha_run).total_seconds() / 3600
    )

    steps = np.arange(
        inicio_step,
        fin_step + 1
    )

    steps = steps[
        (steps >= 0) &
        (steps < uvi.sizes["step"])
    ]

    if len(steps) == 0:
        raise RuntimeError(
            f"No hay datos CAMS para {fecha_valida:%d/%m/%Y}"
        )

    # Máximo de IUV durante el período solar central
    uvi_max = uvi.isel(step=steps).max("step")

    daily.append(
        uvi_max.expand_dims(
            dia=[d + 1]
        )
    )

ds = xr.concat(
    daily,
    dim="dia"
).to_dataset(name="uvi")


# =============================================================================
# CONCATENAR
# =============================================================================

ds = xr.concat(

    daily,

    dim="dia"

).to_dataset(

    name="uvi"

)


# =============================================================================
# LONGITUDES
# =============================================================================

ds = ds.assign_coords(

    longitude=(

        (
            ds.longitude
            + 180
        )

        % 360

    ) - 180

)


ds = ds.sortby(
    "longitude"
)


ds = ds.sortby(
    "latitude"
)


# =============================================================================
# INTERPOLACIÓN
# =============================================================================

print()
print(
    "Realizando interpolación..."
)


lat_min = float(
    ds.latitude.min()
)

lat_max = float(
    ds.latitude.max()
)

lon_min = float(
    ds.longitude.min()
)

lon_max = float(
    ds.longitude.max()
)


new_lat = np.arange(

    lat_max,

    lat_min - 0.001,

    -0.25

)


new_lon = np.arange(

    lon_min,

    lon_max + 0.001,

    0.25

)


ds = ds.interp(

    latitude=new_lat,

    longitude=new_lon

)


# =============================================================================
# ORDEN FINAL
# =============================================================================

ds = ds.sortby(
    "latitude"
)


# =============================================================================
# RECORTE PARAGUAY
# =============================================================================

print()
print(
    "Recortando Paraguay..."
)


ds_py = ds.sel(

    latitude=slice(
        -28,
        -19
    ),

    longitude=slice(
        -65,
        -50
    )

)


if ds_py.latitude.size == 0:

    raise RuntimeError(

        "❌ ECMWF no cubre Paraguay."

    )


lons = (
    ds_py.longitude.values
)


lats = (
    ds_py.latitude.values
)


if lats[0] < lats[-1]:

    lats = lats[::-1]

    ds_py = ds_py.sel(

        latitude=lats

    )


# =============================================================================
# SHAPEFILE
# =============================================================================

print()
print(
    "Cargando shapefile..."
)


if not os.path.exists(
    shp_py
):

    raise FileNotFoundError(
        shp_py
    )


paraguay = (

    gpd.read_file(
        shp_py
    )

    .to_crs(
        4326
    )

)


py_geom = (
    paraguay.geometry
    .unary_union
)


minx, miny, maxx, maxy = (

    paraguay.total_bounds

)


padx = (
    maxx - minx
) * 0.03


pady = (
    maxy - miny
) * 0.03


# =============================================================================
# DEM
# =============================================================================

print(
    "Cargando DEM..."
)


with rasterio.open(
    dem_py
) as src:

    topo = src.read(
        1
    )

    topo[
        topo < 0
    ] = 0

    tform = src.transform


# =============================================================================
# COLORES IUV
# =============================================================================

colors_rgb = np.array([

    (101,242,0),
    (43,146,0),
    (160,206,0),

    (247,228,0),
    (248,182,0),
    (248,135,0),

    (248,89,0),
    (232,44,14),

    (216,0,29),
    (255,0,153),

    (181,76,255),
    (153,140,255),
    (133,120,235),
    (113,100,215),
    (93,80,195),
    (73,60,175),
    (53,40,155),
    (33,20,135),

    (50,204,255),
    (100,245,255),
    (150,255,255)

]) / 255.0


cmap = ListedColormap(
    colors_rgb
)


bounds = np.arange(
    0,
    21,
    1
)


norm = BoundaryNorm(

    bounds,

    cmap.N

)


# =============================================================================
# DÍAS DE LA SEMANA
# =============================================================================

dias_semana = [

    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo"

]


# =============================================================================
# FIGURA
# =============================================================================

print()
print(
    "Generando mapas..."
)


fig, axes = plt.subplots(

    2,
    2,

    figsize=(
        17,
        16
    )

)


axes = axes.flatten()


# =============================================================================
# CELDAS
# =============================================================================

dx = (

    abs(
        lons[1]
        - lons[0]
    )

    / 2

)


dy = (

    abs(
        lats[1]
        - lats[0]
    )

    / 2

)


# =============================================================================
# MAPAS
# =============================================================================

for d in range(4):

    patches = []

    valores = []


    Z = (

        ds_py["uvi"]

        .isel(
            dia=d
        )

        .values

    )


    # -------------------------------------------------------------------------
    # GRILLA
    # -------------------------------------------------------------------------

    for i, lat in enumerate(
        lats
    ):

        for j, lon in enumerate(
            lons
        ):

            cell = box(

                lon - dx,

                lat - dy,

                lon + dx,

                lat + dy

            )


            clipped = (

                cell.intersection(
                    py_geom
                )

            )


            if clipped.is_empty:

                continue


            val = Z[
                i,
                j
            ]


            # -----------------------------------------------------------------
            # POLÍGONO
            # -----------------------------------------------------------------

            if clipped.geom_type == "Polygon":

                patches.append(

                    Polygon(

                        clipped.exterior.coords

                    )

                )

                valores.append(
                    val
                )


            else:

                for g in clipped.geoms:

                    if g.is_empty:

                        continue


                    patches.append(

                        Polygon(

                            g.exterior.coords

                        )

                    )

                    valores.append(
                        val
                    )


    # =============================================================================
    # PATCH COLLECTION
    # =============================================================================

    pc = PatchCollection(

        patches,

        cmap=cmap,

        norm=norm

    )


    pc.set_array(

        np.array(
            valores
        )

    )


    ax = axes[d]


    ax.add_collection(
        pc
    )


    # =============================================================================
    # FRONTERA
    # =============================================================================

    paraguay.boundary.plot(

        ax=ax,

        edgecolor="black",

        linewidth=1.4

    )


    # =============================================================================
    # FECHA VÁLIDA
    # =============================================================================

    fecha_real = fecha_run + timedelta(days=d + 1)

    dia_nombre = dias_semana[fecha_real.weekday()]

    fecha_valida = fecha_real.strftime("%d/%m/%Y")


    # =============================================================================
    # TÍTULO
    # =============================================================================

    titulo = (
        "CAMS/ECMWF – IUV (All Sky - Mediodía Solar)\n"
        f"Inicio de la corrida: {fecha_run:%d/%m/%Y %H}Z\n"
        f"Válido para el día {dia_nombre} {fecha_valida}"
    )

    ax.set_title(
        titulo,
        fontsize=13,
        fontweight="bold"
    )


    # =============================================================================
    # EJES
    # =============================================================================

    ax.set_xlim(

        minx - padx,

        maxx + padx

    )


    ax.set_ylim(

        miny - pady,

        maxy + pady

    )


    ax.set_aspect(
        "equal"
    )


    ax.set_xlabel(

        "Longitud",

        fontsize=11,

        fontweight="bold"

    )


    ax.set_ylabel(

        "Latitud",

        fontsize=11,

        fontweight="bold"

    )


    # =============================================================================
    # GRID
    # =============================================================================

    ax.grid(

        color="gray",

        linestyle="--",

        linewidth=0.5,

        alpha=0.5

    )


    # =============================================================================
    # LOGO
    # =============================================================================

    add_logo(

        ax,

        logo_py

    )


# =============================================================================
# COLORBAR HORIZONTAL
# =============================================================================

fig.subplots_adjust(

    bottom=0.28,

    right=0.80,

    hspace=0.30

)


cax1 = fig.add_axes(

    [
        0.15,
        0.18,
        0.65,
        0.035
    ]

)


sm = ScalarMappable(

    cmap=cmap,

    norm=norm

)


sm.set_array([])


cbar1 = fig.colorbar(

    sm,

    cax=cax1,

    orientation="horizontal"

)


cbar1.set_ticks(

    np.arange(
        0,
        21,
        1
    )

)


cbar1.set_label(

    "IUV",

    fontsize=12,

    fontweight="bold"

)


# =============================================================================
# CATEGORÍAS OMS
# =============================================================================

oms_labels = [

    "Bajo (<2)",
    "Moderado (3–5)",
    "Alto (6–7)",
    "Muy alto (8–10)",
    "Extremo (≥11)"

]


ranges = [

    (0, 2),
    (2, 5),
    (5, 7),
    (7, 10),
    (10, 20)

]


oms_pos = [

    ((a + b) / 2) / 20

    for a, b in ranges

]


for xf, lab in zip(

    oms_pos,

    oms_labels

):

    cbar1.ax.text(

        xf,

        1.35,

        lab,

        ha="center",

        va="bottom",

        fontsize=10,

        fontweight="bold",

        transform=cbar1.ax.transAxes

    )


# =============================================================================
# COLORBAR VERTICAL
# =============================================================================

cax2 = fig.add_axes(

    [
        0.80,
        0.31,
        0.025,
        0.55
    ]

)


cbar2 = fig.colorbar(

    pc,

    cax=cax2,

    orientation="vertical"

)


cbar2.set_label(

    "Nivel de Riesgo",

    fontsize=12,

    fontweight="bold"

)


cbar2.set_ticks([])

cbar2.ax.tick_params(
    length=0
)


niveles = [

    "Bajo",
    "Moderado",
    "Alto",
    "Muy Alto",
    "Extremo"

]


niveles_pos = [

    1.5,
    4.0,
    6.5,
    9.0,
    15.5

]


for y, lab in zip(

    niveles_pos,

    niveles

):

    cbar2.ax.text(

        0.5,

        y,

        lab,

        ha="center",

        va="center",

        rotation=90,

        fontsize=10,

        fontweight="bold",

        transform=(

            cbar2.ax
            .get_yaxis_transform()

        )

    )


# =============================================================================
# GUARDAR
# =============================================================================

plt.savefig(

    salida,

    dpi=300,

    bbox_inches="tight"

)


plt.show()


plt.close()


# =============================================================================
# ZIP
# =============================================================================

zip_salida = os.path.join(

    corrida_dir,

    f"{nombre_corrida}_{run_id}.zip"

)


print()
print(
    "Creando ZIP..."
)


with zipfile.ZipFile(

    zip_salida,

    "w",

    zipfile.ZIP_DEFLATED

) as zipf:


    # -------------------------------------------------------------------------
    # GRIB
    # -------------------------------------------------------------------------

    if os.path.exists(
        grib_file
    ):

        zipf.write(

            grib_file,

            arcname=os.path.join(

                f"DATA_{run_id}",

                os.path.basename(
                    grib_file
                )

            )

        )


    # -------------------------------------------------------------------------
    # MAPA
    # -------------------------------------------------------------------------

    if os.path.exists(
        salida
    ):

        zipf.write(

            salida,

            arcname=os.path.join(

                f"MAPAS_{run_id}",

                os.path.basename(
                    salida
                )

            )

        )


# =============================================================================
# RESUMEN FINAL
# =============================================================================

print()
print("=" * 80)
print("                    PROCESO FINALIZADO")
print("=" * 80)

print()

print(
    f"✓ Modelo       : ECMWF / CAMS"
)

print(
    f"✓ Fecha        : "
    f"{fecha_run:%d/%m/%Y}"
)

print(
    f"✓ Corrida      : "
    f"{hora}Z"
)

print(
    f"✓ Identificador: "
    f"{run_id}"
)

print()

print(
    f"✓ DATA:\n{data_dir}"
)

print()

print(
    f"✓ MAPAS:\n{mapas_dir}"
)

print()

print(
    f"✓ MAPA:\n{salida}"
)

print()

print(
    f"✓ ZIP:\n{zip_salida}"
)

print()
print("=" * 80)