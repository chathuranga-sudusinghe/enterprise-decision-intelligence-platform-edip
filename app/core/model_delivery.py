"""Stage immutable S3 objects, verify integrity, then start load-only serving."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any


def stage_bundle(client: Any, env: dict[str, str]) -> Path:
    bucket = env["EDIP_MODEL_BUCKET"]
    prefix = env["EDIP_MODEL_PREFIX"]
    if not bucket or not re.fullmatch(r"[A-Za-z0-9/_-]+", prefix):
        raise ValueError("Invalid model object location")
    if prefix.startswith("/") or prefix.endswith("/"):
        raise ValueError("Invalid model object prefix")
    root = Path(env["EDIP_FAVORITA_MODEL_BUNDLE_PATH"])
    objects = (
        ("model.txt", "EDIP_MODEL_VERSION_ID", "EDIP_MODEL_SHA256", 64 * 1024 * 1024),
        ("metadata.json", "EDIP_METADATA_VERSION_ID", "EDIP_METADATA_SHA256", 2 * 1024 * 1024),
    )
    for _, version, checksum, _ in objects:
        if not env[version] or env[version] == "null":
            raise ValueError("An immutable S3 object version is required")
        if not re.fullmatch(r"[a-f0-9]{64}", env[checksum]):
            raise ValueError("A SHA-256 checksum is required")
    root.mkdir(parents=True, exist_ok=True)
    for filename, version, checksum, limit in objects:
        response = client.get_object(
            Bucket=bucket, Key=f"{prefix}/{filename}", VersionId=env[version]
        )
        body = response["Body"]
        temporary = root / f".{filename}.download"
        try:
            if response.get("VersionId") != env[version]:
                raise ValueError("Unexpected model object version")
            if response.get("ContentLength", limit + 1) > limit:
                raise ValueError("Model object exceeds size limit")
            digest = hashlib.sha256()
            size = 0
            with temporary.open("wb") as output:
                while chunk := body.read(1024 * 1024):
                    size += len(chunk)
                    if size > limit:
                        raise ValueError("Model object exceeds size limit")
                    digest.update(chunk)
                    output.write(chunk)
            if digest.hexdigest() != env[checksum]:
                raise ValueError("Model object checksum mismatch")
            temporary.replace(root / filename)
        finally:
            body.close()
            temporary.unlink(missing_ok=True)
    return root


def main() -> None:
    import boto3
    from botocore.config import Config

    try:
        client = boto3.client(
            "s3",
            config=Config(connect_timeout=10, read_timeout=30, retries={"max_attempts": 3}),
        )
        stage_bundle(client, dict(os.environ))
    except Exception:
        raise SystemExit("Verified model staging failed; refusing to start") from None
    os.execvp(
        "uvicorn",
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
    )


if __name__ == "__main__":
    main()
