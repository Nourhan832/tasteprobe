# TasteProbe

**The taste agent that learns which question to ask next.**

TasteProbe is a bounded adaptive discovery agent for movie recommendations. It uses
separate cultural anchors, selects a question by expected model information gain,
updates its hypothesis weights, and stops when the question budget or evidence is
exhausted. The browser talks to a Python backend; credentials stay server-side.

## Status

Working backend-connected demo and **one verified live Qloo walkthrough**. Event
entity search, two real movie ranking requests, three adaptive questions, skip
handling, a final shortlist and JSON export passed on October 20, 2026.
See `docs/LIVE_VERIFICATION.md` for the exact scenario and payload findings.

37 automated tests pass locally. Human recommendation quality is not established.
The project still needs an externally hosted demo and consenting user evaluation;
no prize or improvement claim is made.

## Run locally

Python 3.10+ is sufficient for demo mode; no Python dependencies to install.

```text
python server.py
```

Open http://127.0.0.1:8766 . Do not use a static-only server: discovery uses the API.
Sessions are memory-only, expire after an hour, and are pruned every 30 seconds.
Restart or end-session deletes the session immediately. Server restarts delete all.
Ratings are held in the browser, exported only on request, and not collected in a database.

```text
python -m unittest discover -s tests -v
node --check dist/app.js
python benchmark.py
python stress_benchmark.py
```

## Live Qloo setup

For this workspace, `python start_live.py` opens a hidden-input prompt for the existing
event key and serves the app immediately at
http://127.0.0.1:8767 . Qloo access is checked on demand in the UI. A network timeout leaves the app
running so you can retry without re-entering the key.
The key stays in the launcher process environment and
is removed when it exits; it is not written to source or a .env file.
The launcher selects https://hackathon.api.qloo.com from the organizer email.
The adapter maps that validated host to QLOO_BASE_URL and QLOO_TRUSTED_BASE_URL.
The launcher now reloads backend edits while keeping the existing key in process
memory, so future code updates do not require entering it again. This development
mode is loopback-only, and backend updates reset active discovery sessions.


Request event access from https://qloo.devpost.com/resources . The current event
supports the official harness: https://github.com/qloo/qloo-hackathon-kit .
Install Node.js 22.19+ and `@qloo/qloo-harness@0.1.26`, then use
`qloo setup --qloo` to enter the event credential privately. Never paste a key into
chat, source control, a browser frontend, or a command-line argument.

The backend defaults to `QLOO_TRANSPORT=harness` and runs `qloo api search` and
`qloo api insights` without a shell. Use `QLOO_ENABLED=1` when relying on private
harness configuration, or configure `QLOO_API_KEY` in the hosting secret store.
On Windows, set `QLOO_HARNESS_ENTRY` to the installed official package's
`dist/bin.js` and `QLOO_NODE` to node.exe. Example environment variable names are
in `.env.example`; this app does not automatically load .env files.

The legacy HTTP adapter is available only through explicit `QLOO_TRANSPORT=http`;
use that only if organizers approve direct HTTP access for your credential.
`QLOO_API_HOST` must be an allowed official origin. No endpoint or credential fallback.

In live mode, search and confirm 2-4 favorites from movies, artists or books.
Each anchor retrieves one movie ranking. Questions require evidence under every
anchor. Missing candidates mean unknown evidence, not dislike. If overlap is
insufficient, the agent stops and asks the user to try other anchors.

## What the agent actually does

1. Resolve favorite identities with user confirmation.
2. Retrieve seed-specific Qloo movie rankings and retain provenance.
3. Convert returned rank order to heuristic utility within each ranking.
4. Choose the question with greatest expected information gain under a bounded
   response model, over the shared candidate set.
5. Update model weights for like/dislike; keep weights unchanged for unfamiliar.
6. Stop after at most three questions or when modeled gain is too small.
7. Rank unseen-in-session candidates and export decision evidence and optional ratings.

This is an explicit policy agent, not an LLM chat wrapper. No LLM API is required.
The question model is an experimental product layer, not a Qloo-provided feature.
All synthetic affinities are invented; real film titles in demo mode are editorial metadata.
Model weights are not calibrated human confidence, identity, or enjoyment probability.
Rank normalization is heuristic and raw Qloo scores are not compared across requests.
Only shared candidates are eligible, which can limit coverage and novelty.

## Evidence and answer correction

Each recommendation retains separate per-anchor rank evidence. Live recommendation
requests retain IDs, names, and bounded Qloo descriptions and release years when available. Rankings are cached for ten minutes to reduce repeated upstream calls. In normal discovery, expandable panels show how yes/no could change the
shortlist without changing session state. Users can correct the last answer; weights
are rebuilt from the retained history. Correction counts are included in exports.
Research sessions disable previews and corrections to avoid changing the comparison.
Qloo request traces include retrieval timestamps and durations, excluding credentials.

## Evaluation

The optional paired pilot requires explicit adult consent. Each participant completes
adaptive and fixed question rounds in randomized order, using the same retrieved
Qloo snapshot. A disjoint holdout pool supplies a mixed final shortlist with method
labels hidden in the interface. Each arm asks at most three questions. Participants
rate familiar films and voluntarily export the result; no research database receives it.

```text
python analyze_paired.py session1.json session2.json
```

The analyzer deduplicates pilot IDs, rejects labeled scripted QA, separates live and
synthetic evidence, and reports descriptive paired differences and rating coverage.
Repeated people, selective familiarity ratings, carryover, and editable exports remain
limitations. This is an exploratory pilot, not proof of improved recommendations.
The older single-strategy API and `analyze.py` remain available for compatibility.

`benchmark.py` and `benchmark-results.json` are a reproducible, model-matched synthetic
sanity check. The simulated responder follows the model family used by the agent.
Lower model entropy does not prove recommendation improvement or real-user satisfaction.
See `docs/EVALUATION.md` for the real pilot protocol.

The newer `stress_benchmark.py` evaluates disjoint, unasked candidates under matched,
mixed, reversed, and frequent-skip scenarios. Full generated results are in
`stress-results.json`; `docs/STRESS_FINDINGS.md` explains the mixed-taste limitation.
These generated experiments do not establish real-user benefit.

## Deploy

The Dockerfile includes Python, Node 22 and the pinned official harness. Docker
construction and the container API smoke test passed in GitHub Actions. Docker is unavailable in this local workspace.

```text
docker build -t tasteprobe .
docker run --rm -p 8080:8080 tasteprobe
```

A Render Blueprint is included in `render.yaml`; see `docs/DEPLOYMENT.md`.
Render supplies the public origin automatically.
For another host with Docker support, use the supplied Dockerfile, expose its PORT and
configure APP_ORIGIN to the exact public HTTPS origin. Add Qloo credentials only
through the host's secret environment. Keep one instance for the memory session store.
The HTTP server is intended for a small hackathon demo behind a trusted TLS reverse
proxy. Use a proper production gateway and shared state before scaling. Request limits
are local to each instance; event quotas still apply. No hosting account or paid service
was created.

An earlier static Site registration is retained locally, but no hosted deployment has
been completed. The full Python app cannot run on static-only hosting.

## API

- GET /api/config: demo/live availability, no credentials.
- POST /api/search: query and kind, returns confirmed-choice candidates.
- POST /api/session: mode, seeds, optional experiment and explicit consent flags; returns a capability session ID.
- POST /api/answer: session_id, current entity_id, answer (like/dislike/skip).
- POST /api/state: session_id, returns current session.
- POST /api/delete: session_id, deletes session.
- POST /api/undo: session_id, reverses the last answer outside research mode.

All writes require same-origin JSON. Treat the unpredictable session ID as private;
it is excluded from exported evidence. Static serving is an explicit file allowlist.

## Project layout

- engine.py: information-gain policy and preference updates.
- service.py: bounded sessions, search confirmation, live orchestration, study strategies.
- qloo.py: official-harness/default and explicit HTTP transport adapters.
- server.py: static UI and session API.
- dist/: responsive browser UI, ratings, evidence export.
- analyze.py, benchmark.py: pilot summaries and labeled synthetic simulation.
- tests/: policy, service, transport, HTTP and analysis checks.
- docs/: evaluation, demonstration, deployment status and Devpost draft.

## References

- https://qloo.devpost.com/
- https://qloo.devpost.com/resources
- https://github.com/qloo/qloo-hackathon-kit/blob/main/docs/API_ACCESS.md
- https://github.com/qloo/docs-public/blob/main/reference/insights-api-deep-dive.md

MIT license. Built by Nourhan832.
