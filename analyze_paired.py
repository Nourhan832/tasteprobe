"""Descriptive paired pilot summaries from voluntary local exports."""
import argparse
import json
import statistics
from pathlib import Path


def summarize(paths):
    rows, warnings, seen = [], [], set()
    for path in paths:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if data.get("schema_version") != 2 or data.get("method") != "paired" or data.get("next", {}).get("action") != "recommend":
                raise ValueError("Expected a completed paired pilot export")
            if data.get("qa_context") or data.get("consent", {}).get("confirmed") is not True:
                raise ValueError("Scripted QA and non-consented records are not participant evidence")
            pilot = data.get("pilot_id")
            if not isinstance(pilot, str) or len(pilot) != 24:
                raise ValueError("Missing pilot identifier")
            if pilot in seen:
                warnings.append(f"{Path(path).name}: duplicate pilot ignored")
                continue
            seen.add(pilot)
            if data.get("source") not in ("qloo-live", "synthetic-fixture"):
                raise ValueError("Unknown source")
            displayed = {r["entity_id"] for r in data["recommendations"]}
            ratings = data.get("ratings", {})
            if any(c not in displayed or type(r) is not int or not 1 <= r <= 5 for c, r in ratings.items()):
                raise ValueError("Invalid final-candidate ratings")
            arms = {}
            for method in ("adaptive", "fixed"):
                arm = data["paired_results"][method]
                ids = [r["entity_id"] for r in arm["recommendations"]]
                known = [ratings[c] for c in ids if c in ratings]
                arms[method] = {"mean": statistics.mean(known) if known else None,
                                "rated": len(known), "candidates": len(ids), "questions": arm["questions"]}
            if any(arm["mean"] is None for arm in arms.values()):
                warnings.append(f"{Path(path).name}: at least one arm has no rated films; excluded from paired difference")
                continue
            rows.append({"source": data["source"], "arms": arms,
                         "difference": arms["adaptive"]["mean"]-arms["fixed"]["mean"]})
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            warnings.append(f"{Path(path).name}: ignored ({exc})")
    groups = []
    for source in ("qloo-live", "synthetic-fixture"):
        matching = [r for r in rows if r["source"] == source]
        if not matching:
            continue
        groups.append({"source": source, "paired_sessions": len(matching),
                       "mean_adaptive_minus_fixed_rating": statistics.mean(r["difference"] for r in matching),
                       "arms": {m: {"mean_session_rating": statistics.mean(r["arms"][m]["mean"] for r in matching),
                                    "rated_candidates": sum(r["arms"][m]["rated"] for r in matching),
                                    "displayed_candidates": sum(r["arms"][m]["candidates"] for r in matching),
                                    "mean_questions": statistics.mean(r["arms"][m]["questions"] for r in matching)}
                                for m in ("adaptive", "fixed")}})
    return {"summary": groups, "warnings": warnings,
            "limitations": "Exploratory descriptive summaries, not statistical proof. Repeated people cannot be detected; selective familiarity ratings and order effects may bias results. Exports are editable. Synthetic results never establish user benefit."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    print(json.dumps(summarize(args.files), indent=2))
