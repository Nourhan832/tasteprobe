"""Offline interaction and bounded live retrieval for TasteProbe."""
import argparse
import json
from engine import Probe
from qloo import Qloo, rank_profile


def synthetic():
    return Probe({
        "atmosphere": {"a": .95, "b": .1, "c": .3, "d": .8, "e": .2, "f": .7},
        "story": {"a": .1, "b": .95, "c": .3, "d": .2, "e": .8, "f": .6},
        "energy": {"a": .2, "b": .2, "c": .95, "d": .6, "e": .4, "f": .8}
    }, {"a": "Quiet imagery", "b": "A twisting story", "c": "Fast adventure",
        "d": "Synthetic film D", "e": "Synthetic film E", "f": "Synthetic film F"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", help="At least two confirmed Qloo entity UUIDs; one hypothesis per seed")
    args = parser.parse_args()
    client = None
    if args.seeds:
        if not 2 <= len(args.seeds) <= 5:
            parser.error("Provide 2 to 5 confirmed seed IDs")
        client, profiles, labels = Qloo(), {}, {}
        for seed in args.seeds:
            profile, names = rank_profile(client.insights([seed]))
            profiles[seed] = profile
            labels.update(names)
        probe = Probe(profiles, labels)
        print("LIVE QLOO: model hypotheses are seed-specific rankings, not known human taste types.")
    else:
        probe = synthetic()
        print("SYNTHETIC DEMO: invented profiles and labels. No Qloo call or real quality claim.")
    while True:
        question = probe.next_question()
        print(json.dumps(question, indent=2))
        if question["action"] != "ask":
            break
        while True:
            answer = input("Would you enjoy this? [like/dislike/skip]: ").strip().lower()
            if answer in ("like", "dislike", "skip"):
                break
        probe.answer(question["entity_id"], answer)
    print(json.dumps({"recommendations": probe.recommendations(), "trace": probe.history,
                      "retrieval": client.audit if client else "synthetic"}, indent=2))


if __name__ == "__main__":
    main()
