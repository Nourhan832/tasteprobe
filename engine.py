"""Experimental active preference elicitation over Qloo-derived hypotheses.

Weights and information gain describe this model, not calibrated human confidence.
Missing evidence is kept unknown. No demographic inference is used.
"""
import math
from dataclasses import dataclass, field


def entropy(weights):
    return -sum(p * math.log2(p) for p in weights if p > 0)


@dataclass
class Probe:
    profiles: dict[str, dict[str, float]]
    labels: dict[str, str]
    budget: int = 3
    weights: list[float] = field(init=False)
    asked: set[str] = field(default_factory=set)
    history: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if not self.profiles or self.budget < 0:
            raise ValueError("Profiles and a nonnegative question budget are required")
        if any(not math.isfinite(v) or not 0 <= v <= 1
               for profile in self.profiles.values() for v in profile.values()):
            raise ValueError("Utilities must be finite and in [0, 1]")
        self.weights = [1 / len(self.profiles)] * len(self.profiles)

    def _likelihoods(self, candidate):
        # Bounded response model. Missing rank is uninformative, never a dislike.
        return [.5 if candidate not in p else .1 + .8 * p[candidate]
                for p in self.profiles.values()]

    def gain(self, candidate):
        likelihoods = self._likelihoods(candidate)
        positive = sum(w * p for w, p in zip(self.weights, likelihoods))
        expected = 0.
        for answer_probability, likelihood in (
            (positive, likelihoods), (1-positive, [1-p for p in likelihoods])
        ):
            posterior = [w*p/answer_probability for w, p in zip(self.weights, likelihood)]
            expected += answer_probability * entropy(posterior)
        return max(0., entropy(self.weights) - expected)

    def next_question(self, min_gain=.01):
        if len(self.history) >= self.budget:
            return {"action": "recommend", "reason": "Question budget reached"}
        # Only compare entities observed under every hypothesis: missing != dislike.
        common = set.intersection(*(set(p) for p in self.profiles.values()))
        options = common - self.asked
        if not options:
            return {"action": "recommend", "reason": "No unasked question has complete evidence"}
        candidate = min(options, key=lambda c: (-self.gain(c), c))
        gain = self.gain(candidate)
        if gain < min_gain:
            return {"action": "recommend", "reason": "No useful distinction under the current model"}
        return {"action": "ask", "entity_id": candidate,
                "label": self.labels.get(candidate, candidate),
                "model_information_gain_bits": round(gain, 5)}

    def answer(self, candidate, answer):
        if answer not in ("like", "dislike", "skip"):
            raise ValueError("Answer must be like, dislike, or skip")
        if candidate in self.asked or len(self.history) >= self.budget:
            raise ValueError("Question already answered or budget exhausted")
        if any(candidate not in p for p in self.profiles.values()):
            raise ValueError("Question lacks complete evidence")
        before = entropy(self.weights)
        if answer != "skip":
            likelihood = self._likelihoods(candidate)
            if answer == "dislike":
                likelihood = [1-p for p in likelihood]
            updated = [w*p for w, p in zip(self.weights, likelihood)]
            total = sum(updated)
            self.weights = [w/total for w in updated]
        self.asked.add(candidate)
        self.history.append({"entity_id": candidate, "answer": answer,
                             "model_entropy_before": before,
                             "model_entropy_after": entropy(self.weights)})

    def recommendations(self, take=5):
        common = set.intersection(*(set(p) for p in self.profiles.values())) - self.asked
        result = []
        for candidate in common:
            score = sum(w*p[candidate] for w, p in zip(self.weights, self.profiles.values()))
            result.append({"entity_id": candidate, "label": self.labels.get(candidate, candidate),
                           "model_utility": round(score, 5)})
        return sorted(result, key=lambda r: (-r["model_utility"], r["entity_id"]))[:take]
