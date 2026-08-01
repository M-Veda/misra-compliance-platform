"""
create_zip.py — Creates the final release ZIP of the MISRA Analyzer project.
Excludes node_modules, __pycache__, .git, venv, and compiled artifacts.
"""
import zipfile
import pathlib
import datetime

PROJECT = pathlib.Path(".")
ZIP_NAME = "MISRA_Analyzer_RC_" + datetime.date.today().strftime("%Y%m%d") + ".zip"

EXCLUDE_DIRS = {"node_modules", "__pycache__", ".git", ".venv", "venv", "dist", ".cache", ".pytest_cache"}
EXCLUDE_EXTS = {".pyc", ".pyo", ".log"}

count = 0
with zipfile.ZipFile(ZIP_NAME, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    for root, dirs, files in PROJECT.walk():
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for f in files:
            fp = root / f
            if fp.suffix in EXCLUDE_EXTS:
                continue
            rel = fp.relative_to(PROJECT)
            if str(rel) == ZIP_NAME:
                continue
            zf.write(fp, rel)
            count += 1

import os
size_mb = os.path.getsize(ZIP_NAME) / 1024 / 1024
print(f"ZIP created: {ZIP_NAME}")
print(f"  Files: {count}")
print(f"  Size:  {size_mb:.1f} MB")
