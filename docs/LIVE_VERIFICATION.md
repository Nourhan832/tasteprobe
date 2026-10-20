# Live Qloo integration check — October 20, 2026

Result: passed a complete scripted browser walkthrough using the event API at
https://hackathon.api.qloo.com through the official Qloo harness.

## Walkthrough
- Searched and confirmed The Matrix and Interstellar as real movie entities.
- Retrieved 50 movie candidates per anchor; 19 candidates had shared evidence.
- First question: V for Vendetta. Scripted answer: like.
- Second question: Mad Max: Fury Road. Scripted answer: unfamiliar / skip.
- Third question: Terminator 2: Judgment Day. Scripted answer: dislike.
- The agent stopped at the three-question budget.
- Final shortlist: Inception, The Prestige, Back to the Future.
- Inception's evidence panel showed rank 2/50 under The Matrix and 5/50 under
  Interstellar. The displayed model weights were approximately 37% and 63%.
- Export downloaded successfully and was parsed independently. It contained live
  provenance, two retrieval traces, three answer records, no session capability ID,
  and no ratings. No API key was present in the browser or export.

## Payload finding and fix
Even with minimal fields requested, the two harness responses contained 3,253,076
and 3,195,914 decoded characters. The earlier 2-million-character guard was too
small for these event responses. The adapter now accepts a bounded response of up
to 32 million characters, parses it, then retains only entity IDs and names.
The two successful retrieval traces recorded approximately 14.2 and 6.0 seconds.
These are observations from one run, not latency guarantees.

## What this establishes
Authentication, entity resolution, recommendation schema handling, evidence overlap,
adaptive updates, skip behavior, stopping, per-anchor ranks and JSON export worked
in this scenario. The credential remained in the user's launcher process.

## What it does not establish
These were scripted QA answers, not participant feedback. No satisfaction scores,
recommendation uplift, general cross-domain quality or prize outcome is established.
External hosting and a consenting evaluation remain outstanding. Raw live QA data
is kept in the local outputs rather than published as a repository fixture.
