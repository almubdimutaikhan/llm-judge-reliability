# What the generator-family experiment measures

Earlier project notes called an elevated diagonal in a judge-by-generator matrix “self-preference.” The available experiment supports a narrower interpretation.

Every pair contains two answers from **one generator**: a TRIZ answer and a control answer. A judge chooses which is more creative. There is no own-output versus another-model-output choice within a pair. A higher TRIZ rate on the diagonal therefore measures a relationship between generator family, judge family, and treatment preference. It cannot identify a preference for the judge's own text over foreign text.

## Descriptive matrix

[`judge_generator.csv`](../results/judge_generator.csv) reports TRIZ preference for every judge–generator combination, using all valid answer presentations. Both answer orders are included, and the row count accompanies each cell. Same-family cells are outlined in the figure. DeepSeek's `deepseek-v3.1` and `deepseek-chat-v3.1` IDs map to the same family.

The matrix includes CrPO-Llama generations, but CrPO is not a judge. It therefore has no corresponding own-family cell. The raw diagonal and off-diagonal averages also have different mixtures of generators and missing answers, so their difference is not the primary estimate.

## Matched comparison

For each answer pair and persona, require both opposite-order records from each of the four API judges, with valid pick-to-arm mappings. Average each judge's two binary TRIZ choices; an order-inconsistent judge contributes 0.5 rather than being removed. This avoids selecting only the consistent cases when comparing judges.

For generators whose family is represented in the jury:

```
d(pair, persona) = own-family judge's TRIZ rate
                  − mean TRIZ rate of the other three judges
```

Average those differences within each engineering case, then average the 45 case means. A 10,000-draw bootstrap resamples whole cases (seed `20261027`). The estimate is **+3.78 percentage points**, with a 95% percentile interval **[1.38, 6.16]**. The paired table and case-level values are released so the weighting is inspectable.

Holding the answer pair fixed removes one source of quality variation. It still leaves model-specific evaluation criteria, style preferences, and familiarity as possible explanations. A statistically detectable treatment interaction is not a causal self-preference effect.

## A direct follow-up

A direct study would compare outputs from different generators on the same problems, randomize order, and ask every judge to assess all relevant pairings. Blind human or otherwise independent quality assessments would help distinguish a preference for better answers from own-family inflation. A separate experiment could randomize stated authorship while keeping the answer text unchanged to test identity-label effects.

This release contains neither of those interventions. The distinction follows the measurement concerns discussed by [Wataoka et al.](https://arxiv.org/abs/2410.21819) and [Chen et al.](https://aclanthology.org/2025.emnlp-main.86/); it is also why the figure uses “TRIZ preference” rather than “self-preference score.”
