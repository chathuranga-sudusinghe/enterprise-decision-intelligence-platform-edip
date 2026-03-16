from __future__ import annotations

import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


# =========================================================
# Logging
# =========================================================
logger = logging.getLogger("build_rag_metadata")


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


# =========================================================
# Constants
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "rag_ingestion_config.yaml"
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "configs" / "rag_metadata_schema.yaml"

FRONTMATTER_PATTERN = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n?",
    flags=re.DOTALL,
)

SUPPORTED_SIMPLE_TYPES = {"string", "integer", "date"}
LIST_TYPE_PREFIX = "list["


# =========================================================
# Dataclasses
# =========================================================
@dataclass
class DocumentParseResult:
    source_path: Path
    frontmatter: dict[str, Any]
    body: str


# =========================================================
# Generic helpers
# =========================================================
def load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML content in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML object/dict in {path}, but got {type(data).__name__}")

    return data


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def as_list_of_strings(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"Field '{field_name}' must be a list of strings.")
    cleaned: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"Field '{field_name}' must contain only strings.")
        item_clean = item.strip()
        if not item_clean:
            raise ValueError(f"Field '{field_name}' cannot contain empty strings.")
        cleaned.append(item_clean)
    return cleaned


def as_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Field '{field_name}' must be a string.")
    value = value.strip()
    if not value:
        raise ValueError(f"Field '{field_name}' cannot be empty.")
    return value


def as_integer(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"Field '{field_name}' must be an integer, not boolean.")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    raise ValueError(f"Field '{field_name}' must be an integer.")


def as_date_string(value: Any, field_name: str) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()

    value = as_string(str(value), field_name)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"Field '{field_name}' must be in YYYY-MM-DD format.")
    return value


def validate_type(value: Any, field_name: str, declared_type: str) -> Any:
    if declared_type == "string":
        return as_string(value, field_name)
    if declared_type == "integer":
        return as_integer(value, field_name)
    if declared_type == "date":
        return as_date_string(value, field_name)
    if declared_type.startswith(LIST_TYPE_PREFIX):
        inner = declared_type[len(LIST_TYPE_PREFIX):-1]
        if inner != "string":
            raise ValueError(f"Unsupported list type for field '{field_name}': {declared_type}")
        return as_list_of_strings(value, field_name)

    raise ValueError(f"Unsupported declared type for field '{field_name}': {declared_type}")


def find_markdown_files(source_dirs: list[str], project_root: Path, pattern: str) -> list[Path]:
    files: list[Path] = []

    for source_dir in source_dirs:
        resolved_dir = project_root / source_dir
        if not resolved_dir.exists():
            logger.warning("Source directory does not exist: %s", resolved_dir)
            continue

        files.extend(sorted(resolved_dir.rglob(pattern)))

    return sorted(set(files))


def parse_markdown_with_frontmatter(path: Path) -> DocumentParseResult:
    raw_text = path.read_text(encoding="utf-8")
    normalized = normalize_whitespace(raw_text)

    match = FRONTMATTER_PATTERN.match(normalized)
    if not match:
        raise ValueError(
            f"Missing valid YAML frontmatter in document: {path}. "
            "Frontmatter must start with '---' and end with '---'."
        )

    frontmatter_text = match.group(1)
    body = normalized[match.end():].strip()

    if not body:
        raise ValueError(f"Document body is empty after frontmatter: {path}")

    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML frontmatter in {path}: {exc}") from exc

    if not isinstance(frontmatter, dict):
        raise ValueError(f"Frontmatter must be a YAML object/dict in {path}")

    return DocumentParseResult(
        source_path=path,
        frontmatter=frontmatter,
        body=body,
    )


# =========================================================
# Config and schema
# =========================================================
def load_ingestion_config(config_path: Path) -> dict[str, Any]:
    config = load_yaml_file(config_path)

    if "paths" not in config or not isinstance(config["paths"], dict):
        raise ValueError("Ingestion config must contain a 'paths' object.")

    if "metadata_extraction" not in config or not isinstance(config["metadata_extraction"], dict):
        raise ValueError("Ingestion config must contain a 'metadata_extraction' object.")

    return config


def load_metadata_schema(schema_path: Path) -> dict[str, Any]:
    schema = load_yaml_file(schema_path)

    if "document_level_metadata" not in schema:
        raise ValueError("Metadata schema must contain 'document_level_metadata'.")

    doc_meta = schema["document_level_metadata"]
    if not isinstance(doc_meta, dict):
        raise ValueError("'document_level_metadata' must be an object.")

    if "required_fields" not in doc_meta or not isinstance(doc_meta["required_fields"], dict):
        raise ValueError("Metadata schema must contain document_level_metadata.required_fields")

    optional_fields = doc_meta.get("optional_fields", {})
    if optional_fields is not None and not isinstance(optional_fields, dict):
        raise ValueError("document_level_metadata.optional_fields must be an object if provided.")

    return schema


# =========================================================
# Validation
# =========================================================
def validate_required_fields_exist(
    frontmatter: dict[str, Any],
    required_fields: dict[str, Any],
    document_path: Path,
) -> None:
    missing = [field_name for field_name in required_fields if field_name not in frontmatter]
    if missing:
        raise ValueError(
            f"Missing required metadata fields in {document_path}: {', '.join(missing)}"
        )


def validate_allowed_values(value: Any, field_name: str, field_definition: dict[str, Any]) -> None:
    allowed_values = field_definition.get("allowed_values")
    if not allowed_values:
        return

    if value not in allowed_values:
        raise ValueError(
            f"Field '{field_name}' has invalid value '{value}'. "
            f"Allowed values: {allowed_values}"
        )


def validate_expected_value(value: Any, field_name: str, field_definition: dict[str, Any]) -> None:
    expected_value = field_definition.get("expected_value")
    if expected_value is None:
        return

    if value != expected_value:
        raise ValueError(
            f"Field '{field_name}' must equal '{expected_value}', but got '{value}'."
        )


def validate_pattern(value: Any, field_name: str, field_definition: dict[str, Any]) -> None:
    pattern = field_definition.get("pattern")
    if not pattern:
        return

    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError(
            f"Field '{field_name}' value '{value}' does not match pattern '{pattern}'."
        )


def validate_min_items(value: Any, field_name: str, field_definition: dict[str, Any]) -> None:
    min_items = field_definition.get("min_items")
    if min_items is None:
        return

    if not isinstance(value, list) or len(value) < int(min_items):
        raise ValueError(
            f"Field '{field_name}' must contain at least {min_items} item(s)."
        )


def coerce_and_validate_field(
    field_name: str,
    raw_value: Any,
    field_definition: dict[str, Any],
) -> Any:
    declared_type = field_definition.get("type")
    if not declared_type:
        raise ValueError(f"Schema field '{field_name}' is missing 'type'.")

    cleaned_value = validate_type(raw_value, field_name, declared_type)
    validate_allowed_values(cleaned_value, field_name, field_definition)
    validate_expected_value(cleaned_value, field_name, field_definition)
    validate_pattern(cleaned_value, field_name, field_definition)
    validate_min_items(cleaned_value, field_name, field_definition)

    return cleaned_value


def build_validated_metadata(
    parsed_doc: DocumentParseResult,
    schema: dict[str, Any],
    config: dict[str, Any],
    project_root: Path,
) -> dict[str, Any]:
    doc_meta = schema["document_level_metadata"]
    required_fields: dict[str, Any] = doc_meta["required_fields"]
    optional_fields: dict[str, Any] = doc_meta.get("optional_fields", {})

    validate_required_fields_exist(
        frontmatter=parsed_doc.frontmatter,
        required_fields=required_fields,
        document_path=parsed_doc.source_path,
    )

    validated: dict[str, Any] = {}

    for field_name, field_definition in required_fields.items():
        validated[field_name] = coerce_and_validate_field(
            field_name=field_name,
            raw_value=parsed_doc.frontmatter[field_name],
            field_definition=field_definition,
        )

    for field_name, field_definition in optional_fields.items():
        if field_name in parsed_doc.frontmatter and parsed_doc.frontmatter[field_name] is not None:
            validated[field_name] = coerce_and_validate_field(
                field_name=field_name,
                raw_value=parsed_doc.frontmatter[field_name],
                field_definition=field_definition,
            )

    metadata_extraction = config["metadata_extraction"]
    auto_add_fields = metadata_extraction.get("auto_add_fields", {})

    relative_path = parsed_doc.source_path.relative_to(project_root).as_posix()

    if auto_add_fields.get("source_path", False):
        validated["source_path"] = relative_path

    if auto_add_fields.get("source_filename", False):
        validated["source_filename"] = parsed_doc.source_path.name

    if auto_add_fields.get("source_directory", False):
        validated["source_directory"] = parsed_doc.source_path.parent.relative_to(project_root).as_posix()

    if auto_add_fields.get("ingestion_timestamp", False):
        validated["ingestion_timestamp"] = utc_now_iso()

    validated["document_body_char_count"] = len(parsed_doc.body)
    validated["document_body_word_count"] = len(parsed_doc.body.split())

    return validated


def validate_cross_field_rules(metadata: dict[str, Any], document_path: Path) -> None:
    effective_date = metadata.get("effective_date")
    review_date = metadata.get("review_date")

    if effective_date and review_date and effective_date > review_date:
        raise ValueError(
            f"{document_path}: effective_date must be earlier than or equal to review_date."
        )

    if metadata.get("company_name") != "NorthStar Retail & Distribution":
        raise ValueError(
            f"{document_path}: company_name must be 'NorthStar Retail & Distribution'."
        )

    if not metadata.get("tags"):
        raise ValueError(f"{document_path}: tags cannot be empty.")


# =========================================================
# Output
# =========================================================
def write_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    ensure_parent_dir(output_path)
    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


# =========================================================
# Main execution
# =========================================================
def build_document_metadata(
    config_path: Path = DEFAULT_CONFIG_PATH,
    schema_path: Path | None = None,
) -> int:
    config = load_ingestion_config(config_path)

    paths_config = config["paths"]
    schema_path = schema_path or (PROJECT_ROOT / paths_config.get("metadata_schema_path", str(DEFAULT_SCHEMA_PATH)))
    schema = load_metadata_schema(schema_path)

    source_dirs = paths_config.get("source_directories", [])
    source_file_pattern = paths_config.get("source_file_pattern", "*.md")
    output_path = PROJECT_ROOT / paths_config["extracted_metadata_output"]

    markdown_files = find_markdown_files(
        source_dirs=source_dirs,
        project_root=PROJECT_ROOT,
        pattern=source_file_pattern,
    )

    if not markdown_files:
        logger.warning("No markdown files found for metadata build.")
        write_jsonl([], output_path)
        return 0

    required_document_fields: list[str] = config["metadata_extraction"].get("required_document_fields", [])
    schema_required_fields = list(schema["document_level_metadata"]["required_fields"].keys())

    if set(required_document_fields) != set(schema_required_fields):
        raise ValueError(
            "Mismatch between ingestion config required_document_fields and metadata schema required_fields."
        )

    records: list[dict[str, Any]] = []
    seen_document_ids: set[str] = set()

    for markdown_file in markdown_files:
        logger.info("Processing document: %s", markdown_file.relative_to(PROJECT_ROOT).as_posix())

        parsed_doc = parse_markdown_with_frontmatter(markdown_file)
        metadata = build_validated_metadata(
            parsed_doc=parsed_doc,
            schema=schema,
            config=config,
            project_root=PROJECT_ROOT,
        )

        validate_cross_field_rules(metadata, markdown_file)

        document_id = metadata["document_id"]
        if document_id in seen_document_ids:
            raise ValueError(f"Duplicate document_id found: {document_id}")
        seen_document_ids.add(document_id)

        records.append(metadata)

    records.sort(key=lambda item: item["document_id"])
    write_jsonl(records, output_path)

    logger.info("Metadata build complete. Documents processed: %s", len(records))
    logger.info("Output written to: %s", output_path.relative_to(PROJECT_ROOT).as_posix())

    return len(records)


def parse_cli_args(argv: list[str]) -> tuple[Path, Path | None]:
    config_path = DEFAULT_CONFIG_PATH
    schema_path: Path | None = None

    idx = 1
    while idx < len(argv):
        arg = argv[idx]

        if arg == "--config":
            idx += 1
            if idx >= len(argv):
                raise ValueError("Missing value after --config")
            config_path = (PROJECT_ROOT / argv[idx]).resolve()
        elif arg == "--schema":
            idx += 1
            if idx >= len(argv):
                raise ValueError("Missing value after --schema")
            schema_path = (PROJECT_ROOT / argv[idx]).resolve()
        else:
            raise ValueError(f"Unknown argument: {arg}")

        idx += 1

    return config_path, schema_path


def main() -> None:
    setup_logging()

    try:
        config_path, schema_path = parse_cli_args(sys.argv)
        processed_count = build_document_metadata(
            config_path=config_path,
            schema_path=schema_path,
        )
        logger.info("Success. Total validated metadata records: %s", processed_count)
    except Exception as exc:
        logger.exception("Metadata build failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()