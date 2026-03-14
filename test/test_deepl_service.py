import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

if "deepl" not in sys.modules:
    fake_deepl = ModuleType("deepl")
    fake_deepl.DeepLException = Exception
    fake_deepl.DeepLClient = object
    sys.modules["deepl"] = fake_deepl

if "dotenv" not in sys.modules:
    fake_dotenv = ModuleType("dotenv")
    fake_dotenv.dotenv_values = lambda *_args, **_kwargs: {}
    sys.modules["dotenv"] = fake_dotenv

from cv_translator import deepl_service


class FakeDeepLClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls = []

    def translate_text(self, texts, **kwargs):
        self.calls.append((texts, kwargs))
        return [SimpleNamespace(text=value) for value in self.responses]


class DeepLServiceTests(unittest.TestCase):
    def test_apply_pre_translation_exception_converts_escaped_ampersand(self) -> None:
        updated, count = deepl_service._apply_pre_translation_exceptions(r"A \& B")
        self.assertEqual(updated, "A & B")
        self.assertEqual(count, 1)

    def test_restore_post_translation_exception_reescapes_only_original_ampersands(self) -> None:
        restored = deepl_service._restore_post_translation_exceptions("A & B", 1)
        self.assertEqual(restored, r"A \& B")

    def test_build_request_kwargs_uses_auto_detection_by_default(self) -> None:
        kwargs = deepl_service._build_request_kwargs("FR", "EN")
        self.assertEqual(kwargs["target_lang"], "EN-US")
        self.assertNotIn("source_lang", kwargs)

    def test_translate_segments_preserves_outer_whitespace_and_restores_ampersands(self) -> None:
        client = FakeDeepLClient([" Alpha & Beta "])
        with patch("cv_translator.deepl_service.print_translation_pipeline"):
            result = deepl_service.translate_segments(
                deepl_client=client,
                texts=["  Alpha \\& Beta  ".replace("\\\\", "\\")],
                source_lang="FR",
                target_lang="EN",
            )

        self.assertEqual(result, ["  Alpha \\& Beta  ".replace("\\\\", "\\")])
        payloads, kwargs = client.calls[0]
        self.assertEqual(payloads, ["  Alpha & Beta  "])
        self.assertEqual(kwargs["target_lang"], "EN-US")

    def test_translate_segments_keeps_inline_macros_in_payload(self) -> None:
        client = FakeDeepLClient([r"\textbf{Quantum}"])
        with patch("cv_translator.deepl_service.print_translation_pipeline"):
            deepl_service.translate_segments(
                deepl_client=client,
                texts=[r"\textbf{Quantique}".replace("\\\\", "\\")],
                source_lang="FR",
                target_lang="EN-US",
            )

        payloads, _kwargs = client.calls[0]
        self.assertEqual(payloads, [r"\textbf{Quantique}".replace("\\\\", "\\")])


if __name__ == "__main__":
    unittest.main()
