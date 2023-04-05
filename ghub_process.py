import sqlite3
import json
import base64
from dataclasses import dataclass
from datetime import timedelta
from datetime import datetime
from typing import List

from github import UnknownObjectException

from config import PROGRESS_FILE
from detect_license import LicenseParser
from utils import preprocess_text
import csv
from datetime import datetime
import random
import time
from collections import defaultdict

from github import RateLimitExceededException
from github import GithubException
from rich.progress import Progress

from config import DAYS_AGO
from config import NUM_STARS
from nrepo import ProcessedRepoDetails
from nrepo import RepoDetails
from nrepo import save_progress
from utils import preprocess_text
from utils import print
from typing import List
import sqlite3
import json



def wait_with_backoff(retries, max_retries, base_wait_time, backoff_factor):
    """Wait with backoff for a random time between 0 and 0.1 * (backoff_factor ** retries) seconds."""
    max_wait_time = 10
    if retries < max_retries:
        wait_time_with_jitter = (backoff_factor ** retries) * base_wait_time
        wait_time_with_jitter += random.uniform(0, 0.1 * (backoff_factor ** retries))
        wait_time_with_jitter = (
            wait_time_with_jitter
            if wait_time_with_jitter < max_wait_time
            else max_wait_time
        )
        print(f"Waiting {wait_time_with_jitter} seconds for retry.")
        time.sleep(wait_time_with_jitter)
        return True
    else:
        print("Max retries exceeded. Exiting.")
        return False
from pyrate_limiter import RequestRate, Limiter, Duration


def process_readme_keywords(
    gh_fetcher, keyword, start_page=0, max_retries=6
) -> List[ProcessedRepoDetails]:
    """Process the readme keywords and return a list of relevant repos"""
    i = 0
    filtered_repos = []
    processed_urls = {}  # Add a dictionary to keep track of processed URLs
    page = start_page
    break_no = 0  # if githubexception is raised, break if the value is > 0
    retries = 0
    backoff_factor = 2
    while True:
        try:
            gh_repos = gh_fetcher.search_repos_by_readme(
                keyword, NUM_STARS, DAYS_AGO, page
            )
            if not gh_repos:
                break
            with Progress() as progress:
                task = progress.add_task(
                    description=(
                        f"processing repos with keyword: '{keyword.center(35)}' on page '{page}'"
                        f" | {i:^3} repos processed"
                    ),
                    total=len(gh_repos),
                )

                for repo in gh_repos:
                    progress.update(task, advance=1)
                    i += 1
                    repo_url = repo.html_url
                    if repo_url in processed_urls:
                        # If the URL has already been processed, add the keyword to additional_keywords
                        processed_urls[repo_url].additional_keywords.append(keyword)
                    else:
                        repo_details = RepoDetails(repo)
                        repo_details.keyword = keyword
                        repo_details.additional_keywords = "" if processed_urls.get(repo_url) is None else "|".join(processed_urls[repo_url].additional_keywords)
                        repo_details.readme = preprocess_text(repo_details.readme)
                        filtered_repos.append(repo_details)
                        processed_urls[
                            repo_url
                        ] = repo_details  # Add the URL to the processed_urls dictionary
                        progress.update(
                            task,
                            description=(
                                f"processing repos with keyword: '{keyword.center(35)}' on page '{page}'"
                                f" | {i:^3} repos processed"
                            ),
                        )
                        save_progress(keyword, page)
            page += 1
        except RateLimitExceededException as e:
            print("rate limit exeeded, time to reset: ", e.reset")
            save_progress(keyword, page)
            #reset_time = datetime.fromtimestamp(e.reset)  # type: ignore
            #wait_time = (reset_time - datetime.now()).seconds
            #if not wait_with_backoff(retries, max_retries, wait_time, backoff_factor):
            #    break
            #retries += 1
        except GithubException as e:
            print(
                f"An error occurred while processing the keyword '{keyword}' on page {page}: {e}"
            )
            save_progress(keyword, page)
            if break_no == 0:
                break_no = 1
                continue
            else:
                break
    return filtered_repos

