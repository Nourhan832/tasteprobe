"""Held-out synthetic evaluation, including deliberate response-model mismatch.

This is a stress test of assumptions, not a user study or live-Qloo benchmark.
Questions and evaluation candidates are disjoint to avoid evaluating on answers.
"""
import json
import math
import random
import statistics
from engine import Probe, entropy


def run(seed=832, trials=400):
    if trials < 2:
        raise ValueError("At least two trials are required")
    rng = random.Random(seed)
    scenarios = {}
    for scenario in ("matched", "mixed_tastes", "reversed_tastes", "frequent_skips"):
        rows = {method: [] for method in ("adaptive", "fixed", "random", "immediate")}
        for _ in range(trials):
            full = {str(h): {str(c): rng.random() for c in range(24)} for h in range(4)}
            selected = rng.randrange(4)
            truth = dict(full[str(selected)])
            if scenario == "mixed_tastes":
                other = full[str((selected+1) % 4)]
                truth = {c: .5*v+.5*other[c] for c, v in truth.items()}
            elif scenario == "reversed_tastes":
                truth = {c: 1-v for c, v in truth.items()}
            questions = [str(c) for c in range(12)]
            heldout = [str(c) for c in range(12, 24)]
            profiles = {h: {c: values[c] for c in questions} for h, values in full.items()}
            answers = {c: "like" if rng.random() < .1+.8*truth[c] else "dislike" for c in questions}
            if scenario == "frequent_skips":
                answers = {c: "skip" if rng.random() < .4 else answer for c, answer in answers.items()}
            random_order = rng.sample(questions, len(questions))
            oracle = sum(sorted((truth[c] for c in heldout), reverse=True)[:3])/3
            for method in rows:
                probe = Probe(profiles, {}, budget=3)
                if method != "immediate":
                    for step in range(3):
                        if method == "adaptive":
                            next_step = probe.next_question()
                            if next_step["action"] != "ask":
                                break
                            candidate = next_step["entity_id"]
                        else:
                            candidate = (questions if method == "fixed" else random_order)[step]
                        probe.answer(candidate, answers[candidate])
                predicted = {c: sum(w*values[c] for w, values in zip(probe.weights, full.values())) for c in heldout}
                chosen = sorted(heldout, key=lambda c: (-predicted[c], c))[:3]
                utility = sum(truth[c] for c in chosen)/3
                rows[method].append({"regret": max(0., oracle-utility), "utility": utility,
                                     "entropy": entropy(probe.weights), "questions": len(probe.history),
                                     "skips": sum(r["answer"] == "skip" for r in probe.history)})
        differences = [a["regret"]-b["regret"] for a, b in zip(rows["adaptive"], rows["fixed"])]
        mean = statistics.mean(differences)
        margin = 1.96*statistics.stdev(differences)/math.sqrt(trials)
        scenarios[scenario] = {
            "methods": {method: {"mean_"+metric: statistics.mean(r[metric] for r in values)
                                 for metric in ("regret", "utility", "entropy", "questions", "skips")}
                        for method, values in rows.items()},
            "adaptive_minus_fixed_regret": {"mean": mean, "approximate_95pct_monte_carlo_interval": [mean-margin, mean+margin]}}
    return {"source": "synthetic-heldout-stress-test", "seed": seed, "trials_per_scenario": trials,
            "question_candidates": 12, "disjoint_evaluation_candidates": 12,
            "interpretation": "Lower regret is better under generated utilities. Intervals describe simulation variability, not human outcomes. Negative adaptive-minus-fixed regret favors adaptive.",
            "limitations": "Invented profiles and utilities. No real users, Qloo calls, external validity, or calibrated personal confidence.",
            "scenarios": scenarios}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
