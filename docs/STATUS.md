# Delivery status

Implemented: per-anchor evidence ledger, answer previews, answer correction,
held-out/misspecified synthetic stress tests, and Python-connected UI, adaptive policy, official-harness adapter, confirmed
entity selection, bounded sessions, error handling, JSON evidence, local ratings,
randomized comparison strategies, analysis, tests, CI definition and deployment files.

Verified: 27 automated tests and JavaScript syntax locally; the earlier 22-test version also passed GitHub Actions;
synthetic API lifecycle; default and research browser flows, skips, rating control,
restart and session deletion. GitHub Actions also built the Docker image, checked
the installed official harness command, and smoke-tested the container API.
Passing run: https://github.com/Nourhan832/tasteprobe/actions/runs/39229755303

Not verified: event credential, live Qloo responses and coverage,
externally hosted app, and real-user improvement. No prize prediction is made.

External dependencies: Qloo access email, working hosting publication, and consenting
human feedback. These cannot be represented as completed by an offline prototype.

An earlier Sites publication attempt was rejected by session approval policy at the
helper input step. The registered static Site is not a live full-app deployment.

## October 20 live integration

Event authentication and movie entity search succeeded using the user-entered key,
which never entered chat or source files. The first full retrieval exceeded the
2 MB response guard. The adapter now requests only entity_id and name; 30 local
tests pass. Full live retrieval needs a restarted launcher before verification.
The local launcher now supports backend reloads without credential re-entry.
