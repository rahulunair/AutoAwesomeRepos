from functools import partial
import os
import re

import numpy as np
from rank_bm25 import BM25Okapi
from rich.console import Console
from rich.style import Style
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import spacy
import torch
#import intel_extension_for_pytorch
from embeddings import category_examples
from embeddings import openai_normalized_categories
from embeddings import transformer_normalized_categories
from embeddings import generate_transformer_embeddings
from embeddings import generate_openai_embeddings

console = Console()
print = partial(console.print, style=Style.parse("cyan"))

code_pattern = re.compile("```.*?```", re.DOTALL)
non_english_pattern = re.compile("[^a-zA-Z0-9.,!?\\s]+")
BM25_CONSTANT = 100
nlp = spacy.load("en_core_web_sm")


def extract_repo_name(repo_url):
    return repo_url.split("/")[-1]


def normalize_text(text):
    doc = nlp(text)
    return " ".join(token.text for token in doc)


def _squash(x):
    return 1 / (1 + np.exp(-x))


def create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


def preprocess_text(text):
    text = re.sub(r"[\n\r\t,]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = code_pattern.sub(lambda x: " " if x.group() != "." else x.group(), text)
    text = non_english_pattern.sub(
        lambda x: " " if x.group() != "." else x.group(), text
    )
    return text


def extract_topics(readme):
    doc = nlp(readme)
    topics = []
    for chunk in doc.noun_chunks:
        if chunk.root.dep_ == "nsubj" and chunk.text not in topics:
            topics.append(chunk.text)
    return " ".join(topics)


def calculate_bm25_scores(readme, category_examples):
    bm25_scores = []
    for _, keywords in category_examples.items():
        combined_score = 0
        for keyword in keywords.split():
            score = bm25_score(readme, keyword)
            combined_score += score
        bm25_scores.append(combined_score)
    return bm25_scores


def normalize_scores(scores):
    min_score, max_score = min(scores), max(scores)
    if max_score == min_score:
        return [1.0] * len(scores)
    return [(score - min_score) / (max_score - min_score) for score in scores]


def classify_readme(
    readme,
    readme_summary,
    bm25_weight=0.30,
    cosine_weight=0.70,
    use_openai=False,
    use_bm25=False,
):
    category_keys = list(category_examples.keys())
    topics = extract_topics(readme)
    readme = topics + readme_summary
    use_local_models = True
    try:
        if use_openai and os.environ["OPENAI_API_KEY"]:
            readme_embedding = generate_openai_embeddings([readme])[0]
            readme_embedding_normalized = normalize([readme_embedding])[0]
            similarities = cosine_similarity(
                [readme_embedding_normalized], openai_normalized_categories
            )[0]
            use_local_models = False
    except KeyError:
        pass
    if use_local_models:
        readme_embedding = generate_transformer_embeddings([readme])[0]
        readme_embedding_normalized = normalize([readme_embedding])[0]
        similarities = cosine_similarity(
            [readme_embedding_normalized], transformer_normalized_categories
        )[0]
    if use_bm25:
        bm25_scores = calculate_bm25_scores(readme, category_examples)
        normalized_bm25_scores = normalize_scores(bm25_scores)
        normalized_similarity_scores = normalize_scores(similarities)
        combined_scores = [
            bm25_weight * bm25 + cosine_weight * cosine
            for bm25, cosine in zip(
                normalized_bm25_scores, normalized_similarity_scores
            )
        ]
        return category_keys[np.argmax(combined_scores)]
    return category_keys[np.argmax(similarities)]


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
