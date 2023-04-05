from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

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
import sqlite3

def save_progress(keyword, page):
    progress_data = {"keyword": keyword, "last_page": page}
    with open(PROGRESS_FILE, "w") as progress_file:
        json.dump(progress_data, progress_file)



class RepoDetails():
    """Class to hold the details of a repo"""

    def __init__(self, repo):
        self.repo = repo
        self.id = repo.id
        self.url = repo.html_url
        self.license = self.get_repo_license()
        self.readme = self.get_repo_readme_content()
        self.stars_count = repo.stargazers_count
        self.forks_count = repo.forks_count
        self.pushed_at = repo.pushed_at
        self.updated_at = repo.updated_at
        self.created_at = repo.created_at
        self.languages = "| ".join(
        [f"{k} ({v})" for k, v in repo.get_languages().items()])
        self.topics = repo.get_topics()
        self.open_issues = repo.get_issues(state="open").totalCount
        self.closed_issues = repo.get_issues(state="closed").totalCount   
        self.description = repo.description
        self.fork = 1 if repo.fork else 0
        self.size = repo.size  
        self.watchers_count = repo.watchers_count
        self.language = repo.language
        self.readme = self.get_repo_readme_content()


    def get_repo_license(self):
        """Get the license of the repo"""
        try:
            license_file = self.repo.get_license()
        except UnknownObjectException:
            return "Unknown License"
        return LicenseParser(license_file).parse()

    def get_repo_readme_content(self):
        """Get the readme content of the repo"""
        readme = self.repo.get_readme()
        if readme is not None:
            return preprocess_text(
                base64.b64decode(readme.content).decode("utf-8").lower()
            )
        else:
            return "no readme found"

    def get_repo_contributors(self):
        """Get the contributors of the repo"""
        try:
            return list(self.repo.get_contributors())
        except UnknownObjectException:
            return []

    def __str__(self):
        return (
            f"RepoDetails(id={self.id},url={self.url}, "
            f"description={self.description}, "
            f"fork={self.fork}, created_at={self.created_at}, updated_at={self.updated_at}, "
            f"pushed_at={self.pushed_at} size={self.size}, "
            f"stargazers_count={self.stars_count}, watchers_count={self.watchers_count}, "
            f"language={self.language}, forks_count={self.forks_count}, "
            f"open_issues_count={self.open_issues})"
        )

    def __repr__(self):
        return self.__str__()

class ProcessedRepoDetails():
    pass
    #repo_details = relationship("RepoDetails", back_populates="processed_repo_details")
