import hashlib
from io import BytesIO

import pytest

from app.core.model_delivery import stage_bundle


def configuration(tmp_path):
    return {
        "EDIP_MODEL_BUCKET": "edip-test",
        "EDIP_MODEL_PREFIX": "models/reviewed",
        "EDIP_FAVORITA_MODEL_BUNDLE_PATH": str(tmp_path / "bundle"),
        "EDIP_MODEL_VERSION_ID": "model-v1",
        "EDIP_METADATA_VERSION_ID": "metadata-v1",
        "EDIP_MODEL_SHA256": hashlib.sha256(b"model").hexdigest(),
        "EDIP_METADATA_SHA256": hashlib.sha256(b"metadata").hexdigest(),
    }


class S3:
    def __init__(self, corrupt=False, oversized=False, wrong_version=False):
        self.calls = []
        self.corrupt = corrupt
        self.oversized = oversized
        self.wrong_version = wrong_version

    def get_object(self, **kwargs):
        self.calls.append(kwargs)
        data = b"model" if kwargs["Key"].endswith("model.txt") else b"metadata"
        return {
            "Body": BytesIO(b"corrupt" if self.corrupt else data),
            "ContentLength": 100_000_000 if self.oversized else len(data),
            "VersionId": "wrong" if self.wrong_version else kwargs["VersionId"],
        }


def test_stages_exact_versions_and_bytes(tmp_path):
    client = S3()
    root = stage_bundle(client, configuration(tmp_path))
    assert (root / "model.txt").read_bytes() == b"model"
    assert (root / "metadata.json").read_bytes() == b"metadata"
    assert [c["VersionId"] for c in client.calls] == ["model-v1", "metadata-v1"]
    assert all(c["Bucket"] == "edip-test" for c in client.calls)
    assert [c["Key"] for c in client.calls] == [
        "models/reviewed/model.txt", "models/reviewed/metadata.json"
    ]


@pytest.mark.parametrize("failure", ["corrupt", "oversized", "wrong_version"])
def test_bad_download_fails_closed(tmp_path, failure):
    with pytest.raises(ValueError):
        stage_bundle(S3(**{failure: True}), configuration(tmp_path))
    assert not list((tmp_path / "bundle").glob(".*.download"))
    assert not (tmp_path / "bundle" / "model.txt").exists()


@pytest.mark.parametrize("key,value", [
    ("EDIP_MODEL_VERSION_ID", "null"),
    ("EDIP_METADATA_SHA256", "invalid"),
    ("EDIP_MODEL_PREFIX", "../other"),
])
def test_invalid_configuration_never_downloads(tmp_path, key, value):
    env = configuration(tmp_path)
    env[key] = value
    client = S3()
    with pytest.raises(ValueError):
        stage_bundle(client, env)
    assert not client.calls


def test_checksum_mismatch_identifies_metadata_and_both_digests(tmp_path):
    env = configuration(tmp_path)
    actual = env["EDIP_METADATA_SHA256"]
    expected = actual[:-1] + ("0" if actual[-1] != "0" else "1")
    env["EDIP_METADATA_SHA256"] = expected

    with pytest.raises(ValueError) as error:
        stage_bundle(S3(), env)

    assert str(error.value) == (
        f"Checksum mismatch for metadata.json: expected {expected}, actual {actual}"
    )
    assert (tmp_path / "bundle" / "model.txt").read_bytes() == b"model"
    assert not (tmp_path / "bundle" / "metadata.json").exists()
