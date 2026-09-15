"""Deploy one immutable backend revision and reject silent ECS rollback."""

import json
import os
import subprocess
import time
import urllib.error
import urllib.request


def aws(*args):
    return json.loads(subprocess.check_output(["aws", *args, "--output", "json"], text=True))


def successful_service(service, target):
    deployments = service.get("deployments", [])
    return (
        service.get("taskDefinition") == target
        and service.get("desiredCount") == 1
        and service.get("runningCount") == 1
        and service.get("pendingCount") == 0
        and len(deployments) == 1
        and deployments[0].get("taskDefinition") == target
        and deployments[0].get("rolloutState") == "COMPLETED"
    )


def check_public_routes(url):
    # Deliberately do not follow redirects that could hide an unexpected route.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    for path, method, expected in [
        ("/health", "GET", 200), ("/ready", "GET", 200),
        ("/docs", "GET", 200), ("/openapi.json", "GET", 200),
        ("/api/v1/forecast", "POST", 403), ("/api/v1/forecast", "GET", 403),
        ("/metrics", "GET", 403), ("/ready", "POST", 403), ("/", "GET", 403),
    ]:
        try:
            with opener.open(urllib.request.Request(url + path, method=method), timeout=15) as r:
                code = r.status
                body = r.read()
        except urllib.error.HTTPError as error:
            code, body = error.code, error.read()
        if code != expected:
            raise RuntimeError(f"{method} {path}: expected {expected}, got {code}")
        if path == "/ready" and method == "GET":
            if json.loads(body).get("favorita_predictor_loaded") is not True:
                raise RuntimeError("Real model is not ready")
        print(f"{method} {path}: {code}")


def main():
    contract = json.loads(os.environ["DEPLOYMENT"])
    image = os.environ["IMAGE_DIGEST_URI"]
    if not image.startswith(contract["repository_url"] + "@sha256:"):
        raise ValueError("Image must use this EDIP repository and an immutable digest")
    template = aws("ecs", "describe-task-definition", "--task-definition",
                   contract["template_arn"], "--include", "TAGS")
    definition = template["taskDefinition"]
    allowed = [
        "family", "taskRoleArn", "executionRoleArn", "networkMode", "containerDefinitions",
        "volumes", "placementConstraints", "requiresCompatibilities", "cpu", "memory",
        "runtimePlatform", "ephemeralStorage",
    ]
    revision = {key: definition[key] for key in allowed if key in definition}
    revision["tags"] = template.get("tags", [])
    containers = revision["containerDefinitions"]
    if len(containers) != 1 or containers[0]["name"] != "backend":
        raise ValueError("Expected one backend container")
    containers[0]["image"] = image
    previous = aws("ecs", "describe-services", "--cluster", contract["cluster"],
                   "--services", contract["service"])
    if previous.get("failures") or len(previous.get("services", [])) != 1:
        raise RuntimeError("Expected existing EDIP service")
    print("Previous task definition:", previous["services"][0]["taskDefinition"])
    target = aws("ecs", "register-task-definition", "--cli-input-json",
                 json.dumps(revision))["taskDefinition"]["taskDefinitionArn"]
    print("Deploying task definition:", target)
    aws("ecs", "update-service", "--cluster", contract["cluster"], "--service",
        contract["service"], "--task-definition", target, "--desired-count", "1")
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        result = aws("ecs", "describe-services", "--cluster", contract["cluster"],
                     "--services", contract["service"])
        if result.get("failures"):
            raise RuntimeError("ECS service lookup failed")
        service = result["services"][0]
        if successful_service(service, target):
            check_public_routes(contract["url"])
            print("Public documentation:", contract["url"] + "/docs")
            return
        if any(d.get("taskDefinition") == target and d.get("rolloutState") == "FAILED"
               for d in service.get("deployments", [])):
            raise RuntimeError("ECS deployment failed; inspect circuit-breaker rollback")
        if service.get("taskDefinition") != target:
            raise RuntimeError("ECS reverted to a different task definition")
        time.sleep(15)
    raise RuntimeError("Timed out waiting for the intended ECS revision")


if __name__ == "__main__":
    main()
