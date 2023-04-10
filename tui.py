import os
import sys

import toml
from github_api import get_repo_details
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from generate_list import save_to_markdown


def display_welcome_message():
    console.print(
        Panel.fit(
            "[bold magenta]Welcome to the Awesome GitHub Repos Finder![/bold magenta]"
        )
    )


def display_keywords(title="Search keywords"):
    table = Table(show_header=False, header_style="none", title=title)
    table.add_column("", style="cyan")
    table.add_column("", style="cyan")
    keywords = []
    for keyword in config["README_KEYWORDS"]:
        keywords.append(keyword)
    table.add_row("keywords", ", ".join(keywords))
    console.print(table)


def prompt_gen_mkdown():
    user_input = Prompt.ask(
        "\nGenerate a markdown file to showcase the Awesome projects you identified?(yes or y):"
        + " [bold green]>[/bold green] "
    )
    if user_input.strip().lower() != "yes" and user_input.strip().lower() != "y":
        print(f"user input is {user_input}")
        return False
    else:
        return True


def prompt_for_keywords():
    user_input = Prompt.ask(
        "\nPress enter to use the default keywords, or enter a comma-separated list of keywords to search for:"
        + " [bold green]>[/bold green] "
    )
    return (
        [keyword.strip() for keyword in user_input.split(",")] if user_input else None
    )


def update_toml_config(keywords):
    config["README_KEYWORDS"] = keywords
    with open("awesome.toml", "w") as toml_file:
        toml.dump(config, toml_file)


def display_updated_keywords():
    table = Table(title="Updated Keywords")
    table.add_column("Keyword", justify="center", style="cyan")
    for keyword in config["README_KEYWORDS"]:
        table.add_row(keyword)
    console.print(table)


if __name__ == "__main__":
    console = Console()
    config_path = "awesome.toml"
    try:
        if os.path.exists(config_path):
            config = toml.load(config_path)
            display_welcome_message()
            display_keywords("default search keywords")
            new_keywords = prompt_for_keywords()
            if new_keywords:
                update_toml_config(new_keywords)
                display_keywords("new search keywords")
        else:
            with open(config_path, "w") as fh:
                pass
            display_welcome_message()
            new_keywords = prompt_for_keywords()
            if new_keywords:
                update_toml_config(new_keywords)
                display_keywords()
        from main import main

        fname = main()
        if fname is not None:
            console.print(f"Info on the 'Awesome repos' saved to {fname}", style="cyan")
        if prompt_gen_mkdown():
            mkdown_fname = save_to_markdown(fname)
            console.print(
                f"Markdown file generated successfully and saved to {mkdown_fname}",
                style="cyan",
            )
            console.print("Generated AwesomeList.md is: ")
            with open(mkdown_fname, "r") as mkdfh:
                mkdwn_text = mkdfh.read()
            mkdwn = Markdown(mkdwn_text, style="default")
            console.print(mkdwn)
    except KeyboardInterrupt:
        console.print("\nKeyboard interrupt detected. Exiting program...", style="cyan")
        sys.exit(0)
