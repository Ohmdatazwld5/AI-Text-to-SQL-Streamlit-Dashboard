from pathlib import Path
import urllib.request, zipfile, io

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "chinook.db"

# Optional: Auto-download DB if missing
CHINOOK_URL = "https://www.sqlitetutorial.net/wp-content/uploads/2018/03/chinook.zip"

def ensure_db():
    """Ensure chinook.db exists. If not, download it."""
    if DB_PATH.exists() and DB_PATH.stat().st_size > 0:
        return

    print("Downloading Chinook DB...")
    try:
        data = urllib.request.urlopen(CHINOOK_URL).read()
        zf = zipfile.ZipFile(io.BytesIO(data))
        for name in zf.namelist():
            if name.lower().endswith("chinook.db"):
                zf.extract(name, BASE_DIR)
                (BASE_DIR / name).rename(DB_PATH)
                break
        print("Chinook DB ready:", DB_PATH)
    except Exception as e:
        print("Failed to download Chinook DB:", e)

