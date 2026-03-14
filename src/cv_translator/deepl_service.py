import deepl
import re
from dotenv import dotenv_values

from .constants import (
    ENV_PATH,
    FALLBACK_LANGUAGES,
    FORCE_SOURCE_LANGUAGE,
    TARGET_LANG_ALIASES,
)
from .debug import print_translation_pipeline


def get_deepl_client() -> deepl.DeepLClient:
    """Build and return a configured DeepL client from .env credentials."""

    config = dotenv_values(ENV_PATH)
    api_key = config.get("DEEPL_API_KEY")

    if not api_key:
        raise RuntimeError(
            "DEEPL_API_KEY is missing. Add it in .env before running translations."
        )

    return deepl.DeepLClient(api_key)


def canonical_lang(code: str) -> str:
    """Normalize language variants into their canonical comparison family."""

    value = code.upper()
    if value.startswith("EN"):
        return "EN"
    if value.startswith("PT"):
        return "PT"
    return value


def get_available_languages(kind: str) -> dict[str, str]:
    """Return available language codes from DeepL, with local fallback data."""

    languages = dict(FALLBACK_LANGUAGES)

    try:
        deepl_client = get_deepl_client()
        api_languages = (
            deepl_client.get_source_languages()
            if kind == "source"
            else deepl_client.get_target_languages()
        )

        dynamic_languages = {
            language.code.upper(): language.name for language in api_languages
        }
        if dynamic_languages:
            languages = dynamic_languages
    except (RuntimeError, OSError, deepl.DeepLException):
        pass

    return languages


def normalize_target_code(code: str) -> str:
    """Apply target-language aliases expected by the DeepL API."""

    return TARGET_LANG_ALIASES.get(code.upper(), code.upper())


# Keep protection minimal: do not mask inline LaTeX style macros like \textit,
# 	extbf, or \textsuperscript so DeepL receives more natural sentence context.
LATEX_TOKEN_PATTERN = re.compile(r"\\\\|\\[&%$#_{}]")
ESCAPED_AMP_PATTERN = re.compile(r"\\&")


def _build_request_kwargs(source_lang: str | None, target_lang: str) -> dict[str, object]:
    """Prepare keyword arguments for DeepL translation requests."""

    request_kwargs: dict[str, object] = {
        "target_lang": normalize_target_code(target_lang),
        "preserve_formatting": True,
    }
    if FORCE_SOURCE_LANGUAGE and source_lang:
        request_kwargs["source_lang"] = source_lang

    return request_kwargs


def _apply_pre_translation_exceptions(text: str) -> tuple[str, int]:
    """Apply pre-translation exceptions and return transformed text with metadata."""

    # Exception 1: before translation, convert LaTeX escaped ampersand to plain ampersand.
    escaped_amp_count = len(ESCAPED_AMP_PATTERN.findall(text))
    updated = ESCAPED_AMP_PATTERN.sub("&", text)
    return updated, escaped_amp_count


def _restore_post_translation_exceptions(text: str, escaped_amp_count: int) -> str:
    """Restore protected characters after translation based on tracked counts."""

    if escaped_amp_count <= 0:
        return text

    restored = []
    replaced = 0
    for char in text:
        if char == "&" and replaced < escaped_amp_count:
            restored.append(r"\&")
            replaced += 1
        else:
            restored.append(char)

    return "".join(restored)


def _protect_latex_tokens(text: str) -> tuple[str, dict[str, str]]:
    """Replace sensitive LaTeX tokens with placeholders before translation."""

    replacements: dict[str, str] = {}
    counter = 0

    def _replace(match: re.Match[str]) -> str:
        """Generate and register a stable placeholder for a matched token."""

        nonlocal counter
        key = f"__LTX_TOKEN_{counter}__"
        counter += 1
        replacements[key] = match.group(0)
        return key

    protected = LATEX_TOKEN_PATTERN.sub(_replace, text)
    return protected, replacements


def _restore_latex_tokens(text: str, replacements: dict[str, str]) -> str:
    """Restore original LaTeX tokens from placeholder mappings."""

    restored = text
    for key, value in replacements.items():
        restored = restored.replace(key, value)
    return restored


def _preserve_outer_whitespace(original: str, translated: str) -> str:
    """Keep leading and trailing whitespace from the original segment."""

    if not original:
        return translated

    if original.strip() == "":
        return original

    prefix_len = len(original) - len(original.lstrip())
    suffix_len = len(original) - len(original.rstrip())

    prefix = original[:prefix_len]
    suffix = original[len(original) - suffix_len :] if suffix_len else ""
    core = translated.strip()

    return f"{prefix}{core}{suffix}"


def translate_segments(
    deepl_client: deepl.DeepLClient,
    texts: list[str],
    source_lang: str | None,
    target_lang: str,
) -> list[str]:
    """Translate text segments with DeepL while preserving LaTeX-sensitive tokens."""

    if not texts:
        return []

    protected_texts: list[str] = []
    preprocessed_texts: list[str] = []
    token_maps: list[dict[str, str]] = []
    exception_counts: list[int] = []
    for text in texts:
        with_exceptions, exception_count = _apply_pre_translation_exceptions(text)
        protected, mapping = _protect_latex_tokens(with_exceptions)
        preprocessed_texts.append(with_exceptions)
        protected_texts.append(protected)
        token_maps.append(mapping)
        exception_counts.append(exception_count)

    request_kwargs = _build_request_kwargs(source_lang, target_lang)

    results = deepl_client.translate_text(protected_texts, **request_kwargs)

    translated_values = (
        [item.text for item in results] if isinstance(results, list) else [results.text]
    )

    restored: list[str] = []
    for idx, translated_text in enumerate(translated_values):
        unprotected = _restore_latex_tokens(translated_text, token_maps[idx])
        with_exceptions_restored = _restore_post_translation_exceptions(
            unprotected,
            exception_counts[idx],
        )
        restored.append(_preserve_outer_whitespace(texts[idx], with_exceptions_restored))

    print_translation_pipeline(
        original_texts=texts,
        preprocessed_texts=preprocessed_texts,
        payload_texts=protected_texts,
        raw_result_texts=translated_values,
        final_texts=restored,
    )

    return restored
