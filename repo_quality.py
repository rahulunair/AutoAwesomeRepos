import re
from datetime import datetime
from datetime import timedelta

from transformers import pipeline



def evaluate_readme_quality(readme_content):
    desired_sections = [
        "Description", "Installation", "Usage", "Examples", "Contributing", "License"
    ]
    sections_present = 0
    for section in desired_sections:
        if re.search(rf"^#+\s*{section}", readme_content, re.MULTILINE | re.IGNORECASE):
            sections_present += 1
    desired_keywords = [
        "prerequisites", "dependencies", "requirements", "quick start", "documentation",
        "troubleshooting", "testing", "FAQ", "support"
    ]
    keywords_present = 0
    for keyword in desired_keywords:
        if re.search(rf"\b{keyword}\b", readme_content, re.IGNORECASE):
            keywords_present += 1
    sentiment_analysis = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    sentiment_result = sentiment_analysis(readme_content)
    sentiment_score = sentiment_result[0]["label"] == "POSITIVE" and sentiment_result[0]["score"] or 0
    quality_score = (
        (0.5 * sections_present / len(desired_sections)) +
        (0.3 * keywords_present / len(desired_keywords)) +
        (0.2 * sentiment_score)
    )
    return quality_score



def repo_metric_score(star_count, fork_count, created_at, readme_len):
    is_new_repo = (datetime.now() - created_at) <= timedelta(days=30)
    normalized_star_count = star_count / (1000 if is_new_repo else 100)
    normalized_fork_count = fork_count / (500 if is_new_repo else 50)
    normalized_readme_length = readme_len / 10000
    score = (0.3 * normalized_star_count) + (0.3 * normalized_fork_count) + (0.4 * normalized_readme_length)
    return score


def is_license_open_source(repo):
    license = repo.get_license()
    if not license:
        return False
    open_source_licenses = [
        "MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause", "BSD-2-Clause", "LGPL-3.0",
        "AGPL-3.0", "MPL-2.0", "EPL-2.0", "GPL-2.0", "LGPL-2.1"
    ]
    return license.license.key in open_source_licenses

