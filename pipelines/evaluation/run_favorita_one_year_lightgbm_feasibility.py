"""Resource-feasibility experiment for one bounded Favorita LightGBM fit."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from time import perf_counter
from typing import Any

try:
    import resource
except ImportError:  # pragma: no cover - unavailable on Windows
    resource = None  # type: ignore[assignment]

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
from pipelines.models.favorita_lightgbm import FavoritaLightGBMAdapter

TARGET_START = date(2016, 7, 30)
TARGET_END = date(2017, 7, 30)
EXPERIMENT_ARTIFACT_ROOT = Path(
    "artifacts/experiments/favorita_one_year_lightgbm_feasibility"
)
TRAINING_FILENAME = "training.parquet"


@dataclass(frozen=True, slots=True)
class FeasibilityConfig:
    """Fixed-scope paths for the isolated resource-feasibility experiment."""

    source_path: Path = DEFAULT_SOURCE_PATH
    artifact_root: Path = EXPERIMENT_ARTIFACT_ROOT

    @property
    def training_path(self) -> Path:
        return self.artifact_root / TRAINING_FILENAME

    @property
    def unused_manifest_path(self) -> Path:
        return self.artifact_root / "unused_feature_manifest.json"


def training_origins() -> tuple[date, ...]:
    """Return daily origins that stay inside the bounded target/holdout contract."""

    first_origin = TARGET_START - timedelta(days=min(FORECAST_HORIZONS))
    last_origin = TARGET_END - timedelta(days=max(FORECAST_HORIZONS))
    return tuple(
        first_origin + timedelta(days=offset)
        for offset in range((last_origin - first_origin).days + 1)
    )


def _validate_experiment_contract(config: FeasibilityConfig) -> None:
    origins = training_origins()
    if origins[0] + timedelta(days=min(FORECAST_HORIZONS)) != TARGET_START:
        raise AssertionError("First experimental target date is not canonical")
    if origins[-1] + timedelta(days=max(FORECAST_HORIZONS)) != TARGET_END:
        raise AssertionError("Last experimental target date is not canonical")
    if TARGET_END >= FINAL_HOLDOUT.holdout_start:
        raise AssertionError("Experimental target scope enters the final holdout")

    resolved_root = config.artifact_root.resolve()
    for protected_root in (
        CANONICAL_FOUR_FOLD_ROOT.resolve(),
        HISTORICAL_OUTPUT_DIR.resolve(),
    ):
        if resolved_root == protected_root or protected_root in resolved_root.parents:
            raise ValueError(
                "Feasibility artifacts must not use a canonical fold artifact root"
            )
    if not config.source_path.is_file():
        raise FileNotFoundError(config.source_path)


def _file_state(path: Path) -> tuple[int, int]:
    state = path.stat()
    return state.st_size, state.st_mtime_ns


def _validate_artifact_summary(summary: dict[str, Any]) -> None:
    if summary["rows"] <= 0:
        raise AssertionError("Experimental training artifact contains no rows")
    if summary["forecast_date_min"] != TARGET_START.isoformat():
        raise AssertionError("Experimental targets do not start at 2016-07-30")
    if summary["forecast_date_max"] != TARGET_END.isoformat():
        raise AssertionError("Experimental targets do not end at 2017-07-30")
    if summary["store_cardinality"] != len(ALL_FAVORITA_STORES):
        raise AssertionError("Experimental artifact must observe all 54 stores")
    if summary["horizons"] != list(FORECAST_HORIZONS):
        raise AssertionError("Experimental horizons must be exactly 1 through 16")
    if summary["parquet_size_bytes"] <= 0:
        raise AssertionError("Experimental Parquet size must be positive")


def prepare_training_artifact(
    config: FeasibilityConfig,
) -> dict[str, Any]:
    """Build once or validate and reuse the isolated experimental Parquet."""

    _validate_experiment_contract(config)
    started = perf_counter()
    if config.training_path.exists():
        print(
            f"[Feasibility] validating existing {config.training_path.as_posix()}...",
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
            progress_prefix="[Feasibility]",
            progress_phase="features",
        )
        if tuple(build_result["processed_stores"]) != ALL_FAVORITA_STORES:
            raise AssertionError("Feature materialization did not process stores 1-54")
        if _file_state(config.source_path) != source_before:
            raise AssertionError("Cleaned Favorita source changed during materialization")
        artifact_validation = build_result["artifact_validation"]
        creation_status = "created"

    summary = {
        **artifact_validation,
        "creation_status": creation_status,
        "artifact_path": config.training_path.as_posix(),
        "parquet_size_bytes": config.training_path.stat().st_size,
        "artifact_preparation_runtime_seconds": perf_counter() - started,
    }
    _validate_artifact_summary(summary)
    return summary


def _peak_process_ram_gib() -> float | None:
    if resource is None:
        return None
    peak = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    bytes_per_unit = 1 if sys.platform == "darwin" else 1024
    return peak * bytes_per_unit / (1024**3)


def _print_peak_ram() -> None:
    peak_ram = _peak_process_ram_gib()
    if peak_ram is None:
        print("[Feasibility] peak process RAM: not observable", flush=True)
    else:
        print(f"[Feasibility] peak process RAM: {peak_ram:.2f} GiB", flush=True)


def run_feasibility(config: FeasibilityConfig = FeasibilityConfig()) -> dict[str, Any]:
    """Prepare the bounded Parquet and attempt the existing LightGBM fit."""

    summary = prepare_training_artifact(config)
    size_gib = summary["parquet_size_bytes"] / (1024**3)
    print(f"[Feasibility] training rows: {summary['rows']}", flush=True)
    print(
        "[Feasibility] target dates: "
        f"{summary['forecast_date_min']} -> {summary['forecast_date_max']}",
        flush=True,
    )
    print(
        f"[Feasibility] observed stores: {summary['store_cardinality']} of 54",
        flush=True,
    )
    print(
        f"[Feasibility] Parquet size: {summary['parquet_size_bytes']} bytes "
        f"({size_gib:.2f} GiB)",
        flush=True,
    )
    print(
        f"[Feasibility] artifact: {summary['artifact_path']}",
        flush=True,
    )
    print("[Feasibility] starting existing LightGBM Parquet fit...", flush=True)

    training_started = perf_counter()
    model = FavoritaLightGBMAdapter()
    try:
        model.fit_parquet(config.training_path)
    except (Exception, KeyboardInterrupt) as error:
        runtime_seconds = perf_counter() - training_started
        print("[Feasibility] training status: FAILED", flush=True)
        print(
            f"[Feasibility] failure: {type(error).__name__}: {error}",
            flush=True,
        )
        print(
            f"[Feasibility] training runtime: {runtime_seconds:.2f} seconds",
            flush=True,
        )
        _print_peak_ram()
        raise

    runtime_seconds = perf_counter() - training_started
    print("[Feasibility] training status: SUCCEEDED", flush=True)
    print(
        f"[Feasibility] training runtime: {runtime_seconds:.2f} seconds",
        flush=True,
    )
    _print_peak_ram()
    return {
        **summary,
        "training_status": "succeeded",
        "training_runtime_seconds": runtime_seconds,
        "peak_process_ram_gib": _peak_process_ram_gib(),
    }


def main() -> int:
    run_feasibility()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
