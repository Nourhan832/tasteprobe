# Synthetic held-out stress test

Run `python stress_benchmark.py`. `stress-results.json` contains the full output.
Seed: 832. Four scenarios, 400 trials each, 12 question candidates and a separate
12-candidate evaluation set. Four methods share the same generated responses per
trial. Utility is invented. These are **not human or live-Qloo results**.

Adaptive-minus-fixed held-out regret (lower is better):

| Generated scenario | Mean difference | Approximate 95% Monte Carlo interval |
|---|---:|---|
| Matched response model | -0.0367 | [-0.0537, -0.0196] |
| Mixed tastes | -0.0051 | [-0.0144, 0.0042] |
| Reversed tastes | -0.0342 | [-0.0491, -0.0192] |
| Frequent unfamiliar answers | -0.0370 | [-0.0518, -0.0222] |

In this generated experiment adaptive questions reduce average regret relative to
fixed questions in three scenarios. The mixed-taste interval crosses zero, so it
does not show a clear advantage. Full output includes random and immediate baselines;
the comparison table is not a claim that adaptive wins against every alternative.

These intervals describe variability across independent generated trials. They
say nothing about user satisfaction or population-level effectiveness. Simulated
utilities are bounded 0–1 values and are not real ratings. Further seeds, more model
families and a consenting live pilot are required before making product claims.

## Why this is stronger than the earlier sanity check
The original benchmark tracked only model entropy with a model-matched responder.
This one evaluates unasked candidates against generated ground truth and deliberately
violates the single-anchor model. It exposes the mixed-taste limitation instead of
treating lower model entropy as sufficient evidence of better recommendations.
