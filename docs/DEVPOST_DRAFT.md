# TasteProbe — Ask better. Discover better.

**Draft. Do not submit until the live demo and public repository checks are complete.**

## Inspiration
An agent can ask someone what they like, but choosing the next useful question is
harder. We wanted cultural discovery to act on uncertainty instead of covering it
with confident language. Our background in uncertainty-aware ML and LLM evaluation
led us to build an explicit, inspectable question policy.

## What it does
TasteProbe helps someone discover a movie from a few cultural favorites. In the
implemented live workflow, users confirm favorite identities, the backend retrieves
Qloo movie rankings per anchor, and the agent chooses follow-up questions using
expected model information gain. Likes and dislikes update anchor weights; unfamiliar
responses preserve them. The agent stops after at most three questions or when
evidence no longer supports an informative question.

The interface includes a decision journal, source labels, session deletion and JSON
evidence export. An optional research flow compares adaptive, fixed, random and
immediate strategies. This is an experimental policy agent, with no LLM dependency.

## How it is built
Python standard-library backend, a buildless HTML/CSS/JavaScript UI, and the official
Qloo harness invoked from a server process. Keys remain outside the browser and
repository. Tests exercise the policy, request contracts, session handling, adapter
errors and evaluation imports. A Docker deployment definition is included.

## Why Qloo
The proposed live experience uses cross-domain cultural rankings as the evidence
for competing taste anchors. Those rankings shape the question itself, not simply
the wording of a final response. An LLM alone is not substituted for missing Qloo data.

## What is established today
The backend-connected synthetic workflow works and its automated tests pass.
The live adapter has mocked integration tests; real API execution is pending access.
No real-user recommendation uplift has been established.

## Challenges
Truncated candidate lists make absence ambiguous. We keep missing evidence unknown
and restrict questions to shared candidates. Normalized rank utility and the
response likelihood model remain heuristics. Limited shared coverage is a visible
failure mode rather than something the app hides.

## Next
Verify the event credential and live contract, publish an externally accessible
functional demo, then run a consenting pilot with equal budgets and user-rated
outcomes. Update this draft with actual evidence and deployment links before submitting.

## Links
Public source: https://github.com/Nourhan832/tasteprobe
Live application: PENDING — a localhost address does not satisfy the requirement.
