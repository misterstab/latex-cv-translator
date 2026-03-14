import json
from pathlib import Path

from .constants import CV_DIR, ROOT


def load_json(path: Path, default: dict) -> dict:
    """Load JSON content from disk and return a fallback on failure."""

    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return default


def save_json(path: Path, data: dict) -> None:
    """Persist dictionary data as formatted UTF-8 JSON."""

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def ensure_cv_dir() -> None:
    """Ensure the root directory for generated CV files exists."""

    CV_DIR.mkdir(parents=True, exist_ok=True)


def build_cv_filename(lang_code: str) -> Path:
    """Return the output path for a language-specific CV file."""

    ensure_cv_dir()
    lang_dir = CV_DIR / lang_code.lower()
    lang_dir.mkdir(parents=True, exist_ok=True)
    return lang_dir / f"cv_{lang_code.lower()}.tex"


def resolve_configured_cv_path(native_file: str) -> Path:
    """Resolve configured native file paths across supported legacy layouts."""

    configured = Path(native_file)
    if configured.is_absolute():
        return configured

    default_path = ROOT / configured
    if default_path.exists():
        return default_path

    fallback_in_cv = CV_DIR / configured.name
    if fallback_in_cv.exists():
        return fallback_in_cv

    lang_prefix = configured.stem.removeprefix("cv_")
    nested_fallback = CV_DIR / lang_prefix / configured.name
    if nested_fallback.exists():
        return nested_fallback

    return default_path
