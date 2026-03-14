import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cv_translator import storage


class StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cv_dir = self.temp_dir / "cv"

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir)

    def test_build_cv_filename_uses_language_subdirectory(self) -> None:
        with patch("cv_translator.storage.CV_DIR", self.cv_dir):
            path = storage.build_cv_filename("EN-US")

        self.assertEqual(path, self.cv_dir / "en-us" / "cv_en-us.tex")
        self.assertTrue((self.cv_dir / "en-us").exists())

    def test_resolve_configured_cv_path_finds_nested_language_file(self) -> None:
        nested = self.cv_dir / "fr" / "cv_fr.tex"
        nested.parent.mkdir(parents=True)
        nested.write_text("content", encoding="utf-8")

        with patch("cv_translator.storage.ROOT", self.temp_dir), patch(
            "cv_translator.storage.CV_DIR", self.cv_dir
        ):
            resolved = storage.resolve_configured_cv_path("cv_fr.tex")

        self.assertEqual(resolved, nested)


if __name__ == "__main__":
    unittest.main()
