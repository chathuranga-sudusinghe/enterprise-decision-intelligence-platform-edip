# pipelines/airflow_dags/edip_orchestration_demo_dag.py

from __future__ import annotations

import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator


# =========================================================
# Logging
# =========================================================
logger = logging.getLogger(__name__)


# =========================================================
# Paths
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]

SCORE_SCRIPT_PATH = PROJECT_ROOT / "pipelines" / "inference" / "score_demand_forecast.py"
RECOMMEND_SCRIPT_PATH = PROJECT_ROOT / "pipelines" / "inference" / "generate_recommendations.py"

FORECAST_ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "forecasts"

EXPECTED_OUTPUT_FILES = [
    FORECAST_ARTIFACTS_DIR / "demand_forecast_scored.csv",
    FORECAST_ARTIFACTS_DIR / "demand_forecast_scoring_summary.json",
    FORECAST_ARTIFACTS_DIR / "replenishment_recommendations.csv",
    FORECAST_ARTIFACTS_DIR / "replenishment_recommendation_summary.json",
]


# =========================================================
# Task helpers
# =========================================================
def validate_project_setup() -> None:
    """
    Validate that the required project scripts exist before the DAG runs.
    Also ensure the forecast artifacts directory exists.
    """
    required_script_paths = [
        SCORE_SCRIPT_PATH,
        RECOMMEND_SCRIPT_PATH,
    ]

    missing_paths = [str(path) for path in required_script_paths if not path.exists()]
    if missing_paths:
        raise FileNotFoundError(
            "EDIP orchestration setup validation failed. Missing paths: "
            + ", ".join(missing_paths)
        )

    FORECAST_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Project setup validation passed.")
    logger.info("Project root: %s", PROJECT_ROOT)
    logger.info("Forecast artifacts directory: %s", FORECAST_ARTIFACTS_DIR)


def run_python_script(script_path: Path, task_label: str) -> None:
    """
    Execute a project Python script using the current Python interpreter.
    This keeps the DAG aligned with the Airflow container environment.
    """
    if not script_path.exists():
        raise FileNotFoundError(f"{task_label} script not found: {script_path}")

    command = [sys.executable, str(script_path)]

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{PROJECT_ROOT}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else str(PROJECT_ROOT)
    )

    logger.info("Starting task: %s", task_label)
    logger.info("Running command: %s", " ".join(command))
    logger.info("Working directory: %s", PROJECT_ROOT)

    result = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.stdout:
        logger.info("[%s stdout]\n%s", task_label, result.stdout)

    if result.stderr:
        logger.warning("[%s stderr]\n%s", task_label, result.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"{task_label} failed with exit code {result.returncode}. "
            f"Script: {script_path.name}"
        )

    logger.info("Task completed successfully: %s", task_label)


def run_forecast_scoring() -> None:
    """Run the demand forecast scoring pipeline."""
    run_python_script(
        script_path=SCORE_SCRIPT_PATH,
        task_label="forecast_scoring",
    )


def run_recommendation_generation() -> None:
    """Run the replenishment recommendation generation pipeline."""
    run_python_script(
        script_path=RECOMMEND_SCRIPT_PATH,
        task_label="recommendation_generation",
    )


def validate_output_artifacts() -> None:
    """
    Confirm that the expected forecast and recommendation artifacts exist
    after the orchestration run.
    """
    missing_files = [str(path) for path in EXPECTED_OUTPUT_FILES if not path.exists()]
    if missing_files:
        raise FileNotFoundError(
            "EDIP orchestration artifact validation failed. Missing files: "
            + ", ".join(missing_files)
        )

    logger.info("Output artifact validation passed.")
    for output_file in EXPECTED_OUTPUT_FILES:
        logger.info("Validated artifact: %s", output_file)


# =========================================================
# DAG definition
# =========================================================
default_args = {
    "owner": "edip",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="edip_orchestration_demo_dag",
    description="EDIP demo DAG for forecast scoring and replenishment recommendation generation.",
    default_args=default_args,
    start_date=datetime(2026, 3, 1),
    schedule=None,  # Manual trigger for initial validation
    catchup=False,
    tags=["edip", "forecast", "recommendation", "orchestration-demo"],
) as dag:
    start_task = EmptyOperator(
        task_id="start",
    )

    validate_setup_task = PythonOperator(
        task_id="validate_project_setup",
        python_callable=validate_project_setup,
    )

    score_forecast_task = PythonOperator(
        task_id="run_forecast_scoring",
        python_callable=run_forecast_scoring,
    )

    generate_recommendations_task = PythonOperator(
        task_id="run_recommendation_generation",
        python_callable=run_recommendation_generation,
    )

    validate_outputs_task = PythonOperator(
        task_id="validate_output_artifacts",
        python_callable=validate_output_artifacts,
    )

    end_task = EmptyOperator(
        task_id="end",
    )

    (
        start_task
        >> validate_setup_task
        >> score_forecast_task
        >> generate_recommendations_task
        >> validate_outputs_task
        >> end_task
    )