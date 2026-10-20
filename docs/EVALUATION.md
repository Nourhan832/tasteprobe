# Exploratory paired pilot

Hypothesis: adaptive onboarding improves stated fit over fixed questions under the
same maximum three-question budget. This remains unproven.

Recruit 10–20 consenting adults for an exploratory pilot, with one session per person.
This target is logistical, not a power calculation. Explain the purpose and voluntary
export before collection. Do not collect names, emails, or sensitive attributes.

1. Select Live Qloo, confirm the same favorite anchors, and enable the comparison.
2. Read and accept the adult voluntary-consent statement.
3. Complete both rounds. Order is randomized; both use a frozen ranking snapshot.
4. Rate only familiar suggestions from the mixed shortlist; leave unfamiliar ones blank.
5. Export voluntarily and share only through a channel agreed with the organizer.
6. Run `python analyze_paired.py export1.json export2.json`.

Question and holdout pools are disjoint. Both arms recommend from the same holdout;
films appearing in both lists are displayed once and receive the same rating. Fixed
questions use stable entity-ID order. This is a deliberately simple baseline, not an
optimized fixed questionnaire. Adaptive rounds can stop early for low modeled gain.

Primary descriptive outcome: mean within-session adaptive-minus-fixed stated-fit
rating among sessions with at least one rated film per arm. Report eligible and
excluded counts, coverage, question counts, and all missing-rating reasons. Inspect
exports for skipped questions and randomized order. Keep synthetic and live results
separate. The analyzer deduplicates pilot IDs and excludes explicitly labeled QA.

Method labels are hidden in the participant interface, but network responses and
exports are inspectable. Repeat questions, carryover, familiarity, recruitment bias,
selective missing ratings, overlapping lists, and repeated people limit interpretation.
Exports are editable. No statistical significance or causal benefit is established.
Later work should use prospective post-viewing outcomes and a prespecified powered study.

Until actual participants complete the pilot, report zero human evaluation results.
Scripted walkthroughs and simulations demonstrate operation only.
