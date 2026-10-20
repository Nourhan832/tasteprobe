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
evidence export. An optional consented paired pilot compares adaptive and fixed questions using
the same ranking snapshot, randomized round order, and disjoint unasked holdout films. This is an experimental policy agent, with no LLM dependency.

## How it is built
Python standard-library backend, a buildless HTML/CSS/JavaScript UI, and the official
Qloo harness invoked from a server process. Keys remain outside the browser and
repository. Tests exercise the policy, request contracts, session handling, adapter
errors and evaluation imports. A Docker deployment definition is included.

## Why Qloo
The implemented live experience uses cross-domain cultural rankings as the evidence
for competing taste anchors. Those rankings shape the question itself, not simply
the wording of a final response. An LLM alone is not substituted for missing Qloo data.

## What is established today
A full live movie walkthrough passed on October 20, 2026, including real Qloo
rankings, adaptive questions, evidence and JSON export. The project has 37 passing
local automated tests. See LIVE_VERIFICATION.md for the exact scripted scenario.
No real-user recommendation uplift has been established.

## Challenges
Truncated candidate lists make absence ambiguous. We keep missing evidence unknown
and restrict questions to shared candidates. Normalized rank utility and the
response likelihood model remain heuristics. Limited shared coverage is a visible
failure mode rather than something the app hides.

## Intended audience and impact
TasteProbe targets discovery products whose new users provide a few favorites but
lack a useful interaction history. Its proposed role is a short, inspectable taste
onboarding layer. The movie app demonstrates that layer; an embeddable SDK and
commercial integrations are future work. User benefit and customer demand remain
unproven, and the pilot is designed to test stated recommendation fit.

## What we learned
A cultural graph does not automatically tell an agent what to ask. Separate anchor
rankings let the policy choose an informative next question. Shared-candidate limits,
heuristic likelihoods, and unfamiliar films also expose why the agent needs an
explicit stop rule and transparent evidence rather than a confident explanation.

## Next
Run the consenting exploratory paired pilot and report coverage, missing ratings,
question counts, and descriptive paired differences. Extend to prospective viewing
feedback before claiming better real-world enjoyment. Optimize upstream latency.

## Links
Live application: https://tasteprobe.onrender.com/
Public source: https://github.com/Nourhan832/tasteprobe
License: MIT (LICENSE at repository root).

## Verification and limitations
The externally hosted application passed a scripted live Qloo walkthrough on
October 20, 2026: confirmed searches, two rankings, three questions including a skip,
three final suggestions with provenance, and a JSON export without the session token.
This is operational QA, not participant evaluation. No real-user uplift is claimed.
Render's free tier can sleep; open the demo before presenting. Initial upstream
ranking retrieval can take approximately one minute in the observed hosted scenario.

Submission description prepared against the official criteria at https://qloo.devpost.com/.
Video is optional under the current requirements. Final submission is not yet filed.
