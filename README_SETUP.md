# IUVPY – automatización GitHub Actions

Este paquete adapta los scripts GFS y CAMS enviados para ejecución en un runner Linux de GitHub Actions.

## Archivos que contiene
- `scripts/gfs_iuv.py`: script GFS, con fecha/ruta adaptadas a variables de entorno.
- `scripts/cams_iuv.py`: script CAMS, con fecha/hora/ruta adaptadas.
- `run_iuvpy.py`: orquestador, descarga DEM, ejecuta modelo, copia mapa a web y archiva corrida en Drive.
- `drive_sync.py`: descarga/subida de archivos con OAuth refresh token.
- `.github/workflows/iuvpy.yml`: corridas automáticas y manuales.
- `site/`: página GitHub Pages.

## Antes de usar
1. Copiar el contenido de este paquete a la raíz del repositorio `meteik/iuvpy` y confirmar los cambios en `main`.
2. Copiar los cuatro componentes del shapefile a `assets/`:
   - `Departamentos_Paraguay.shp`
   - `Departamentos_Paraguay.shx`
   - `Departamentos_Paraguay.dbf`
   - `Departamentos_Paraguay.prj`
3. Copiar `NORTE.png` a `assets/NORTE.png`.
4. En la carpeta raíz de tu Google Drive IUVPY colocar `DEM_PY.tif`.
5. Configurar los Secrets indicados abajo.
6. En GitHub: Settings → Pages → Build and deployment → Source: **GitHub Actions**.

## Secrets requeridos (Settings → Secrets and variables → Actions)
- `ADS_API_KEY`: personal access token de Atmosphere Data Store (ADS).
- `GOOGLE_CLIENT_ID`: OAuth Client ID.
- `GOOGLE_CLIENT_SECRET`: OAuth Client Secret.
- `GOOGLE_REFRESH_TOKEN`: refresh token autorizado con scope `https://www.googleapis.com/auth/drive`.
- `GOOGLE_DRIVE_FOLDER_ID`: ID de la carpeta Drive IUVPY.

La carpeta Drive debe contener `DEM_PY.tif`. El workflow crea `IUVPY_WEB` dentro de esa carpeta para guardar los mapas latest y `status.json`; los ZIP de cada corrida se guardan en la carpeta principal.

## Horarios UTC
- CAMS 00Z: 11:13 UTC
- GFS 12Z: 20:17 UTC
- CAMS 12Z: 23:23 UTC

Los cron son UTC y pueden sufrir demoras de GitHub Actions. Se ejecutan diariamente en la rama default.

## Ejecución manual
Actions → IUVPY - Pronostico automatico → Run workflow → elegir `gfs`, `cams00` o `cams12`.

## Seguridad
No subir `credentials.json`, `.cdsapirc`, refresh tokens ni API keys al repositorio. Si una clave/token fue compartido en un chat o archivo público, revocarlo y generar otro.

## Nota de validación
El workflow debe probarse primero manualmente con cada modelo. El dataset CAMS requiere haber aceptado los términos de uso del dataset en ADS. El token ADS de `.cdsapirc` se usa como valor `key:` según la configuración API actual de ADS.
