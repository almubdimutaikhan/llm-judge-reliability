#!/usr/bin/env python3
"""Recompute judge-family and creative-selection results from released metadata."""
import csv
import hashlib
import itertools
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from metrics import bootstrap_cases, jaccard, kendall

VALID = {"ok", "discard_only"}


def read(name):
    with (ROOT / "data" / name).open(newline="") as f:
        return list(csv.DictReader(f))


def write(name, rows):
    with (ROOT / "results" / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in rows for k in r)), lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def unique(rows, fields):
    keys = [tuple(r[k] for k in fields) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError(f"Duplicate records: {fields}")


def validate():
    m = json.loads((ROOT / "data/manifest.json").read_text())
    for r in m["files"]:
        path = ROOT / r["export"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != r["export_sha256"]:
            raise ValueError(f"Evidence hash mismatch: {path.name}")
    return m


def jury_results():
    rows = read("jury.csv")
    unique(rows, "pair_id judge_model persona order".split())
    good = [r for r in rows if not r["error"] and r["pick"] in ("A", "B") and r["picked_arm"] == r["a_arm" if r["pick"] == "A" else "b_arm"]]
    family = lambda m: m.split("/")[0].lower()
    matrix = []
    for jm in sorted({r["judge_model"] for r in good}):
        for gm in sorted({r["gen_model"] for r in good}):
            rs = [r for r in good if r["judge_model"] == jm and r["gen_model"] == gm]
            matrix.append({"judge": jm, "generator": gm, "same_family": family(jm) == family(gm),
                "rows": len(rs), "triz_rate": st.mean(r["picked_arm"] == "triz" for r in rs)})
    by = defaultdict(list)
    for r in good:
        by[r["pair_id"], r["persona"], r["judge_model"]].append(r)
    paired = defaultdict(dict)
    for (pid, persona, jm), rs in by.items():
        if len(rs) == 2 and len({r["order"] for r in rs}) == 2 and rs[0]["a_arm"] == rs[1]["b_arm"]:
            paired[pid, persona][jm] = {"p": st.mean(r["picked_arm"] == "triz" for r in rs), "case": rs[0]["case_id"], "gen": rs[0]["gen_model"]}
    case_values = defaultdict(list); effects = []
    for (pid, persona), judges in paired.items():
        if len(judges) != 4:
            continue
        own = [(jm, r) for jm, r in judges.items() if family(jm) == family(r["gen"])]
        if len(own) != 1:
            continue
        jm, r = own[0]; others = [x["p"] for name, x in judges.items() if name != jm]
        delta = r["p"]-st.mean(others)
        effects.append({"pair_id": pid, "persona": persona, "case_id": r["case"], "generator": r["gen"],
            "own_family_triz_rate": r["p"], "other_judges_triz_rate": st.mean(others), "difference": delta})
        case_values[r["case"]].append(delta)
    case_rows = [{"case_id": k, "paired_groups": len(v), "difference": st.mean(v)} for k, v in sorted(case_values.items())]
    estimate = bootstrap_cases([r["difference"] for r in case_rows])
    write("judge_generator.csv", matrix); write("family_paired.csv", effects); write("family_cases.csv", case_rows)
    return {"valid_rows": len(good), "matrix": matrix, "paired_groups": len(effects),
            "family_interaction": estimate, "interpretation": "TRIZ treatment-preference interaction, not identified own-vs-other self-preference"}


def parse_discard(r, key, order_key="presented_order"):
    ids = r[order_key].split(";")
    d = r[key]
    if r["parse_status"] not in VALID or not d or d not in ids:
        return False
    pos_key = "discard_position" if "discard_position" in r else "discarded_position"
    assert ids[int(r[pos_key])-1] == d and len(set(ids)) == int(r.get("n", r.get("n_presented", len(ids))))
    return True


def creative_results():
    calls = read("selection.csv"); fixed = read("same_order.csv"); victims = read("permutations.csv")
    unique(calls, "set_id condition judge shuffle target_candidate_id".split())
    unique(victims, "set_id condition judge perm".split())
    same_summary = []; permutation_rows = []; selection_summary = []
    groups = defaultdict(list)
    for r in calls:
        if r["condition"] != "score_solo":
            groups[r["judge"], r["condition"], r["n"]].append(r)
    for (judge, condition, n), rs in sorted(groups.items()):
        usable = [r for r in rs if parse_discard(r, "discard_candidate_id")]
        by = defaultdict(list)
        for r in usable:
            by[r["set_id"]].append(r)
        pairs = [v for v in by.values() if len(v) == 2 and len({r["shuffle"] for r in v}) == 2]
        selection_summary.append({"judge": judge, "condition": condition, "n": int(n), "attempted_calls": len(rs),
            "usable_calls": len(usable), "complete_pairs": len(pairs),
            "agreement": st.mean(a["discard_candidate_id"] == b["discard_candidate_id"] for a, b in pairs) if pairs else None,
            "last_slot_rate": st.mean(int(r["discard_position"]) == int(n) for r in usable) if usable else None,
            "mean_tokens": st.mean(int(r["prompt_tokens"])+int(r["completion_tokens"]) for r in rs),
            "median_latency": st.median(float(r["latency_seconds"]) for r in rs)})
    for (judge, condition), rs in itertools.groupby(sorted(fixed, key=lambda r: (r["judge"], r["condition"])), key=lambda r: (r["judge"], r["condition"])):
        rs = list(rs)
        good = [r for r in rs if r["rep0_status"] in VALID and r["rep1_status"] in VALID and r["rep0_discard"] and r["rep1_discard"]]
        same_summary.append({"judge": judge, "condition": condition, "trials": len(rs), "valid_trials": len(good),
            "agreement": st.mean(r["rep0_discard"] == r["rep1_discard"] for r in good) if good else None})
    by = defaultdict(list)
    for r in victims:
        by[r["judge"], r["condition"], r["set_id"]].append(r)
    for (judge, condition, slate), rs in sorted(by.items()):
        good = [r for r in rs if parse_discard(r, "discarded_id")]
        pairs = list(itertools.combinations(good, 2))
        permutation_rows.append({"judge": judge, "condition": condition, "set_id": slate,
            "attempted_calls": len(rs), "usable_calls": len(good), "distinct_removals": len({r["discarded_id"] for r in good}),
            "agreement": st.mean(a["discarded_id"] == b["discarded_id"] for a, b in pairs) if pairs else None,
            "last_slot_rate": st.mean(r["discarded_position"] == "41" for r in good) if good else None})
    sessions = read("sessions.csv"); unique(sessions, "session judge condition arm round".split())
    by = defaultdict(list)
    for r in sessions:
        by[r["judge"], r["condition"], r["session"]].append(r)
    session_rows = []
    for (judge, condition, session), rs in sorted(by.items()):
        arms = {a: [r for r in rs if r["arm"] == a] for a in ("A", "B")}
        complete = all(len(v) == 10 and {int(r["round"]) for r in v} == set(range(1, 11)) and all(parse_discard(r, "discarded_id") for r in v) for v in arms.values())
        a, b = ({r["discarded_id"] for r in arms[x]} for x in ("A", "B"))
        if complete:
            assert len(a) == len(b) == 10, "A discarded item cannot be removed twice in one session"
        session_rows.append({"judge": judge, "condition": condition, "session": session, "rows_A": len(arms["A"]),
            "rows_B": len(arms["B"]), "complete": complete, "shared_removals": len(a & b) if complete else None,
            "removal_overlap_fraction": len(a & b)/10 if complete else None, "removal_jaccard": jaccard(a, b) if complete else None})
    resolution = read("resolution.csv"); by = defaultdict(list)
    for r in resolution:
        by[r["judge"], r["perm"], r["rep"]].append(r)
    rankings = defaultdict(list)
    invalid = Counter()
    for (judge, perm, rep), rs in sorted(by.items()):
        ids = [r["candidate_id"] for r in sorted(rs, key=lambda r: int(r["rank_position"] or 0))]
        if len(rs) == len(set(ids)) == 40 and {int(r["rank_position"]) for r in rs} == set(range(1, 41)) and all(r["parse_status"] == "ok" for r in rs):
            rankings[judge].append((perm, rep, ids))
        else:
            invalid[judge] += 1
    resolution_rows = []
    for judge, ranks in sorted(rankings.items()):
        for which in ("same_order", "cross_order"):
            pairs = [(a[2], b[2]) for a, b in itertools.combinations(ranks, 2) if (a[0] == b[0]) == (which == "same_order")]
            row = {"judge": judge, "comparison": which, "valid_calls": len(ranks), "invalid_calls": invalid[judge],
                   "ranking_pairs": len(pairs), "kendall_tau": st.mean(kendall(a, b) for a, b in pairs)}
            for q in range(4):
                row[f"Q{q+1}_jaccard"] = st.mean(jaccard(a[q*10:(q+1)*10], b[q*10:(q+1)*10]) for a, b in pairs)
            resolution_rows.append(row)
    write("selection.csv", selection_summary); write("fixed_order.csv", same_summary)
    write("permutations.csv", permutation_rows); write("sessions.csv", session_rows); write("resolution.csv", resolution_rows)
    solo_cost = []
    for judge in sorted({r["judge"] for r in calls if r["condition"] == "score_solo"}):
        sub = [r for r in calls if r["judge"] == judge and r["condition"] == "score_solo" and r["n"] == "41"]
        by_set = defaultdict(list)
        for r in sub:
            by_set[r["set_id"]].append(r)
        complete = [rs for rs in by_set.values() if len(rs) == len({r["target_candidate_id"] for r in rs}) == 41]
        solo_cost.append({"judge": judge, "complete_sets": len(complete), "calls_per_set": 41,
            "mean_tokens_per_set": st.mean(sum(int(r["prompt_tokens"])+int(r["completion_tokens"]) for r in rs) for rs in complete)})
    return {"selection": selection_summary, "fixed_order": same_summary, "permutations": permutation_rows,
            "sessions": session_rows, "resolution": resolution_rows, "isolated_scoring_cost": solo_cost}


def report(summary):
    names = {"deepseek/deepseek-chat-v3.1": "DeepSeek V3.1", "google/gemini-2.5-flash": "Gemini 2.5 Flash",
             "anthropic/claude-sonnet-5": "Claude Sonnet (logged ID)"}
    family = summary["jury"]["family_interaction"]
    lines = ["# Results", "", "Generated by `python scripts/analyze.py` from the six released data files.", "",
             "## Generator-family diagnostic", "",
             f"On matched TRIZ/control answer pairs, own-family judges choose TRIZ **{family['mean']*100:.2f} percentage points** more often than the other three judges (95% case bootstrap [{family['ci_low']*100:.2f}, {family['ci_high']*100:.2f}], {family['cases']} cases). Both answers in each pair come from the same generator. This estimates a treatment-preference interaction, not own-output versus other-output self-preference.", "",
             "[Matrix](judge_generator.csv) · [Matched groups](family_paired.csv) · [Case-level differences](family_cases.csv)", "",
             "## Creative rankings", "", "One slate of 40 concepts, five permutations, ten requested repeats per permutation.", "",
             "| Model | Valid rankings | Same-order tau | Cross-order tau |", "|---|---:|---:|---:|"]
    creative = summary["creative"]
    for model in sorted({r["judge"] for r in creative["resolution"]}):
        rows = {r["comparison"]: r for r in creative["resolution"] if r["judge"] == model}
        lines.append(f"| {names[model]} | {rows['same_order']['valid_calls']}/50 | {rows['same_order']['kendall_tau']:.3f} | {rows['cross_order']['kendall_tau']:.3f} |")
    lines += ["", "Four Claude calls lack complete rankings. The comparisons reuse one slate and are not independent samples. [Quartile overlap and denominators](resolution.csv).", "",
              "## Elimination over ten permutations", "", "| Model | Format | Sets | Mean distinct removals | Mean agreement |", "|---|---|---:|---:|---:|"]
    for model, condition in sorted({(r["judge"], r["condition"]) for r in creative["permutations"]}):
        rows = [r for r in creative["permutations"] if r["judge"] == model and r["condition"] == condition]
        lines.append(f"| {names[model]} | {condition} | {len(rows)} | {st.mean(r['distinct_removals'] for r in rows):.2f} | {st.mean(r['agreement'] for r in rows):.1%} |")
    lines += ["", "Each set has ten attempted calls. One Gemini ranking set and one Claude set have nine usable calls; the others have ten. Sets overlap and all concern one Mars-boot problem.", "",
              "## Ten-round sessions", "", "| Model | Format | Complete sessions | Shared removals / 10 |", "|---|---|---:|---:|"]
    for model, condition in sorted({(r["judge"], r["condition"]) for r in creative["sessions"]}):
        rows = [r for r in creative["sessions"] if r["judge"] == model and r["condition"] == condition and r["complete"]]
        lines.append(f"| {names[model]} | {condition} | {len(rows)} | {st.mean(r['removal_overlap_fraction'] for r in rows):.1%} |")
    lines += ["", "One Gemini ranking session has nine rows rather than ten in one arm and is excluded. The figure uses only sessions complete in both ranking and scoring. This overlap is intersection size divided by ten; [session-level data](sessions.csv) also reports Jaccard.", "",
              "See [methods](../docs/METHODS.md), [interpretation](../docs/SELF_PREFERENCE.md), and [limitations](../docs/LIMITATIONS.md)."]
    (ROOT / "results/RESULTS.md").write_text("\n".join(lines) + "\n")


def main():
    validate()
    summary = {"jury": jury_results(), "creative": creative_results()}
    (ROOT / "results/summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    report(summary)
    print("Verified data hashes; rebuilt judge-family and creative-selection results.")


if __name__ == "__main__":
    main()
