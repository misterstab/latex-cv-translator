from .constants import DEBUG_TRANSLATION


def print_translation_pipeline(
    original_texts: list[str],
    preprocessed_texts: list[str],
    payload_texts: list[str],
    raw_result_texts: list[str],
    final_texts: list[str],
) -> None:
    """Print each translation stage for debugging when debug mode is enabled."""

    if not DEBUG_TRANSLATION:
        return

    print("\n[DEBUG] Translation pipeline")
    for idx in range(len(original_texts)):
        print(f"[DEBUG][SEGMENT {idx + 1}] ------------------------------")
        print("[DEBUG][ORIGINAL]")
        print(original_texts[idx])
        print("[DEBUG][PREPROCESSED]")
        print(preprocessed_texts[idx])
        print("[DEBUG][PAYLOAD SENT TO DEEPL]")
        print(payload_texts[idx])
        print("[DEBUG][RAW DEEPL RESULT]")
        print(raw_result_texts[idx])
        print("[DEBUG][FINAL RESTORED RESULT]")
        print(final_texts[idx])
