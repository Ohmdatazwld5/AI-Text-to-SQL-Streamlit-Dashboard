from pathlib import Path
import urllib.request, zipfile, io
import sys

# Project root (folder containing this file)
BASE_DIR = Path(__file__).resolve().parent

# Default name we want to use
DEFAULT_DB_NAME = "chinook.db"
DEFAULT_DB_PATH = BASE_DIR / DEFAULT_DB_NAME

# Download URL for fallback (official Chinook sample)
CHINOOK_URL = "https://www.sqlitetutorial.net/wp-content/uploads/2018/03/chinook.zip"


def _find_existing_chinook_db() -> Path | None:
    """
    Scan the project directory for any file that looks like a Chinook SQLite DB.
    Case-insensitive match on name, endswith .db / .sqlite / .sqlite3.
    """
    for p in BASE_DIR.iterdir():
        if not p.is_file():
            continue
        low = p.name.lower()
        if "chinook" in low and (low.endswith(".db") or low.endswith(".sqlite") or low.endswith(".sqlite3")):
            return p
    return None


def ensure_db() -> Path:
    """
    Ensure we have a usable Chinook DB and return its path.

    Priority:
      1. If DEFAULT_DB_PATH exists and has size > 0, use it.
      2. Else search for any Chinook-like DB file in repo root.
      3. Else download from CHINOOK_URL and extract.
    """
    # 1. Already present at expected name?
    if DEFAULT_DB_PATH.exists() and DEFAULT_DB_PATH.stat().st_size > 0:
        return DEFAULT_DB_PATH

    # 2. Search for alternate name (case differences, etc.)
    found = _find_existing_chinook_db()
    if found and found.stat().st_size > 0:
        # Normalize name to chinook.db if different
        if found.name != DEFAULT_DB_NAME:
            try:
                found.rename(DEFAULT_DB_PATH)
                return DEFAULT_DB_PATH
            except Exception:
                # can't rename (read-only FS) -> just use found path
                return found
        return found

    # 3. Download fallback
    try:
        print("Downloading Chinook DB...", file=sys.stderr)
        data = urllib.request.urlopen(CHINOOK_URL).read()
        zf = zipfile.ZipFile(io.BytesIO(data))
        extracted_path = None
        for name in zf.namelist():
            if name.lower().endswith("chinook.db"):
                zf.extract(name, BASE_DIR)
                extracted_path = BASE_DIR / name
                break
        if extracted_path and extracted_path.exists():
            # Normalize name
            try:
                extracted_path.rename(DEFAULT_DB_PATH)
                return DEFAULT_DB_PATH
            except Exception:
                return extracted_path
        else:
            print("Chinook DB not found in downloaded zip!", file=sys.stderr)
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)

    # 4. Final fallback: return default path (will create empty DB if opened writeable)
    return DEFAULT_DB_PATH


# Public: resolved DB path (call ensure_db at import)
DB_PATH = ensure_db()


