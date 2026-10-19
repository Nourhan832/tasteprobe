"""Model-matched simulation only: NOT a real-user or Qloo quality benchmark."""
import json
import random
from engine import Probe, entropy


def run(seed=832, trials=300):
    rng = random.Random(seed)
    summary = {name: [] for name in ("adaptive", "fixed", "random")}
    questions = {name: [] for name in summary}
    for _ in range(trials):
        profiles = {str(h): {str(c): rng.random() for c in range(24)} for h in range(4)}
        truth = profiles[str(rng.randrange(4))]
        # Shared pre-sampled responses provide paired comparisons.
        answers = {c: "like" if rng.random() < .1+.8*v else "dislike" for c, v in truth.items()}
        random_order = list(truth)
        rng.shuffle(random_order)
        for method in summary:
            probe = Probe(profiles, {}, budget=3)
            for step in range(3):
                if method == "adaptive":
                    question = probe.next_question()
                    if question["action"] != "ask":
                        break
                    candidate = question["entity_id"]
                else:
                    candidate = (list(truth) if method == "fixed" else random_order)[step]
                probe.answer(candidate, answers[candidate])
            summary[method].append(entropy(probe.weights))
            questions[method].append(len(probe.history))
    return {"source": "synthetic-model-matched", "seed": seed, "trials": trials,
            "warning": "Tests model discrimination only. Not human satisfaction, recommendation lift, or Qloo performance.",
            "methods": {m: {"mean_model_entropy_bits": sum(v)/len(v),
                             "mean_questions": sum(questions[m])/trials} for m, v in summary.items()}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
