# AI Phase 2 plan

This dashboard is intentionally set up so AI can be added in controlled, low-risk steps.

## Phase 2: semantic search
Use `analysis_text` and the normalized comment timeline to power:
- issue similarity search
- natural-language search across root cause and comments
- nearest-neighbor lookup for duplicate detection

## Phase 3: issue summaries
Generate concise structured summaries per issue:
- what failed
- likely component involved
- what evidence is attached
- current root cause status
- recommended next investigation action

## Phase 4: clustering and trend detection
Cluster issues by:
- failure mode
- component
- product family / SKU
- investigation pattern

This is where the dashboard can start showing AI-discovered themes next to the current rule-based tags.

## Phase 5: guided workflows
Add copilots for:
- root cause drafting
- corrective action drafting
- duplicate-ticket suggestions
- closure readiness checks

## Guardrails to keep
- keep the raw Jira text untouched in source columns
- store AI outputs in new columns, never overwrite source fields
- log model version and prompt template for each generated field
- allow humans to accept, reject, or edit AI-generated values
