import pickle
import os
from llama_index import GPTSimpleVectorIndex

assert (
    os.getenv("OPENAI_API_KEY") is not None
), "Please set the OPENAI_API_KEY environment variable."

from llama_index import download_loader

download_loader("GithubRepositoryReader")

from llama_index.readers.llamahub_modules.github_repo import (
    GithubClient,
    GithubRepositoryReader,
)


github_client = GithubClient(os.getenv("GTOKEN"))
loader = GithubRepositoryReader(
    github_client,
    owner="tensorflow",
    repo="tensorflow",
    filter_directories=(
        ["tensorflow", "docs"],
        GithubRepositoryReader.FilterType.INCLUDE,
    ),
    filter_file_extensions=([".py"], GithubRepositoryReader.FilterType.INCLUDE),
    verbose=True,
    concurrent_requests=10,
)

docs = loader.load_data(branch="main")
with open("docs.pkl", "wb") as f:
    pickle.dump(docs, f)

index = GPTSimpleVectorIndex(docs)

index.query("Explain each tensorflow class?")
