# Codingal Code Studio
## Learning Intelligence & Teacher Collaboration — Product Brief

### The product thesis

Codingal already has coding experiences. Code Studio should earn a place in the product by improving what teachers can understand and do after observing students code. The core value is not “another browser editor”; it is a workflow that turns observable learning evidence into a timely teaching action and makes that action visible to a colleague.

**Product promise:** *Know what a learner understands, agree on what to try next, and see whether it helped.*

### What the standalone pilot demonstrates

1. **Learning intelligence:** learner profiles combine concept mastery, assignment completion, recent mastery movement and activity context. Transparent rules surface learners to review without treating a score as a diagnosis.
2. **Concept-level insight:** educators can identify lower-scoring concepts, use them to plan a worked example or retrieval task, and inspect learner-level context.
3. **Collaborative follow-through:** teachers can assign an owner, priority and target date, write context, discuss a handoff and mark it resolved. The record survives a local app restart in the SQLite database.
4. **Assignment workflow:** teachers can create learning tasks and inspect demo completion and scores.
5. **Code and project continuity:** the standalone workspace saves project files and uses local Git repositories for version history and non-destructive restore commits.
6. **Delivery proof:** the product starts locally, has a documented API, seeded demonstration data and an optional isolated Docker runner for native language execution.

### What the CEO should be shown in a short demo

1. Open the class overview and point out the concept mastery map and priority learner queue.
2. Open a learner profile and explain why a teacher would investigate the combination of concept scores, completion and recent movement.
3. Create a teacher follow-up, assign an owner and due date, add a comment, then mark the item resolved.
4. Create an assignment and inspect its completion summary.
5. Open a project, save code, create a Git checkpoint, edit it and demonstrate that the earlier checkpoint can be restored as a new commit.

This sequence tells a product story: **signal → teacher judgement → collaborative action → follow-up**, with coding work preserved as evidence.

### Core user journeys

**Teacher:** review class → inspect concept signal → open learner profile → create/assign follow-up → agree on a teaching strategy → review next submission.

**Collaborating teacher:** open the shared follow-up → read context → comment or accept ownership → update status → document the outcome.

**Student (pilot workspace):** open a project → edit and save code → run in an isolated local runner where configured → save a named Git version → return to previous work.

### Metrics worth validating in a real pilot

The initial deployment should measure the product's use and usefulness before claiming learning impact:

- Teacher time from noticing a concern to creating a documented next step.
- Percentage of follow-ups with an owner, due date and a recorded outcome.
- Median follow-up resolution time and proportion overdue.
- Assignment completion and retry rates by concept, not only by student.
- Change in rubric-based concept mastery after an intervention, compared against a suitable baseline.
- Teacher-reported usefulness and reduction in fragmented handoff messages.
- Student experience: whether project continuity reduces lost work and setup time.

Define metrics with curriculum and research stakeholders. Avoid using keystrokes, time in editor or number of runs as stand-alone proxies for learning. Review confounders such as assignment difficulty, attendance and prior experience.

### Explicit non-goals for this pilot

- It is not an AI tutor or an automated grading oracle.
- It does not claim predictive accuracy for student risk.
- It does not access or alter the live Codingal dashboard.
- It does not authenticate real teachers or students.
- It does not yet share follow-ups or projects across separate machines.
- It is not an approved multi-tenant production code execution service.

### Recommended next-stage product work

1. Validate the workflows with a small group of teachers using fictional data first.
2. Partner with Curriculum/Academic Operations to define a consistent concept and rubric taxonomy.
3. Obtain the approved identity and classroom integration contract.
4. Add authentication, class-scoped permissions and multi-user collaboration.
5. Connect real, authorised assessment events through a documented event schema with source and timestamp provenance.
6. Harden and separately deploy execution workers; complete security and privacy review.
7. Run a measured pilot with explicit success criteria, support process and rollback plan.
