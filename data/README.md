# Released data

Six files contain **16,565 metadata rows**. Row counts are not counts of independent cases or API calls.

| File | Rows | Grain |
|---|---:|---|
| `jury.csv` | 6,768 | One TRIZ/control judge presentation, including errors |
| `selection.csv` | 2,714 | One creative ranking/scoring call, including isolated scoring |
| `same_order.csv` | 90 | One fixed-order repeat comparison |
| `permutations.csv` | 750 | One attempted 41-candidate permutation |
| `sessions.csv` | 399 | One round of a ten-round removal session |
| `resolution.csv` | 5,844 | One candidate/rank row, or a failed-ranking marker |

Creative tables preserve candidate IDs, order, rankings, numeric scores, removals, parser status, usage, and timing. They exclude generated concepts and raw model replies. Resolution rows repeat call-level fields for each ranked candidate; they must not be counted as separate API calls.

`manifest.json` records source/export hashes, source project HEADs, and working-tree status. The analysis verifies each export hash. Logged aliases, missing calls, and failures are preserved. Public clones of the source projects may not contain every record in the local snapshots.

The MIT license covers newly written software in `src/`, `scripts/`, and `tests/`. It grants no rights to underlying benchmark texts or model outputs. Consult source project terms before redistributing those materials.
