# Demonstration script

## Synthetic walkthrough (available now)
1. Open the Python-backed app and point out the synthetic-data label.
2. Start sample discovery. The first question is Whiplash.
3. Choose like. The next question becomes Her and the model favors a different anchor.
4. Choose unfamiliar. The next question changes; weights stay the same.
5. Choose dislike. The agent stops after three questions and lists unasked candidates.
6. Rate a familiar final film. Export the session to inspect decisions and provenance.
7. Restart; the previous server session is deleted.

## Live demonstration (requires API access)
1. Configure the official harness privately and start the backend.
2. Search two favorites across music and movies. Confirm exact Qloo identities.
3. Show real movie candidates from separate anchor queries, then the selected question.
4. Answer and show how the next question changes under the model.
5. Inspect source provenance; distinguish returned Qloo data from product interpretation.
6. Show no-overlap or API-failure behavior without fabricating a successful result.

## Pitch
Most recommendation agents guess too early. TasteProbe asks what it still needs to
learn. Qloo supplies cross-domain cultural evidence; a bounded agent turns that
evidence into informative questions, preference updates and an explicit stop decision.
The product hypothesis is better discovery with less onboarding effort. The project
includes a comparison workflow so this claim can be tested rather than asserted.
