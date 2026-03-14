# CV Translator CLI (LaTeX + DeepL)

A command-line application to translate a LaTeX CV into multiple languages with DeepL.

DeepL can be used for free as long as you stay within the Free API quota (500,000 characters per month).
Rough equivalence: this is typically around 80 to 150 full CV translations, depending on CV length.
For example, with a CV around 3,500 to 6,000 characters, 500,000 characters gives about 140 to 83 translations.

On first launch, the app initializes a base CV from [template.tex](template.tex), then applies incremental translations:
- only new or modified text in the source language is translated again;
- manual edits already present in target files are preserved as long as the source segment did not change.

## Features

- First-run wizard to choose the main language (native language).
- Source CV creation as `cv_xx.tex` inside a language folder under [cv](cv) (examples: [cv/fr/cv_fr.tex](cv/fr/cv_fr.tex), [cv/en-us/cv_en-us.tex](cv/en-us/cv_en-us.tex)).
- Generated CV files are stored in [cv](cv), one subfolder per language.
- Translation of all text segments extracted from the LaTeX document.
- Non-destructive incremental translation per target language.
- Language list loaded from DeepL API (with local fallback if API is unavailable).
- Arrow-key navigation in the main menu.
- Persistent configuration in `.cv_config.json` (generated automatically).
- Synchronization index in `.cv_translation_index.json` (generated automatically).

## Prerequisites

- Python 3.10+
- A [DeepL API account and API key](https://www.deepl.com/en/pro#developer) (Free or Pro)

## Installation

1. Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create an [.env](.env) file at the project root.

```env
DEEPL_API_KEY=your_deepl_api_key_here
```

4. Test that the DeepL API key works.

```bash
python scripts/deepl_api_key_test.py
```

If the API key is valid, the script should print a translated sample.

## Run

```bash
python main.py
```

## First Launch

At first startup, the app:
- asks for the main CV language;
- reads [template.tex](template.tex);
- creates the corresponding source file in [cv](cv) (for example [cv/fr/cv_fr.tex](cv/fr/cv_fr.tex));
- if the main language is not FR, translates the template into that language;
- saves configuration in `.cv_config.json`.

## Daily Usage

Main menu:
- use arrow keys to select:
- `Translate CV to another language`
- `Show configuration`
- `Quit`

Language selection:
- type a language code shown in the list (for example `FR`, `DE`, `EN-US`, `PT-BR`).
- type `CANCEL` to stop target-language selection.

When you choose a target language:
- the tool compares previous and current source CV states;
- it translates only new or modified segments;
- it rebuilds the target file without retranslating unchanged segments;
- it updates `.cv_translation_index.json`.

## Important Files

- [main.py](main.py): thin entrypoint.
- [template.tex](template.tex): CV template used on first launch.
- [requirements.txt](requirements.txt): Python dependencies.
- [.env](.env): DeepL API key.
- `.cv_config.json`: source language and source file (generated).
- `.cv_translation_index.json`: incremental tracking per target language (generated).

## Project Structure

The codebase is organized as a Python package for better maintainability:

```text
translation-code/
├── main.py
├── template.tex
├── requirements.txt
├── README.md
├── scripts/
│   └── deepl_api_key_test.py
├── src/
│   └── cv_translator/
│       ├── __init__.py
│       ├── cli.py
│       ├── workflow.py
│       ├── ui.py
│       ├── deepl_service.py
│       ├── latex.py
│       ├── storage.py
│       ├── constants.py
│       ├── models.py
│       └── debug.py
├── test/
│   ├── test_latex.py
│   ├── test_deepl_service.py
│   ├── test_storage.py
│   └── test_workflow.py
└── cv/
	├── fr/
	│   └── cv_fr.tex
	└── en-us/
		└── cv_en-us.tex
```

Structure overview:

- `src/cv_translator/`: application source code.
- `test/`: regression tests for parsing, DeepL integration helpers, storage, and workflow behavior.
- `scripts/`: manual utility scripts, such as checking that the DeepL API key works.
- `cv/`: generated CV files, one folder per language.
- root files: entrypoint, template, dependencies, and documentation.

- [main.py](main.py): thin entrypoint.
- [src/cv_translator/cli.py](src/cv_translator/cli.py): app loop and top-level exception handling.
- [src/cv_translator/workflow.py](src/cv_translator/workflow.py): first-run setup and incremental translation workflow.
- [src/cv_translator/ui.py](src/cv_translator/ui.py): terminal interactions (language input and arrow-key menu).
- [src/cv_translator/deepl_service.py](src/cv_translator/deepl_service.py): DeepL client and language APIs.
- [src/cv_translator/latex.py](src/cv_translator/latex.py): LaTeX segment extraction and text stitching.
- [src/cv_translator/storage.py](src/cv_translator/storage.py): JSON persistence and generated file paths.
- [src/cv_translator/constants.py](src/cv_translator/constants.py): centralized paths and language constants.
- [src/cv_translator/models.py](src/cv_translator/models.py): data models.

## Notes DeepL

- Some DeepL languages require specific variants.
- Language options are requested from DeepL API at runtime.
- Internal alias mapping converts `EN` to `EN-US`.
- Internal alias mapping converts `PT` to `PT-PT`.

## Known Limitations

- The tool preserves manual edits in a target language file as long as source segments in the native language file remain unchanged.
- If LaTeX structure is heavily edited manually in a target file, reconstruction differences may appear.
- LaTeX comments (`% ...`) are not translated.

## Troubleshooting

- Error `DEEPL_API_KEY is missing`: check that [.env](.env) exists and contains `DEEPL_API_KEY`.
- DeepL API error: verify that your API key is valid and active.
- No changes after translation: this is expected if the source CV was not modified.
- Reset from scratch: delete `.cv_config.json`, `.cv_translation_index.json`, and generated files inside [cv](cv), then run [main.py](main.py) again.

## Useful Commands

Quick script compilation:

```bash
python -m py_compile main.py
```

Simple DeepL API key test:

```bash
python scripts/deepl_api_key_test.py
```

Run the regression test suite:

```bash
python3 -m unittest discover -s test -v
```

## Finish your setup

Once translation is generated, you can compile the output `.tex` files from the language subfolders inside [cv](cv).

Recommended local workflow:
- Use the [LaTeX Workshop](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop) extension in VS Code.
- Open the relevant language folder in [cv](cv), then build the target file (for example [cv/fr/cv_fr.tex](cv/fr/cv_fr.tex)).

Terminal alternative:

```bash
cd cv/fr
pdflatex -interaction=nonstopmode -halt-on-error cv_fr.tex
```

Online alternative:
- Upload the generated `.tex` file (and required assets) to [Overleaf](https://www.overleaf.com).