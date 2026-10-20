"""Session orchestration shared by the HTTP API and integration tests."""
import copy
import secrets
import threading
import time
from dataclasses import dataclass, field
from engine import Probe
from fixtures import METADATA, PROFILES
from qloo import Qloo, rank_profile
from experiment import PairedStudy


@dataclass
class Session:
    probe: Probe
    metadata: dict
    source: str
    audit: list
    evidence: dict = field(default_factory=dict)
    method: str = "adaptive"
    order: list = field(default_factory=list)
    study: bool = False
    undo_count: int = 0
    created: float = field(default_factory=time.monotonic)
    lock: threading.Lock = field(default_factory=threading.Lock)


class Service:
    def __init__(self, client_factory=Qloo, max_sessions=300, ttl=3600):
        self.factory = client_factory
        self.sessions = {}
        self.verified = {}
        self.insight_cache = {}
        self.max_sessions = max_sessions
        self.ttl = ttl
        self.lock = threading.Lock()

    def prune(self):
        now = time.monotonic()
        self.sessions = {k: v for k, v in self.sessions.items() if now-v.created < self.ttl}
        self.verified = {k: v for k, v in self.verified.items() if now-v[1] < self.ttl}
        self.insight_cache = {k: v for k, v in self.insight_cache.items() if now-v["stored"] < 600}

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
                    if isinstance(item.get("properties"), dict):
                        safe["release_year"] = item["properties"].get("release_year")
                    self.verified[safe["entity_id"]] = (safe, time.monotonic())
                    result.append(safe)
        return {"results": result, "source": "qloo-live"}

    def create(self, mode="demo", seeds=None, study=False, experiment=False, consent=False):
        if experiment and consent is not True:
            raise ValueError("Explicit pilot consent is required")
        if mode == "demo":
            profiles, metadata, source, audit = copy.deepcopy(PROFILES), copy.deepcopy(METADATA), "synthetic-fixture", []
            evidence = {}
            for anchor, values in profiles.items():
                ordered = sorted(values, key=lambda c: (-values[c], c))
                for rank, candidate in enumerate(ordered, 1):
                    evidence.setdefault(candidate, {})[anchor] = {"returned_rank": rank, "ranking_size": len(ordered),
                        "rank_utility": values[candidate], "source": "synthetic-fixture", "explainability": None}
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
            client, profiles, metadata, evidence = self.factory(), {}, {}, {}
            for index, seed in enumerate(seeds):
                with self.lock:
                    cached = self.insight_cache.get(seed)
                    cached = copy.deepcopy(cached) if cached and time.monotonic()-cached["stored"] < 600 else None
                if cached:
                    response = cached["response"]
                    client.audit.append({**cached["trace"], "cache_hit": True,
                                         "cache_age_seconds": round(time.monotonic()-cached["stored"], 2)})
                else:
                    response = client.insights([seed], take=50)
                    with self.lock:
                        self.prune()
                        if len(self.insight_cache) >= 200:
                            self.insight_cache.pop(min(self.insight_cache, key=lambda k: self.insight_cache[k]["stored"]))
                        self.insight_cache[seed] = {"stored": time.monotonic(), "response": copy.deepcopy(response),
                                                    "trace": copy.deepcopy(client.audit[-1]) if client.audit else {"source": "qloo-live"}}
                profile, _ = rank_profile(response)
                # Known seed favorites must not be asked about or recommended.
                anchor = f"Anchor {index+1}: {names[seed]}"
                profiles[anchor] = {k: v for k, v in profile.items() if k not in seeds}
                for rank, item in enumerate(response["results"]["entities"], 1):
                    identifier = item["entity_id"]
                    explanation = item.get("query", {}).get("explainability") if isinstance(item.get("query"), dict) else None
                    evidence.setdefault(identifier, {})[anchor] = {"returned_rank": rank, "ranking_size": len(profile),
                        "rank_utility": profile[identifier], "source": "qloo-live", "explainability": explanation}
                    metadata[identifier] = {"entity_id": identifier, "name": item.get("name", identifier),
                                            "subtitle": "Qloo movie candidate", "description": ""}
                    properties = item.get("properties")
                    if isinstance(properties, dict):
                        description = properties.get("description")
                        if isinstance(description, str):
                            metadata[identifier]["description"] = description[:1200]
                        year = properties.get("release_year")
                        if isinstance(year, int):
                            metadata[identifier]["subtitle"] = f"Film · {year} · Qloo metadata"
            source, audit = "qloo-live", client.audit
        else:
            raise ValueError("Mode must be demo or live")
        probe = Probe(profiles, {k: v["name"] for k, v in metadata.items()})
        method = secrets.choice(["adaptive", "fixed", "random", "immediate"]) if study else "adaptive"
        order = sorted(set.intersection(*(set(p) for p in profiles.values())))
        if method == "random":
            secrets.SystemRandom().shuffle(order)
        session = PairedStudy(profiles, metadata, source, evidence, audit, consent) if experiment else Session(
            probe, metadata, source, audit, evidence=evidence, method=method, order=order, study=study)
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
        if isinstance(session, PairedStudy):
            return session.state(identifier)
        probe = session.probe
        question = self._next(session)
        if question["action"] == "ask":
            question["entity"] = session.metadata[question["entity_id"]]
            if not session.study:
                question["answer_previews"] = probe.previews(question["entity_id"])
        common = set.intersection(*(set(p) for p in probe.profiles.values()))
        return {"session_id": identifier, "source": session.source, "budget": probe.budget,
                "method": session.method, "study": session.study,
                "undo_count": session.undo_count,
                "answered": len(probe.history), "next": question,
                "weights": dict(zip(probe.profiles, probe.weights)),
                "history": [{**row, "name": probe.labels[row["entity_id"]]} for row in probe.history],
                "recommendations": [{**r, "entity": session.metadata[r["entity_id"]],
                                     "evidence": session.evidence.get(r["entity_id"], {})} for r in probe.recommendations(3)],
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
            if isinstance(session, PairedStudy):
                return session.answer(identifier, candidate, answer)
            question = self._next(session)
            if question["action"] != "ask" or candidate != question["entity_id"]:
                raise ValueError("This question is no longer current; refresh the session")
            session.probe.answer(candidate, answer)
            return self._state(identifier, session)

    def delete(self, identifier):
        with self.lock:
            self.sessions.pop(identifier, None)

    def undo(self, identifier):
        session = self._get(identifier)
        with session.lock:
            if session.study:
                raise ValueError("Changing answers is disabled in research sessions to preserve the comparison")
            session.probe.undo()
            session.undo_count += 1
            return self._state(identifier, session)
