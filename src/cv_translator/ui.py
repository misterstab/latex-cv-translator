import sys

from .deepl_service import get_available_languages, normalize_target_code

try:
    import questionary
except ImportError:
    questionary = None


def choose_language_by_kind(
    prompt: str,
    allow_skip: bool = False,
    kind: str = "target",
) -> str | None:
    """Prompt the user to select a valid language code for source or target."""

    languages = get_available_languages(kind=kind)

    print(f"\n{prompt}")
    sorted_languages = sorted(languages.items(), key=lambda item: item[0])
    for code, name in sorted_languages:
        print(f"- {code:<2} : {name}")

    if allow_skip:
        print("- CANCEL : cancel language selection")

    input_label = "Native language code: " if kind == "source" else "Language code: "

    while True:
        raw = input(input_label).strip().upper()
        if allow_skip and raw == "CANCEL":
            return None

        if kind == "target":
            raw = normalize_target_code(raw)

        if raw in languages:
            return raw

        print("Please enter a valid language code from the list.")


def choose_main_menu_action() -> str:
    """Return the main menu action code selected by the user."""

    options = [
        "Translate CV to another language",
        "Show configuration",
        "Quit",
    ]

    if questionary is not None:
        action = questionary.select(
            "Main menu",
            choices=options,
            use_shortcuts=False,
        ).ask()

        if action == "Translate CV to another language":
            return "1"
        if action == "Show configuration":
            return "2"
        return "3"

    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            import curses
        except ImportError:
            curses = None

        if curses is not None:
            def _run_menu(stdscr: "curses.window") -> str:
                """Render and control the fallback curses-based main menu."""

                curses.curs_set(0)
                selected = 0

                while True:
                    stdscr.erase()
                    stdscr.addstr(0, 0, "Main menu (use UP/DOWN and ENTER)")

                    for idx, option in enumerate(options):
                        prefix = "> " if idx == selected else "  "
                        line = f"{prefix}{option}"
                        if idx == selected:
                            stdscr.addstr(idx + 2, 0, line, curses.A_REVERSE)
                        else:
                            stdscr.addstr(idx + 2, 0, line)

                    key = stdscr.getch()
                    if key in (curses.KEY_UP, ord("k")):
                        selected = (selected - 1) % len(options)
                    elif key in (curses.KEY_DOWN, ord("j")):
                        selected = (selected + 1) % len(options)
                    elif key in (10, 13, curses.KEY_ENTER):
                        return str(selected + 1)

            try:
                return curses.wrapper(_run_menu)
            except curses.error:
                pass

    print("\nMain menu")
    print("1. Translate CV to another language")
    print("2. Show configuration")
    print("3. Quit")
    return input("Choice: ").strip()
