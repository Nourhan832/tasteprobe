"""Summarize consented exported pilot sessions; no synthetic/live pooling."""
import argparse
import hashlib
import json
from pathlib import Path
from collections import defaultdict


def summarize(paths):
    groups, seen, warnings = defaultdict(list), set(), []
    for path in paths:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if data.get("schema_version") != 1 or data.get("next", {}).get("action") != "recommend":
                raise ValueError("Not a completed version-1 session")
            source, method = data.get("source"), data.get("method")
            if source not in ("synthetic-fixture", "qloo-live") or method not in ("adaptive", "fixed", "random", "immediate"):
                raise ValueError("Unknown source or method")
            # Session tokens are intentionally absent from exports. Deduplicate exact exports.
            digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
            if digest in seen:
                warnings.append(f"{Path(path).name}: duplicate export ignored")
                continue
            seen.add(digest)
            candidates = {r["entity_id"] for r in data["recommendations"]}
            values = []
            for identifier, rating in data.get("ratings", {}).items():
                if identifier not in candidates or type(rating) is not int or not 1 <= rating <= 5:
                    raise ValueError("Ratings must be integers 1–5 for final candidates")
                values.append(rating)
            if not values:
                warnings.append(f"{Path(path).name}: no rated recommendations")
                continue
            groups[(source, method)].append({"mean_rating": sum(values)/len(values), "rated": len(values),
                                             "questions": len(data["history"])})
        except (ValueError, KeyError, TypeError) as exc:
            warnings.append(f"{Path(path).name}: ignored ({exc})")
    return {"summary": [{"source": source, "method": method, "rated_sessions": len(rows),
             "mean_session_rating": sum(r["mean_rating"] for r in rows)/len(rows),
             "mean_questions": sum(r["questions"] for r in rows)/len(rows),
             "rated_candidates": sum(r["rated"] for r in rows)} for (source, method), rows in sorted(groups.items())],
            "warnings": warnings,
            "limitations": "Descriptive only. Sessions may repeat people; exports are user-editable. No causal improvement or statistical significance established. Synthetic sessions are not evidence of real recommendation quality."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    print(json.dumps(summarize(args.files), indent=2))
