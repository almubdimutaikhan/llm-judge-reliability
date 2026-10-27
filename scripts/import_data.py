#!/usr/bin/env python3
"""Export decision records and identifiers, excluding generated concepts and model prose."""
import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--triz", type=Path, required=True)
    p.add_argument("--bvsr", type=Path, required=True)
    a = p.parse_args()
    manifest = {"snapshot_date": "2026-10-27", "files": [], "sources": []}
    def record(base, source, target, rows):
        manifest["files"].append({"source_project": base.name, "source_path": source,
            "source_sha256": sha(base / source), "export": "data/" + target,
            "export_sha256": sha(ROOT / "data" / target), "rows": rows})
    def export(base, source, target, fields=None):
        with (base / source).open(newline="") as f:
            reader = csv.DictReader(f)
            fields = fields or reader.fieldnames
            rows = [{k: r[k] for k in fields} for r in reader]
        with (ROOT / "data" / target).open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            w.writeheader(); w.writerows(rows)
        record(base, source, target, len(rows))

    export(a.triz, "results/main/judgements.csv", "jury.csv")
    export(a.bvsr, "results/mitigation/calls.csv", "selection.csv",
        "set_id n condition judge shuffle target_candidate_id presented_order parse_status ranking scores discard_position discard_candidate_id n_tied_at_min prompt_tokens completion_tokens latency_seconds cached".split())
    export(a.bvsr, "results/mitigation/determinism.csv", "same_order.csv")
    export(a.bvsr, "results/mitigation/victim_diversity.csv", "permutations.csv")
    export(a.bvsr, "results/mitigation/survival.csv", "sessions.csv")
    export(a.bvsr, "results/resolution/rankings.csv", "resolution.csv")
    for directory in (a.triz, a.bvsr):
        head = subprocess.check_output(["git", "-C", str(directory), "rev-parse", "HEAD"], text=True).strip()
        dirty = bool(subprocess.check_output(["git", "-C", str(directory), "status", "--porcelain"], text=True))
        manifest["sources"].append({"project": directory.name, "head": head, "uncommitted_changes": dirty})
    (ROOT / "data/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Exported", sum(x["rows"] for x in manifest["files"]), "rows; source text excluded.")


if __name__ == "__main__":
    main()
