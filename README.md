# IUVPY — Pronóstico automático del Índice UV de Paraguay

Automatización de pronósticos de Índice Ultravioleta con GFS y CAMS/ECMWF, publicación de mapas y archivo de corridas en Google Drive.

## Instalación
Ver [README_SETUP.md](README_SETUP.md) para cargar archivos, configurar secretos y habilitar GitHub Pages.

## Modelos y horarios UTC
- CAMS 00Z: 11:13 UTC
- GFS 12Z: 20:17 UTC
- CAMS 12Z: 23:23 UTC

## Página
GitHub Pages se publica desde GitHub Actions. Tras habilitar Pages con origen **GitHub Actions**, la página estará en:
https://meteik.github.io/iuvpy/

## Seguridad
Nunca guardar claves API, `.cdsapirc`, `credentials.json` ni tokens OAuth en el repositorio.
