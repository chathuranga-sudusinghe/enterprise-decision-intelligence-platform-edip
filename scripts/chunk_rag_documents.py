from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd
import yaml


# =========================================================
# Logging
# =========================================================
logger = logging.getLogger("chunk_rag_documents")


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
DEFAULT_METADATA_JSONL = PROJECT_ROOT / "data" / "processed" / "rag" / "document_metadata.jsonl"

FRONTMATTER_PATTERN = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n?",
    flags=re.DOTALL,
)

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$", flags=re.MULTILINE)


# =========================================================
# Dataclasses
# =========================================================
@dataclass
class HeadingNode:
    level: int
    title: str
    line_index: int


@dataclass
class SectionBlock:
    heading_path: str
    section_title: str
    text: str
    order_index: int


# =========================================================
# Path helpers
# =========================================================
def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_default_paths() -> Dict[str, Path]:
    processed_dir = PROJECT_ROOT / "data" / "processed" / "rag"
    ensure_dir(processed_dir)

    return {
        "metadata_jsonl": DEFAULT_METADATA_JSONL,
        "chunks_jsonl": processed_dir / "document_chunks.jsonl",
        "chunks_csv": processed_dir / "document_chunks.csv",
    }


# =========================================================
# Config loading
# =========================================================
def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing YAML config file: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc


def get_chunking_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Supports a few safe shapes so the script is resilient to minor config edits.
    """
    candidates = [
        config.get("chunking", {}),
        config.get("chunk_settings", {}),
        config.get("document_chunking", {}),
        config.get("ingestion", {}).get("chunking", {}) if isinstance(config.get("ingestion"), dict) else {},
    ]

    resolved: Dict[str, Any] = {}
    for candidate in candidates:
        if isinstance(candidate, dict):
            resolved.update({k: v for k, v in candidate.items() if v is not None})

    min_words = int(resolved.get("min_words", 400))
    max_words = int(resolved.get("max_words", 800))
    overlap_words = int(resolved.get("overlap_words", 80))

    if min_words <= 0 or max_words <= 0 or overlap_words < 0:
        raise ValueError("Chunk word settings must be positive, with overlap_words >= 0.")

    if min_words > max_words:
        raise ValueError("min_words cannot be greater than max_words.")

    return {
        "min_words": min_words,
        "max_words": max_words,
        "overlap_words": overlap_words,
    }


# =========================================================
# Metadata loading
# =========================================================
def load_metadata_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing metadata file: {path}. Run build_rag_metadata.py first."
        )

    rows: List[Dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON line in {path} at line {line_number}: {exc}"
                ) from exc

    if not rows:
        raise ValueError(f"No metadata records found in {path}")

    return rows


# =========================================================
# Markdown parsing
# =========================================================
def strip_frontmatter(markdown_text: str) -> str:
    match = FRONTMATTER_PATTERN.match(markdown_text)
    if match:
        return markdown_text[match.end():].lstrip()
    return markdown_text


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def clean_markdown_text(text: str) -> str:
    text = normalize_newlines(text)
    text = strip_frontmatter(text)

    # Remove obvious editor noise lines if present.
    cleaned_lines: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()

        if stripped in {"```", "~~~"}:
            cleaned_lines.append(line)
            continue

        # Skip empty duplicate separators only if isolated.
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines).strip()
    return cleaned


def extract_headings(lines: List[str]) -> List[HeadingNode]:
    headings: List[HeadingNode] = []

    for idx, line in enumerate(lines):
        match = HEADING_PATTERN.match(line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append(HeadingNode(level=level, title=title, line_index=idx))

    return headings


def build_heading_path(active_headings: List[HeadingNode]) -> str:
    if not active_headings:
        return "root"
    return " > ".join(h.title for h in active_headings)


def split_markdown_into_sections(markdown_text: str) -> List[SectionBlock]:
    """
    Splits by markdown heading boundaries while keeping heading with its related content.
    If a document has no headings, returns one root section.
    """
    text = clean_markdown_text(markdown_text)
    if not text:
        return []

    lines = text.splitlines()
    headings = extract_headings(lines)

    if not headings:
        return [
            SectionBlock(
                heading_path="root",
                section_title="root",
                text=text.strip(),
                order_index=1,
            )
        ]

    sections: List[SectionBlock] = []
    active_stack: List[HeadingNode] = []

    for idx, heading in enumerate(headings):
        start_line = heading.line_index
        end_line = headings[idx + 1].line_index if idx + 1 < len(headings) else len(lines)

        while active_stack and active_stack[-1].level >= heading.level:
            active_stack.pop()
        active_stack.append(heading)

        section_lines = lines[start_line:end_line]
        section_text = "\n".join(section_lines).strip()

        if section_text:
            sections.append(
                SectionBlock(
                    heading_path=build_heading_path(active_stack),
                    section_title=heading.title,
                    text=section_text,
                    order_index=len(sections) + 1,
                )
            )

    return sections


# =========================================================
# Text / chunk helpers
# =========================================================
def word_count(text: str) -> int:
    return len(text.split())


def tokenize_words(text: str) -> List[str]:
    return text.split()


def build_overlap_text(words: List[str], overlap_words: int) -> str:
    if overlap_words <= 0 or not words:
        return ""
    return " ".join(words[-overlap_words:])


def guess_topic(section_title: str, document_title: str, tags: List[str]) -> str:
    base = section_title if section_title and section_title != "root" else document_title
    base = re.sub(r"[^a-zA-Z0-9\s]+", " ", base).strip().lower()
    base = re.sub(r"\s+", "_", base)

    if base and base != "root":
        return base

    if tags:
        return str(tags[0]).strip().lower()

    return "general_topic"


def serialize_keyword_tags(tags: Any) -> List[str]:
    if tags is None:
        return []
    if isinstance(tags, list):
        return [str(t).strip() for t in tags if str(t).strip()]
    return [str(tags).strip()] if str(tags).strip() else []


def chunk_long_text(
    text: str,
    min_words: int,
    max_words: int,
    overlap_words: int,
) -> List[str]:
    """
    Word-window fallback for long section text.
    Keeps overlap between adjacent chunks.
    """
    words = tokenize_words(text)
    if not words:
        return []

    if len(words) <= max_words:
        return [" ".join(words)]

    chunks: List[str] = []
    start = 0

    while start < len(words):
        end = min(start + max_words, len(words))
        current_words = words[start:end]
        if not current_words:
            break

        chunks.append(" ".join(current_words))

        if end >= len(words):
            break

        next_start = max(end - overlap_words, start + min_words)
        if next_start <= start:
            next_start = end
        start = next_start

    return chunks


def chunk_sections(
    sections: List[SectionBlock],
    min_words: int,
    max_words: int,
    overlap_words: int,
) -> List[Tuple[SectionBlock, str]]:
    """
    Keeps sections intact where possible.
    If a section is too long, splits internally with overlap.
    Also merges small adjacent sections when practical.
    """
    results: List[Tuple[SectionBlock, str]] = []

    buffer_texts: List[str] = []
    buffer_paths: List[str] = []
    buffer_titles: List[str] = []
    buffer_order_start: int | None = None

    def flush_buffer() -> None:
        nonlocal buffer_texts, buffer_paths, buffer_titles, buffer_order_start

        if not buffer_texts:
            return

        merged_text = "\n\n".join(buffer_texts).strip()
        merged_path = " > ".join(dict.fromkeys(buffer_paths)) if buffer_paths else "root"
        merged_title = buffer_titles[-1] if buffer_titles else "root"

        results.append(
            (
                SectionBlock(
                    heading_path=merged_path,
                    section_title=merged_title,
                    text=merged_text,
                    order_index=buffer_order_start or 1,
                ),
                merged_text,
            )
        )

        buffer_texts = []
        buffer_paths = []
        buffer_titles = []
        buffer_order_start = None

    for section in sections:
        section_wc = word_count(section.text)

        if section_wc > max_words:
            flush_buffer()
            for part in chunk_long_text(
                section.text,
                min_words=min_words,
                max_words=max_words,
                overlap_words=overlap_words,
            ):
                results.append((section, part))
            continue

        if not buffer_texts:
            buffer_texts = [section.text]
            buffer_paths = [section.heading_path]
            buffer_titles = [section.section_title]
            buffer_order_start = section.order_index
            continue

        candidate_text = "\n\n".join(buffer_texts + [section.text]).strip()
        candidate_wc = word_count(candidate_text)

        if candidate_wc <= max_words:
            buffer_texts.append(section.text)
            buffer_paths.append(section.heading_path)
            buffer_titles.append(section.section_title)
        else:
            flush_buffer()
            buffer_texts = [section.text]
            buffer_paths = [section.heading_path]
            buffer_titles = [section.section_title]
            buffer_order_start = section.order_index

    flush_buffer()
    return results


# =========================================================
# Chunk record building
# =========================================================
def build_chunk_record(
    document_metadata: Dict[str, Any],
    chunk_index: int,
    chunk_text: str,
    section_block: SectionBlock,
) -> Dict[str, Any]:
    document_id = str(document_metadata["document_id"])
    tags = serialize_keyword_tags(document_metadata.get("tags"))

    chunk_record: Dict[str, Any] = {
        "chunk_id": f"{document_id}-chunk-{chunk_index:04d}",
        "source_document_id": document_id,
        "chunk_index": chunk_index,
        "chunk_text": chunk_text.strip(),
        "document_type": document_metadata.get("document_type"),
        "department": document_metadata.get("department"),
        "business_domain": document_metadata.get("business_domain"),
        "region_scope": document_metadata.get("region_scope"),
        "owner_role": document_metadata.get("owner_role"),
        "topic": guess_topic(
            section_title=section_block.section_title,
            document_title=str(document_metadata.get("document_title", "")),
            tags=tags,
        ),
        "heading_path": section_block.heading_path,
        "section_title": section_block.section_title,
        "chunk_word_count": word_count(chunk_text),
        "keyword_tags": tags,
        "effective_date": document_metadata.get("effective_date"),
        "review_date": document_metadata.get("review_date"),
        "version": document_metadata.get("version"),
        "confidentiality_level": document_metadata.get("confidentiality_level"),
        "document_status": document_metadata.get("document_status"),
        "approval_level": document_metadata.get("approval_level"),
        "source_system": document_metadata.get("source_system"),
        "company_name": document_metadata.get("company_name"),
        "source_path": document_metadata.get("source_path"),
        "document_title": document_metadata.get("document_title"),
        "related_structured_domains": document_metadata.get("related_structured_domains", []),
    }

    return chunk_record


def validate_chunk_record(chunk_record: Dict[str, Any]) -> None:
    required = [
        "chunk_id",
        "source_document_id",
        "chunk_index",
        "chunk_text",
        "document_type",
        "business_domain",
        "region_scope",
        "owner_role",
        "topic",
    ]

    for field in required:
        value = chunk_record.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"Chunk record missing required field: {field}")

    if int(chunk_record["chunk_index"]) <= 0:
        raise ValueError("chunk_index must start at 1.")

    if not chunk_record["chunk_text"].strip():
        raise ValueError("chunk_text cannot be empty.")


# =========================================================
# Main chunking flow
# =========================================================
def resolve_source_markdown_path(document_metadata: Dict[str, Any]) -> Path:
    source_path = document_metadata.get("source_path")
    if not source_path:
        raise ValueError(
            f"Document {document_metadata.get('document_id')} is missing source_path."
        )

    path = PROJECT_ROOT / str(source_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Source markdown file not found for {document_metadata.get('document_id')}: {path}"
        )

    return path


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_chunks_for_document(
    document_metadata: Dict[str, Any],
    min_words: int,
    max_words: int,
    overlap_words: int,
) -> List[Dict[str, Any]]:
    markdown_path = resolve_source_markdown_path(document_metadata)
    markdown_text = read_markdown(markdown_path)

    sections = split_markdown_into_sections(markdown_text)
    if not sections:
        logger.warning(
            "Skipping empty document after parsing: %s",
            document_metadata.get("source_path"),
        )
        return []

    chunk_pairs = chunk_sections(
        sections=sections,
        min_words=min_words,
        max_words=max_words,
        overlap_words=overlap_words,
    )

    chunk_records: List[Dict[str, Any]] = []
    for idx, (section_block, chunk_text) in enumerate(chunk_pairs, start=1):
        record = build_chunk_record(
            document_metadata=document_metadata,
            chunk_index=idx,
            chunk_text=chunk_text,
            section_block=section_block,
        )
        validate_chunk_record(record)
        chunk_records.append(record)

    return chunk_records


# =========================================================
# Output writers
# =========================================================
def write_jsonl(records: Iterable[Dict[str, Any]], path: Path) -> int:
    ensure_dir(path.parent)
    count = 0

    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

    return count


def write_csv(records: List[Dict[str, Any]], path: Path) -> None:
    ensure_dir(path.parent)
    df = pd.DataFrame(records)
    df.to_csv(path, index=False)


# =========================================================
# CLI
# =========================================================
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chunk EDIP RAG markdown documents into chunk-level records."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to rag_ingestion_config.yaml",
    )
    parser.add_argument(
        "--metadata-jsonl",
        type=Path,
        default=DEFAULT_METADATA_JSONL,
        help="Path to document_metadata.jsonl",
    )
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=None,
        help="Optional override for output chunk JSONL",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional override for output chunk CSV",
    )
    return parser.parse_args()


# =========================================================
# Main
# =========================================================
def main() -> None:
    setup_logging()
    args = parse_args()

    default_paths = build_default_paths()
    config = load_yaml(args.config)
    chunking = get_chunking_config(config)

    metadata_records = load_metadata_jsonl(args.metadata_jsonl)
    logger.info("Loaded metadata records: %s", len(metadata_records))

    all_chunks: List[Dict[str, Any]] = []
    seen_chunk_ids: set[str] = set()

    for document_metadata in metadata_records:
        document_id = document_metadata.get("document_id")
        source_path = document_metadata.get("source_path")

        logger.info("Chunking document: %s | %s", document_id, source_path)

        doc_chunks = build_chunks_for_document(
            document_metadata=document_metadata,
            min_words=chunking["min_words"],
            max_words=chunking["max_words"],
            overlap_words=chunking["overlap_words"],
        )

        for chunk in doc_chunks:
            chunk_id = str(chunk["chunk_id"])
            if chunk_id in seen_chunk_ids:
                raise ValueError(f"Duplicate chunk_id found: {chunk_id}")
            seen_chunk_ids.add(chunk_id)

        all_chunks.extend(doc_chunks)

    if not all_chunks:
        raise ValueError("No chunk records were generated.")

    output_jsonl = args.output_jsonl or default_paths["chunks_jsonl"]
    output_csv = args.output_csv or default_paths["chunks_csv"]

    jsonl_count = write_jsonl(all_chunks, output_jsonl)
    write_csv(all_chunks, output_csv)

    logger.info("Chunking complete. Documents processed: %s", len(metadata_records))
    logger.info("Chunks written to JSONL: %s", output_jsonl)
    logger.info("Chunks written to CSV: %s", output_csv)
    logger.info("Total chunk records: %s", jsonl_count)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.error("Chunking failed: %s", exc)
        raise