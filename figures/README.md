# Figures

The intro uses Excalidraw. The three result charts use standard plotting fonts and axes.

| Figure | Files |
|---|---|
| Overview | [Editable Excalidraw](overview.excalidraw) · [PNG](overview.png) · [SVG](overview.svg) |
| Judge and generator | [PNG](family.png) · [SVG](family.svg) |
| Creative rankings | [PNG](creative_rankings.png) · [SVG](creative_rankings.svg) |
| Candidate removal | [PNG](elimination.png) · [SVG](elimination.svg) |

Open `overview.excalidraw` in [Excalidraw](https://excalidraw.com) to edit its native text, boxes, and arrows. Every figure reads `results/summary.json`.

```bash
pip install -r requirements.txt
npm ci
npx playwright install chromium
python scripts/figures.py
```

The renderer serves font assets locally and uses installed Chrome on macOS or Playwright Chromium elsewhere. `EXCALIDRAW_CHROME` selects another Chromium executable. No experiment data is sent to Excalidraw’s website.

Intro: Excalidraw 0.18.1 with Virgil. Result charts: Matplotlib 3.11.0 with DejaVu Sans. Fonts and renderers retain their upstream licenses.
