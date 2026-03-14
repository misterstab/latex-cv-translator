import json
from difflib import SequenceMatcher

from .constants import (
    CONFIG_PATH,
    CV_DIR,
    INDEX_PATH,
    ROOT,
    TEMPLATE_PATH,
    TRANSLATION_ENGINE_VERSION,
)
from .deepl_service import canonical_lang, get_deepl_client, translate_segments
from .latex import extract_translatable_segments, hash_text, stitch_content
from .storage import (
    build_cv_filename,
    ensure_cv_dir,
    load_json,
    resolve_configured_cv_path,
    save_json,
)
from .ui import choose_language_by_kind


def first_run_setup() -> dict:
    """Initialize configuration and create the first native CV file."""

    print("First launch setup")
    native_lang = choose_language_by_kind(
        "Choose your native CV language:",
        kind="source",
    )

    if native_lang is None:
        raise RuntimeError("No language selected.")

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError("template.tex not found.")

    source_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    native_file = build_cv_filename(native_lang)

    if native_lang == "FR":
        native_file.write_text(source_text, encoding="utf-8")
    else:
        deepl_client = get_deepl_client()
        source_segments = extract_translatable_segments(source_text)
        translated_chunks = translate_segments(
            deepl_client,
            [segment.text for segment in source_segments],
            source_lang="FR",
            target_lang=native_lang,
        )
        translated_text = stitch_content(source_text, source_segments, translated_chunks)
        native_file.write_text(translated_text, encoding="utf-8")

    config = {
        "native_lang": native_lang,
        "native_file": str(native_file.relative_to(ROOT)),
    }

    save_json(CONFIG_PATH, config)
    save_json(INDEX_PATH, load_json(INDEX_PATH, {"version": 1, "languages": {}}))

    print(f"Native CV created: {native_file.relative_to(ROOT)}")
    return config


def load_or_create_config() -> dict:
    """Load existing config or create it, including path migration handling."""

    config = load_json(CONFIG_PATH, {})
    if config.get("native_lang") and config.get("native_file"):
        ensure_cv_dir()

        native_path = resolve_configured_cv_path(config["native_file"])
        canonical_path = build_cv_filename(config["native_lang"])

        if native_path.exists() and native_path != canonical_path:
            if not canonical_path.exists():
                native_path.replace(canonical_path)
                native_path = canonical_path
            else:
                native_path = canonical_path

            config["native_file"] = str(native_path.relative_to(ROOT))
            save_json(CONFIG_PATH, config)

        return config

    return first_run_setup()


def build_equal_mapping(old_hashes: list[str], new_hashes: list[str]) -> dict[int, int]:
    """Map unchanged segment indices from old hashes to new hashes."""

    mapping: dict[int, int] = {}
    matcher = SequenceMatcher(a=old_hashes, b=new_hashes)

    for tag, old_start, _old_end, new_start, new_end in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(new_end - new_start):
                mapping[new_start + offset] = old_start + offset

    return mapping


def translate_incremental(config: dict) -> None:
    """Translate only modified segments and preserve unchanged target content."""

    native_lang = config["native_lang"]
    native_file = resolve_configured_cv_path(config["native_file"])

    if not native_file.exists():
        raise FileNotFoundError(f"Native CV file not found: {native_file.name}")

    target_lang = choose_language_by_kind(
        "Choose target language:",
        allow_skip=True,
        kind="target",
    )
    if target_lang is None:
        print("Cancelled.")
        return

    if canonical_lang(target_lang) == canonical_lang(native_lang):
        print("Target language is the native language. Nothing to do.")
        return

    source_content = native_file.read_text(encoding="utf-8")
    source_segments = extract_translatable_segments(source_content)
    source_hashes = [hash_text(segment.text) for segment in source_segments]

    target_file = build_cv_filename(target_lang)
    if target_file.exists():
        existing_target_content = target_file.read_text(encoding="utf-8")
        existing_target_segments = extract_translatable_segments(existing_target_content)
    else:
        existing_target_segments = []

    index_state = load_json(INDEX_PATH, {"version": 1, "languages": {}})
    language_state = index_state.get("languages", {}).get(target_lang, {})
    cached_engine_version = language_state.get("engine_version")
    force_retranslate = cached_engine_version != TRANSLATION_ENGINE_VERSION
    old_source_hashes = [] if force_retranslate else language_state.get("source_hashes", [])

    equal_mapping = build_equal_mapping(old_source_hashes, source_hashes)

    replacements = [""] * len(source_segments)
    to_translate_idx: list[int] = []
    preserved_count = 0

    for new_idx in range(len(source_segments)):
        old_idx = equal_mapping.get(new_idx)
        can_preserve = old_idx is not None and old_idx < len(existing_target_segments)

        if can_preserve:
            replacements[new_idx] = existing_target_segments[old_idx].text
            preserved_count += 1
        else:
            to_translate_idx.append(new_idx)

    if to_translate_idx:
        deepl_client = get_deepl_client()
        translated = translate_segments(
            deepl_client,
            [source_segments[idx].text for idx in to_translate_idx],
            source_lang=native_lang,
            target_lang=target_lang,
        )
        for idx, translated_text in zip(to_translate_idx, translated):
            replacements[idx] = translated_text

    output_content = stitch_content(source_content, source_segments, replacements)
    target_file.write_text(output_content, encoding="utf-8")

    index_state.setdefault("languages", {})[target_lang] = {
        "source_hashes": source_hashes,
        "engine_version": TRANSLATION_ENGINE_VERSION,
    }
    save_json(INDEX_PATH, index_state)

    print(f"Updated file: {target_file.relative_to(ROOT)}")
    if force_retranslate:
        print("Engine rules changed: full retranslation applied for this language.")
    print(f"Preserved segments: {preserved_count}")
    print(f"Translated segments: {len(to_translate_idx)}")


def show_config(config: dict) -> None:
    """Print current application configuration in JSON format."""

    print("\nCurrent configuration")
    print(json.dumps(config, indent=2, ensure_ascii=False))
