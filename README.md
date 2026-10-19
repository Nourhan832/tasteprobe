# TasteProbe

**The taste agent that learns which question to ask next.**

TasteProbe is a bounded adaptive discovery agent for movie recommendations. It uses
separate cultural anchors, selects a question by expected model information gain,
updates its hypothesis weights, and stops when the question budget or evidence is
exhausted. The browser talks to a Python backend; credentials stay server-side.

## Status

Working backend-connected synthetic demo; official Qloo harness adapter implemented
and tested with mocked responses. Live authentication, API behavior and human
recommendation quality are **not yet verified**. No prize or improvement claim is made.
The app is not submission-ready until live Qloo access and external hosting work.

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
```

## Live Qloo setup

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

## Evaluation

The optional research flow randomly assigns adaptive, fixed, random, or immediate
recommendation strategies. Adaptive/fixed/random have the same maximum three-question
budget; immediate is a zero-question baseline. Strategy labels stay out of the rating
flow. This is a pilot aid, not a validated blinded study platform: participants can
inspect network responses, and the sessions are not identity-linked.

Export a completed session after rating familiar final suggestions, then run:

```text
python analyze.py session1.json session2.json
```

The analyzer separates synthetic and live sources, rejects invalid ratings, ignores
exact duplicate exports, and reports descriptive session-level summaries. Repeated
people cannot be detected. User-editable exports are not tamper-proof research data.
Do not report causal benefit or statistical significance from this output.

`benchmark.py` and `benchmark-results.json` are a reproducible, model-matched synthetic
sanity check. The simulated responder follows the model family used by the agent.
Lower model entropy does not prove recommendation improvement or real-user satisfaction.
See `docs/EVALUATION.md` for the real pilot protocol.

## Deploy

The Dockerfile includes Python, Node 22 and the pinned official harness. Docker
construction has not been executed in this workspace because Docker is unavailable.

```text
docker build -t tasteprobe .
docker run --rm -p 8080:8080 tasteprobe
```

For a host with Docker support, use the supplied Dockerfile, expose its PORT and
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
- POST /api/session: mode, seeds, optional study flag; returns a capability session ID.
- POST /api/answer: session_id, current entity_id, answer (like/dislike/skip).
- POST /api/state: session_id, returns current session.
- POST /api/delete: session_id, deletes session.

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
