import os

from github import Github
from rich import box
from rich.console import Console
from rich.table import Table


class RepoDetails:
    url: str = ""
    name: str = ""
    stars: int = 0
    pulls: int = 0
    open_issues: int = 0
    closed_issues: int = 0
    summary: str = ""
    readme: str = ""
    languages: str = ""
    forks: int = 0
    topics: list[str] = []


def get_repo_details(url):
    """Get the details of a repo

    Args:
        gh (Github): Github object
        repo (Repository): Repository object

    """
    gh = Github(os.environ["GTOKEN"])
    print(f"repo: {url.split('/')[-2] + '/' + url.split('/')[-1]}")
    repo = gh.get_repo(url.split("/")[-2] + "/" + url.split("/")[-1])
    repo_details = RepoDetails()
    repo_details.url = repo.html_url
    repo_details.name = repo.name
    repo_details.stars = repo.stargazers_count
    repo_details.pulls = repo.get_pulls(state="all").totalCount
    repo_details.open_issues = repo.get_issues(state="open").totalCount
    repo_details.closed_issues = repo.get_issues(state="closed").totalCount
    repo_details.summary = repo.description
    repo_details.readme = repo.get_readme().decoded_content.decode("utf-8")
    repo_details.topics = repo.get_topics()
    repo_details.languages = "| ".join(
        [f"{k} ({v})" for k, v in repo.get_languages().items()]
    )
    return repo_details


def print_rich_repo_details(repo_details):
    """Print the details of a repo using rich package in the format:
    Name: <name>
    url: <url>
    summary: <summary>

    start: <stars>             open issues: <open_issues>           languages: <languages>
    pulls: <pulls>             closed issues: <closed_issues>       forks: <forks>

    Args:
        repo_details (RepoDetails): RepoDetails object

    """
    console = Console()
    table = Table(title="Repo Details", header_style="", show_header=False)
    table.add_row("Name:", repo_details.name)
    table.add_row("url:", repo_details.url)
    table.add_row("summary:", repo_details.summary)
    table2 = Table(box=box.SIMPLE, header_style="", show_header=False)
    table2.add_row(
        "stars:",
        str(repo_details.stars),
        "open issues:",
        str(repo_details.open_issues),
        "languages:",
        repo_details.languages,
    )
    table2.add_row(
        "pulls:",
        str(repo_details.pulls),
        "closed issues:",
        str(repo_details.closed_issues),
        "forks:",
        str(repo_details.forks),
    )
    console.print(table)
    console.print(table2)


import random

from github import Github, InputFileContent


def create_gist_from_file(markdown_file_path):
    # Authenticate with GitHub using the provided access token
    github = Github(os.environ["GTOKEN"])

    # Read the contents of the Markdown file
    with open(markdown_file_path, "r") as f:
        markdown_contents = f.read()

    # Generate a random filename for the Gist
    random_filename = f"file_{random.randint(100000, 999999)}.md"

    # Create the Gist payload
    gist_payload = {random_filename: InputFileContent(markdown_contents)}

    try:
        # Create the Gist using the PyGithub library
        gist = github.get_user().create_gist(public=True, files=gist_payload)

        # Get the URL of the new Gist
        gist_url = gist.html_url

        return gist_url

    except Exception as e:
        print(f"Error creating Gist: {e}")
        return None


if __name__ == "__main__":
    repo_details = get_repo_details("https://github.com/psf/black")
    print_rich_repo_details(repo_details)
