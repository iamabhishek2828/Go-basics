
![Uploading image.png…]()
flowchart TD

    A[Secure Intake\nChecksums, validation, logs] --> B[Parse Filings]

    B --> B1[XML or XBRL → Direct field extraction]
    B --> B2[PDF → OCR + Layout + Simple NLP]

    B1 --> C[Rules + Confidence Scoring]
    B2 --> C

    C --> C1[Low-confidence → Hybrid Reviewer Lane\n(Knowledge Transfer)]
    C --> D[Canonical Store\nVersioned tables, lineage, ownership]

    D --> E[Serve Layer]
    E --> E1[Policy Dashboard]
    E --> E2[Enforcement Dashboard]
    E --> E3[Read-only API\nKeys, quotas, logs]

    E --> F[Dual Gates]
    F --> F1[Quality Gate]
    F1 --> F2[Legal Gate\nAligned with all policies]
https://egovstandards.gov.in/sites/default/files/2023-05/Open%20API%20Policyfor%20e-Governance%20Applications%20in%20India.pdf
