import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
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

from cv_translator.models import Segment
from cv_translator import workflow


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.native_file = self.root / "cv_fr.tex"
        self.target_file = self.root / "cv_en-us.tex"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_translate_incremental_preserves_manual_segments_and_translates_only_new_content(self) -> None:
        self.native_file.write_text("SOURCE", encoding="utf-8")
        self.target_file.write_text("TARGET", encoding="utf-8")
        deepl_client = object()
        saved_states = []

        def fake_extract(content: str) -> list[Segment]:
            if content == "SOURCE":
                return [
                    Segment(0, 1, "existing-source"),
                    Segment(1, 2, "new-source"),
                ]
            if content == "TARGET":
                return [
                    Segment(0, 1, "manual-existing-translation"),
                    Segment(1, 2, "old-target-text"),
                ]
            raise AssertionError(f"Unexpected content: {content}")

        config = {"native_lang": "FR", "native_file": "cv/fr/cv_fr.tex"}
        index_state = {
            "version": 1,
            "languages": {
                "EN-US": {
                    "source_hashes": ["hash:existing-source"],
                    "engine_version": workflow.TRANSLATION_ENGINE_VERSION,
                }
            },
        }

        with patch("cv_translator.workflow.choose_language_by_kind", return_value="EN-US"), patch(
            "cv_translator.workflow.resolve_configured_cv_path", return_value=self.native_file
        ), patch("cv_translator.workflow.build_cv_filename", return_value=self.target_file), patch(
            "cv_translator.workflow.ROOT", self.root
        ), patch(
            "cv_translator.workflow.extract_translatable_segments", side_effect=fake_extract
        ), patch("cv_translator.workflow.hash_text", side_effect=lambda text: f"hash:{text}"), patch(
            "cv_translator.workflow.get_deepl_client", return_value=deepl_client
        ), patch(
            "cv_translator.workflow.translate_segments", return_value=["translated-new-content"]
        ) as translate_mock, patch(
            "cv_translator.workflow.stitch_content",
            side_effect=lambda _source, _segments, replacements: " || ".join(replacements),
        ), patch("cv_translator.workflow.load_json", return_value=index_state), patch(
            "cv_translator.workflow.save_json", side_effect=lambda _path, state: saved_states.append(state)
        ):
            workflow.translate_incremental(config)

        translate_mock.assert_called_once_with(
            deepl_client,
            ["new-source"],
            source_lang="FR",
            target_lang="EN-US",
        )
        self.assertEqual(
            self.target_file.read_text(encoding="utf-8"),
            "manual-existing-translation || translated-new-content",
        )
        self.assertEqual(
            saved_states[-1]["languages"]["EN-US"]["source_hashes"],
            ["hash:existing-source", "hash:new-source"],
        )

    def test_translate_incremental_retranslates_everything_when_engine_version_changes(self) -> None:
        self.native_file.write_text("SOURCE", encoding="utf-8")
        self.target_file.write_text("TARGET", encoding="utf-8")
        deepl_client = object()
        saved_states = []

        def fake_extract(content: str) -> list[Segment]:
            if content == "SOURCE":
                return [
                    Segment(0, 1, "existing-source"),
                    Segment(1, 2, "new-source"),
                ]
            if content == "TARGET":
                return [
                    Segment(0, 1, "manual-existing-translation"),
                    Segment(1, 2, "old-target-text"),
                ]
            raise AssertionError(f"Unexpected content: {content}")

        config = {"native_lang": "FR", "native_file": "cv/fr/cv_fr.tex"}
        index_state = {
            "version": 1,
            "languages": {
                "EN-US": {
                    "source_hashes": ["hash:existing-source"],
                    "engine_version": "outdated-engine-version",
                }
            },
        }

        with patch("cv_translator.workflow.choose_language_by_kind", return_value="EN-US"), patch(
            "cv_translator.workflow.resolve_configured_cv_path", return_value=self.native_file
        ), patch("cv_translator.workflow.build_cv_filename", return_value=self.target_file), patch(
            "cv_translator.workflow.ROOT", self.root
        ), patch(
            "cv_translator.workflow.extract_translatable_segments", side_effect=fake_extract
        ), patch("cv_translator.workflow.hash_text", side_effect=lambda text: f"hash:{text}"), patch(
            "cv_translator.workflow.get_deepl_client", return_value=deepl_client
        ), patch(
            "cv_translator.workflow.translate_segments",
            return_value=["translated-existing-content", "translated-new-content"],
        ) as translate_mock, patch(
            "cv_translator.workflow.stitch_content",
            side_effect=lambda _source, _segments, replacements: " || ".join(replacements),
        ), patch("cv_translator.workflow.load_json", return_value=index_state), patch(
            "cv_translator.workflow.save_json", side_effect=lambda _path, state: saved_states.append(state)
        ):
            workflow.translate_incremental(config)

        translate_mock.assert_called_once_with(
            deepl_client,
            ["existing-source", "new-source"],
            source_lang="FR",
            target_lang="EN-US",
        )
        self.assertEqual(
            self.target_file.read_text(encoding="utf-8"),
            "translated-existing-content || translated-new-content",
        )
        self.assertEqual(
            saved_states[-1]["languages"]["EN-US"]["engine_version"],
            workflow.TRANSLATION_ENGINE_VERSION,
        )


if __name__ == "__main__":
    unittest.main()