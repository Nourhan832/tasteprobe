"""Server-side Qloo HTTP adapter. No silent fixture fallback."""
import json
import os
import uuid
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


class Qloo:
    def __init__(self):
        self.key = os.environ.get("QLOO_API_KEY")
        self.host = os.environ.get("QLOO_API_HOST", "https://api.qloo.com").rstrip("/")
        parsed = urlparse(self.host)
        if parsed.scheme != "https" or parsed.hostname not in (
            "api.qloo.com", "hackathon.api.qloo.com", "staging.api.qloo.com"
        ) or parsed.port not in (None, 443) or parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise ValueError("Use an official Qloo HTTPS API origin")
        self.transport = os.environ.get("QLOO_TRANSPORT", "harness")
        if self.transport not in ("harness", "http"):
            raise ValueError("QLOO_TRANSPORT must be harness or http")
        if not self.key and os.environ.get("QLOO_ENABLED") != "1":
            raise ValueError("Configure the event credential on the server or run qloo setup --qloo")
        self.audit = []

    def harness(self, command, args):
        entry = os.environ.get("QLOO_HARNESS_ENTRY")
        if entry:
            if not Path(entry).is_file():
                raise ValueError("QLOO_HARNESS_ENTRY must point to the installed official harness bin.js")
            node = os.environ.get("QLOO_NODE") or shutil.which("node")
            if not node:
                raise ValueError("Install Node.js 22.19+ or configure QLOO_NODE")
            prefix = [node, entry]
        else:
            executable = shutil.which("qloo")
            if not executable or executable.lower().endswith((".cmd", ".bat")):
                raise ValueError("Install @qloo/qloo-harness; on Windows set QLOO_HARNESS_ENTRY to its bin.js and QLOO_NODE to node.exe")
            prefix = [executable]
        try:
            result = subprocess.run(prefix+["api", command]+args+["--json"],
                                    capture_output=True, text=True, timeout=45, shell=False)
        except subprocess.TimeoutExpired:
            raise TimeoutError("Qloo harness timed out") from None
        if result.returncode:
            raise RuntimeError("Qloo harness failed. Check event authentication, quota, and assigned API access. No fallback was used.")
        if len(result.stdout) > 2_000_000:
            raise ValueError("Qloo harness response exceeded size limit")
        data = json.loads(result.stdout)
        if not isinstance(data, list):
            raise ValueError("Unexpected harness JSON: expected entity array")
        return data

    def get(self, route, params):
        req = Request(self.host + route + "?" + urlencode(params),
                      headers={"X-Api-Key": self.key, "Accept": "application/json"})
        with urlopen(req, timeout=25) as response:
            data = json.load(response)
        self.audit.append({"origin": self.host, "route": route, "parameters": params,
                           "source": "qloo-live"})
        return data

    def search(self, text, kind="movie"):
        if kind not in ("movie", "artist", "book") or not text.strip() or len(text) > 200:
            raise ValueError("Supply a short search and movie, artist, or book type")
        if self.transport == "harness":
            data = self.harness("search", ["--query", text, "--type", kind, "--take", "10"])
            self.audit.append({"source": "qloo-live", "transport": "official-harness", "route": "/search", "query": text, "kind": kind})
            return {"results": data}
        return self.get("/search", {"query": text, "types": "urn:entity:" + kind, "take": 10})

    def insights(self, entity_ids, kind="movie", take=30):
        if kind not in ("movie", "artist", "book") or not 1 <= take <= 50 or not entity_ids:
            raise ValueError("Invalid insights inputs")
        ids = [str(uuid.UUID(value)) for value in entity_ids]
        if self.transport == "harness":
            data = self.harness("insights", ["--type", kind, "--signal-entities", ",".join(ids),
                                "--take", str(take), "--params", '{"feature.explainability":true}'])
            self.audit.append({"source": "qloo-live", "transport": "official-harness", "route": "/v2/insights", "seeds": ids, "take": take})
            return {"results": {"entities": data}}
        return self.get("/v2/insights", {"filter.type": "urn:entity:" + kind,
                        "signal.interests.entities": ",".join(ids), "take": take,
                        "feature.explainability": "true"})


def rank_profile(response):
    """Preserve ordering; use relative utility, never cross-request raw scores."""
    results = response.get("results")
    if not isinstance(results, dict) or not isinstance(results.get("entities"), list):
        raise ValueError("Unexpected Qloo response: expected results.entities; verify assigned API schema")
    entities = results["entities"]
    if not entities:
        raise ValueError("Qloo returned no candidates")
    profile, labels = {}, {}
    for i, entity in enumerate(entities):
        identifier = entity.get("entity_id")
        if not identifier or identifier in profile:
            raise ValueError("Missing or duplicate Qloo entity ID")
        profile[identifier] = 1 - i / max(1, len(entities)-1)
        labels[identifier] = entity.get("name", identifier)
    return profile, labels
