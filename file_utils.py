import argparse
import csv
import os

from tqdm import tqdm

csv.field_size_limit(10 * 1024 * 1024)


expected_header = ["repo_url", "license"]
"""
 num_stars"
 last_push
 is_forked
 keyword
 is_relevant
 readme
 brief_desc
 topic
 additional_keywords
]
"""


def extract_repo_name(repo_url):
    return repo_url.split("/")[-1]


def _fix_row(row, header):
    fixed_row = []
    for col_name in header:
        if col_name in row:
            fixed_row.append(row[col_name])
        else:
            fixed_row.append("")
    return fixed_row


def fix_csv_file(input_file):
    output_file = os.path.splitext(os.path.basename(input_file))[0]
    output_file = "fixed_" + output_file + ".csv"
    with open(input_file, "r") as input_csv, open(
        output_file, "w", newline=""
    ) as output_csv:
        reader = csv.DictReader(input_csv, delimiter="\t")
        writer = csv.writer(output_csv, delimiter="\t")
        writer.writerow(expected_header)
        for row in reader:
            fixed_row = _fix_row(row, expected_header)
            writer.writerow(fixed_row)
    print(f"Fixed CSV file saved as '{output_file}'")


"""
1   repo_url
2   license
3   num_stars
4   last_push
5   is_forked
6   keyword
7   is_relevant
8   readme
9   brief_desc
10  topic
11  additional_keywords
"""  #
# [repo_url,repo_license,star_count,fork_count,last_push,languages,topics,keyword,is_relevant,readme,brief_desc,topic,additional_keywords])


def save_to_markdown(csv_fname):
    processed_urls = set()  # Create a set to store processed repository URLs
    duplicate_urls = []
    # iltered_readme_repos_20230328-173301.md
    mkdwn_fname = "{}.md".format(os.path.splitext(csv_fname)[0]).replace(
        "filtered_readme_repos_", "AwesomeList"
    )
    with open(csv_fname, "r") as csvfile, open(mkdwn_fname, "w") as f:
        csv_reader = csv.reader(csvfile)
        f.write("# Awesome GitHub Repos\n\n")
        f.write(
            "A curated list of awesome oneAPI GitHub repositories related to various categories.\n\n"
        )
        f.write("## Table of Contents\n\n")
        topic_dict = {}
        for row in tqdm(
            csv_reader, desc="converting the csv file to markdown", unit="rows"
        ):
            (
                repo_url,
                license_spdx,
                star_count,
                _,
                _,
                languages,
                topics,
                keyword,
                _,
                _,
                brief_desc,
                topic,
                keywords,
            ) = row
            if repo_url == "repo_url":
                continue
            if repo_url in processed_urls:
                duplicate_urls.append(repo_url)
                continue
            processed_urls.add(repo_url)
            repo_name = extract_repo_name(repo_url)
            if topic not in topic_dict:
                topic_dict[topic] = f"### {topic}\n\n"
            topic_dict[
                topic
            ] += f"- [{repo_name}]({repo_url}): License: {license_spdx}: {brief_desc} ![GitHub stars](https://img.shields.io/badge/stars-{star_count}-blue)\noneAPI Component used : {keyword} \nLanguages: {languages} \n "
        for topic_content in topic_dict.values():
            f.write(topic_content)
            f.write("\n")
    with open("./results/duplicate_urls.txt", "w") as dup:
        dup.write("\n".join(duplicate_urls))
    return mkdwn_fname


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix or convert a CSV file")
    parser.add_argument("input_file", help="the input CSV file")
    parser.add_argument("--fix-csv", action="store_true", help="fix the input CSV file")
    parser.add_argument(
        "--output-file", help="the output file for the Markdown conversion"
    )
    args = parser.parse_args()
    if 0:  # args.fix_csv:
        fix_csv_file(args.input_file)
    else:
        if args.output_file:
            save_to_markdown(args.input_file, args.output_file)
            print(f"Markdown file saved as '{args.output_file}'")
        else:
            save_to_markdown(args.input_file, "AwesomeList.md")
            print("Markdown file saved as 'AwesomeList.md'")
