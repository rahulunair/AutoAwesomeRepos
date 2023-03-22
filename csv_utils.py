import argparse
import csv
import os

import torch
import intel_extension_for_pytorch as ipex
import json
import spacy
from tqdm import tqdm

from utils import classify_readme

csv.field_size_limit(10 * 1024 * 1024)

expected_header = [
    "repo_url",
    "num_stars",
    "last_push",
    "is_forked",
    "keyword",
    "relevancy_score",
    "readme",
    "brief_desc",
    "possible_topic",
]


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


def _extract_repo_name(repo_url):
    return repo_url.split("/")[-1]


def _normalize_text(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    return " ".join(token.text for token in doc)

def save_to_markdown(csv_filename, output_filename="AwesomeList.md"):
    with open(csv_filename, "r") as csvfile, open(output_filename, "w") as f:
        csv_reader = csv.reader(csvfile)
        f.write("# Awesome GitHub Repos\n\n")
        f.write(
            "A curated list of awesome GitHub repositories related to various categories.\n\n"
        )
        f.write("## Table of Contents\n\n")
        topic_dict = {}
        for row in tqdm(csv_reader, desc="converting the csv file to markdown", unit="rows"):
            repo_url, star_count, _, _, keyword, _, readme, brief_desc, _ = row
            topic = classify_readme(readme)
            repo_name = _extract_repo_name(repo_url)
            normalized_brief_desc = _normalize_text(brief_desc)
            if topic not in topic_dict:
                topic_dict[topic] = f"### {topic}\n\n"
            topic_dict[topic] += f"- [{repo_name}]({repo_url}):keyword: {keyword}: {normalized_brief_desc} ![GitHub stars](https://img.shields.io/badge/stars-{star_count}-blue)\n"
        for topic_content in topic_dict.values():
            f.write(topic_content)
            f.write("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix or convert a CSV file")
    parser.add_argument("input_file", help="the input CSV file")
    parser.add_argument("--fix-csv", action="store_true", help="fix the input CSV file")
    parser.add_argument("--output-file", help="the output file for the Markdown conversion")
    args = parser.parse_args()
    if 0: #args.fix_csv:
        fix_csv_file(args.input_file)
    else:
        if args.output_file:
            save_to_markdown(args.input_file, args.output_file)
            print(f"Markdown file saved as '{args.output_file}'")
        else:
            save_to_markdown(args.input_file, "AwesomeList.md")
            print("Markdown file saved as 'AwesomeList.md'")
