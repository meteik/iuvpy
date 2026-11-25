"""
Google Drive helpers for IUVPY.
Secrets are read only from environment variables; never put credentials in the repository.
"""
import os
import io
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_ID = os.environ["GOOGLE_DRIVE_FOLDER_ID"]

def service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def find_file(api, name, parent_id):
    q = f"name = '{name.replace(chr(39), chr(92)+chr(39))}' and '{parent_id}' in parents and trashed = false"
    result = api.files().list(
        q=q, pageSize=100,
        fields="files(id,name,mimeType,size)",
        supportsAllDrives=True, includeItemsFromAllDrives=True
    ).execute()
    return result.get("files", [])

def ensure_folder(api, name, parent_id):
    found = find_file(api, name, parent_id)
    for item in found:
        if item.get("mimeType") == "application/vnd.google-apps.folder":
            return item["id"]
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id]}
    return api.files().create(
        body=meta, fields="id", supportsAllDrives=True
    ).execute()["id"]

def download_file(api, file_id, destination):
    os.makedirs(os.path.dirname(destination) or ".", exist_ok=True)
    request = api.files().get_media(
        fileId=file_id, supportsAllDrives=True
    )
    with open(destination, "wb") as f:
        downloader = MediaIoBaseDownload(f, request, chunksize=8*1024*1024)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return destination

def download_named(api, name, parent_id, destination, required=False):
    files = find_file(api, name, parent_id)
    if not files:
        if required:
            raise FileNotFoundError(
                f"No se encontró '{name}' dentro de la carpeta Drive IUVPY. "
                "Subí el archivo allí y revisá el ID de carpeta."
            )
        return False
    download_file(api, files[0]["id"], destination)
    return True

def download_dem(destination):
    if os.path.isfile(destination) and os.path.getsize(destination) > 1_000_000:
        print("DEM ya disponible en el runner/cache; no se vuelve a descargar.")
        return
    api = service()
    download_named(api, "DEM_PY.tif", FOLDER_ID, destination, required=True)
    print(f"DEM descargado desde Google Drive: {destination}")

def download_site_state(site_maps_dir, site_dir):
    api = service()
    web_id = ensure_folder(api, "IUVPY_WEB", FOLDER_ID)
    os.makedirs(site_maps_dir, exist_ok=True)
    for name in ("GFS_latest.png", "CAMS_00_latest.png", "CAMS_12_latest.png"):
        download_named(api, name, web_id, os.path.join(site_maps_dir, name))
    download_named(api, "status.json", web_id, os.path.join(site_dir, "status.json"))
    return api, web_id

def upload_file(api, local_path, name, parent_id):
    existing = find_file(api, name, parent_id)
    media = MediaFileUpload(local_path, resumable=True)
    if existing:
        api.files().update(
            fileId=existing[0]["id"], media_body=media,
            supportsAllDrives=True
        ).execute()
        print(f"Drive actualizado: {name}")
    else:
        api.files().create(
            body={"name": name, "parents": [parent_id]},
            media_body=media, fields="id",
            supportsAllDrives=True
        ).execute()
        print(f"Drive subido: {name}")
