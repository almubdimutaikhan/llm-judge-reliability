# Reproduce the analysis

Python 3.12 or later. Numerical analysis uses the standard library and makes no network requests or model calls.

```bash
python scripts/analyze.py
python -m unittest discover -s tests -v
```

The analysis verifies all six exported file hashes, checks record uniqueness and candidate mappings, and rebuilds the family diagnostic, creative-ranking comparisons, elimination tables, summary, and report.

To draw the figures:

```bash
pip install -r requirements.txt
npm ci
npx playwright install chromium
python scripts/figures.py
```

`make reproduce` runs analysis, tests, and figure generation. GitHub Actions runs the same commands and checks that numerical outputs match the committed files. The intro is editable Excalidraw; the three result charts use Matplotlib. Rendering serves font assets locally without sending experiment data to Excalidraw. Font rasterization can differ across systems.

| Output | Contents |
|---|---|
| `judge_generator.csv` | TRIZ preference by judge and generator |
| `family_paired.csv`, `family_cases.csv` | Matched differences and case-bootstrap inputs |
| `resolution.csv` | Full-ranking tau, quartile Jaccard, valid comparison counts |
| `permutations.csv`, `sessions.csv` | Removal diversity, completeness, session overlap |
| `selection.csv`, `fixed_order.csv` | Two-order selection and identical-order repeat comparisons |
| `summary.json`, `RESULTS.md` | Summary and generated report |

All outputs are in `results/`.

## Optional source reimport

The included data already supports analysis. To export a new version from the original local snapshots:

```bash
python scripts/import_data.py \
  --triz /path/to/triz-on-vs-off-agent \
  --bvsr /path/to/bvsr-llm-creativity
```

The source snapshots contain ignored or uncommitted records that may be absent from their public clones. Reimporting updates the manifest and creates a new data version. Source files are read without modification. New inference is a separate experiment.
