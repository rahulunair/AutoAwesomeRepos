import re

import openai
from pyrate_limiter import Limiter, RequestRate
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_fixed)

limiter = Limiter(RequestRate(60, 60), RequestRate(60000, 600))


def _truncate_tokens(text, max_chars=10000):
    return text[:max_chars]


def process_string(s: str) -> str:
    s = re.sub(r"^[^a-zA-Z]+", "", s)
    s = re.sub(r"[^a-zA-Z]+$", "", s)
    s = re.sub(r"([^a-zA-Z\s])", r" \1 ", s)
    s = re.sub(r"\s+", " ", s)
    return s


@retry(
    stop=stop_after_attempt(5),
    wait=wait_fixed(1),
    retry_error_callback=lambda _: None,
    retry=retry_if_exception_type(openai.APIError),
)
def call_openai_api(system_message: str, user_message: str, readme_text: str) -> str:
    readme_text = _truncate_tokens(readme_text)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message.format(readme_text=readme_text)},
        ],
    )
    assistant_message = response.choices[0].message.content.strip()
    return assistant_message


def classify_readme_category(readme_text: str) -> str:
    limiter.try_acquire("classify_text")
    system_message = "You are a helpful and an expert assistant who classifies GitHub repos into categories based on their README content."
    user_message = "Please provide the most relevant category for the following GitHub project README without explanation. Choose from: 'AI - Machine Learning', 'AI - Natural Language Processing', 'Rendering', 'AI - Computer Vision', 'AI - Data Science', 'AI - Reinforcement Learning', 'Medical and Life Sciences', 'Mathematics and Science', 'Tools & Development', 'Financial Services', 'Manufacturing', 'Tutorials', 'HPC', 'AI-Frameworks'. The input README is:\n\n{readme_text}"
    assistant_message = call_openai_api(system_message, user_message, readme_text)
    return process_string(assistant_message)


def summarize_readme(readme_text: str) -> str:
    limiter.try_acquire("summarize_text")
    system_message = "You are a helpful assistant that generates a brief 2 to 3 line summary of GitHub project READMEs."
    user_message = "Please provide a brief 2 to 3 line summary of the following GitHub project README without explaining it:\n\n{readme_text}"
    return call_openai_api(system_message, user_message, readme_text)


def get_relevancy_score_and_reasons(readme_text, debug=False):
    limiter.try_acquire("relevant_repo")
    system_message = (
        "You are a helpful assistant who is an expert in finding relevant documents."
    )
    user_message = """Please provide a score between 0 to 1 (0 lowest, 1 highest) on how much the following GitHub project README, mentions the use or uses of any Intel oneAPI components or any of the components from the list: '- oneDAL, intel_extension_for_pytorch', '- intel_extension_for_transformers', '- intel_extension_for_horovod', '- intel_neural_compressor', '- intel_extension_for_tensorflow', '- oneAPI Base Toolkit', '- oneAPI AI Toolkit', '- oneAPI HPC Toolkit', '- oneAPI Rendering Toolkit', '- openvino', '- daal4py', '- scikit-learn-intelex', '- oneTBB', '- oneMKL', '- oneVPL', '- oneDPL', '- oneCCL', '- onednn', '- open VKL', '- Embree', '- OSPRay', '- Open Image Denoise'. If the project or its development has been discontinued, then the score should be set to zero. Format your response as 'Relevancy_score = x, Reasons = [reason1, reason2]'. Consider any mention of oneAPI, its components, or the listed libraries as relevant. The input README is:\n\n{readme_text}\n\nExample 1:\nInput: The README mentions OneDAL library which is designed to accelerate big data analysis using Intel hardware. However, there is no mention of any specific oneAPI components or libraries being used or integrated with OneDAL.\nOutput: Relevancy_score = 0.7, Reasons = [Mentions OneDAL, which is a specific oneAPI components or libraries]\n\nExample 2:\nInput: The README provides information about using the oneapi.jl package to work with the oneAPI unified programming model, which is part of the Intel Compute Runtime available on Linux.\nOutput: Relevancy_score = 0.8, Reasons = [Mentions oneapi.jl package and oneAPI unified programming model, Part of Intel Compute Runtime on Linux]"""
    assistant_message = call_openai_api(system_message, user_message, readme_text)
    first_line = assistant_message.strip().split("\n")[0]
    score_match = re.search(r"Relevancy_score\s*=\s*([\d.]+)", first_line)
    reasons_match = re.search(r"Reasons\s*=\s*\[(.+)\]", first_line)
    if score_match and reasons_match:
        relevancy_score = float(score_match.group(1))
        reasons_str = reasons_match.group(1)
        reasons = [
            reason.strip() for reason in reasons_str.split(",") if reason.strip()
        ]
    else:
        if debug:
            print(
                "Unable to extract relevancy score and reasons from the model's response"
            )
            print("score_match: ", score_match)
            print("reasons_match: ", reasons_match)
        relevancy_score = 0.1234
        reasons = []
    return {"score": relevancy_score, "reasons": reasons}
