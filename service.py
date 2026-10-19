"""Session orchestration shared by the HTTP API and integration tests."""
import copy
import secrets
import threading
import time
from dataclasses import dataclass, field
from engine import Probe
from fixtures import METADATA, PROFILES
from qloo import Qloo, rank_profile


@dataclass
class Session:
    probe: Probe
    metadata: dict
    source: str
    audit: list
    method: str = "adaptive"
    order: list = field(default_factory=list)
    study: bool = False
    created: float = field(default_factory=time.monotonic)
    lock: threading.Lock = field(default_factory=threading.Lock)


class Service:
    def __init__(self, client_factory=Qloo, max_sessions=300, ttl=3600):
        self.factory = client_factory
        self.sessions = {}
        self.verified = {}
        self.max_sessions = max_sessions
        self.ttl = ttl
        self.lock = threading.Lock()

    def prune(self):
        now = time.monotonic()
        self.sessions = {k: v for k, v in self.sessions.items() if now-v.created < self.ttl}
        self.verified = {k: v for k, v in self.verified.items() if now-v[1] < self.ttl}

    def search(self, query, kind):
        client = self.factory()
        payload = client.search(query, kind)
        # Search and Insights have different envelopes. Fail closed on changes.
        items = payload.get("results")
        if not isinstance(items, list):
            raise ValueError("Unexpected search schema: expected results array")
        result = []
        with self.lock:
            self.prune()
            if len(self.verified) > 3000:
                self.verified.clear()
            for item in items[:10]:
                if isinstance(item, dict) and isinstance(item.get("entity_id"), str) and isinstance(item.get("name"), str):
                    safe = {"entity_id": item["entity_id"], "name": item["name"], "kind": kind}
                    self.verified[safe["entity_id"]] = (safe, time.monotonic())
                    result.append(safe)
        return {"results": result, "source": "qloo-live"}

    def create(self, mode="demo", seeds=None, study=False):
        if mode == "demo":
            profiles, metadata, source, audit = copy.deepcopy(PROFILES), copy.deepcopy(METADATA), "synthetic-fixture", []
        elif mode == "live":
            if not isinstance(seeds, list) or not 2 <= len(seeds) <= 4 or any(not isinstance(s, str) for s in seeds):
                raise ValueError("Confirm 2 to 4 favorites from search")
            if len(set(seeds)) != len(seeds):
                raise ValueError("Choose different favorites")
            with self.lock:
                self.prune()
                if any(seed not in self.verified for seed in seeds):
                    raise ValueError("Search and confirm each favorite again; selection expired or unverified")
                names = {seed: self.verified[seed][0]["name"] for seed in seeds}
            client, profiles, metadata = self.factory(), {}, {}
            for index, seed in enumerate(seeds):
                response = client.insights([seed], take=50)
                profile, _ = rank_profile(response)
                # Known seed favorites must not be asked about or recommended.
                profiles[f"Anchor {index+1}: {names[seed]}"] = {k: v for k, v in profile.items() if k not in seeds}
                for item in response["results"]["entities"]:
                    identifier = item["entity_id"]
                    metadata[identifier] = {"entity_id": identifier, "name": item.get("name", identifier),
                                            "subtitle": "Qloo movie candidate", "description": "", 
                                            "explainability": item.get("query", {}).get("explainability") if isinstance(item.get("query"), dict) else None}
            source, audit = "qloo-live", client.audit
        else:
            raise ValueError("Mode must be demo or live")
        probe = Probe(profiles, {k: v["name"] for k, v in metadata.items()})
        method = secrets.choice(["adaptive", "fixed", "random", "immediate"]) if study else "adaptive"
        order = sorted(set.intersection(*(set(p) for p in profiles.values())))
        if method == "random":
            secrets.SystemRandom().shuffle(order)
        session = Session(probe, metadata, source, audit, method=method, order=order, study=study)
        with self.lock:
            self.prune()
            if len(self.sessions) >= self.max_sessions:
                raise RuntimeError("Session capacity reached; please try again later")
            identifier = secrets.token_urlsafe(32)
            self.sessions[identifier] = session
        return self.state(identifier)

    def _get(self, identifier):
        if not isinstance(identifier, str):
            raise ValueError("Invalid session")
        with self.lock:
            session = self.sessions.get(identifier)
            if not session or time.monotonic()-session.created >= self.ttl:
                self.sessions.pop(identifier, None)
                raise LookupError("Session expired; start again")
            return session

    def _next(self, session):
        probe = session.probe
        if session.method == "immediate":
            return {"action": "recommend", "reason": "Immediate recommendation baseline"}
        if session.method == "adaptive":
            return probe.next_question()
        remaining = [c for c in session.order if c not in probe.asked]
        if len(probe.history) >= probe.budget or not remaining:
            return {"action": "recommend", "reason": "Question budget reached or evidence exhausted"}
        return {"action": "ask", "entity_id": remaining[0], "label": probe.labels[remaining[0]]}

    def _state(self, identifier, session):
        probe = session.probe
        question = self._next(session)
        if question["action"] == "ask":
            question["entity"] = session.metadata[question["entity_id"]]
        common = set.intersection(*(set(p) for p in probe.profiles.values()))
        return {"session_id": identifier, "source": session.source, "budget": probe.budget,
                "method": session.method, "study": session.study,
                "answered": len(probe.history), "next": question,
                "weights": dict(zip(probe.profiles, probe.weights)),
                "history": [{**row, "name": probe.labels[row["entity_id"]]} for row in probe.history],
                "recommendations": [{**r, "entity": session.metadata[r["entity_id"]]} for r in probe.recommendations(3)],
                "evidence_coverage": {"shared_candidates": len(common), "profile_candidates": {k: len(v) for k, v in probe.profiles.items()}},
                "retrieval": session.audit,
                "notice": "Model weights and rank utilities are experimental, not calibrated enjoyment probabilities."}

    def state(self, identifier):
        session = self._get(identifier)
        with session.lock:
            return self._state(identifier, session)

    def answer(self, identifier, candidate, answer):
        session = self._get(identifier)
        with session.lock:
            question = self._next(session)
            if question["action"] != "ask" or candidate != question["entity_id"]:
                raise ValueError("This question is no longer current; refresh the session")
            session.probe.answer(candidate, answer)
            return self._state(identifier, session)

    def delete(self, identifier):
        with self.lock:
            self.sessions.pop(identifier, None)
