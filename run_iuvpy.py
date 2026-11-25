import os, sys, glob, json, shutil, subprocess
from datetime import datetime, timezone
from drive_sync import service, FOLDER_ID, ensure_folder, download_dem, download_site_state, upload_file

REPO = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(REPO, "output")
SITE = os.path.join(REPO, "site")
MAPS = os.path.join(SITE, "maps")
os.makedirs(OUTPUT, exist_ok=True)
os.makedirs(MAPS, exist_ok=True)

model = os.environ.get("IUVPY_MODEL", "").lower()
run_date = os.environ.get("RUN_DATE", datetime.now(timezone.utc).strftime("%Y%m%d"))
run_hour = os.environ.get("RUN_HOUR", "12")

if model not in ("gfs", "cams"):
    raise ValueError("IUVPY_MODEL debe ser gfs o cams")
if model == "gfs":
    run_hour = "12"
elif run_hour not in ("00", "12"):
    raise ValueError("RUN_HOUR CAMS debe ser 00 o 12")

# Pull latest published maps from Drive so every deployment keeps the other models.
api, web_folder_id = download_site_state(MAPS, SITE)
download_dem(os.path.join(OUTPUT, "DEM_PY.tif"))

env = os.environ.copy()
env["IUVPY_OUTPUT_DIR"] = OUTPUT
env["RUN_DATE"] = run_date
env["RUN_HOUR"] = run_hour
env["MPLBACKEND"] = "Agg"
script = os.path.join(REPO, "scripts", "gfs_iuv.py" if model == "gfs" else "cams_iuv.py")
subprocess.run([sys.executable, script], cwd=REPO, env=env, check=True)

if model == "gfs":
    png_pattern = os.path.join(OUTPUT, f"GFS_IUV_12_{run_date}", f"MAPAS_{run_date}", f"IUV_GFS_{run_date}.png")
    zip_pattern = os.path.join(OUTPUT, f"GFS_IUV_12_{run_date}", "*.zip")
    web_name = "GFS_latest.png"
    model_label = "GFS 12Z"
else:
    run_id = run_date + run_hour
    png_pattern = os.path.join(OUTPUT, f"ECMWF_CAMS_IUV_{run_hour}_{run_date}", f"MAPAS_{run_id}", f"IUV_ECMWF_{run_date}_{run_hour}.png")
    zip_pattern = os.path.join(OUTPUT, f"ECMWF_CAMS_IUV_{run_hour}_{run_date}", "*.zip")
    web_name = f"CAMS_{run_hour}_latest.png"
    model_label = f"CAMS {run_hour}Z"

if not os.path.isfile(png_pattern):
    raise FileNotFoundError(f"No se generó el mapa esperado: {png_pattern}")
zip_files = glob.glob(zip_pattern)
if not zip_files:
    raise FileNotFoundError(f"No se generó el ZIP de corrida: {zip_pattern}")

# Copy current map to the static site and upload the run archive + latest map to Drive.
site_map = os.path.join(MAPS, web_name)
shutil.copy2(png_pattern, site_map)
archive_name = os.path.basename(zip_files[0])
upload_file(api, zip_files[0], archive_name, FOLDER_ID)
upload_file(api, site_map, web_name, web_folder_id)

status_path = os.path.join(SITE, "status.json")
if os.path.exists(status_path):
    try:
        with open(status_path, encoding="utf-8") as f:
            status = json.load(f)
    except Exception:
        status = {}
else:
    status = {}
status[model + ("_" + run_hour if model == "cams" else "")] = {
    "label": model_label,
    "run_date": run_date,
    "run_hour_utc": run_hour,
    "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "image": "maps/" + web_name,
}
with open(status_path, "w", encoding="utf-8") as f:
    json.dump(status, f, ensure_ascii=False, indent=2)
upload_file(api, status_path, "status.json", web_folder_id)
print("IUVPY finalizado; mapa publicado y corrida archivada en Drive.")
