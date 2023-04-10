from datetime import datetime, timedelta

from github import GithubException, RateLimitExceededException
from pyrate_limiter import Duration, Limiter, RequestRate
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.text import Text

from config import DAYS_AGO, NUM_STARS
from repo_details import RepoDetails, save_progress
from utils import preprocess_text, print

hourly_rate = RequestRate(5000, Duration.HOUR)
limiter = Limiter(hourly_rate)


def progress_with_checkmark(progress):
    completed = progress.completed
    if completed < progress.total:
        return Text(" ", style="bold green")
    else:
        return Text("✔", style="bold green")


class RepoProcessor:
    def __init__(self, gh_instance, keyword, start_page=0, max_retries=6):
        self.gh = gh_instance
        self.keyword = keyword
        self.start_page = start_page
        self.max_retries = max_retries
        self.filtered_repos = []
        self.processed_urls = {}

        self.limiter = Limiter(
            RequestRate(30, Duration.MINUTE),
            RequestRate(1000, Duration.HOUR),
        )

    @limiter.ratelimit("github", delay=True)
    def search_repos_by_readme(self, keyword, num_stars, days_ago, page):
        query = f'"{keyword}" in:readme stars:>={num_stars} pushed:{(datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")}..*'
        return self.gh.search_repositories(
            query=query, sort="updated", order="desc"
        ).get_page(page)

    def _fetch_repo_details(self, repo):
        repo_url = repo.html_url
        if repo_url in self.processed_urls:
            pass
            # self.processed_urls[repo_url].additional_keywords.append(self.keyword)
        else:
            repo_details = RepoDetails(repo)
            repo_details.keyword = self.keyword
            repo_details.additional_keywords = (
                ""
                if self.processed_urls.get(repo_url) is None
                else "|".join(self.processed_urls[repo_url].additional_keywords)
            )
            repo_details.readme = preprocess_text(repo_details.readme)
            self.processed_urls[repo_url] = repo_details
            return repo_details

    def fetch_repos_details(self, gh_repos, task, progress, page):
        all_repos_details = []
        for repo in gh_repos:
            repo_details = self._fetch_repo_details(repo)
            if repo_details:
                all_repos_details.append(repo_details)
                progress.update(task, advance=1)
                progress.update(
                    task,
                    description=(
                        f"processing repos with keyword: '{self.keyword.center(35)}' on page '{page}'"
                        f" | {len(self.filtered_repos) + len(all_repos_details):^3} repos processed"
                    ),
                )

        return all_repos_details

    def fetch_filtered_repos(self):
        page = self.start_page
        break_no = 0
        while True:
            try:
                gh_repos = self.search_repos_by_readme(
                    self.keyword, NUM_STARS, DAYS_AGO, page
                )
                if not gh_repos:
                    break

                with Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(bar_width=5),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
                ) as progress:
                    task = progress.add_task(
                        description=(
                            f"processing repos with keyword: '{self.keyword.center(35)}' on page '{page}'"
                            f" | {len(self.filtered_repos):^3} repos processed"
                        ),
                        total=len(gh_repos),
                    )

                    filtered_repos_page = self.fetch_repos_details(
                        gh_repos, task, progress, page
                    )
                    self.filtered_repos.extend(filtered_repos_page)

                save_progress(self.keyword, page)
                page += 1
            except RateLimitExceededException as e:
                print("rate limit exceeded, time to reset:", e.reset)
                save_progress(self.keyword, page)
            except GithubException as e:
                print(
                    f"An error occurred while processing the keyword '{self.keyword}' on page {page}: {e}"
                )
                save_progress(self.keyword, page)
                if break_no == 0:
                    break_no = 1
                    continue
                else:
                    break
        return self.filtered_repos
