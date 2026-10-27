# Methods

| Study | Logged design | Unit for interpretation |
|---|---|---|
| Generator-family diagnostic | 45 engineering cases; TRIZ/control answers; four judge models, two personas, both answer orders | Engineering case |
| Creative rankings | One slate of 40 concepts; five permutations, ten requested repeats, three models | One slate |
| Elimination under permutation | 15 overlapping 41-candidate sets per judge/format; ten attempted permutations | Descriptive set variation; one problem |
| Elimination sessions | Five seeds; ten rounds, two orderings; ranking and batch scoring | Descriptive session variation; one problem |

## Generator-family diagnostic

Every pair contains TRIZ and control answers from one generator. The matrix uses all valid judge presentations, including order-inconsistent choices. A valid pick must map to its recorded answer arm and have no error.

The matched estimate requires both answer orders from each of the four API judges for a pair and persona. Average each judge’s two binary TRIZ choices, subtract the other three judges’ mean from the own-family judge’s rate, then average within case. A 10,000-draw bootstrap resamples the 45 case means with seed `20261027`. The independent unit is the case. [Full definition](SELF_PREFERENCE.md).

## Creative rankings

All creative follow-ups concern one Mars-boot design problem. In the resolution experiment, Gemini and DeepSeek each have 50 complete rankings; Claude has 46. Kendall tau compares complete permutations of the same candidate IDs. Quartile Jaccard compares groups of ten. Same-order and cross-order comparison counts are reported explicitly; these comparisons reuse rankings and are not independent observations.

## Elimination and sessions

A discard is usable only when the parser returns a candidate present in the input and its ID agrees with the recorded position. A parsed discard can be accepted even if the full ranking is unavailable. Failed calls are never counted as agreements.

Removal diversity counts distinct discarded candidates across the usable calls for each set. The results preserve attempted and usable call counts. Two ten-permutation sets have nine usable calls; the others have ten.

A session comparison requires ten rounds and ten distinct removals in both orderings. One Gemini ranking session has nine rows in one arm and is excluded. Session overlap is shared removals divided by ten; Jaccard is reported separately. The figure compares only seeds complete under both ranking and batch scoring.

The logged Claude identifier is `anthropic/claude-sonnet-5`; the release preserves that string without independently certifying the underlying version. The 41-candidate logs also contain GPT-4o failures. They remain in the data and result tables even where valid-pair counts are too small for the main figures.
