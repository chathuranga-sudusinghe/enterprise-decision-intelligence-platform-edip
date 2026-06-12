# Contributing to EDIP

Thank you for your interest in contributing to the Enterprise Decision Intelligence Platform (EDIP). Contributions that improve the project's quality, clarity, reliability, and usability are welcome.

## Contribution Scope

Good contributions include:

- Documentation improvements
- Tests and test coverage improvements
- Small, focused bug fixes
- Examples that clarify supported workflows
- Setup and troubleshooting improvements
- Feature improvements that have been clearly discussed with the maintainers

## Maintainer-Led Roadmap

EDIP follows a maintainer-led roadmap to keep the architecture and project direction coherent. Before starting major features, broad refactors, architectural changes, or work that affects several parts of the system, open an issue or comment on an existing issue and wait for maintainer agreement.

Unsolicited large changes may be declined even when the implementation is technically sound.

## Contribution Guidelines

- Open or comment on an issue before beginning major work.
- Keep pull requests small, focused, and easy to review.
- Do not add large or new runtime dependencies without prior approval.
- Do not commit datasets, secrets, credentials, model artifacts, or large generated files.
- Follow the existing project structure and established implementation patterns.
- Run relevant tests and checks before opening a pull request where applicable.
- Avoid unrelated refactoring or formatting changes in the same pull request.

## Fork, Branch, and Pull Request Workflow

1. Fork the repository and clone your fork.
2. Create a focused branch from the current development base, using a descriptive name such as `docs/improve-setup-guide` or `fix/forecast-validation`.
3. Make the smallest change needed to address the issue.
4. Run the relevant tests, checks, or documentation validation.
5. Commit with a clear, concise message.
6. Push the branch to your fork and open a pull request.
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

Maintainers review contributions for correctness, scope, clarity, tests, security, maintainability, and alignment with the project roadmap. Review may include requests for changes, a narrower scope, or additional validation.

Approval is not guaranteed, and maintainers may close pull requests that are out of scope, duplicate planned work, introduce unnecessary complexity, or do not follow these guidelines. Please keep discussion professional and allow maintainers reasonable time to review.
