from .ui import choose_main_menu_action
from .workflow import load_or_create_config, show_config, translate_incremental


def run() -> None:
    """Run the interactive application loop."""

    config = load_or_create_config()

    while True:
        choice = choose_main_menu_action()
        if choice == "1":
            try:
                translate_incremental(config)
            except Exception as exc:
                print(f"Translation failed: {exc}")
        elif choice == "2":
            show_config(config)
        elif choice == "3":
            print("Bye")
            return
        else:
            print("Invalid option.")


def main() -> None:
    """Application entrypoint with top-level error handling."""

    try:
        run()
    except Exception as exc:
        print(f"Startup error: {exc}")
