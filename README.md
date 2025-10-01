
## Proof of Concept (PoC)

### 1. Executive Summary (one paragraph)

This PoC demonstrates a compact, deliverable 30-day route to prove that an AI-enabled Financial Reporting System (FRS) can transform routine treasury and procurement workflows into continuous, auditable assurance. The system integrates a governed data foundation, a rule and machine learning risk engine and business intelligence-grade ‘as-of’ reporting to detect and prevent payment risk, expedite audits and enhance fiscal transparency. Expected PoC outcomes include identifying the top 100 ranked risk exposures, generating 50–150 meaningful flags for human review and demonstrating a 10-fold faster risk triage process with a measurable audit trail for each decision. The design enforces on-premise/sovereign hosting, human-in-the-loop controls and donor-aligned governance.

### 2. Objectives (what this PoC must prove)

1. **Detect & Prioritise**: Identify and rank risky procurement and payment items using rules and machine learning so auditors focus on the highest-value cases.
2. **Prevent & Evidence**: Demonstrate that preventive controls and evidence packs can prevent or escalate suspect payments before payout.
3. **Explain & Audit**: Every alert must link to exact source evidence (contract clause, invoice page) and a concise human-readable explanation.
4. **Operational Fit**: Demonstrate a workflow that a treasury team can operate (rule updates, review queues, evidence export).

### 3. PoC Scope (Data & Functionality)

**Data Sample** (anonymised): 6 months procurement contracts (5,000–10,000 rows), 3 months payments (50,000–100,000 transactions), supplier master (5,000 vendors), budget versus actuals snapshot.

**Core Functions to Deliver:** Ingest documents (PDFs), extract key fields (supplier, contract number, clause), run rule checks (caps, approvals, ineligible vendors), run two machine learning detectors (anomaly on payment patterns; supplier collusion signals), produce a ranked risk list and executive dashboard, provide evidence packs for the top 20 items.

**Success thresholds:** identify 50–150 flags; manual review true-positive ≥70% (PoC target); dashboard with drill-through to documents.



—



## 4. Risk-management lifecycle (functional, client language)



**Identify:** all transactions and contracts are screened automatically using configurable business rules and pattern detectors; no manual reading is required to generate candidate risks.

**Assess & score:** each candidate receives a simple likelihood × impact score using rule breaches (hard) and behavioural signals (soft); the highest scores appear at the top of the queue.

**Mitigate (preventive controls):** configurable actions include payment hold pending sign-off, automatic request for supporting evidence or notification to approving authority. Human approval is required before any payment is blocked.

**Monitor:** continuous re-scoring and trending dashboards surface emerging sectors, suppliers or departments that drift above thresholds.

**Learn & improve:** investigator outcomes (false positive, confirmed, recovered) are recorded and used to tune rules and models; all changes are versioned.



—



## 5. How AI adds value — short practical examples



* **Document extraction:** NLP/OCR converts contract PDFs into structured fields so rules can reference exact clauses without manual transcription.

* **Pattern detection:** ML flags supplier networks (repeated collusive indicators) and unusual invoice sequencing that human reviewers miss at scale.

* **Prioritisation:** scoring blends policy breaches with model signals so auditors see what to act on and why – reducing time to decision.

* **Narrative explanation:** the system generates a two-line natural-language rationale for each flag with links to the documents.



—



## 6. Benchmarks & substantiation (real examples)



These examples guided the design and provide expected magnitudes of benefit: Brazil’s GRAS piloted procurement risk analytics and flagged hundreds to thousands of suspect suppliers (reports cite approximately 850+ suspicious suppliers and several thousand politically linked firms). Singapore’s continuous audit covered payroll and pensions for approximately 90,000 workers and 34,000 pensioners. Kazakhstan’s COSO-aligned preventive checks reportedly prevented approximately 1.2 trillion tenge (US$2.7 billion) in violations. Jacksonville’s public dashboards recovered over 600 staff hours annually. These are used as reference performance targets for detection speed, percentage coverage and staff time savings.



—



## 7. Vendor & delivery model (procurement-ready)



**Prime: System Integrator (SI)** — responsible for end-to-end delivery, integration with IFMS, test environment and cutover.

**AI/ML partner** — supplies model IP, training pipelines and ongoing model governance; model artefacts reside in the client environment.

**BI partner** — implements semantic layer and executive dashboards (Power BI / Tableau / open alternative).

**Infra provider** — on-premises or sovereign cloud operator (compute, storage, backups, network).

**OCR / Document capture** — specialist for PDFs, e-invoices and images.

**Cyber & IAM partner** — encryption, SIEM, role-based controls and audit logging.

**Change & Training partner** — frontline training, process adoption and SOPs.

Contracting: SI as prime; others as subcontractors with service level agreements (SLAs) for model performance, data locality and retraining cadence. All vendors must sign data locality and non-disclosure clauses; model outputs used for high-impact actions require documented human sign-off and independent validation.



—



## 8. 30-day PoC plan (detailed deliverables by week)



**Week 1 — Setup & extraction:** sandbox provisioning, ingest anonymised sample data, deploy OCR/NLP pipeline for contracts and invoices. Deliverable: accessible sample dataset + first extracted document fields.

**Week 2 — Rules & Detectors:** Implement 10 business rules and two machine learning detectors; run a full sample. Deliverable: first ranked risk list and audit evidence links.

**Week 3 — Human Validation & Dashboards:** Auditors review the top 100 flags; populate outcomes. Deploy an executive dashboard with drill-through functionality. Deliverable: Validated top-20 evidence packs and dashboard.

**Week 4 — Wrap & Handover:** Metrics, lessons learned, rule tuning and a recommended 90-day roadmap for scale. Deliverable: PoC executive report (1-pager), evidence zip file, model and rule registry extract.

—

## 9. PoC Success Metrics (Leadership Measurement)

* **Detection Coverage:** Percentage of transactions screened (target 100% of sample).
* **Top-100 Validation Rate:** Manual review true positives (PoC target ≥70%, operational target ≥85%).
* **Time to Triage:** Median time vs baseline (target 10× improvement).
* **Manual Hours Saved:** FTE hours saved on routine checks (target ≥50% reduction).
* **Auditability:** 100% of flags have downloadable evidence (PDF + link + clause).

—

## 10. Governance & Safeguards (Non-Negotiable)

* **Human-in-the-Loop:** All blocking/preventive actions require explicit human approval.
* **Data Locality:** On-premises or sovereign cloud; no external model training on live PII.
* **Explainability:** Every alert must contain a short, auditable explanation and source link.
* **Model & Rule Registry:** Versioned with rollback and change logs; independent auditor access.

**11. Deliverables (what you will receive)**

1. Executive PoC report (1 page) and detailed PoC findings (10–12 pages).
2. Interactive dashboard (demo link or packaged artefact).
3. Evidence pack: top 20 flagged cases with source documents and review notes.
4. Model & rule registry extract (CSV) showing deployed rules and model version.
5. Recommended 90-day scaling roadmap and procurement SOW template for SI engagement.

**12. Next steps (recommended immediate actions)**

1. Approve data access and sign PoC engagement letter (30 days).
2. Nominate 1–2 SME reviewers (audit/treasury) and a data steward.
3. Provide anonymised sample extracts (secure transfer) and a development VM or access to a sovereign test environment.
4. Schedule an inception workshop (2 hours) to agree rules and PoC acceptance criteria.

**Contact (for PoC delivery):** Project Lead (SI contact) | AI Lead | Treasury Sponsor (names to be inserted).
