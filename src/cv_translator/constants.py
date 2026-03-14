from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CV_DIR = ROOT / "cv"
CONFIG_PATH = ROOT / ".cv_config.json"
INDEX_PATH = ROOT / ".cv_translation_index.json"
TEMPLATE_PATH = ROOT / "template.tex"
ENV_PATH = ROOT / ".env"

FALLBACK_LANGUAGES = {
    "BG": "Bulgarian",
    "CS": "Czech",
    "DA": "Danish",
    "DE": "German",
    "EL": "Greek",
    "EN": "English",
    "ES": "Spanish",
    "ET": "Estonian",
    "FI": "Finnish",
    "FR": "French",
    "HU": "Hungarian",
    "ID": "Indonesian",
    "IT": "Italian",
    "JA": "Japanese",
    "KO": "Korean",
    "LT": "Lithuanian",
    "LV": "Latvian",
    "NB": "Norwegian Bokmal",
    "NL": "Dutch",
    "PL": "Polish",
    "PT": "Portuguese",
    "RO": "Romanian",
    "RU": "Russian",
    "SK": "Slovak",
    "SL": "Slovenian",
    "SV": "Swedish",
    "TR": "Turkish",
    "UK": "Ukrainian",
    "ZH": "Chinese",
}

TARGET_LANG_ALIASES = {
    "EN": "EN-US",
    "PT": "PT-PT",
}

# If False, DeepL auto-detects the source language for better robustness on mixed LaTeX/text.
FORCE_SOURCE_LANGUAGE = False

# Keep translation payload/result logging configurable from one place.
DEBUG_TRANSLATION = False

# Bump this when segmentation or exception rules change so target files are retranslated once.
TRANSLATION_ENGINE_VERSION = "2026-03-14-inline-commands-v3"
