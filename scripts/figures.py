#!/usr/bin/env python3
"""Build the Excalidraw introduction and three standard result charts."""
import subprocess
import sys
from pathlib import Path

from draw_scenes import build

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    build()
    subprocess.run(["node", str(ROOT / "scripts/render_excalidraw.mjs")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/plot_results.py")], cwd=ROOT, check=True)
