# ERROR_LOG.md
# Deliberate Errors Found in Zetheta Project Document
# Identified by: Aman Singh
# The document states exactly 7 deliberate errors exist

---

## Error 1 - Source Reliability Tier Ordering (Section A6.2)

Location: Part A, Section A6.2, Source Reliability Hierarchy

What the document says:
Tier 4 is Social media posts and anonymous forum discussions
Tier 5 is Major news outlets (Reuters, Bloomberg News, Financial Times)

Why this is wrong:
Major news outlets with professional journalists and editorial
oversight are significantly more reliable than anonymous social
media posts. Tiers 4 and 5 are inverted.

Correct ordering:
Tier 4 should be Major news outlets
Tier 5 should be Social media and anonymous forums

---

## Error 2 - Memory Utilization Formula (Section A5.2, Metric AB-4)

Location: Part A, Section A5.2, Category 5 Agent Behaviour, metric AB-4

What the document says:
"This metric is calculated as memory_hits multiplied by total_api_calls"

Why this is wrong:
The document defines AB-4 as a ratio of memory hits to total API calls.
Multiplying gives a number that grows as API calls increase, which is
the opposite of what the metric intends to measure.

Correct formula:
memory_utilization = memory_hits divided by total_api_calls

---

## Error 3 - SCAP Date and Legislation (Section A7.3)

Location: Part A, Section A7.3, Handling Ambiguous Queries

What the document says:
"The first US bank stress tests under SCAP were conducted in 2007
following the Dodd-Frank Act"

Why this is wrong:
Two factual errors in one sentence.
First: SCAP was conducted in 2009, not 2007.
It was a direct response to the 2008 financial crisis.
Second: The Dodd-Frank Act was signed in July 2010, which is after
SCAP concluded. SCAP could not have followed it.

Correct statement:
SCAP was conducted in 2009. Dodd-Frank was enacted in 2010 afterward.

---

## Error 4 - Form 20-F Filing Attribution (Section C4.2)

Location: Part C, Case Study 4, Section C4.2

What the document says:
"Indian companies file annual returns using Form 20-F with the
MCA (Ministry of Corporate Affairs)"

Why this is wrong:
Form 20-F is a US SEC filing used by foreign private issuers
listed on US stock exchanges like NYSE or NASDAQ.
It is filed with the US SEC, not India's MCA.
Indian domestic companies file with MCA using AOC-4 and MGT-7 forms.

Correct statement:
Form 20-F is filed with the US SEC by Indian companies listed on
US exchanges. Domestic Indian filings with MCA use different forms.

---

## Error 5 - Embedding Dimensions for OpenAI Models (Section E2.2)

Location: Part E, Section E2.2, Embedding Models

What the document says:
text-embedding-3-small has 1536 dimensions
text-embedding-3-large has 1024 dimensions

Why this is wrong:
The dimension count for text-embedding-3-large is incorrect.
Actual OpenAI specifications:
text-embedding-3-small: 1536 dimensions (this one is correct)
text-embedding-3-large: 3072 dimensions (document says 1024, wrong)

---

## Error 6 - European Banking Authority Reference (Section A7.3)

Location: Part A, Section A7.3, Handling Ambiguous Queries

What the document says:
A query about bank stress tests in 2007 likely refers to the
European Banking Authority stress test programme.

Why this is wrong:
The European Banking Authority was not established until January 2011.
It could not have conducted stress tests in 2007.
The 2007 reference should be to earlier EU stress test exercises
run by CEBS (Committee of European Banking Supervisors), not the EBA.

---

## Error 7 - Hallucination Rate Statistic (Section C3.2)

Location: Part C, Case Study 3, Section C3.2, What Went Wrong

What the document says:
"Industry average hallucination rates for unverified financial
agents are typically around 45-60%"

Why this is wrong:
This figure is presented as a known industry statistic but has
no citation or source. Published research on LLM hallucination
rates does not support this specific figure. The number appears
to be fabricated to make the case study seem more dramatic.
This is itself an example of the hallucination problem the
document is warning about.

---

## Summary

Error 1: Section A6.2 - Source reliability tiers inverted
Error 2: Section A5.2 - Wrong math operation in AB-4 formula
Error 3: Section A7.3 - Wrong year and wrong legislation for SCAP
Error 4: Section C4.2 - Wrong filing form and wrong authority
Error 5: Section E2.2 - Wrong embedding dimensions for large model
Error 6: Section A7.3 - EBA did not exist until 2011
Error 7: Section C3.2 - Unsourced hallucination rate statistic