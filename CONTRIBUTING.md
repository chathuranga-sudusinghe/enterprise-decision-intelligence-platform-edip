# Contributing to EDIP

Thank you for your interest in contributing to the Enterprise Decision Intelligence Platform (EDIP). Contributions that improve the project's quality, clarity, reliability, and usability are welcome.

## Contribution Scope

Good contributions include:

- Documentation improvements
- Tests and test coverage improvements
- Small, focused bug fixes
- Examples that clarify supported workflows
- Setup and troubleshooting improvements
- Feature improvements with an approved scope

## Issue-First Workflow

The roadmap is governed through approved GitHub Issues. Before material implementation,
identify an applicable issue or prepare a proposed issue with the problem, evidence,
scope, exclusions, acceptance criteria, and validation. Proposed issue content must
be reviewed and explicitly approved before creation. Implementation requires separate
approval; issue creation alone is insufficient.

Read-only inspection, discussion, and drafts do not require an issue. Contributions
outside approved scope may be declined even when technically sound.

[AGENTS.md](AGENTS.md) defines coding-agent permissions, AI-assistance standards,
protected evidence, and independent-review requirements. Suggested workflow steps
are not permission for automated Git or GitHub operations.

## Contribution Guidelines

- Identify an applicable approved issue before material implementation.
- Keep pull requests small, focused, and easy to review.
- Do not add large or new runtime dependencies without prior approval.
- Do not commit datasets, secrets, credentials, model artifacts, or large generated files.
- Follow the existing project structure and established implementation patterns.
- Run relevant tests and checks before opening a pull request where applicable.
- Avoid unrelated refactoring or formatting changes in the same pull request.

## Fork, Branch, and Pull Request Workflow

1. Fork the repository and clone your fork.
2. After scope approval, create a focused branch from `dev`, such as `docs/issue-130-edip-agent-governance`. Reuse an appropriate existing branch.
3. Make the smallest change needed to address the issue.
4. Run the relevant tests, checks, or documentation validation.
5. Commit with a clear, concise message.
6. Push the branch to your fork and open a pull request targeting `dev`. Each Git operation requires explicit authorization when performed by an AI coding agent.
7. Complete the pull request template and link the related issue.

## Good First Contributions

Examples of suitable first contributions include:

- Correcting unclear or outdated documentation
- Adding a focused test for existing behavior
- Improving an error message or troubleshooting note
- Adding a small usage example for an existing feature
- Fixing a reproducible, well-scoped bug
- Clarifying local setup steps without changing runtime behavior

Look for issues labeled `good first issue` for tasks with a defined scope.

## Pull Request Review

Contributions are reviewed for correctness, scope, clarity, tests, security, maintainability, and alignment with the project roadmap. Review may include requests for changes, a narrower scope, or additional validation.

Approval is not guaranteed. Pull requests may be closed when scope is exceeded, planned work is duplicated, unnecessary complexity is introduced, or these guidelines are not followed. Professional discussion and reasonable review time are expected.
