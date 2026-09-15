import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "deploy_backend",
    Path(__file__).resolve().parents[2] / ".github/scripts/deploy_backend.py",
)
deployment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deployment)


def service(revision="new", state="COMPLETED"):
    return {
        "taskDefinition": revision,
        "desiredCount": 1,
        "runningCount": 1,
        "pendingCount": 0,
        "deployments": [{"taskDefinition": revision, "rolloutState": state}],
    }


def test_intended_healthy_revision_succeeds():
    assert deployment.successful_service(service(), "new")


def test_healthy_rollback_must_not_pass_release():
    assert not deployment.successful_service(service("old"), "new")


def test_incomplete_or_zero_task_service_does_not_pass():
    assert not deployment.successful_service(service(state="IN_PROGRESS"), "new")
    current = service()
    current["runningCount"] = 0
    assert not deployment.successful_service(current, "new")
