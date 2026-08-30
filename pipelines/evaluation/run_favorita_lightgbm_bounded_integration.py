"""Bounded real-data SCRUM-15 infrastructure integration runner."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

import numpy as np

from pipelines.evaluation.favorita_metrics import FavoritaMetricAccumulator
from pipelines.evaluation.favorita_temporal_validation import (
    FINAL_HOLDOUT,
    FORECAST_HORIZONS,
    TemporalValidationFold,
    derive_target_window,
)
from pipelines.evaluation.run_favorita_lightgbm_evaluation import (
    DEFAULT_FOLD_OUTPUT_DIR,
    _StreamingPredictionWriter,
    _validate_validation_batch,
    _ValidationKeyTracker,
    iter_model_ready_validation_batches,
)
from pipelines.evaluation.run_favorita_lightgbm_evaluation import (
    DEFAULT_OUTPUT_DIR as OFFICIAL_EVALUATION_OUTPUT_DIR,
)
from pipelines.features.favorita_model_ready import (
    FeatureBuildConfig,
    materialize_feature_dataset,
    write_json_atomic,
)
from pipelines.models.favorita_lightgbm import (
    LIGHTGBM_PARAMETERS,
    NUM_BOOST_ROUND,
    FavoritaLightGBMAdapter,
)

DEFAULT_SOURCE_PATH = Path(
    "data/processed/favorita_cleaned/favorita_cleaned.parquet"
)
SMALL_OUTPUT_DIR = Path("artifacts/integration/favorita_scrum15_bounded")
MEDIUM_OUTPUT_DIR = Path("artifacts/integration/favorita_scrum15_medium")
LARGE_OUTPUT_DIR = Path("artifacts/integration/favorita_scrum15_large")
DEFAULT_OUTPUT_DIR = SMALL_OUTPUT_DIR
SMALL_STORES: tuple[int, ...] = (1, 2)
SMALL_ITEM_CAP = 50
SMALL_TRAINING_ORIGINS: tuple[date, ...] = (
    date(2017, 5, 15),
    date(2017, 5, 31),
    date(2017, 6, 14),
)
MEDIUM_STORES: tuple[int, ...] = (1, 2, 3, 4, 5)
MEDIUM_ITEM_CAP = 200
MEDIUM_TRAINING_ORIGINS: tuple[date, ...] = (
    date(2017, 1, 15),
    date(2017, 1, 31),
    date(2017, 2, 14),
    date(2017, 2, 28),
    date(2017, 3, 15),
    date(2017, 3, 31),
    date(2017, 4, 14),
    date(2017, 4, 30),
    date(2017, 5, 15),
    date(2017, 5, 31),
    date(2017, 6, 7),
    date(2017, 6, 14),
)
LARGE_STORES: tuple[int, ...] = tuple(range(1, 11))
LARGE_ITEM_CAP = 500
LARGE_TRAINING_ORIGINS: tuple[date, ...] = (
    date(2017, 1, 2),
    date(2017, 1, 9),
    date(2017, 1, 16),
    date(2017, 1, 23),
    date(2017, 1, 30),
    date(2017, 2, 6),
    date(2017, 2, 13),
    date(2017, 2, 20),
    date(2017, 2, 27),
    date(2017, 3, 6),
    date(2017, 3, 13),
    date(2017, 3, 20),
    date(2017, 3, 27),
    date(2017, 4, 3),
    date(2017, 4, 10),
    date(2017, 4, 17),
    date(2017, 4, 24),
    date(2017, 5, 1),
    date(2017, 5, 8),
    date(2017, 5, 15),
    date(2017, 5, 22),
    date(2017, 5, 29),
    date(2017, 6, 5),
    date(2017, 6, 14),
)
BOUNDED_VALIDATION_ORIGIN = date(2017, 6, 30)
BOUNDED_VALIDATION_BATCH_SIZE = 128
BOUNDED_STORES = SMALL_STORES
BOUNDED_ITEM_CAP = SMALL_ITEM_CAP
BOUNDED_TRAINING_ORIGINS = SMALL_TRAINING_ORIGINS


@dataclass(frozen=True, slots=True)
class BoundedIntegrationProfile:
    name: str
    output_dir: Path
    stores: tuple[int, ...]
    item_cap: int
    training_origins: tuple[date, ...]
    validation_origin: date = BOUNDED_VALIDATION_ORIGIN


INTEGRATION_PROFILES: dict[str, BoundedIntegrationProfile] = {
    "small": BoundedIntegrationProfile(
        name="small",
        output_dir=SMALL_OUTPUT_DIR,
        stores=SMALL_STORES,
        item_cap=SMALL_ITEM_CAP,
        training_origins=SMALL_TRAINING_ORIGINS,
    ),
    "medium": BoundedIntegrationProfile(
        name="medium",
        output_dir=MEDIUM_OUTPUT_DIR,
        stores=MEDIUM_STORES,
        item_cap=MEDIUM_ITEM_CAP,
        training_origins=MEDIUM_TRAINING_ORIGINS,
    ),
    "large": BoundedIntegrationProfile(
        name="large",
        output_dir=LARGE_OUTPUT_DIR,
        stores=LARGE_STORES,
        item_cap=LARGE_ITEM_CAP,
        training_origins=LARGE_TRAINING_ORIGINS,
    ),
}
PROFILE_NAMES: tuple[str, ...] = tuple(INTEGRATION_PROFILES)


@dataclass(frozen=True, slots=True)
class BoundedIntegrationConfig:
    profile: str = "small"
    source_path: Path = DEFAULT_SOURCE_PATH
    output_dir: Path = DEFAULT_OUTPUT_DIR
    stores: tuple[int, ...] = SMALL_STORES
    item_cap: int = SMALL_ITEM_CAP
    training_origins: tuple[date, ...] = SMALL_TRAINING_ORIGINS
    validation_origin: date = BOUNDED_VALIDATION_ORIGIN
    validation_batch_size: int = BOUNDED_VALIDATION_BATCH_SIZE
    overwrite: bool = False


def integration_config_for_profile(
    profile: str,
    *,
    source_path: Path = DEFAULT_SOURCE_PATH,
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> BoundedIntegrationConfig:
    try:
        definition = INTEGRATION_PROFILES[profile]
    except KeyError as exc:
        raise ValueError(
            f"profile must be one of {', '.join(PROFILE_NAMES)}"
        ) from exc
    return BoundedIntegrationConfig(
        profile=definition.name,
        source_path=source_path,
        output_dir=(
            output_dir if output_dir is not None else definition.output_dir
        ),
        stores=definition.stores,
        item_cap=definition.item_cap,
        training_origins=definition.training_origins,
        validation_origin=definition.validation_origin,
        overwrite=overwrite,
    )


@dataclass(frozen=True, slots=True)
class BoundedIntegrationArtifactPaths:
    training: Path
    validation: Path
    predictions: Path
    manifest: Path


def _artifact_paths(output_dir: Path) -> BoundedIntegrationArtifactPaths:
    return BoundedIntegrationArtifactPaths(
        training=output_dir / "training.parquet",
        validation=output_dir / "validation.parquet",
        predictions=output_dir / "predictions.parquet",
        manifest=output_dir / "bounded_integration_manifest.json",
    )


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def validate_integration_config(config: BoundedIntegrationConfig) -> None:
    if not config.source_path.is_file():
        raise FileNotFoundError(config.source_path)
    if config.profile not in INTEGRATION_PROFILES:
        raise ValueError(f"profile must be one of {', '.join(PROFILE_NAMES)}")
    if len(set(config.stores)) != len(config.stores):
        raise ValueError("Bounded integration stores must be unique")
    if any(store not in range(1, 55) for store in config.stores):
        raise ValueError("Bounded integration stores must be within 1 through 54")
    if config.item_cap <= 0:
        raise ValueError("Bounded integration item_cap must be positive")
    if not config.training_origins:
        raise ValueError("Bounded integration requires explicit training origins")
    if tuple(sorted(set(config.training_origins))) != config.training_origins:
        raise ValueError("Training origins must be unique and sorted")
    if config.training_origins[-1] + timedelta(
        days=max(FORECAST_HORIZONS)
    ) > config.validation_origin:
        raise ValueError(
            "Every bounded training label must be available by validation origin"
        )
    validation_start, validation_end = derive_target_window(
        config.validation_origin
    )
    if (
        config.validation_origin == FINAL_HOLDOUT.forecast_origin
        or validation_start >= FINAL_HOLDOUT.holdout_start
        or validation_end >= FINAL_HOLDOUT.holdout_start
    ):
        raise ValueError("Bounded integration must not score the final holdout")
    definition = INTEGRATION_PROFILES[config.profile]
    if (
        config.stores != definition.stores
        or config.item_cap != definition.item_cap
        or config.training_origins != definition.training_origins
        or config.validation_origin != definition.validation_origin
    ):
        raise ValueError(
            "Bounded integration values must match the selected profile"
        )
    if config.validation_batch_size <= 0:
        raise ValueError("validation_batch_size must be positive")
    for official_path in (
        OFFICIAL_EVALUATION_OUTPUT_DIR,
        DEFAULT_FOLD_OUTPUT_DIR,
    ):
        if _is_within(config.output_dir, official_path):
            raise ValueError(
                "Bounded integration output must be separate from official artifacts"
            )
    other_profile_paths = (
        definition.output_dir
        for name, definition in INTEGRATION_PROFILES.items()
        if name != config.profile
    )
    if any(_is_within(config.output_dir, path) for path in other_profile_paths):
        raise ValueError(
            "Bounded integration output must be separate from other profiles"
        )
    if config.source_path.resolve() == config.output_dir.resolve():
        raise ValueError("Source and integration output paths must be distinct")


def _source_state(path: Path) -> dict[str, int]:
    stat = path.stat()
    return {"size_bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def _require_source_unchanged(
    path: Path,
    expected_state: dict[str, int],
) -> dict[str, int]:
    current_state = _source_state(path)
    if current_state != expected_state:
        raise AssertionError("Cleaned source changed during bounded integration")
    return current_state


def _peak_process_rss() -> dict[str, Any]:
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        get_current_process = kernel32.GetCurrentProcess
        get_current_process.restype = wintypes.HANDLE
        get_process_memory_info = psapi.GetProcessMemoryInfo
        get_process_memory_info.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(ProcessMemoryCounters),
            wintypes.DWORD,
        ]
        get_process_memory_info.restype = wintypes.BOOL
        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        if not get_process_memory_info(
            get_current_process(),
            ctypes.byref(counters),
            counters.cb,
        ):
            return {"measured": False, "reason": "GetProcessMemoryInfo failed"}
        return {
            "measured": True,
            "peak_rss_bytes": int(counters.PeakWorkingSetSize),
            "method": "Windows GetProcessMemoryInfo PeakWorkingSetSize",
        }

    try:
        import resource
    except ImportError:
        return {"measured": False, "reason": "resource module unavailable"}
    maximum_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    multiplier = 1 if sys.platform == "darwin" else 1024
    return {
        "measured": True,
        "peak_rss_bytes": int(maximum_rss * multiplier),
        "method": "resource.getrusage(RUSAGE_SELF).ru_maxrss",
    }


def _publish_stage(stage_dir: Path, output_dir: Path, *, overwrite: bool) -> None:
    backup_dir = output_dir.with_name(f".{output_dir.name}.backup")
    if output_dir.exists() and not overwrite:
        raise FileExistsError(output_dir)
    try:
        if output_dir.exists():
            if backup_dir.exists():
                raise FileExistsError(backup_dir)
            os.replace(output_dir, backup_dir)
        os.replace(stage_dir, output_dir)
    except Exception:
        if not output_dir.exists() and backup_dir.exists():
            os.replace(backup_dir, output_dir)
        raise
    else:
        shutil.rmtree(backup_dir, ignore_errors=True)


def run_bounded_integration(
    config: BoundedIntegrationConfig,
) -> BoundedIntegrationArtifactPaths:
    validate_integration_config(config)
    if config.output_dir.exists() and not config.overwrite:
        raise FileExistsError(config.output_dir)
    config.output_dir.parent.mkdir(parents=True, exist_ok=True)
    source_before = _source_state(config.source_path)
    total_started = perf_counter()
    stage_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{config.output_dir.name}.",
            dir=config.output_dir.parent,
        )
    )
    stage_paths = _artifact_paths(stage_dir)
    validation_start, validation_end = derive_target_window(
        config.validation_origin
    )
    fold = TemporalValidationFold(
        fold_id=0,
        forecast_origin=config.validation_origin,
        validation_start=validation_start,
        validation_end=validation_end,
    )
    store_batches = tuple((store,) for store in config.stores)
    try:
        feature_started = perf_counter()
        training_result = materialize_feature_dataset(
            FeatureBuildConfig(
                source_path=config.source_path,
                output_path=stage_paths.training,
                manifest_path=stage_dir / "training_feature_manifest.json",
                forecast_origins=config.training_origins,
                store_batches=store_batches,
                max_items_per_store=config.item_cap,
            ),
            forecast_date_cutoff=config.validation_origin,
            drop_targets_without_origin_history=True,
            bounded_memory_validation=True,
        )
        validation_result = materialize_feature_dataset(
            FeatureBuildConfig(
                source_path=config.source_path,
                output_path=stage_paths.validation,
                manifest_path=stage_dir / "validation_feature_manifest.json",
                forecast_origins=(config.validation_origin,),
                store_batches=store_batches,
                max_items_per_store=config.item_cap,
            ),
            drop_targets_without_origin_history=True,
            bounded_memory_validation=True,
        )
        feature_duration = perf_counter() - feature_started

        model = FavoritaLightGBMAdapter()
        fit_started = perf_counter()
        model.fit_parquet(stage_paths.training)
        fit_duration = perf_counter() - fit_started

        accumulator = FavoritaMetricAccumulator()
        key_tracker = _ValidationKeyTracker()
        prediction_writer = _StreamingPredictionWriter(stage_paths.predictions)
        validation_batches = 0
        prediction_started = perf_counter()
        try:
            for frame in iter_model_ready_validation_batches(
                stage_paths.validation,
                batch_size=config.validation_batch_size,
            ):
                _validate_validation_batch(fold, frame, key_tracker)
                predictions = np.asarray(
                    model.predict_frame(frame),
                    dtype="float64",
                )
                if predictions.ndim != 1 or len(predictions) != len(frame):
                    raise ValueError(
                        "Prediction row count must match bounded validation rows"
                    )
                if not np.isfinite(predictions).all():
                    raise ValueError("Predictions must contain only finite values")
                accumulator.update(
                    frame["unit_sales"].to_numpy(dtype="float64", copy=False),
                    predictions,
                    frame["perishable"].to_numpy(copy=False),
                )
                prediction_writer.write(fold, frame, predictions)
                validation_batches += 1
                del frame, predictions
            prediction_writer.close()
        except Exception:
            prediction_writer.abort()
            raise
        prediction_duration = perf_counter() - prediction_started
        del model

        training_rows = int(training_result["artifact_validation"]["rows"])
        validation_rows = int(validation_result["artifact_validation"]["rows"])
        if validation_result["artifact_validation"]["horizons"] != list(
            FORECAST_HORIZONS
        ):
            raise AssertionError(
                "Bounded validation must cover exact horizons 1 through 16"
            )
        if validation_batches < 2:
            raise AssertionError(
                "Bounded validation must exercise multiple Parquet batches"
            )
        if accumulator.count != validation_rows:
            raise AssertionError(
                "Streamed prediction count differs from validation artifact rows"
            )
        if prediction_writer.rows_written != validation_rows:
            raise AssertionError(
                "Prediction Parquet rows differ from validation artifact rows"
            )
        source_after = _require_source_unchanged(
            config.source_path,
            source_before,
        )
        total_duration = perf_counter() - total_started
        manifest: dict[str, Any] = {
            "scope": "bounded_real_data_integration_only",
            "profile": config.profile,
            "source": {
                "path": config.source_path.as_posix(),
                "before": source_before,
                "after": source_after,
            },
            "configuration": {
                "profile": config.profile,
                "stores": list(config.stores),
                "item_cap_per_store": config.item_cap,
                "training_origins": [
                    origin.isoformat() for origin in config.training_origins
                ],
                "validation_origin": config.validation_origin.isoformat(),
                "validation_start": validation_start.isoformat(),
                "validation_end": validation_end.isoformat(),
                "horizons": list(FORECAST_HORIZONS),
                "validation_batch_size": config.validation_batch_size,
            },
            "rows": {
                "training": training_rows,
                "validation": validation_rows,
                "predictions": prediction_writer.rows_written,
                "validation_batches": validation_batches,
            },
            "artifact_sizes_bytes": {
                "training_parquet": stage_paths.training.stat().st_size,
                "validation_parquet": stage_paths.validation.stat().st_size,
                "prediction_parquet": stage_paths.predictions.stat().st_size,
            },
            "timings_seconds": {
                "feature_materialization": feature_duration,
                "lightgbm_fit": fit_duration,
                "validation_prediction_and_evidence": prediction_duration,
                "total_before_manifest_write": total_duration,
            },
            "resources": {
                "peak_process_rss": _peak_process_rss(),
                "temporary_label_memmap_bytes_expected": training_rows * 8,
            },
            "model": {
                "name": "FavoritaLightGBMAdapter",
                "parameters": dict(LIGHTGBM_PARAMETERS),
                "num_boost_round": NUM_BOOST_ROUND,
            },
            "metrics": asdict(accumulator.finalize()),
            "source_not_mutated": True,
            "final_holdout_scored": False,
            "official_backtest": False,
            "limitations": [
                "Infrastructure evidence only; not model selection evidence.",
                (
                    f"{len(config.stores)} stores and at most "
                    f"{config.item_cap} items per store."
                ),
                "Full-data peak RAM and runtime remain unmeasured.",
            ],
        }
        write_json_atomic(manifest, stage_paths.manifest, overwrite=False)
        _require_source_unchanged(config.source_path, source_before)
        _publish_stage(stage_dir, config.output_dir, overwrite=config.overwrite)
    except Exception:
        shutil.rmtree(stage_dir, ignore_errors=True)
        raise
    return _artifact_paths(config.output_dir)


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the isolated bounded real-data SCRUM-15 integration."
    )
    parser.add_argument(
        "--profile",
        choices=PROFILE_NAMES,
        default="small",
    )
    parser.add_argument("--source-path", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    paths = run_bounded_integration(
        integration_config_for_profile(
            args.profile,
            source_path=args.source_path,
            output_dir=args.output_dir,
            overwrite=args.overwrite,
        )
    )
    print(json.dumps({"manifest": paths.manifest.as_posix()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
