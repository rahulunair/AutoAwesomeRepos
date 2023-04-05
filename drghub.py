import os
import sys
import toml
from typing import Optional, List
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.markdown import Markdown

from file_utils import save_to_markdown
from ghub_api import get_repo_details
from ghub_api import print_rich_repo_details
from ghub_api import create_gist_from_file

app = typer.Typer()

config_path = "awesome.toml"
console = Console()

config_path = "awesome.toml"
config = {}

if os.path.exists(config_path):
    config = toml.load(config_path)


def load_config():
    if os.path.exists(config_path):
        return toml.load(config_path)
    else:
        with open(config_path, "w") as fh:
            pass
        return {}


def save_config(config):
    with open(config_path, "w") as toml_file:
        toml.dump(config, toml_file)


def display_welcome_message():
    console.print(
        Panel.fit(
            "[bold magenta]Welcome to the Awesome GitHub Repos Finder![/bold magenta]"
        )
    )


def display_keywords(title: str = "Search keywords"):
    table = Table(show_header=False, header_style="none", title=title)
    table.add_column("", style="cyan")
    table.add_column("", style="cyan")
    keywords = []
    for keyword in config["README_KEYWORDS"]:
        keywords.append(keyword)
    table.add_row("keywords", ", ".join(keywords))
    console.print(table)


def prompt_gen_mkdown() -> bool:
    user_input = Prompt.ask(
        "\nGenerate a markdown file to showcase the Awesome projects you identified?(yes or y):"
        + " [bold green]>[/bold green] "
    )
    return user_input.strip().lower() in ["yes", "y"]


def prompt_gen_gist() -> bool:
    user_input = Prompt.ask(
        "\nCreate a github gist to showcase the Awesome projects you identified to the public?(yes or y):"
        + " [bold green]>[/bold green] "
    )
    return user_input.strip().lower() in ["yes", "y"]


def prompt_for_keywords() -> Optional[List[str]]:
    user_input = Prompt.ask(
        "\nPress enter to use the default keywords, or enter a comma-separated list of keywords to search for:"
        + " [bold green]>[/bold green] "
    )
    return (
        [keyword.strip() for keyword in user_input.split(",")] if user_input else None
    )


def update_toml_config(keywords: Optional[list[str]]):
    if keywords:
        config["README_KEYWORDS"] = keywords
    with open("awesome.toml", "w") as toml_file:
        toml.dump(config, toml_file)


def display_updated_keywords():
    table = Table(title="Updated Keywords")
    table.add_column("Keyword", justify="center", style="cyan")
    for keyword in config["README_KEYWORDS"]:
        table.add_row(keyword)
    console.print(table)


@app.command()
def analyze_repo(repo_url: str):
    # TODO: Implement analyze_repo functionality
    console.print(f"Analyzing repo: {repo_url}")
    repo_details = get_repo_details(repo_url)
    print_rich_repo_details(repo_details)


def render_markdown_file(markdown_file_path):
    with open(markdown_file_path, "r") as f:
        markdown_contents = f.read()
    mkdwn = Markdown(markdown_contents, style="default")
    console.print(mkdwn)


def prompt_for_int(prompt_message: str, default_value: Optional[int]) -> Optional[int]:
    user_input = Prompt.ask(
        prompt_message
        + f" (Press enter to use default: {default_value}):"
        + " [bold green]>[/bold green] "
    )
    return int(user_input) if user_input else default_value


@app.command()
def gen_awesome_list(
    num_stars: Optional[int] = typer.Option(
        None, help="Minimum number of stars for a repository to be included"
    ),
    days_ago: Optional[int] = typer.Option(
        None, help="Number of days ago the repository should have a commit"
    ),
):
    try:
        display_welcome_message()

        new_keywords = prompt_for_keywords()
        update_toml_config(new_keywords)
        display_keywords("Search keywords")

        if num_stars is None:
            num_stars = config.get("NUM_STARS", 0)
            num_stars = prompt_for_int("Enter the minimum number of stars", num_stars)

        if days_ago is None:
            days_ago = config.get("DAYS_AGO", 0)
            days_ago = prompt_for_int(
                "Enter the minimum days since last commit", days_ago
            )

        console.print(f"Minimum number of stars: {num_stars}", style="cyan")
        console.print(f"Minimum days since last commit: {days_ago}", style="cyan")

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
            if prompt_gen_mkdown():
                console.print("Generated AwesomeList.md is: ")
                create_gist_from_file(mkdown_fname)
    except KeyboardInterrupt:
        console.print("\nKeyboard interrupt detected. Exiting program...", style="cyan")
        sys.exit(0)


if __name__ == "__main__":
    app()
