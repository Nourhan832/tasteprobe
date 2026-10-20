# Internal judge rehearsal — not an official score

Technical implementation: live Qloo search/rankings feed the actual question policy;
37 local tests and public end-to-end QA support operation. Missing: wider live scenario
coverage and a comparator against generic recommendations. Never assert that latter win.

Design: complete discovery, skip, answer correction, evidence, delete, and export flows.
Largest observed friction: the initial live retrieval can take approximately a minute.

Potential impact: specific audience is discovery-product onboarding teams. The movie
app demonstrates the workflow. Customer demand, reduced abandonment, and enjoyment
improvement are hypotheses until measured.

Originality: position the contribution as selecting the next useful question over
Qloo evidence, not another generated movie list. The policy is explicit and bounded;
do not imply an LLM or multi-agent framework that the app does not use.

Highest-priority evidence still missing: voluntary participant exports, reported with
coverage and exclusions. A first-place prediction would be unsupported.
