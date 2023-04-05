import base64
from dataclasses import dataclass
from dataclasses import field
from datetime import timedelta
from datetime import datetime
import json
from typing import List

from github import UnknownObjectException

from config import PROGRESS_FILE
from detect_license import LicenseParser
from utils import preprocess_text
from pyrate_limiter import RequestRate, Limiter, Duration

hourly_rate = RequestRate(5000, Duration.HOUR)
limiter = Limiter(hourly_rate)


class RepoAnalyzer:
    """Class to search for repos by readme content."""
    def __init__(self, gh_instance):
        self.gh = gh_instance

    @limiter.ratelimit("github", delay=True)
    def search_repos_by_readme(self, keyword, num_stars, days_ago, page):
        """Search for repos by readme content."""
        query = f'"{keyword}" in:readme stars:>={num_stars} pushed:{(datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")}..*'
        return self.gh.search_repositories(
            query=query, sort="updated", order="desc"
        ).get_page(page)


def save_progress(keyword, page):
    """Save the progress of the search."""
    progress_data = {"keyword": keyword, "last_page": page}
    with open(PROGRESS_FILE, "w") as progress_file:
        json.dump(progress_data, progress_file)

class RepoDetails:
    """Class to hold the details of a repo."""
    def __init__(self, repo):
        self.repo = repo
        self.languages = "| ".join(
        [f"{k} ({v})" for k, v in repo.get_languages().items()])
        self.topics = repo.get_topics()
        self.pulls = repo.get_pulls().totalCount
        self.open_issues = repo.get_issues(state="open").totalCount
        self.closed_issues = repo.get_issues(state="closed").totalCount
        self.license = self.get_repo_license()
        self.readme = self.get_repo_readme_content()
        self.id = repo.id
        self.url = repo.html_url
        self.name = repo.name
        self.full_name = repo.full_name
        self.owner = repo.owner
        self.private = repo.private
        self.description = repo.description
        self.fork = repo.fork
        self.created_at = repo.created_at
        self.updated_at = repo.updated_at
        self.pushed_at = repo.pushed_at
        self.homepage = repo.homepage
        self.size = repo.size
        self.stargazers_count = repo.stargazers_count
        self.watchers_count = repo.watchers_count
        self.language = repo.language
        self.forks_count = repo.forks_count
        self.open_issues = repo.open_issues_count
        self.closed_issues = repo.get_issues(state="closed").totalCount
        self.languages = repo.get_languages()
        self.readme = self.get_repo_readme_content()
        self.topics = repo.get_topics()
        self.num_pulls = repo.get_pulls().totalCount
        self.num_contributors = len(self.get_repo_contributors())

    def get_repo_license(self) -> str:
        """Get the license of the repo."""
        try:
            license_file = self.repo.get_license()
        except UnknownObjectException:
            return "Unknown License"
        return LicenseParser(license_file).parse()

    def get_repo_readme_content(self) -> str:
        """Get the content of the readme file in the repo."""
        readme = self.repo.get_readme()
        if readme is not None:
            return preprocess_text(
                base64.b64decode(readme.content).decode("utf-8").lower()
            )
        else:
            return "no readme found"

    def get_repo_contributors(self) -> List:
        """Get the list of contributors for the repo."""
        try:
            return list(self.repo.get_contributors())
        except UnknownObjectException:
            return []

    def __str__(self):
        """String representation of the RepoDetails object."""
        return (
            f"RepoDetails(id={self.id}, name={self.name}, url={self.url}, full_name={self.full_name}, "
            f"owner={self.owner}, private={self.private}, description={self.description}, "
            f"fork={self.fork}, created_at={self.created_at}, updated_at={self.updated_at}, "
            f"pushed_at={self.pushed_at}, homepage={self.homepage}, size={self.size}, "
            f"stargazers_count={self.stargazers_count}, watchers_count={self.watchers_count}, "
            f"language={self.language}, forks_count={self.forks_count}, "
            f"open_issues_count={self.open_issues})"
            f"languages={self.languages}, readme={self.readme}, topics={self.topics}, "
            f"num_pulls={self.num_pulls}, num_contributors={self.num_contributors})"

        )

    def __repr__(self):
        return self.__str__()


class RepoInfo:
    def __init__(
        self,
        topic,
        repo,
        license,
        keyword,
        is_relevant,
        readme,
        brief_desc,
        languages,
        topics,
        open_issues,
        closed_issues,
        forks_count,
        stargazers_count,
        watchers_count,
        size,
        homepage,
        pushed_at,
        updated_at,
        created_at,
        fork,
        description,
        private,
        owner,
        full_name,
        name,
        url,
        id,
    ):
        self.topic = topic
        self.repo = repo
        self.license = license
        self.keyword = keyword
        self.is_relevant = is_relevant
        self.readme = readme
        self.brief_desc = brief_desc
        self.additional_keywords = []
        self.languages = languages
        self.topics = topics
        self.open_issues = open_issues
        self.closed_issues = closed_issues
        self.owner = owner
        self.forks_count = forks_count
        self.stars_count = stargazers_count
        self.watchers_count = watchers_count
        self.size = size
        self.homepage = homepage
        self.pushed_at = pushed_at
        self.updated_at = updated_at
        self.created_at = created_at
        self.fork = fork
        self.description = description
        self.private = private
        self.full_name = full_name
        self.name = name
        self.url = url
        self.id = id



