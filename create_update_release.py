import os
import zipfile

UPDATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "updates")
os.makedirs(UPDATES_DIR, exist_ok=True)

zip_path = os.path.join(UPDATES_DIR, "FlipkartBot_v3.1.zip")

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("version_3_1_installed.txt", "SUCCESS: Version 3.1 Has Been Successfully Installed!")
    z.writestr("release_info.json", '{"version": "3.1", "status": "updated"}')

print(f"[SUCCESS] Created release package at: {zip_path}")
