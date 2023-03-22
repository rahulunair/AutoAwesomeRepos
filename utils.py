import csv
import os
import re

import torch
import intel_extension_for_pytorch as ipex

import numpy as np
from rank_bm25 import BM25Okapi
import spacy
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
device = "xpu" if ipex.xpu.is_available() else "cpu"
print(f"using device: {device}")

code_pattern = re.compile("```.*?```", re.DOTALL)
non_english_pattern = re.compile("[^a-zA-Z0-9.,!?\\s]+")
BM25_CONSTANT = 100

category_examples = {
    "AI - Machine Learning": "machine learning project using libraries like scikit-learn, daal4py, R",
    "AI - Natural Language Processing": "natural language processing project using libraries like TensorFlow, PyTorch, Transformers, Huggingface, deep learning",
    "AI - Computer Vision": "computer vision project using libraries like opencv, pillow, TensorFlow, Pytorch, deep learning",
    "AI - Data Science": "data science project using libraries like pandas numpy",
    "Medical and Life Sciences": "medical and life sciences project using mkl, machine learning libraries but related to health",
    "Mathematics and Science": "mathematics and science project using libraries like mkl oneMKL, tbb",
    "Tools & Development": "software development project like compiler, optimization libraries, media libraries",
    "Financial Services": "financial services project",
    "Manufacturing": "manufacturing project",
    "Tutorials": "tutorial, examples and showcase of projects",
    "Other": "A project that doesn't fit into any of the other categories or is not specific enought"
}


nlp = spacy.load("en_core_web_sm")
classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1", device=device)
model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
category_embeddings = model.encode(list(category_examples.values()))
category_embeddings_normalized = normalize(category_embeddings)


def extract_repo_name(repo_url):
    return repo_url.split("/")[-1]

def normalize_text(text):
    doc = nlp(text)
    return " ".join(token.text for token in doc)


def save_results_to_file(csv_filename, output_filename):
    with open(csv_filename, "r") as csvfile, open(output_filename, "w") as f:
        csv_reader = csv.reader(csvfile)

        f.write("# Awesome GitHub Repos\n\n")
        f.write("A curated list of awesome GitHub repositories related to various categories.\n\n")
        f.write("## Table of Contents\n\n")

        current_topic = None
        for row in csv_reader:
            repo_url, star_count, _, _, keyword, _, _, brief_desc, topic = row
            repo_name = extract_repo_name(repo_url)
            normalized_brief_desc = normalize_text(brief_desc)
            if current_topic != topic:
                if current_topic is not None:
                    f.write("\n")
                f.write(f"### {topic}\n\n")
                current_topic = topic
                f.write(f"- [{repo_name}]({repo_url}):keyword: {keyword}: {normalized_brief_desc} ![GitHub stars](https://img.shields.io/badge/stars-{star_count}-blue)\n")


def _squash(x):
    return 1 / (1 + np.exp(-x))

def create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path

def preprocess_text(text):
    text = re.sub(r'[\n\r\t,]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = code_pattern.sub(lambda x: " " if x.group() != "." else x.group(), text)
    text = non_english_pattern.sub(
        lambda x: " " if x.group() != "." else x.group(), text
    )
    return text


"""
def classify_readme(readme_text):
    result = classifier(readme_text, list(category_examples.keys()))
    category = result["labels"][0]
    return category
"""

def classify_readme(readme_text):
    readme_embedding = model.encode([readme_text])[0]
    readme_embedding_normalized = normalize([readme_embedding])[0]
    similarities = cosine_similarity(
        [readme_embedding_normalized], category_embeddings_normalized
    )[0]
    category_index = np.argmax(similarities)
    return list(category_examples.keys())[category_index]


def bm25_score(text, keyword):
    tokenized_text = text.split()
    bm25 = BM25Okapi([tokenized_text])
    return _squash(bm25.get_scores([keyword])[0])


def tfidf_score(text, keyword):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([keyword, text])
    return (tfidf_matrix * tfidf_matrix.T).A[0, 1]


def is_relevant_context(text, keyword):
    """if relevant, returns True, else returns false"""
    tfidf_weight = 0.3
    bm25_weight = 0.7
    max_score = np.sqrt(tfidf_weight ** 2 + bm25_weight ** 2)
    normalized_score = bm25_weight * bm25_score(
        text, keyword
    ) + tfidf_weight * tfidf_score(text, keyword)
    normalized_score /= max_score
    return True if normalized_score > 0.5 else False
