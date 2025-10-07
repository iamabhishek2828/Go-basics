https://pension-assistant-ddbqwpnml.vercel.app/
A. Replace the Input → Processing → Output (Functional Implementation) cell with:

Inputs: high-certainty flags and candidate metadata.
Processing: determine owner using configurable assignment rules (role, department, risk tier, workload); create case record with owner, priority, SLA and evidence pack; set case status (New → Assigned → Under review → Resolved). Route notifications to the owner and their manager; record every action in the audit log.
Outputs: held payments log, assigned case records with owner and SLA timestamps, notification trail and resolution disposition.

B. Replace the Brief step explanation & where emerging tech is used cell with:

Places high-certainty items on controlled hold and opens a tracked case assigned to a responsible owner (procurement officer / treasury investigator / audit). Cases are auto-routed by role and risk tier; owners receive notifications, must acknowledge, and record a disposition. (Tech: Workflow automation, case-management, RBAC.)

C. Update the Acceptance Criteria cell with:

At least 95% of high-priority cases assigned to an owner automatically within 2 hours of flag creation; owner acknowledgement within 24 hours; 90% of high-risk cases resolved or escalated within 7 working days. Audit trail and owner note required for every disposition.
