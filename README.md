Done — I updated your functional PoC to follow **Option B (undated phases / outcomes-only)**. I removed the week-by-week timeline and replaced it with outcome-focused phases so you — as an intern — are not committing dates or resources. Below is the ready-to-share PoC text (copy-paste into Word/PowerPoint or email to your manager).

---

# Functional PoC — AI-Enabled Financial Reporting & Risk Management (FRS)

**Purpose:** a compact, manager-focused Proof of Concept that is strictly functional — processes, inputs/outputs, roles, and measurable outcomes — so treasury teams can run, validate and adopt the capability without needing deep technical detail.

---

## Executive summary (one short paragraph)

This PoC proves that an operational FRS can detect, prioritise and prevent high-risk payments and procurement events using simple business rules plus lightweight AI scoring, while keeping humans in control. The focus is on end-to-end workflows (identify → score → act → monitor → learn), clear inputs and outputs, and measurable targets that treasury managers can validate in operational terms.

---

## Objectives (what the PoC must demonstrate)

1. Identify risky transactions and contracts automatically across the sample dataset and present a ranked worklist for auditors.
2. Prevent clear rule breaches from proceeding without human sign-off (e.g., over-limit payment, missing approval).
3. Produce evidence packs for each high-risk item that auditors can review in under 10 minutes.
4. Show measurable operational gains: faster triage, fewer manual hours, and at least 50 validated flags for review.

---

## Core functional workflows (each described as inputs → processing → outputs)

### 1) Identification workflow

**Inputs:** payment records, supplier master, contracts (PDF), approval logs.
**Processing:** run a set of configurable business rules (caps, duplicate invoice, missing approval) and run pattern checks that group related transactions by supplier and timing.
**Outputs:** a daily candidate list with one line per suspect item containing reason codes, reference IDs, and a link to the source document.

### 2) Prioritisation workflow

**Inputs:** candidate list, rule severity matrix, simple ML score (optional).
**Processing:** assign a likelihood × impact score using rule severity and basic behavioral signals (frequency, amount, past flags). Sort into high/medium/low buckets.
**Outputs:** a ranked worklist for auditors showing top items with short plain-language rationale for each.

### 3) Mitigation / prevention workflow

**Inputs:** top N flagged items, policy map (who can approve), payment lifecycle hooks.
**Processing:** apply configured actions: auto-hold payment pending approval, request evidence from responsible official, or auto-escalate. All actions log the rule and user decision.
**Outputs:** action log, blocked/held transactions list, notifications to approvers, and timestamps for SLA tracking.

### 4) Human review & resolution workflow

**Inputs:** ranked worklist, evidence pack (contract excerpt, invoice image, metadata).
**Processing:** auditor reviews evidence, tags outcome (false positive, confirmed, recovered, referral), and writes a short disposition note. Outcome updates the system and feeds learning.
**Outputs:** disposition log, recovered amounts (if any), and labeled records for tuning rules.

### 5) Continuous monitoring & reporting workflow

**Inputs:** resolved outcomes, transaction stream.
**Processing:** re-score flows regularly, compute KPIs (flags/day, true positive rate, reviewer hours), and generate dashboard tiles for leadership.
**Outputs:** dashboard, periodic risk heatmap, exception trend emails to managers.

---

## Inputs and outputs (simple table in text)

* **Inputs:** procurement contracts (PDFs), payment ledger, supplier master, approval logs, budget positions.
* **Primary outputs:** ranked risk list, evidence packs (per item), action logs (holds/escalations), executive dashboard, operational PoC report with validation metrics.

---

## Roles & responsibilities (who does what)

* **Treasury Sponsor / Head:** approves PoC scope, accepts final report.
* **Audit / SME Reviewers:** validate flagged items, provide dispositions and feedback.
* **Data Steward:** provides sample extracts, confirms data lineage and unit mapping.
* **SI / Delivery Lead:** deploys PoC sandbox, configures rule engine, produces dashboards and evidence packs.
* **AI/Ops Contact (if used):** manages lightweight model scoring and ensures retraining only on labeled outcomes.
* **IT / Security:** provides secure sandbox, ensures data locality and access control.

---

## Acceptance criteria (literal, testable)

1. System screens 100% of supplied sample transactions and produces a ranked list within an operational run window (example: within one system run).
2. At least **50 flags** are produced and at least **70%** of the top-50 flags are confirmed as true issues or require further action after auditor review.
3. Evidence packs for each top-20 item contain the exact contract page / invoice image and can be reviewed in under **10 minutes**.
4. Preventive action: at least **5** true rule-based holds occur and are resolved through the defined approval workflow.
5. Dashboard shows key KPIs and a trend line; leadership can export a one-page report showing top risks and actions.

---

## Quick wins (what to build first)

1. Implement the **rules that are easy to validate**: missing approval, over-limit, duplicate invoice, blacklisted vendor.
2. Deliver an **evidence viewer** that opens the contract PDF at the cited page and highlights the clause.
3. Provide a **one-page executive report** with top 10 risks and the proposed action for each.
4. Add a **manual override log** so reviewers can immediately mark false positives and record why.

---

## What not to automate in PoC

Do not automate payment blocks without explicit human sign-off. Do not train models on PII outside secure environments. Do not attempt full beneficiary-level entitlement rules in the PoC — stick to supplier/payment risk.

---

## Phased approach (outcomes-only — no dates)

**Foundation (scope & data readiness):** provision a secure sandbox, ingest anonymised sample data, and deploy document extraction so rules can run on live-style inputs. *Outcome:* validated sample ingestion and extracted document fields ready for rules.

**Intelligence (detection & prioritisation):** deploy the rule engine and initial anomaly detectors; produce a ranked risk list and evidence packs. *Outcome:* a ranked worklist and evidence viewer showing top candidate items.

**Validation (human review & tuning):** SME/audit review of the priority flags and disposition capture; tune rules and scoring using labeled outcomes. *Outcome:* validated top items, labeled dataset for tuning, and reduced false positives.

**Transparency & scale (operational fit & handover):** deliver executive dashboards, evidence export, operational playbook and a recommended procurement/SI approach for scale. *Outcome:* governance artefacts, SOW language, and readiness checklist for full deployment.

*Note: exact dates and resource allocations will be finalised by the Project Sponsor and the chosen System Integrator.*

---

## Success metrics to report (operational)

* Number of transactions screened; flags generated; confirmed issues; FTE hours saved; median review time per case; blocked amounts recovered; percentage of rules that required tuning after review.

---

## Governance & safeguards (short)

Keep human-in-the-loop for all blocking actions, store full evidence lineage for each decision, version rules and keep an audit trail of changes, and restrict training data to anonymised samples only. Use role-based access and require independent sign-off before scaling to production.

---

## Deliverables (what the treasury receives)

1. Running PoC sandbox with dashboards and evidence viewer.
2. Ranked risk list with evidence packs and auditor dispositions.
3. One-page executive summary with validated numbers.
4. Operational playbook showing workflows, responsibilities and SOW language for prime SI and partners.

---

If you want, I can now (pick one and I’ll produce it immediately):

* Convert this Option-B PoC into a **two-page Word/PDF** with PwC-style headers and layout, ready for print.
* Update the Excel registry and add a **“PoC functional checklist”** tab that maps acceptance criteria to rows for tracking.

Tell me which one to produce and I’ll create it right away.

