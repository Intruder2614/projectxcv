# Production Roadmap & Acceptance Gates

## Stage 0 — Standalone pilot (included)
- [x] Responsive teacher-facing workspace UI
- [x] Seeded fictional learner/class/assignment data
- [x] Learner search, filters and detail profile
- [x] Explainable mastery/support rules and insight recommendations
- [x] Teacher follow-ups with owner, priority, due date, discussion comments and status
- [x] Assignment creation and status workflow
- [x] SQLite persistence
- [x] Local Git repositories, commit history and restore-as-new-commit
- [x] Optional Docker execution path that fails closed when unavailable
- [x] Setup docs and API docs

## Stage 1 — Product and data validation
- Confirm target roles, class/lesson relationships and existing Codingal feature overlap.
- Define concept IDs and rubric mappings with curriculum owners.
- Validate whether the analytics help teachers select actionable interventions.
- Define the minimum student-data fields and retention requirements.
- Agree the pilot cohort, instrumentation and success thresholds.

**Gate:** teachers can explain a proposed action from the evidence; analytics are interpretable and do not overstate certainty.

## Stage 2 — Identity and live collaboration
- Integrate Codingal-approved OIDC/OAuth SSO or identity API.
- Implement authenticated sessions, roles and class membership checks.
- Add PostgreSQL migrations and transaction tests.
- Make projects and follow-ups visible only to authorised class members.
- Add audit trail, CSRF protections as applicable, rate limits and secure secrets handling.
- Add optimistic concurrency for shared notes and project files.

**Gate:** cross-class and cross-tenant authorisation tests pass, including negative cases.

## Stage 3 — Evidence pipeline and analytics quality
- Define versioned event schemas for lesson, assignment, rubric and execution outcomes.
- Add idempotent event ingestion, event provenance, timestamp validation and deduplication.
- Store event summaries separately from personal notes; apply retention limits.
- Validate all aggregates against known test fixtures.
- Add trend windows and uncertainty/coverage indicators; distinguish missing data from poor performance.
- Track intervention outcomes without claiming causality from correlation alone.

**Gate:** every metric has a definition, source, owner and data-quality check.

## Stage 4 — Production project and execution service
- Move Git storage into a managed service or controlled repository service with backup and quotas.
- Separate the run control plane from isolated execution workers.
- Use hardened sandbox/VM isolation, no default egress, short-lived credentials, resource and concurrency quotas.
- Add queue back-pressure, idempotent job creation, log/output caps and cleanup verification.
- Add abuse detection and escape-response drills.

**Gate:** sandbox threat model and escape testing are independently reviewed; load tests pass at forecast peak concurrency.

## Stage 5 — Reliability and rollout
- Infrastructure as code and immutable build artifacts.
- CI for lint, unit, integration, browser, security dependency and API contract tests.
- Observability for service latency, queue age, run duration, failure rate, database load and storage growth.
- Backup restore drills, documented RPO/RTO, incident playbooks and staged/rollback deployments.
- Accessibility, browser and device testing.
- Privacy/legal review and teacher training.

**Gate:** written sign-off from engineering, security, curriculum/product, privacy/legal and operations.
