"""
Dataset registry - discovery and resolution of datasets under learn/app/data

Layout convention:
    learn/app/data/<name>/<class>/*.png     -> image_folder dataset
    learn/app/data/<name>.csv               -> csv dataset (preview only)

This module is the single source of truth for where datasets live. Nothing else
should build a dataset path by hand.
"""

import json
from pathlib import Path
from typing import Any, Literal, TypedDict

DATA_ROOT = Path(__file__).parent.parent / "data"

# Maps a downloaded dataset's filename to the URL it came from, so provenance
# survives a restart. A dot-prefixed name keeps it out of the dataset listing.
SOURCES_FILE = DATA_ROOT / ".sources.json"

IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".bmp"})

DatasetKind = Literal["image_folder", "csv"]


class DatasetEntry(TypedDict):
    """A dataset discovered under DATA_ROOT"""

    name: str
    kind: DatasetKind
    path: Path  # absolute; the directory for image_folder, the file for csv
    num_classes: int  # 0 for csv
    num_samples: int  # image count, or row count for csv
    source_url: str | None  # set when the dataset was downloaded from a URL


def read_sources() -> dict[str, str]:
    """Load the filename -> source URL map. Returns {} when absent or corrupt."""
    try:
        with open(SOURCES_FILE, encoding="utf-8") as handle:
            sources = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}

    return sources if isinstance(sources, dict) else {}


def record_source(name: str, url: str) -> None:
    """Remember which URL a downloaded dataset came from.

    Provenance is a nice-to-have, so a write failure must not fail the download
    that just succeeded.
    """
    sources = read_sources()
    sources[name] = url

    try:
        SOURCES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SOURCES_FILE, "w", encoding="utf-8") as handle:
            json.dump(sources, handle, indent=2, sort_keys=True)
    except OSError:
        pass


def forget_source(name: str) -> None:
    """Drop a dataset's recorded source URL"""
    sources = read_sources()
    if sources.pop(name, None) is None:
        return

    try:
        with open(SOURCES_FILE, "w", encoding="utf-8") as handle:
            json.dump(sources, handle, indent=2, sort_keys=True)
    except OSError:
        pass


def is_valid_dataset_name(name: str) -> bool:
    """Reject names that could escape DATA_ROOT or address a hidden entry.

    Dataset names reach the filesystem, so validate them even though the only
    current producer is a picker populated from the filesystem itself.
    """
    if not name or name in (".", ".."):
        return False

    if name.startswith("."):
        return False

    return "/" not in name and "\\" not in name


def _count_images(directory: Path) -> int:
    """Count image files directly inside a directory"""
    return sum(
        1
        for entry in directory.iterdir()
        if entry.is_file() and entry.suffix.lower() in IMAGE_SUFFIXES
    )


def _scan_image_folder(directory: Path) -> DatasetEntry | None:
    """Build an entry for a directory whose subfolders are classes.

    Returns None when the directory holds no class subfolder with images, so a
    stray folder in data/ never shows up as an empty dataset.
    """
    num_classes = 0
    num_samples = 0

    for class_dir in sorted(directory.iterdir()):
        if not class_dir.is_dir() or class_dir.name.startswith("."):
            continue

        image_count = _count_images(class_dir)
        if image_count == 0:
            continue

        num_classes += 1
        num_samples += image_count

    if num_classes == 0:
        return None

    return {
        "name": directory.name,
        "kind": "image_folder",
        "path": directory,
        "num_classes": num_classes,
        "num_samples": num_samples,
        "source_url": None,
    }


def _count_csv_rows(csv_path: Path) -> int:
    """Count data rows in a CSV, excluding the header. Returns 0 if unreadable."""
    try:
        with open(csv_path, encoding="utf-8", errors="replace") as handle:
            return max(sum(1 for _ in handle) - 1, 0)
    except OSError:
        return 0


def _scan_csv(csv_path: Path, sources: dict[str, str]) -> DatasetEntry:
    """Build an entry for a single CSV file"""
    return {
        "name": csv_path.name,
        "kind": "csv",
        "path": csv_path,
        "num_classes": 0,
        "num_samples": _count_csv_rows(csv_path),
        "source_url": sources.get(csv_path.name),
    }


def list_datasets() -> list[DatasetEntry]:
    """Discover every dataset under DATA_ROOT, sorted by name.

    Never raises: a missing or unreadable data directory yields an empty list so
    the UI can show its own empty state.
    """
    if not DATA_ROOT.is_dir():
        return []

    entries: list[DatasetEntry] = []
    sources = read_sources()

    try:
        candidates = sorted(DATA_ROOT.iterdir())
    except OSError:
        return []

    for candidate in candidates:
        if candidate.name.startswith("."):
            continue

        if candidate.is_dir():
            entry = _scan_image_folder(candidate)
            if entry:
                entries.append(entry)
        elif candidate.is_file() and candidate.suffix.lower() == ".csv":
            entries.append(_scan_csv(candidate, sources))

    return entries


def default_dataset_name(datasets: list[DatasetEntry] | None = None) -> str:
    """Best dataset to land on: the first image dataset, else the first of any kind.

    The Model, Training and Interpretability pages only handle image folders, so
    dropping a user straight onto a CSV would dead-end the workflow.
    """
    entries = list_datasets() if datasets is None else datasets
    if not entries:
        return ""

    for entry in entries:
        if entry["kind"] == "image_folder":
            return entry["name"]

    return entries[0]["name"]


def get_dataset(name: str) -> DatasetEntry | None:
    """Look up a single dataset by name. Returns None if absent or invalid."""
    if not is_valid_dataset_name(name):
        return None

    for entry in list_datasets():
        if entry["name"] == name:
            return entry

    return None


def resolve_dataset_path(dataset_config: dict[str, Any]) -> Path:
    """Turn a saved dataset_config into an absolute dataset path.

    Handles three shapes, newest first:
      1. "dataset_name" resolved through the registry (survives moving the repo)
      2. an absolute "dataset_path"
      3. a legacy cwd-relative "dataset_path" (pre-registry sessions)

    The returned path may not exist - callers report that to the user rather
    than crashing on a stale session.
    """
    name = dataset_config.get("dataset_name")
    if name:
        entry = get_dataset(name)
        if entry:
            return entry["path"]

        return DATA_ROOT / name if is_valid_dataset_name(name) else DATA_ROOT

    raw_path = Path(dataset_config.get("dataset_path", ""))
    if raw_path.is_absolute():
        return raw_path

    return Path.cwd() / raw_path
