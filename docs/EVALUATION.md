# Evaluation plan

## Hypothesis
Qloo-guided adaptive questions can improve user-rated movie suggestions with the
same maximum question budget as fixed or random questions. This is unproven.

## Exploratory pilot
Recruit consenting adults who understand that the system is experimental. Do not
infer identity or sensitive attributes from favorites. No contact details are
required in the app. Explain how exported ratings will be used before collection.

Use the same confirmed anchor seeds and same retrieved evidence snapshot for paired
comparisons. The current UI randomizes strategies between sessions, so it supports
an exploratory between-session pilot; paired snapshot replay is not implemented.
For repeated participation, keep pseudonymous participant assignments separately
with consent and account for person effects in subsequent analysis.

Compare adaptive, fixed and random questions with a maximum budget of three.
Immediate Qloo-derived recommendations provide a zero-question baseline. Do not
call this an LLM-only comparison: an LLM baseline has not been implemented.

Ask people to rate final, unasked recommendations from 1 to 5, leaving unfamiliar
films unrated. Report familiarity and rating coverage; selective missing ratings
can bias comparisons. Rated familiar films measure stated fit, not later enjoyment.
A later prospective study should collect feedback after actually watching a film.

## Outcomes
- Primary exploratory outcome: session mean of rated final suggestions.
- Secondary: rating coverage, question count, skip count, abandonment, request count,
  latency and evidence coverage.
- Show denominators, method allocation counts, and all missing-rating rules.
- Separate synthetic and live evidence; do not use synthetic sessions as user evidence.
- The included analyzer reports descriptive summaries only. A defensible inference
  needs a specified sampling plan, participant handling, and uncertainty analysis.

## Stress tests before deployment
Verify contradictory answers, all skips, no common candidates, entity ambiguity,
API authentication failure, quota failure, response-schema changes and expired sessions.
Test response-model misspecification; model-matched simulation alone is optimistic.

## Claim gate
Until the pilot is completed, say "we test adaptive onboarding," not "we improve
recommendations." Do not describe model entropy as calibrated uncertainty about a person.
