import base64
import json
import os
import time
from datetime import datetime
from datetime import timedelta

from github import Github
from github import RateLimitExceededException
from tqdm import tqdm

from summary import generate_summary as summary
from utils import is_relevant_context
from utils import preprocess_text
from utils import create_dir
from config import PROGRESS_FILE
from config import README_KEYWORDS
from config import NUM_STARS
from config import DAYS_AGO

SLEEP_TIME = 1


class RepoAnalyzer:
    def __init__(self, gh_instance):
        self.gh = gh_instance

    def search_repos_by_readme(self, keyword, num_stars, days_ago, page):
        query = f'"{keyword}" in:readme stars:>={num_stars} pushed:{(datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")}..*'
        return self.gh.search_repositories(
            query=query, sort="updated", order="desc"
        ).get_page(page)

    def get_repo_readme_content(self, repo):
        readme = repo.get_readme()
        if readme is not None:
            return preprocess_text(
                base64.b64decode(readme.content).decode("utf-8").lower()
            )
        else:
            return "no readme found"

    def get_repo_license(self, repo):
        if repo.get_license():
            return repo.get_license().key
        else:
            return "No License"


class RepoInfo:
    def __init__(self, repo, repo_license, keyword, is_relevant, readme, brief_desc):
        self.repo = repo
        self.repo_license = repo_license
        self.keyword = keyword
        self.is_relevant = is_relevant
        self.readme = readme
        self.brief_desc = brief_desc


def save_progress(keyword, page):
    progress_data = {"keyword": keyword, "last_page": page}
    with open(PROGRESS_FILE, "w") as progress_file:
        json.dump(progress_data, progress_file)


def process_readme_keywords(analyzer, keyword, start_page=0):
    i = 0
    filtered_repos = []
    page = start_page
    while True:
        try:
            search_results = analyzer.search_repos_by_readme(
                keyword, NUM_STARS, DAYS_AGO, page
            )
            if not search_results:
                print(f"no github repos found for {keyword}")
                break
            for repo in tqdm(
                search_results,
                desc=f"processing repos with keyword: '{keyword}' on page '{page}'...",
            ):
                i += 1
                repo_license = analyzer.get_repo_license(repo)
                readme_content = analyzer.get_repo_readme_content(repo)
                is_relevant = is_relevant_context(readme_content, keyword)
                brief_desc = preprocess_text(summary(readme_content))
                repo_info = RepoInfo(
                    repo, repo_license, keyword, is_relevant, readme_content, brief_desc
                )
                filtered_repos.append(repo_info)
                save_progress(keyword, page)
            page += 1
        except RateLimitExceededException as e:
            save_progress(keyword, page)
            reset_time = datetime.fromtimestamp(e.reset)
            wait_time = (reset_time - datetime.now()).seconds
            print(f"Rate limit exceeded. Waiting {wait_time} seconds for reset.")
            time.sleep(wait_time)
        except:
            break
    print(f"{i} repos with {keyword} processed")
    return filtered_repos


def save_results_to_file(repos, filename):
    with open(filename, "a") as f:
        for repo_info in repos:
            repo = repo_info.repo
            repo_url = repo.html_url
            repo_license = repo_info.repo_license
            star_count = repo.stargazers_count
            last_push = repo.pushed_at
            is_forked = repo.fork
            keyword = repo_info.keyword
            is_relevant = repo_info.is_relevant
            readme = repo_info.readme
            brief_desc = repo_info.brief_desc
            f.write(
                f"{repo_url},{repo_license},{star_count},{last_push},{is_forked},{keyword},{is_relevant},{readme},{brief_desc}\n"
            )


def main():
    gh = Github(os.environ["GTOKEN"])
    analyzer = RepoAnalyzer(gh)
    dir_path = create_dir("./repo_lists")
    fname = f"filtered_readme_repos_{time.strftime('%Y%m%d-%H%M%S')}.csv"
    filename = os.path.join(dir_path, fname)
    last_keyword = None
    last_page = None

    with open(filename, "w") as f:
        f.write(
            "repo_url,license,num_stars,last_push,is_forked,keyword,is_relevant,readme,brief_desc\n"
        )
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as progress_file:
            progress_data = json.load(progress_file)
            last_keyword = progress_data["keyword"]
            last_page = progress_data["last_page"]
    resume = last_keyword is None

    for kw in README_KEYWORDS:
        if last_keyword == kw:
            readme_filtered_repos = process_readme_keywords(analyzer, kw, last_page)
        elif not resume:
            continue
        else:
            readme_filtered_repos = process_readme_keywords(analyzer, kw)
        save_results_to_file(readme_filtered_repos, filename)
        time.sleep(SLEEP_TIME)


if __name__ == "__main__":
    main()
