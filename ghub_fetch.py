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
from repo import RepoInfo
from repo import RepoDetails
from repo import save_progress
from summary import generate_summary as summary
from utils import classify_readme
from utils import preprocess_text
from utils import print
from utils import is_relevant_context
from typing import List


def wait_with_backoff(retries, max_retries, base_wait_time, backoff_factor):
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


def process_readme_keywords(
    gh_fetcher, keyword, start_page=0, max_retries=6
) -> List[RepoInfo]:
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
                        repo_license = repo_details.license
                        readme_content = preprocess_text(repo_details.readme)
                        is_relevant = is_relevant_context(readme_content, keyword)
                        brief_desc = summary(readme_content, use_openai=True)
                        topic = classify_readme(
                            readme=readme_content,
                            readme_summary=brief_desc,
                            use_openai=True,
                        )

                        repo_info = RepoInfo(
                            topic=topic,
                            repo=repo,
                            license=repo_license,
                            keyword=keyword,
                            is_relevant=is_relevant,
                            readme=readme_content,
                            brief_desc=brief_desc,
                            languages=repo_details.languages,
                            open_issues=repo_details.open_issues,
                            closed_issues=repo_details.closed_issues,
                            topics=repo_details.topics,
                        )  # type: ignore
                        filtered_repos.append(repo_info)
                        processed_urls[
                            repo_url
                        ] = repo_info  # Add the URL to the processed_urls dictionary
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
            save_progress(keyword, page)
            reset_time = datetime.fromtimestamp(e.reset)  # type: ignore
            wait_time = (reset_time - datetime.now()).seconds
            if not wait_with_backoff(retries, max_retries, wait_time, backoff_factor):
                break
            retries += 1
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


def save_results_to_file(repos, filename):
    with open(filename, "a") as csvf:
        csvf = csv.writer(csvf)
        for repo_info in repos:
            repo = repo_info.repo
            repo_url = repo.html_url
            repo_license = repo_info.license
            star_count = repo.stargazers_count
            fork_count = repo.forks_count
            last_push = repo.pushed_at
            languages = repo_info.languages
            keyword = repo_info.keyword
            topics = repo_info.topics
            is_relevant = repo_info.is_relevant
            readme = preprocess_text(repo_info.readme)
            brief_desc = repo_info.brief_desc
            topic = repo_info.topic
            additional_keywords = ",".join(
                repo_info.additional_keywords
            )  # Combine additional keywords into a single string
            csvf.writerow(
                [
                    repo_url,
                    repo_license,
                    star_count,
                    fork_count,
                    last_push,
                    languages,
                    topics,
                    keyword,
                    is_relevant,
                    readme,
                    brief_desc,
                    topic,
                    additional_keywords,
                ]
            )
