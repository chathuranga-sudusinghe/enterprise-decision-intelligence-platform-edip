from __future__ import annotations

import pytest

from app.core.config import Settings


@pytest.fixture(autouse=True)
def _clear_settings_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "APP_NAME",
        "APP_VERSION",
        "APP_ENV",
        "API_HOST",
        "API_PORT",
        "ALLOW_CREDENTIALS",
        "ALLOWED_ORIGINS",
    ):
        monkeypatch.delenv(name, raising=False)


def test_environment_values_override_local_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "Deployed EDIP")
    monkeypatch.setenv("API_PORT", "9000")

    configured = Settings()

    assert configured.app_name == "Deployed EDIP"
    assert configured.api_port == 9000


@pytest.mark.parametrize(
    ("name", "value", "message"),
    (
        ("API_PORT", "not-a-port", "API_PORT must be an integer"),
        ("ALLOW_CREDENTIALS", "sometimes", "ALLOW_CREDENTIALS must be a boolean"),
    ),
)
def test_invalid_supplied_values_fail_instead_of_falling_back(
    name: str,
    value: str,
    message: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match=message):
        Settings()


def test_production_requires_explicit_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")

    with pytest.raises(ValueError, match="ALLOWED_ORIGINS is required"):
        Settings()


def test_production_rejects_loopback_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://127.0.0.1:3000")

    with pytest.raises(ValueError, match="loopback"):
        Settings()


def test_valid_production_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://edip.example.com")

    configured = Settings()

    assert configured.allowed_origins == ("https://edip.example.com",)
