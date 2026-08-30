"""Build and size one isolated six-month Favorita model-ready Parquet."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from time import perf_counter
from typing import Any

from pipelines.evaluation.favorita_temporal_validation import (
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
)
from pipelines.features.build_favorita_fold_datasets import (
    ALL_FAVORITA_STORES,
    ALL_STORE_BATCHES,
    DEFAULT_SOURCE_PATH,
    HISTORICAL_OUTPUT_DIR,
)
from pipelines.features.build_favorita_fold_datasets import (
    DEFAULT_OUTPUT_DIR as CANONICAL_FOUR_FOLD_ROOT,
)
from pipelines.features.favorita_model_ready import (
    FeatureBuildConfig,
    materialize_feature_dataset,
    validate_feature_artifact,
)

TARGET_START = date(2017, 1, 1)
TARGET_END = date(2017, 6, 30)
EXPERIMENT_ARTIFACT_ROOT = Path(
    "artifacts/experiments/favorita_six_month_lightgbm_feasibility"
)
PREVIOUS_ONE_YEAR_ARTIFACT_ROOT = Path(
    "artifacts/experiments/favorita_one_year_lightgbm_feasibility"
)
TRAINING_FILENAME = "training.parquet"
SIZE_THRESHOLD_BYTES = 3 * 1024**3


@dataclass(frozen=True, slots=True)
class FeasibilityConfig:
    """Fixed paths for the isolated six-month Parquet-size experiment."""

    source_path: Path = DEFAULT_SOURCE_PATH
    artifact_root: Path = EXPERIMENT_ARTIFACT_ROOT

    @property
    def training_path(self) -> Path:
        return self.artifact_root / TRAINING_FILENAME

    @property
    def unused_manifest_path(self) -> Path:
        return self.artifact_root / "unused_feature_manifest.json"


def training_origins() -> tuple[date, ...]:
    """Return daily origins whose source slices remain inside the target end."""

    first_origin = TARGET_START - timedelta(days=min(FORECAST_HORIZONS))
    last_origin = TARGET_END - timedelta(days=max(FORECAST_HORIZONS))
    return tuple(
        first_origin + timedelta(days=offset)
        for offset in range((last_origin - first_origin).days + 1)
    )


def _validate_experiment_contract(config: FeasibilityConfig) -> None:
    origins = training_origins()
    if origins[0] + timedelta(days=min(FORECAST_HORIZONS)) != TARGET_START:
        raise AssertionError("First experimental target date is not 2017-01-01")
    if origins[-1] + timedelta(days=max(FORECAST_HORIZONS)) != TARGET_END:
        raise AssertionError("Last experimental target date is not 2017-06-30")
    if TARGET_END >= FINAL_HOLDOUT.holdout_start:
        raise AssertionError("Experimental target scope enters the final holdout")

    resolved_root = config.artifact_root.resolve()
    protected_roots = (
        CANONICAL_FOUR_FOLD_ROOT.resolve(),
        HISTORICAL_OUTPUT_DIR.resolve(),
        PREVIOUS_ONE_YEAR_ARTIFACT_ROOT.resolve(),
    )
    if any(
        resolved_root == root or root in resolved_root.parents
        for root in protected_roots
    ):
        raise ValueError(
            "Six-month feasibility artifacts require their dedicated artifact root"
        )
    if not config.source_path.is_file():
        raise FileNotFoundError(config.source_path)


def _file_state(path: Path) -> tuple[int, int]:
    state = path.stat()
    return state.st_size, state.st_mtime_ns


def _validate_artifact_summary(summary: dict[str, Any]) -> None:
    if summary["rows"] <= 0:
        raise AssertionError("Six-month training artifact contains no rows")
    if summary["forecast_date_min"] != TARGET_START.isoformat():
        raise AssertionError("Six-month targets do not start at 2017-01-01")
    if summary["forecast_date_max"] != TARGET_END.isoformat():
        raise AssertionError("Six-month targets do not end at 2017-06-30")
    if summary["store_cardinality"] != len(ALL_FAVORITA_STORES):
        raise AssertionError("Six-month artifact must observe all 54 stores")
    if summary["horizons"] != list(FORECAST_HORIZONS):
        raise AssertionError("Six-month horizons must be exactly 1 through 16")
    if summary["parquet_size_bytes"] <= 0:
        raise AssertionError("Six-month Parquet size must be positive")


def prepare_training_artifact(
    config: FeasibilityConfig,
) -> dict[str, Any]:
    """Build once or validate and reuse only the six-month Parquet."""

    _validate_experiment_contract(config)
    started = perf_counter()
    if config.training_path.exists():
        print(
            f"[Six-month feasibility] validating existing "
            f"{config.training_path.as_posix()}...",
            flush=True,
        )
        artifact_validation = validate_feature_artifact(
            config.training_path,
            bounded_memory=True,
        )
        creation_status = "reused"
    else:
        source_before = _file_state(config.source_path)
        build_config = FeatureBuildConfig(
            source_path=config.source_path,
            output_path=config.training_path,
            manifest_path=config.unused_manifest_path,
            forecast_origins=training_origins(),
            store_batches=ALL_STORE_BATCHES,
            max_items_per_store=None,
            allow_assumed_future_promotion=False,
            allow_assumed_future_holidays=False,
            overwrite=False,
        )
        build_result = materialize_feature_dataset(
            build_config,
            forecast_date_cutoff=TARGET_END,
            drop_targets_without_origin_history=True,
            bounded_memory_validation=True,
            reuse_source_across_origins=True,
            progress_prefix="[Six-month feasibility]",
            progress_phase="features",
        )
        if tuple(build_result["processed_stores"]) != ALL_FAVORITA_STORES:
            raise AssertionError("Feature materialization did not process stores 1-54")
        if _file_state(config.source_path) != source_before:
            raise AssertionError("Cleaned Favorita source changed during materialization")
        artifact_validation = build_result["artifact_validation"]
        creation_status = "created"

    parquet_size_bytes = config.training_path.stat().st_size
    summary = {
        **artifact_validation,
        "creation_status": creation_status,
        "artifact_path": config.training_path.as_posix(),
        "parquet_size_bytes": parquet_size_bytes,
        "parquet_size_gib": parquet_size_bytes / (1024**3),
        "within_training_size_threshold": (
            parquet_size_bytes <= SIZE_THRESHOLD_BYTES
        ),
        "artifact_preparation_runtime_seconds": perf_counter() - started,
    }
    _validate_artifact_summary(summary)
    return summary


def run_feasibility(config: FeasibilityConfig = FeasibilityConfig()) -> dict[str, Any]:
    """Materialize, validate, and report size without starting LightGBM."""

    summary = prepare_training_artifact(config)
    print(f"[Six-month feasibility] training rows: {summary['rows']}", flush=True)
    print(
        "[Six-month feasibility] target dates: "
        f"{summary['forecast_date_min']} -> {summary['forecast_date_max']}",
        flush=True,
    )
    print(
        f"[Six-month feasibility] observed stores: "
        f"{summary['store_cardinality']} of 54",
        flush=True,
    )
    print(
        f"[Six-month feasibility] Parquet size: "
        f"{summary['parquet_size_bytes']} bytes "
        f"({summary['parquet_size_gib']:.2f} GiB)",
        flush=True,
    )
    print(
        f"[Six-month feasibility] artifact: {summary['artifact_path']}",
        flush=True,
    )
    if summary["within_training_size_threshold"]:
        print(
            "[Six-month feasibility] size threshold: ACCEPTABLE CANDIDATE "
            "(<= 3 GiB)",
            flush=True,
        )
    else:
        print(
            "[Six-month feasibility] size threshold: EXCEEDS 3 GiB; "
            "do not train",
            flush=True,
        )
    print(
        "[Six-month feasibility] LightGBM training: NOT STARTED",
        flush=True,
    )
    return summary


def main() -> int:
    run_feasibility()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
