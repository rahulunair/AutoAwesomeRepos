import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from generate_list import export as export_to_markdown
from gh_fetch_save import fetch
from sql_utils import process

import torch
import intel_extension_for_pytorch

app = typer.Typer()
console = Console()


def display_welcome_message():
    console.print(
        Panel.fit(
            "[bold magenta]Welcome to the Awesome GitHub Repos Finder![/bold magenta]"
        )
    )


def prompt_continue(message: str) -> bool:
    user_input = Prompt.ask(f"\n{message}(yes or y): [bold green]>[/bold green] ")
    return user_input.strip().lower() in ["yes", "y"]


@app.command()
def generate_list():
    display_welcome_message()
    if prompt_continue("Fetch repos based on awesome.toml?"):
        fetch()
        console.print("Repositories fetched successfully.", style="cyan")
    if prompt_continue("Process the fetched repos?"):
        process()
        console.print("Repositories processed successfully.", style="cyan")
    if prompt_continue("Export the processed repos to AwesomeList.md?"):
        export_to_markdown()
        console.print("AwesomeList.md generated successfully.", style="cyan")


def main():
    app()


if __name__ == "__main__":
    main()
