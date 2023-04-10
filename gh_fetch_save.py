import json
import sys

from github import Github

from config import DAYS_AGO, NUM_STARS, PROGRESS_FILE, README_KEYWORDS
from gh_process import RepoProcessor
from sql_utils import reset_repo_info, save_results_to_db
from suppress_warnings import *
from utils import create_dir, print


def _check_env():
    try:
        os.environ["OPENAI_API_KEY"]
    except KeyError:
        print(
            "\nExport 'OPENAI_API_KEY=<openai_api_key>' to your environment, to use openai emebddings."
        )
    try:
        os.environ["GTOKEN"]
    except KeyError:
        print(
            "\nExport 'GTOKEN=<github_token>' to your environment, it is a prerequisite to continue, exiting..."
        )
        sys.exit(0)


def _get_progress_info():
    last_keyword, last_page = None, None
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as progress_file:
            progress_data = json.load(progress_file)
            last_keyword = progress_data["keyword"]
            last_page = progress_data["last_page"]
    return last_keyword, last_page


def fetch_and_save(gh_instance, last_keyword, last_page):
    reset_repo_info()  # Reset the repo_details table before saving new data
    process_all = False if last_keyword else True
    if README_KEYWORDS is None:
        print("No keywords found in awesome.toml, exiting...")
        sys.exit(0)
    for kw in set(README_KEYWORDS):
        if kw == last_keyword:
            processor = RepoProcessor(gh_instance, kw, start_page=last_page)
            process_all = True
        elif process_all:
            processor = RepoProcessor(gh_instance, kw)
        else:
            continue
        filtered_repos = processor.fetch_filtered_repos()
        save_results_to_db(filtered_repos, NUM_STARS, DAYS_AGO)


def fetch():
    _check_env()
    gh_instance = Github(os.environ["GTOKEN"])
    dir_path = create_dir("./results")
    try:
        fetch_and_save(gh_instance, *_get_progress_info())
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Exiting program.")
        sys.exit(0)


if __name__ == "__main__":
    fetch()
