# =============================================================================
# GFS IUV - PRONÓSTICO AUTOMÁTICO ORGANIZADO POR FECHA DE CORRIDA
# =============================================================================
import os
import numpy as np
import geopandas as gpd
import xarray as xr
import matplotlib.pyplot as plt
import rasterio
import requests
import zipfile
from shapely.geometry import box
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from datetime import datetime, timedelta, timezone
from matplotlib.cm import ScalarMappable
# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# -----------------------------------------------------------------------------
# CARPETA PRINCIPAL
# -----------------------------------------------------------------------------

script_dir = os.path.dirname(os.path.abspath(__file__))
# gfs_iuv.py vive en scripts/; la raíz del repositorio es su directorio padre.
repo_dir = os.path.dirname(script_dir)
base_dir = os.environ.get("IUVPY_OUTPUT_DIR", os.path.join(repo_dir, "output"))


# -----------------------------------------------------------------------------
# FECHA Y HORA DE LA CORRIDA
# -----------------------------------------------------------------------------
#
# SOLO CAMBIAS ESTAS DOS LÍNEAS
#
# Ejemplo:
# 20260813 12Z
# -----------------------------------------------------------------------------

fecha = os.environ.get(
    "RUN_DATE",
    datetime.now(timezone.utc).strftime("%Y%m%d")
)

fecha_run = datetime.strptime(fecha, "%Y%m%d").replace(
    hour=12,
    tzinfo=timezone.utc
)


# =============================================================================
# NOMBRE AUTOMÁTICO DE LA CORRIDA
# =============================================================================

nombre_corrida = (
    f"GFS_IUV_12_{fecha}"
)


# =============================================================================
# CARPETA PRINCIPAL DE LA CORRIDA
# =============================================================================

corrida_dir = os.path.join(
    base_dir,
    nombre_corrida
)


# =============================================================================
# CARPETA DATA
# =============================================================================

data_dir = os.path.join(
    corrida_dir,
    f"DATA_{fecha}"
)


# =============================================================================
# CARPETA MAPAS
# =============================================================================

mapas_dir = os.path.join(
    corrida_dir,
    f"MAPAS_{fecha}"
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

shp_py = os.environ.get(
    "PARAGUAY_SHP",
    os.path.join(repo_dir, "assets", "Departamentos_Paraguay.shp")
)


dem_py = os.environ.get(
    "IUVPY_DEM_PATH",
    os.path.join(base_dir, "DEM_PY.tif")
)


logo_py = os.environ.get(
    "IUVPY_LOGO_PATH",
    os.path.join(repo_dir, "assets", "NORTE.png")
)


# =============================================================================
# ARCHIVO DE SALIDA DEL MAPA
# =============================================================================

salida = os.path.join(
    mapas_dir,
    f"IUV_GFS_{fecha}.png"
)


# =============================================================================
# INFORMACIÓN DE LA CORRIDA
# =============================================================================

print()
print("=" * 80)
print("                  PRONÓSTICO GFS - IUV")
print("=" * 80)

print()
print(f"Fecha de corrida : {fecha_run:%d/%m/%Y}")
print(f"Hora de corrida  : {fecha_run:%H}Z")
print(f"Identificador     : {nombre_corrida}")

print()
print("Carpeta de corrida:")
print(corrida_dir)

print()
print("Carpeta DATA:")
print(data_dir)

print()
print("Carpeta MAPAS:")
print(mapas_dir)

print()
print("Salida:")
print(salida)

print()
print("=" * 80)

# Validar los recursos locales antes de iniciar descargas/procesamiento.
if not os.path.isfile(shp_py):
    raise FileNotFoundError(
        f"No se encontró el shapefile: {shp_py}. "
        "Debe estar en la carpeta assets de la raíz del repositorio, "
        "junto con .shx, .dbf y .prj."
    )

if not os.path.isfile(dem_py):
    raise FileNotFoundError(
        f"No se encontró el DEM: {dem_py}. "
        "Verificá que DEM_PY.tif esté disponible en la carpeta de salida/Drive."
    )


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
            f"⚠ No se encontró el logo: {logo_path}"
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
# DESCARGA DE GFS
# =============================================================================

base_url = (
    f"https://nomads.ncep.noaa.gov/"
    f"pub/data/nccf/com/uvi/prod/"
    f"uvi.{fecha}/"
)


dias = [
    "d1",
    "d2",
    "d3",
    "d4"
]


archivos = []
dias_disponibles = []


print()
print("=" * 80)
print("                    DESCARGA GFS")
print("=" * 80)


for d in dias:

    archivo = (
        f"uv.noontime.t12z.{d}.grib2"
    )


    ruta = os.path.join(
        data_dir,
        archivo
    )


    # -------------------------------------------------------------------------
    # Si ya existe no vuelve a descargar
    # -------------------------------------------------------------------------

    if os.path.exists(
        ruta
    ):

        print(
            f"✓ Ya existe: {archivo}"
        )


    else:

        print(
            f"\nDescargando: {archivo}"
        )

        url = (
            base_url
            + archivo
        )

        print(
            url
        )


        try:

            r = requests.get(
                url,
                timeout=180
            )


            r.raise_for_status()


            with open(
                ruta,
                "wb"
            ) as f:

                f.write(
                    r.content
                )


            print(
                f"✓ Descargado: {archivo}"
            )


        except Exception as e:

            print(
                f"❌ Error descargando {archivo}"
            )

            print(
                e
            )

            continue


    archivos.append(
        ruta
    )
    dias_disponibles.append(int(d[1:]))


print()
print(
    f"Total de archivos disponibles: "
    f"{len(archivos)}"
)


# =============================================================================
# COMPROBAR QUE HAYA ARCHIVOS
# =============================================================================

if len(archivos) == 0:

    raise Exception(
        "No se pudo descargar ningún archivo GFS."
    )


# =============================================================================
# LECTURA
# =============================================================================

print()
print("=" * 80)
print("                    LECTURA GFS")
print("=" * 80)


datasets = []


for i, (a, dia_archivo) in enumerate(
    zip(archivos, dias_disponibles)
):

    print(
        f"Leyendo archivo {i + 1}: "
        f"{os.path.basename(a)}"
    )


    ds_tmp = xr.open_dataset(
        a,
        engine="cfgrib"
    )


    # -------------------------------------------------------------------------
    # Renombrar variable
    # -------------------------------------------------------------------------

    primera_variable = (
        list(
            ds_tmp.data_vars
        )[0]
    )


    ds_tmp = ds_tmp.rename({

        primera_variable:
        "uvi"

    })


    # -------------------------------------------------------------------------
    # Agregar dimensión día
    # -------------------------------------------------------------------------

    ds_tmp = ds_tmp.expand_dims(

        dia=[
            dia_archivo
        ]

    )


    datasets.append(
        ds_tmp
    )


# =============================================================================
# CONCATENAR
# =============================================================================

ds = xr.concat(
    datasets,
    dim="dia"
)


# =============================================================================
# NORMALIZAR LONGITUD
# =============================================================================

ds = ds.assign_coords(

    longitude=(

        (
            ds.longitude
            + 180
        )
        % 360
    )
    - 180

).sortby(
    "longitude"
).sortby(
    "latitude"
)


# =============================================================================
# CONVERSIÓN DEL IUV
# =============================================================================

ds["uvi"] *= 40.0


# =============================================================================
# RECORTE
# =============================================================================

print()
print(
    "Recortando dominio de Paraguay..."
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


lons = ds_py.longitude.values

lats = ds_py.latitude.values


# =============================================================================
# ORDEN DE LATITUD
# =============================================================================

if lats[0] < lats[-1]:

    lats = lats[::-1]

    ds_py = ds_py.sel(
        latitude=lats
    )


# =============================================================================
# SHAPEFILE
# =============================================================================

print(
    "Cargando shapefile..."
)


if not os.path.exists(
    shp_py
):

    raise FileNotFoundError(
        f"No se encontró:\n{shp_py}"
    )


paraguay = gpd.read_file(
    shp_py
).to_crs(
    "EPSG:4326"
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


if not os.path.exists(
    dem_py
):

    raise FileNotFoundError(
        f"No se encontró:\n{dem_py}"
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
print("=" * 80)
print("                    GENERANDO MAPAS")
print("=" * 80)


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
# TAMAÑO DE CELDAS
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
# FACTOR TOPOGRÁFICO
# =============================================================================

grz = 0.00005


# =============================================================================
# MAPAS
# =============================================================================

for map_idx, dia_forecast in enumerate(dias_disponibles):

    print(
        f"\nGenerando mapa día {dia_forecast}/4..."
    )


    patches = []

    valores = []


    Z = ds_py[
        "uvi"
    ].sel(
        dia=dia_forecast
    ).values


    # -------------------------------------------------------------------------
    # RECORRER GRILLA
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


            # -----------------------------------------------------------------
            # DEM
            # -----------------------------------------------------------------

            col, row = (
                ~tform
                * (lon, lat)
            )

            row = int(row)
            col = int(col)

            if (
                0 <= row < topo.shape[0]
                and
                0 <= col < topo.shape[1]
            ):

                h = topo[row, col]

            else:

                h = 0


            # -----------------------------------------------------------------
            # IUV
            # -----------------------------------------------------------------

            val = (
                Z[i, j]
                *
                np.exp(
                    grz * h
                )
            )


            # -----------------------------------------------------------------
            # GEOMETRÍA
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


    ax = axes[map_idx]


    ax.add_collection(
        pc
    )


    # =============================================================================
    # LÍMITES DE PARAGUAY
    # =============================================================================

    paraguay.boundary.plot(

        ax=ax,

        edgecolor="black",

        linewidth=1.4

    )


    # =============================================================================
    # FECHA VÁLIDA
    # =============================================================================

    fecha_real = (
        fecha_run
        + timedelta(
            days=dia_forecast
        )
    )


    # =============================================================================
    # TÍTULO
    # =============================================================================

    ax.set_title(

        f"GFS 0.25 – IUV "
        f"(All Sky – Mediodía Solar)\n"

        f"Inicio de la corrida: "
        f"{fecha_run:%d/%m/%Y %H}Z\n"

        f"Válido para el día "
        f"{dias_semana[fecha_real.weekday()]} "
        f"{fecha_real:%d/%m/%Y}",

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
# COLORBARS
# =============================================================================

fig.subplots_adjust(

    bottom=0.22,

    right=0.82,

    hspace=0.28

)


# =============================================================================
# BARRA HORIZONTAL
# =============================================================================

cax1 = fig.add_axes(

    [
        0.15,
        0.12,
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


niveles_pos = [

    1.5,
    4.0,
    6.5,
    9.0,
    15.5

]


oms_pos = [

    (v - 0.5) / 20.0

    for v in niveles_pos

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
# BARRA VERTICAL
# =============================================================================

cax2 = fig.add_axes(

    [
        0.83,
        0.25,
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


niveles = [

    "Bajo",
    "Moderado",
    "Alto",
    "Muy Alto",
    "Extremo"

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
# GUARDAR MAPA
# =============================================================================

plt.savefig(

    salida,

    dpi=300,

    bbox_inches="tight"

)


plt.show()


# =============================================================================
# CERRAR FIGURA
# =============================================================================

plt.close()


# =============================================================================
# CREAR ZIP DE LA CORRIDA
# =============================================================================

zip_salida = os.path.join(

    corrida_dir,

    f"{nombre_corrida}.zip"

)


print()
print("=" * 80)
print("                    CREANDO ZIP")
print("=" * 80)


with zipfile.ZipFile(

    zip_salida,

    "w",

    zipfile.ZIP_DEFLATED

) as zipf:


    # -------------------------------------------------------------------------
    # Archivos GRIB2
    # -------------------------------------------------------------------------

    for archivo in archivos:

        if os.path.exists(
            archivo
        ):

            zipf.write(

                archivo,

                arcname=os.path.join(

                    f"DATA_{fecha}",

                    os.path.basename(
                        archivo
                    )

                )

            )


    # -------------------------------------------------------------------------
    # Mapas
    # -------------------------------------------------------------------------

    if os.path.exists(
        salida
    ):

        zipf.write(

            salida,

            arcname=os.path.join(

                f"MAPAS_{fecha}",

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
print(f"✓ Corrida       : {nombre_corrida}")

print(
    f"✓ Fecha corrida : "
    f"{fecha_run:%d/%m/%Y %H}Z"
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
