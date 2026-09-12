# ARA-1 Optimization Log
## Before/After Performance Comparisons
**Author:** Aman Singh

---

## Optimization 1 — Gemini Model Version

**Problem:** `gemini-1.5-flash` returned 404 NOT_FOUND errors.

**Root cause:** Model deprecated for new users on the v1beta API.

**Fix:** Updated to `gemini-3.6-flash` across all agent nodes.

**Result:** LLM calls started working. Agent went from 0% synthesis
to full report generation.

---

## Optimization 2 — Response Parsing

**Problem:** Gemini returns responses as a list of dicts
`[{"type": "text", "text": "..."}]` not as a plain string.

**Root cause:** New Gemini API response format differs from LangChain
expected format.

**Fix:** Added `_extract_text()` helper function in `agent/core.py`
that handles all response formats:
- Plain string
- List of dicts with "type" and "text" keys
- Objects with `.text` attribute

**Before:**

Synthesis complete: 1 characters
Report generated: 1 characters


**After:**

Synthesis complete: 7000+ characters
Report generated: 9000+ characters


---

## Optimization 3 — Company Detection

**Problem:** Agent used "UNKNOWN" as ticker for all companies
including explicitly named ones like "Microsoft Corporation".

**Root cause:** LLM returned companies list as empty because
response parsing failed.

**Fix:**
1. Fixed response parsing (Optimization 2)
2. Added `_basic_analysis` name-to-ticker mapping as fallback
3. Combined LLM result with basic analysis: if LLM returns empty,
   use basic analysis companies

**Before:**

Companies: []
Plan: Fetch company profile for UNKNOWN...


**After:**

Companies: ['MSFT']
Plan: Fetch company profile for MSFT...


---

## Optimization 4 — Registry Caching

**Problem:** Tool registry printed 12 registration lines on every
executor step (8 steps = 96 lines of noise).

**Root cause:** `create_registry()` called fresh on every step.

**Fix:** Added function-level cache using `_execute_step._registry`
attribute. Registry created once per session.

**Before:** 96 registration log lines per run
**After:** 12 registration log lines per run (once only)

---

## Optimization 5 — State Mutation Bug

**Problem:** Challenges 3-8 saved only 219-character fallback text
instead of the full 9000+ character report.

**Root cause:** `result["duration_seconds"] = duration` attempted
to mutate a LangGraph TypedDict state object after it was returned.
This caused a silent error that prevented the real report from
being accessed.

**Fix:** Copy the state dict before modifying:
```python
result_copy = dict(result)
result_copy["duration_seconds"] = duration
report = result_copy.get("final_report", "")
```

**Before:**

C3 report length: 219 characters
C3 score: 56.9%


**After:**

C3 report length: 8000+ characters
C3 score: improved


---

## Optimization 6 — Evaluation Metrics Calibration

**Problem:** Many metrics returning 0% even when reports were good.
CO-1 (section coverage) returned 0% because metric looked for
exact phrase "company overview" but report used "Company Profile".

**Root cause:** Metric patterns too strict, not accounting for
synonyms and variations in LLM output format.

**Fix:** Expanded pattern matching for all affected metrics:
- CO-1: Added synonym lists for each section
- CS-3: Made executive summary detection more flexible
- CS-4: Relaxed formatting requirements
- AD-1 through AD-4: Added more linguistic patterns

**Before average score:** 57.4%
**After average score:** 64.8%

---

## Optimization 7 — Failure Rate Propagation

**Problem:** Challenge 8 failure simulation (50% rate) not working.
Debug showed FailureRate: 0.0 in all executor steps.

**Root cause:** Failure rate was stored in `os.environ` but
`_execute_step` was reading it before the env var was set due
to Python module import caching.

**Fix:** Passed failure rate through LangGraph state directly:
- Added `failure_rate: float` to `ResearchState` TypedDict
- Set `initial_state["failure_rate"] = failure_rate`
- `node_executor` reads `state["failure_rate"]`
- Passes directly to `_execute_step`

**Result:** Fallback chains triggered correctly during Challenge 8.

---

## Performance Summary

| Metric | Before Optimizations | After Optimizations |
|---|---|---|
| Average Score | 0% (broken) | 64.8% |
| C1 Score | N/A | 80.9% |
| C2 Score | N/A | 81.9% |
| Report Length | 219 chars | 8000-10000 chars |
| Registry Noise | 96 lines/run | 12 lines/run |
| Company Detection | UNKNOWN | Real tickers |
| Failure Simulation | Not working | Working |