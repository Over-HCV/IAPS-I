"""
Download a CSV dataset from a URL into the dataset registry

A downloaded file becomes an ordinary CSV dataset on disk; the source URL is
recorded alongside it so the origin is not lost.
"""

from pathlib import Path
import re
from urllib.parse import unquote, urlparse

import requests

from utils.dataset_registry import DATA_ROOT, is_valid_dataset_name, record_source

ALLOWED_SCHEMES = frozenset({"http", "https"})
MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024
CHUNK_BYTES = 64 * 1024
REQUEST_TIMEOUT_SECONDS = 30
MAX_REDIRECTS = 5

FALLBACK_NAME = "downloaded.csv"

_UNSAFE_NAME_CHARS = re.compile(r"[^A-Za-z0-9._-]")


class DownloadError(Exception):
    """Raised when a dataset URL cannot be turned into a local CSV"""


def filename_from_url(url: str) -> str:
    """Derive a safe local filename from a URL.

    Only the last path segment is used, and everything outside a conservative
    character set is replaced, so a crafted URL cannot escape DATA_ROOT.
    """
    last_segment = unquote(urlparse(url).path).rsplit("/", maxsplit=1)[-1]
    cleaned = _UNSAFE_NAME_CHARS.sub("_", last_segment).lstrip(".")

    if not cleaned:
        return FALLBACK_NAME

    if not cleaned.lower().endswith(".csv"):
        cleaned = f"{cleaned}.csv"

    return cleaned


def _validate_url(url: str) -> str:
    """Check the URL is a fetchable http(s) address. Returns the trimmed URL."""
    url = url.strip()
    if not url:
        raise DownloadError("Enter a URL.")

    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise DownloadError(
            f"Only http and https URLs are supported (got '{parsed.scheme or 'no scheme'}')."
        )

    if not parsed.netloc:
        raise DownloadError("The URL is missing a host.")

    return url


def _target_path(name: str) -> Path:
    """Resolve the destination inside DATA_ROOT, refusing anything outside it."""
    if not is_valid_dataset_name(name):
        raise DownloadError(f"'{name}' is not a usable dataset name.")

    target = (DATA_ROOT / name).resolve()

    # Defence in depth: is_valid_dataset_name already rejects separators, but the
    # destination is a filesystem write, so confirm it really lands in DATA_ROOT.
    if target.parent != DATA_ROOT.resolve():
        raise DownloadError(f"'{name}' would be written outside the dataset folder.")

    return target


def _stream_to_file(response: requests.Response, destination: Path) -> int:
    """Write a streamed response to disk, enforcing the size cap.

    Returns the number of bytes written. The caller owns cleanup on failure.
    """
    written = 0
    with open(destination, "wb") as handle:
        for chunk in response.iter_content(chunk_size=CHUNK_BYTES):
            if not chunk:
                continue

            written += len(chunk)
            if written > MAX_DOWNLOAD_BYTES:
                raise DownloadError(
                    f"File is larger than the {MAX_DOWNLOAD_BYTES // (1024 * 1024)} MB limit."
                )

            handle.write(chunk)

    if written == 0:
        raise DownloadError("The URL returned an empty file.")

    return written


def download_csv(url: str, name: str = "", overwrite: bool = False) -> Path:
    """Download a CSV from a URL into DATA_ROOT.

    Args:
        url: http(s) address of the CSV
        name: local filename; derived from the URL when empty
        overwrite: replace an existing dataset of the same name

    Returns:
        Path to the downloaded file

    Raises:
        DownloadError: on a bad URL, a failed request, or a name clash
    """
    url = _validate_url(url)
    target = _target_path(name.strip() or filename_from_url(url))

    if target.exists() and not overwrite:
        raise DownloadError(
            f"`{target.name}` already exists. Rename it, or tick 'Replace' to overwrite."
        )

    DATA_ROOT.mkdir(parents=True, exist_ok=True)

    # Download to a temporary file so a failure never leaves a half-written
    # dataset in the registry.
    partial = target.with_suffix(target.suffix + ".part")

    try:
        session = requests.Session()
        session.max_redirects = MAX_REDIRECTS
        with session.get(
            url, stream=True, timeout=REQUEST_TIMEOUT_SECONDS
        ) as response:
            response.raise_for_status()
            _stream_to_file(response, partial)

        partial.replace(target)
    except requests.RequestException as exception:
        partial.unlink(missing_ok=True)
        raise DownloadError(f"Could not fetch the URL: {exception}") from exception
    except DownloadError:
        partial.unlink(missing_ok=True)
        raise

    record_source(target.name, url)
    return target
