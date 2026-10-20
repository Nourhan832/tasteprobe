# 90-second demonstration script

Most recommendation demos ask what you like and immediately produce a list.
TasteProbe asks a different question: what is the most useful thing to ask next?

Start with two real favorites. Qloo retrieves a separate movie ranking for each.
TasteProbe keeps those anchors separate, finds a film that can distinguish them,
and updates its experimental preference weights after an answer. Unfamiliar films
can be skipped without pretending they were disliked. After at most three questions,
it stops and shows a shortlist with the original per-anchor rank evidence.

[Demonstrate a confirmed search, one answer, one skip, and the final evidence panel.]

Qloo supplies the cultural evidence; our contribution is the bounded decision policy
on top: select a question, update, decide whether to continue, and explain the result.
This could become an onboarding layer for products that need useful taste signals
without a long questionnaire.

We verified an end-to-end live Qloo walkthrough and maintain 37 automated tests.
Synthetic stress tests also expose failure cases rather than proving human benefit.
The app includes a voluntary paired pilot: adaptive and fixed rounds use the same
Qloo snapshot, reserve unasked films, and mix their final suggestions for ratings.
Human improvement is still a hypothesis. Our next evidence is consenting user data,
not a simulated satisfaction claim.

Close: TasteProbe turns a taste graph into a short, inspectable discovery conversation.

Submission gate: add the verified public URL, a real recorded walkthrough, and actual
pilot findings if available. Do not invent participants, metrics, or prize predictions.
