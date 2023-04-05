import json
import sys
import time

from github import Github

from suppress_warnings import *
from config import README_KEYWORDS
from config import PROGRESS_FILE
from repo import RepoAnalyzer
from utils import create_dir
from utils import print
from ghub_process import process_readme_keywords
from ghub_process import save_results_to_db
from utils import is_relevant_context
from summary import generate_summary as summary
from utils import classify_readme



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


def fetch_and_save(gh_fetcher, last_keyword, last_page, filename):
    process_all = False if last_keyword else True
    if README_KEYWORDS is None:
        print("No keywords found in awesome.toml, exiting...")
        sys.exit(0)
    #create_database_table()
    for kw in set(README_KEYWORDS):
        
        if kw == last_keyword:
            readme_filtered_repos = process_readme_keywords(
                gh_fetcher=gh_fetcher, keyword=kw, start_page=last_page
            )
            process_all = True
        elif process_all:
            readme_filtered_repos = process_readme_keywords(
                gh_fetcher=gh_fetcher, keyword=kw
            )
        else:
            continue 
        save_results_to_db(readme_filtered_repos)


def main():
    _check_env()
    gh = Github(os.environ["GTOKEN"])
    analyzer = RepoAnalyzer(gh)
    dir_path = create_dir("./results")
    fname = f"filtered_readme_repos_{time.strftime('%Y%m%d-%H%M%S')}.csv"
    filename = os.path.join(dir_path, fname)
    last_keyword = None
    try:
        last_keyword, last_page = _get_progress_info()
        fetch_and_save(analyzer, last_keyword, last_page, filename)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Exiting program.")
        sys.exit(0)
    return filename


if __name__ == "__main__":
    main()
