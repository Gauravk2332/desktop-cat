"""scripts/build.py — Build Windows executable with PyInstaller."""

import subprocess
import sys


def main():
    """Run PyInstaller to create a single-file Windows executable."""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "DesktopCat",
        "--icon", "assets/icon.ico",
        "--add-data", "assets;assets",
        "--noconfirm",
        "main.py",
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
