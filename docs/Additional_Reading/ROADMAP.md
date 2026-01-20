# Compass Framework Roadmap & Milestones

> Purpose: Track planned work with checkable milestones. Audience: maintainers and contributors executing the migration phases. Out of scope: detailed testing instructions or live test counts.

Related docs: [PROJECT_STATUS.md](PROJECT_STATUS.md), [docs/TESTING.md](docs/TESTING.md)

## How to Use
- Check off items (`[x]`) when completed.
- Keep status tags concise: In Progress, Blocked, Deferred.
- Update links to commits or PRs when relevant.

## Roadmap Principles
- **High-level and outcome-oriented**: Define what we aim to achieve, not how to implement it.
- **Flexible implementation**: Encourage creative solutions; avoid prescribing tools or patterns unless essential.
- **Evolve responsibly**: Adjust scope as learning occurs; keep changes minimal and clearly noted.
- **Avoid brittle details**: No hard-coded test counts or environment specifics—see [docs/TESTING.md](docs/TESTING.md) for execution details.

## Updating Milestones (Lightweight)
- **Mark completion**: Change `[ ]` to `[x]` when a milestone’s outcome is achieved.
- **Optionally reference work**: Link to a PR or commit for traceability.
- **Status tags**: Use brief labels (In Progress, Blocked, Deferred) when helpful.
- **Scope changes**: Add a short bullet under the item describing what changed and why.
- **Keep ordering stable**: Reorder phases only when priorities fundamentally shift.

## Completed Foundations
- [x] Protocol architecture established for 5 core domains
  - Navigator → `SeleniumNavigator`
  - Configuration → `JsonConfiguration`, `IniConfiguration`
  - VersionChecker → `BrowserVersionChecker`
  - Logging → `StandardLogger`, `StandardLoggerFactory`
  - DriverManager → `StandardDriverManager`
- [x] Public API with conditional imports in [src/compass_core/__init__.py](src/compass_core/__init__.py)
- [x] Test suite structured (unit, integration, E2E) — see [docs/TESTING.md](docs/TESTING.md)
- [x] Package build via [pyproject.toml](pyproject.toml)

## Phase 1: DevCompass Analysis
- [ ] Inventory `core/` for business rule extraction opportunities
- [ ] Inventory `flows/` for workflow orchestration patterns
- [ ] Inventory `data/` module for data management needs
- [ ] Identify authentication-related flows for final E2E coverage

## Phase 2: Core Business Logic Extraction
- [ ] Design `BusinessRuleEngine` protocol and a baseline implementation
- [ ] Design `WorkflowManager` protocol and a baseline implementation
- [ ] Ensure backward compatibility for DevCompass during migration
- [ ] Add integration tests covering rule/workflow composition

## Phase 3: Data & Artifact Management
- [ ] Design `DataManager` protocol (file/database implementations)
- [ ] Design `ArtifactManager` protocol (reports/artifacts lifecycle)
- [ ] Extract remaining utilities (file ops, validation, formatting)
- [ ] Extend tests for data persistence and artifact generation

## Phase 4: Production Readiness
- [ ] Client integration testing across real projects
- [ ] Performance review and optimizations
- [ ] Documentation and migration guides for DevCompass users
- [ ] Versioning and release management improvements

## Governance & Quality Gates
- [ ] CI: run unit + integration suites on PRs
- [ ] Pre-release: run E2E (enabled) on tagged builds
- [ ] API stability checks: prevent breaking changes to public interfaces
- [ ] Developer docs: keep README and status pages current

## Notes
- Use [PROJECT_STATUS.md](PROJECT_STATUS.md) for the current snapshot and completion summary.
- Avoid hard-coded test counts; rely on runner output described in [docs/TESTING.md](docs/TESTING.md).
