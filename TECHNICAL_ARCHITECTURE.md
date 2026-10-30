# Codingal Code Studio — Technical Architecture

## 1. Architecture in this package

The included application is deliberately lightweight to make the standalone pilot easy to run and inspect.

```text
Browser (HTML / CSS / JavaScript)
       │ same-origin JSON API
       ▼
FastAPI application (Python)
       ├── SQLAlchemy ── SQLite (local metadata and collaboration records)
       ├── Git CLI ───── local repository per project
       └── Docker CLI ─ optional short-lived, network-disabled runner containers
```

**Implemented now:** REST endpoints, request-schema validation, persistent local database records, learner and assignment APIs, shared-note data model/comments, local Git operations, safe filenames, execution limits and fail-closed behaviour if Docker/image is missing.

**Not implemented now:** production identity, network-shared collaboration, tenant isolation, live Codingal integration, central Git hosting, a durable event pipeline, production observability, migrations/backup automation, or an independently deployed runner service.

## 2. Recommended scale-ready target

```text
Next.js + React + TypeScript + Monaco
                 │ TLS / OIDC session
                 ▼
          Edge / WAF / API routing
                 │
                 ▼
      FastAPI modular application API
       ├── PostgreSQL (transactional records)
       ├── Redis (cache / distributed limits)
       ├── Git service (private repositories)
       ├── S3 (artifacts, exports, backups)
       ├── SQS (durable run and analytics jobs)
       └── event pipeline → precomputed analytics / reporting store

       Isolated execution control plane
                 │ authenticated job contract
                 ▼
      Separate runner fleet / hardened sandbox
     Python · Java · C++ · strict resource / egress policies
```

A modular monolith is preferred for the first production version: it keeps project, assignment, note and access-control rules in one transaction-oriented codebase while the execution fleet is isolated and scales independently. Avoid splitting every CRUD route into a microservice before load data justifies the operational cost.

## 3. Product data model

- `Student`: class membership, grade label, teacher assignment and aggregate learning signals.
- `Assignment`: intended language, learning instructions, class, due date and status.
- `Submission`: learner, assignment, timestamp, status, rubric/test measures and debugging evidence.
- `TeacherNote`: actionable follow-up linked optionally to a learner, assigned owner, priority, target date and workflow status.
- `NoteComment`: discussion attached to a follow-up, preserving the handoff context.
- `Project`: title, language, class/learner link and Git repository path.
- `RunRecord`: language, outcome, duration, bounded output and optional project association.

The target design should add organisation/tenant IDs, stable curriculum concept IDs, lesson and rubric IDs, identity-provider subject IDs, audit events, event provenance, retention metadata and concurrency versions before real multi-tenant data is introduced.

## 4. Analytics principles

1. Every measure needs a written definition and source: e.g. rubric-derived concept mastery versus assignment completion.
2. Missing data must remain visibly missing. It must not be silently treated as a zero score.
3. Concept scores should map to curriculum-owned identifiers and rubrics, not arbitrary labels only.
4. Explain the visible support signal, show contributing evidence and let teachers add context or override follow-ups.
5. Do not use editor time, number of keystrokes or run count as a stand-alone measure of learning.
6. Track interventions over time, but do not claim causal impact without an appropriate evaluation design.
7. Collect only evidence necessary for teaching, with retention periods and access logs.

## 5. API conventions

- Version routes under `/api/v1/` when moving from pilot to a versioned production contract.
- Publish OpenAPI schemas and generate TypeScript clients.
- Validate all input and return structured, non-sensitive errors.
- Use idempotency keys for expensive job creation and retries.
- Use ETags / `If-Match` or explicit record versions for shared-file and note updates.
- Use cursor pagination for large lists, not unbounded list responses.
- Authorise every object against an authenticated actor's tenant/class membership and allowed action.
- Keep runner credentials separate from API/database secrets.

## 6. Security boundaries

The local pilot binds to `127.0.0.1` and has no authentication. It is not safe to expose publicly. The Docker runner is a development baseline, not a production security certification. For a real student-facing multi-tenant platform:

- Require a security-approved sandbox design and independent escape testing.
- Put execution workers in a separate network/account with no path to databases, metadata services or internal control planes.
- Default to no network egress, non-root execution, read-only base image, bounded scratch storage, CPU/memory/PID/output/time limits and reliable cleanup.
- Use short-lived workload identities; never inject application or cloud credentials into student code.
- Implement authentication, class-scoped authorisation, audit logging, rate limits, abuse detection and incident response.
- Define privacy notice, parent/guardian and child-data requirements with the relevant legal/privacy team before using real students' records.

## 7. Capacity planning inputs

Before committing to EKS/VMs/queue sizes, collect:

- Expected concurrent active editors and simultaneous `Run` bursts by class schedule.
- Runtime split across Python / Java / C++ and average/95th-percentile execution time.
- Typical and maximum source code, output and artifact sizes.
- Assignment submissions per minute and teacher-report query patterns.
- Data retention, backup and recovery objectives.

Scale the API on latency/CPU and the runner fleet on queue age/depth plus measured worker saturation. Bound each tenant/class's concurrency so a busy class cannot starve others. Set performance budgets only after representative load tests.
