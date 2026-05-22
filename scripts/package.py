"""scripts/package.py — Create a portable zip distribution of the built exe."""

import os
import shutil
import zipfile
from pathlib import Path

DIST_DIR = Path("dist")
PACKAGE_NAME = "DesktopCat"


def main():
    """Package dist/DesktopCat.exe + README into a portable zip."""
    exe_path = DIST_DIR / "DesktopCat.exe"
    readme_path = Path("README.md")

    if not exe_path.exists():
        print("Error: DesktopCat.exe not found. Run build.py first.")
        return

    zip_name = f"{PACKAGE_NAME}.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(exe_path, arcname="DesktopCat.exe")
        if readme_path.exists():
            zf.write(readme_path, arcname="README.md")

    print(f"Packaged {zip_name} ({os.path.getsize(zip_name) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
