"""Check the actual release trigger without executing GitHub or deployment jobs."""

import re
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def release_paths() -> tuple[str, ...]:
    workflow = (
        REPOSITORY_ROOT / ".github/workflows/release-orchestrator.yml"
    ).read_text(encoding="utf-8")
    # Deliberately accept only the checked-in main-only push trigger and its
    # quoted path list. A syntax/event/branch change requires explicit review;
    # this is not a general YAML parser or a GitHub glob implementation.
    trigger = re.search(
        r"^on:\n  push:\n    branches: \[main\]\n    paths:\n"
        r'((?:      - "[^"\n]+"\n)+)(?=\n\S)',
        workflow,
        flags=re.MULTILINE,
    )
    if trigger is None:
        raise AssertionError("Expected the reviewed main-only push/path trigger")
    patterns = tuple(re.findall(r'      - "([^"\n]+)"', trigger.group(1)))
    if not all(re.fullmatch(r"[\w./-]+(?:/\*\*)?", p) for p in patterns):
        raise AssertionError("Release paths must use exact files or directory/**")
    return patterns


def selects_release(branch: str, changed_paths: tuple[str, ...]) -> bool:
    patterns = release_paths()
    return branch == "main" and any(
        path.startswith(pattern[:-2]) if pattern.endswith("/**") else path == pattern
        for path in changed_paths
        for pattern in patterns
    )


class ReleasePolicyTests(unittest.TestCase):
    def test_documentation_only_changes_do_not_select_release(self) -> None:
        for path in (
            "docs/deployment/EDIP_BACKEND_FIRST.md",
            "docs/deployment/nested/operations.md",
            "docs/governance/EDIP_ENGINEERING_DELIVERY_WORKFLOW.md",
            "docs/architecture/EDIP_V2_FLAGSHIP_ARCHITECTURE_PLAN.md",
            "README.md",
            "AGENTS.md",
            "LICENSE",
        ):
            with self.subTest(path=path):
                self.assertFalse(selects_release("main", (path,)))

    def test_deployable_inputs_remain_covered(self) -> None:
        for path in (
            "app/main.py",
            "app/core/config.py",
            "pipelines/runtime_paths.py",
            "pipelines/models/favorita_bundle_inference.py",
            "Dockerfile",
            ".dockerignore",
            "pyproject.toml",
            ".github/workflows/application-deploy.yml",
            ".github/scripts/deploy_backend.py",
            "infra/terraform/modules/backend-hosting/main.tf",
            "infra/terraform/aws/main.tf",
            "infra/terraform/aws-bootstrap/main.tf",
            ".github/workflows/terraform-apply.yml",
            ".github/workflows/release-orchestrator.yml",
        ):
            with self.subTest(path=path):
                self.assertTrue(selects_release("main", (path,)))

    def test_mixed_changes_still_select_release(self) -> None:
        self.assertTrue(
            selects_release(
                "main", ("docs/deployment/EDIP_BACKEND_FIRST.md", "app/main.py")
            )
        )

    def test_other_branches_do_not_select_release(self) -> None:
        for branch in ("dev", "ci/issue-144-release-trigger-safety", "main-copy"):
            with self.subTest(branch=branch):
                self.assertFalse(selects_release(branch, ("app/main.py",)))

    def test_offline_and_policy_test_changes_do_not_select_release(self) -> None:
        self.assertFalse(
            selects_release(
                "main",
                (
                    "pipelines/models/favorita_lightgbm.py",
                    "pipelines/evaluation/favorita_metrics.py",
                    ".github/scripts/test_release_policy.py",
                ),
            )
        )
        self.assertFalse(selects_release("main", ()))


if __name__ == "__main__":
    unittest.main()
