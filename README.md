https://pension-assistant-ddbqwpnml.vercel.app/
Input: assigned case record with evidence pack (contract pages, invoice image, rule excerpt) and case metadata.
Processing: assigned reviewer opens the evidence pack, reads the minimal required material, selects one disposition (Confirmed — action required / False positive / Refer for deeper investigation / Recovery), types a short 1–2 line rationale, and records required next steps (approve release, escalate, recover funds). The disposition is captured as structured metadata for downstream tuning.
Output: finalized disposition entry (with reviewer ID and timestamp), disposition notes, updated case status, and labeled dataset row for rule/prioritisation tuning.
Purpose (one line): enables fast, auditable decisions with minimal reviewer effort and creates labeled outcomes to improve system accuracy. (Tech: lightweight annotation UI; audit log)
