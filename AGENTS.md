# AGENTS.md

## Mandatory Behavior for AI Coding Agents

Every AI coding agent working on this repository must follow these rules. They are non-negotiable and apply to every conversation, model, and session.

### Before Starting Work

1. **Read `AGENTS.md`** in full before making any changes.
2. **Read the relevant technical documentation** in the repository root:
   - `ARCHITECTURE.md` — system architecture, modules, responsibilities
   - `DATABASE.md` — entities, relationships, constraints
   - `API_SPECIFICATION.md` — API conventions, endpoints, contracts
   - `SECURITY.md` — authentication, authorization, roles, security requirements
   - `DEVELOPMENT_PLAN.md` — implementation phases, dependencies, completion criteria
   - `PROGRESS.md` — actual implementation status and pending work
3. **Read `.agent/CURRENT_TASK.md`, `.agent/IMPLEMENTATION_LOG.md`, `.agent/DECISIONS.md`, and `.agent/NEXT_STEPS.md`** when starting or resuming work.
4. **Inspect Git status** (`git status`) before modifying any files.
5. **Never assume previous conversation history is available.** Each session starts fresh.

### Decision Integrity

- **Never invent project decisions or requirements.** If something is not documented, mark it as TBD and request user approval.
- **Never silently change approved architecture.** Approved decisions are recorded in `.agent/DECISIONS.md` and the root documentation files.
- **Preserve existing project structure.** Do not modify or delete the six root documentation files unless explicitly authorized.
- **Do not modify backend source code** unless implementing an authorized task.
- **Do not create database migrations** unless explicitly authorized.
- **Do not install dependencies** unless explicitly authorized.

### Implementation Workflow

- **Work incrementally.** One clearly defined implementation unit at a time (method, function, class, endpoint, validation rule, configuration component, test case).
- **Commit every completed unit immediately.** Do not wait until an entire file or module is finished.
- **Follow the mandatory incremental Git commit policy.**
- **Use Conventional Commits in English.** Format: `<type>(<scope>): <description>` (e.g., `feat(auth): add user registration endpoint`).
- **Stage only relevant files.** Never use `git add .` blindly.
- **Never create empty commits.** Never include unfinished or unrelated changes.
- **Never combine unrelated implementation units** just to reduce the number of commits.
- **A file can and should appear in multiple commits** as its implementation progresses.
- **Test each completed implementation unit** when applicable.
- **Never claim something is implemented without verifying the code and relevant tests.**
- **Never commit secrets, credentials, `.env` files, or unrelated user changes.**

### Context Management

Agents must proactively preserve project continuity. Before ending a session, when the context is becoming large, or when requested:

1. Finish or safely pause the current implementation unit.
2. Record exactly what was completed in `.agent/IMPLEMENTATION_LOG.md`.
3. Record what remains unfinished in `.agent/CURRENT_TASK.md` and `.agent/NEXT_STEPS.md`.
4. Record relevant files and locations.
5. Record test results and associated commit hashes.
6. Update `.agent/CURRENT_TASK.md` and `.agent/NEXT_STEPS.md`.
7. Ensure another agent can resume without relying on conversation history.

Never mark unfinished work as completed.

### Authorization

- **Do not authorize implementation automatically.** The user must explicitly approve each new implementation task.
- **Do not push to GitHub** until the user explicitly authorizes the push.
