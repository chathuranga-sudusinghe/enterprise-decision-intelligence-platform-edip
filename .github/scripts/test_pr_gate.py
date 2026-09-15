"""Exercise PR routing and required-gate policy without GitHub or cloud access."""

import itertools
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pr_gate import classify_paths, gate_errors, main


class PullRequestGateTests(unittest.TestCase):
    def needs_for(self, paths):
        selected = classify_paths(paths)
        return {
            "changes": {
                "result": "success",
                "outputs": {job: str(value).lower() for job, value in selected.items()},
            },
            **{
                job: {"result": "success" if value else "skipped"}
                for job, value in selected.items()
            },
        }

    def test_requested_scenarios(self):
        scenarios = [
            (["app/main.py"], (True, True, False)),
            (["infra/terraform/aws/main.tf"], (False, False, True)),
            (["app/main.py", "infra/terraform/aws/main.tf"], (True, True, True)),
            (["docs/architecture.md", "README.md"], (False, False, False)),
        ]
        for paths, expected in scenarios:
            with self.subTest(paths=paths):
                self.assertEqual(tuple(classify_paths(paths).values()), expected)
                self.assertEqual(gate_errors(self.needs_for(paths)), [])

    def test_infrastructure_and_terraform_workflows(self):
        for path in (
            "infra/kubernetes/deployment.yaml",
            "infra/terraform/README.md",
            ".github/workflows/terraform-ci.yml",
            ".github/workflows/terraform-apply.yml",
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    classify_paths([path]),
                    {"application": False, "docker": False, "terraform": True},
                )

    def test_routing_policy_changes_validate_all_specialists(self):
        for path in (
            ".github/workflows/pr-gate.yml",
            ".github/scripts/pr_gate.py",
            ".github/scripts/test_pr_gate.py",
        ):
            self.assertTrue(all(classify_paths([path]).values()))

    def test_unknown_and_build_paths_fail_safe(self):
        for path in (
            "pyproject.toml",
            "Dockerfile",
            ".dockerignore",
            ".github/workflows/integration-ci.yml",
            ".github/workflows/docker-ci.yml",
            "new-component/settings.yaml",
        ):
            self.assertEqual(
                classify_paths([path]),
                {"application": True, "docker": True, "terraform": False},
            )

    def test_all_required_and_filtered_result_combinations(self):
        for paths in (["app/main.py"], ["infra/main.tf"], ["docs/a.md"]):
            selected = classify_paths(paths)
            for results in itertools.product(
                ("success", "failure", "cancelled", "skipped"), repeat=3
            ):
                needs = self.needs_for(paths)
                for job, result in zip(selected, results):
                    needs[job]["result"] = result
                expected = all(
                    result == "success" or (not required and result == "skipped")
                    for required, result in zip(selected.values(), results)
                )
                self.assertEqual(not gate_errors(needs), expected)

    def test_failed_detection_or_missing_results_cannot_pass(self):
        for result in ("failure", "cancelled", "skipped", None):
            needs = self.needs_for(["docs/a.md"])
            needs["changes"]["result"] = result
            self.assertTrue(gate_errors(needs))
        needs = self.needs_for(["app/main.py"])
        del needs["application"]
        self.assertTrue(gate_errors(needs))
        for value in (None, "", "unknown"):
            needs = self.needs_for(["docs/a.md"])
            needs["changes"]["outputs"]["terraform"] = value
            self.assertTrue(gate_errors(needs))

    def test_diff_uses_both_rename_paths_and_null_separators(self):
        # A rename out of infrastructure into docs must still select Terraform.
        diff = b"infra/old.tf\0docs/renamed.tf\0app/name with\nnewline.py\0"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "outputs"
            with (
                patch.dict(
                    os.environ,
                    {
                        "BASE_SHA": "base",
                        "HEAD_SHA": "head",
                        "GITHUB_OUTPUT": str(output),
                    },
                ),
                patch("sys.argv", ["pr_gate.py", "changes"]),
                patch("pr_gate.subprocess.check_output", return_value=diff) as git,
            ):
                main()
                git.assert_called_once_with(
                    [
                        "git",
                        "diff",
                        "--name-only",
                        "--no-renames",
                        "-z",
                        "base...head",
                        "--",
                    ]
                )
            self.assertEqual(
                output.read_text(), "application=true\ndocker=true\nterraform=true\n"
            )

    def test_gate_command_exits_unsuccessfully_for_required_skip(self):
        needs = self.needs_for(["app/main.py"])
        needs["application"]["result"] = "skipped"
        with (
            patch.dict(os.environ, {"NEEDS_JSON": json.dumps(needs)}),
            patch("sys.argv", ["pr_gate.py", "gate"]),
            self.assertRaises(SystemExit),
        ):
            main()


if __name__ == "__main__":
    unittest.main()
