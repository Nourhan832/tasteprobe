"""Paired pilot: frozen evidence, disjoint holdout, randomized order, blind ratings.

This collects a local export, not automatic proof of effectiveness or consented
recruitment. Participants must explicitly consent in the UI before creation.
"""
import copy
import secrets
import threading
import time
from datetime import datetime, timezone
from engine import Probe


class PairedStudy:
    study = True
    method = "paired"
    undo_count = 0

    def __init__(self, profiles, metadata, source, evidence, audit, consent):
        if consent is not True:
            raise ValueError("Explicit pilot consent is required")
        common = sorted(set.intersection(*(set(p) for p in profiles.values())))
        if len(common) < 6:
            raise ValueError("The paired pilot needs at least 6 shared candidates; try other favorites")
        rng = secrets.SystemRandom()
        rng.shuffle(common)
        holdout_size = min(9, len(common)//2)
        self.holdout = set(common[:holdout_size])
        self.questions = set(common[holdout_size:])
        self.fixed_order = sorted(self.questions)
        self.probes = {method: Probe(copy.deepcopy(profiles), {k: v["name"] for k, v in metadata.items()},
                                    question_pool=self.questions, recommendation_pool=self.holdout)
                       for method in ("adaptive", "fixed")}
        self.order = ["adaptive", "fixed"]
        rng.shuffle(self.order)
        self.metadata, self.source, self.evidence, self.audit = metadata, source, evidence, audit
        self.stage = 0
        self.display_order = common[:holdout_size]
        self.created = time.monotonic()
        self.lock = threading.Lock()
        self.pilot_id = secrets.token_hex(12)  # Export identifier, never an access token.
        self.consent = {"confirmed": True, "recorded_at": datetime.now(timezone.utc).isoformat(),
                        "version": "exploratory-pilot-v1"}

    def _question(self, method):
        probe = self.probes[method]
        if method == "adaptive":
            return probe.next_question()
        remaining = [c for c in self.fixed_order if c not in probe.asked]
        if len(probe.history) >= 3 or not remaining:
            return {"action": "recommend", "reason": "Round completed"}
        return {"action": "ask", "entity_id": remaining[0], "label": probe.labels[remaining[0]]}

    def _advance(self):
        while self.stage < 2 and self._question(self.order[self.stage])["action"] != "ask":
            self.stage += 1

    def state(self, identifier):
        self._advance()
        complete = self.stage == 2
        question = {"action": "recommend", "reason": "Both rounds completed"} if complete else self._question(self.order[self.stage])
        if not complete:
            question = {**question, "entity": self.metadata[question["entity_id"]]}
            # The adaptive/fixed labels are withheld in the participant interface.
            question.pop("model_information_gain_bits", None)
        final = {method: probe.recommendations(3) for method, probe in self.probes.items()}
        shortlisted = {row["entity_id"] for rows in final.values() for row in rows}
        mixed = [{"entity_id": c, "label": self.metadata[c]["name"], "entity": self.metadata[c], "evidence": {}}
                 for c in self.display_order if c in shortlisted] if complete else []
        history = [{**row, "name": self.metadata[row["entity_id"]]["name"], "round": i+1}
                   for i, method in enumerate(self.order) for row in self.probes[method].history]
        result = {"session_id": identifier, "source": self.source, "method": "paired", "study": True,
                  "pilot_id": self.pilot_id, "consent": self.consent, "budget": 6,
                  "answered": len(history), "round_index": min(2, self.stage+1), "round_count": 2,
                  "round_answered": 0 if complete else len(self.probes[self.order[self.stage]].history),
                  "next": question, "weights": {}, "history": history, "recommendations": mixed,
                  "undo_count": 0, "retrieval": self.audit,
                  "evidence_coverage": {"shared_candidates": len(self.questions)+len(self.holdout),
                                        "question_pool": len(self.questions), "holdout_pool": len(self.holdout)},
                  "notice": "Exploratory paired pilot. No participant outcomes are inferred from the model."}
        if complete:
            result["paired_results"] = {method: {"recommendations": final[method],
                                                 "questions": len(probe.history),
                                                 "skips": sum(r["answer"] == "skip" for r in probe.history)}
                                         for method, probe in self.probes.items()}
            result["round_order"] = self.order
        return result

    def answer(self, identifier, candidate, answer):
        self._advance()
        if self.stage == 2:
            raise ValueError("Both pilot rounds are complete")
        method = self.order[self.stage]
        expected = self._question(method)
        if candidate != expected.get("entity_id"):
            raise ValueError("Question is no longer current; refresh the session")
        self.probes[method].answer(candidate, answer)
        return self.state(identifier)
