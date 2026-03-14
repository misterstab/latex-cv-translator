import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cv_translator.latex import extract_translatable_segments


class LatexParserTests(unittest.TestCase):
    def test_escaped_ampersand_stays_in_single_segment(self) -> None:
        segments = extract_translatable_segments(r"Logiciels \& programmation")
        self.assertEqual([segment.text for segment in segments], [r"Logiciels \& programmation"])

    def test_unescaped_ampersand_splits_segments(self) -> None:
        segments = extract_translatable_segments("A & B")
        self.assertEqual([segment.text for segment in segments], ["A ", " B"])

    def test_inline_text_command_stays_in_segment(self) -> None:
        segments = extract_translatable_segments(
            r"Élève-ingénieur en 2\textsuperscript{ème} année à CentraleSupélec".replace("\\\\", "\\")
        )
        self.assertEqual(len(segments), 1)
        self.assertEqual(
            segments[0].text,
            r"Élève-ingénieur en 2\textsuperscript{ème} année à CentraleSupélec".replace("\\\\", "\\"),
        )

    def test_begin_arguments_are_ignored(self) -> None:
        content = "\\begin{minipage}[t]{0.23\\textwidth}\n\\section*{Langues}\n"
        segments = extract_translatable_segments(content)
        self.assertEqual([segment.text for segment in segments], ["Langues"])

    def test_href_arguments_are_ignored(self) -> None:
        content = "\\href{mailto:test@example.com}{test@example.com}"
        segments = extract_translatable_segments(content)
        self.assertEqual(segments, [])

    def test_vspace_and_hspace_arguments_are_ignored(self) -> None:
        content = "\\vspace{0.3cm}\nTexte utile\n\\hspace{1em}\n"
        segments = extract_translatable_segments(content)
        self.assertEqual([segment.text for segment in segments], ["Texte utile\n"])


if __name__ == "__main__":
    unittest.main()
