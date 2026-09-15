"""Path routing and fail-closed aggregation for EDIP pull-request CI."""

import json
import os
import subprocess
import sys

TERRAFORM_WORKFLOWS = {
    ".github/workflows/terraform-ci.yml",
    ".github/workflows/terraform-apply.yml",
}
ROUTING_FILES = {
    ".github/workflows/pr-gate.yml",
    ".github/scripts/pr_gate.py",
    ".github/scripts/test_pr_gate.py",
}


def classify_paths(paths: list[str]) -> dict[str, bool]:
    required = dict.fromkeys(("application", "docker", "terraform"), False)
    for path in paths:
        if path in ROUTING_FILES:
            required = dict.fromkeys(required, True)
        elif path.startswith("infra/") or path in TERRAFORM_WORKFLOWS:
            required["terraform"] = True
        elif path.startswith("docs/") or path in {"README.md", "LICENSE", "LICENSE.md"}:
            continue
        else:
            # Unknown paths run application/Docker checks rather than bypassing CI.
            required["application"] = required["docker"] = True
    return required


def gate_errors(needs: dict) -> list[str]:
    if needs.get("changes", {}).get("result") != "success":
        return ["Change detection did not succeed."]
    outputs = needs["changes"].get("outputs", {})
    errors = []
    for job in ("application", "docker", "terraform"):
        required = outputs.get(job)
        result = needs.get(job, {}).get("result")
        if required not in {"true", "false"}:
            errors.append(f"{job}: missing or invalid routing output.")
        elif result != "success" and not (required == "false" and result == "skipped"):
            errors.append(f"{job}: required={required}, result={result!r}.")
    return errors


def main() -> None:
    if sys.argv[1:] == ["changes"]:
        # No rename collapsing: both old and new paths affect routing. A full
        # checkout avoids the file-count limits of PR API/workflow path filters.
        diff = subprocess.check_output(
            [
                "git",
                "diff",
                "--name-only",
                "--no-renames",
                "-z",
                f"{os.environ['BASE_SHA']}...{os.environ['HEAD_SHA']}",
                "--",
            ]
        )
        paths = [os.fsdecode(path) for path in diff.split(b"\0") if path]
        required = classify_paths(paths)
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            for job, enabled in required.items():
                output.write(f"{job}={str(enabled).lower()}\n")
        print(json.dumps(required))
    elif sys.argv[1:] == ["gate"]:
        errors = gate_errors(json.loads(os.environ["NEEDS_JSON"]))
        if errors:
            raise SystemExit("\n".join(errors))
        print("All required PR checks passed; only path-filtered jobs may be skipped.")
    else:
        raise SystemExit("Usage: pr_gate.py changes|gate")


if __name__ == "__main__":
    main()
