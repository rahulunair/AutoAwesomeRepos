import os
import pickle

import torch
#import intel_extension_for_pytorch as ipex
import openai
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize

from pyrate_limiter import Duration, Limiter, RequestRate


rate_limits = (RequestRate(50, Duration.MINUTE),)
limiter = Limiter(*rate_limits)
#device = "xpu" if torch.xpu.is_available() else "cpu"
device = "cpu"
category_examples = {
    "AI - Machine Learning": "scikit-learn, lighgbm,  xgboost, gradient boosting Linear Regression, Logistic Regression, Decision Trees, Random Forest, Naïve Bayes, k-Nearest Neighbors, Support Vector Machines, Principal Component Analysis, k-Means, DBSCAN, Hierarchical Clustering, AdaBoost, Gradient Boosting, XGBoost, LightGBM, CatBoost, Hidden Markov Models, Expectation Maximization, Gaussian Mixture Models, Latent Dirichlet Allocation, streaming processing,  Supervised and unsupervised machine learning projects using scikit-learn, daal4py, or R for classification, regression, or clustering tasks",
    "AI - Natural Language Processing": "RNN, LSTM, GRU, Transformer, BERT, GPT, RoBERTa, T5, XLNet, ALBERT, DistilBERT, ERNIE, GPT-2, GPT-3, Transformer-XL, ELECTRA, XLM, XLM-R, BART, ELMO, ULMFiT, reading comprehension, summarize, embedding, Text analysis, Natural Language Processing, sentiment analysis, text generation, or chatbot projects using Huggingface Transformers, TensorFlow, or PyTorch",
    "AI - Computer Vision": "AlexNet, VGG, ResNet, DenseNet, MobileNet, EfficientNet, U-Net, R-CNN, YOLO, GAN, HRNet, DeepLab, RetinaNet, Text-To-Image, stable diffusion, controlnet, neural processing, DETR, YOLOv, SegFormer, ViT, face detection, face alignment, hair segmentation, pose estimation, OCR, Computer vision, Image classification, Image processing, object detection, or face recognition projects using OpenCV, Pillow, TensorFlow, visual, PaddlePaddle, or PyTorch",
    "AI - Data Science": "Data analysis, SparkSQL, clickhouse, analytics, big data, recommendation systems,ray, rayonspark, bigdl, spark, sql, data science, data visualization, or data preprocessing projects using pandas, numpy, or matplotlib",
    "AI - RL": "Q-Learning, Deep Q-Network (DQN), Double DQN, Dueling DQN, SARSA, Expected SARSA, Temporal Difference (TD) Learning, Policy Gradients, REINFORCE, Proximal Policy Optimization (PPO), Advantage Actor-Critic (A2C), Asynchronous Advantage Actor-Critic (A3C), Trust Region Policy Optimization (TRPO), Soft Actor-Critic (SAC), Deep Deterministic Policy Gradient (DDPG), Twin Delayed DDPG (TD3), Distributional RL (C51, QR-DQN), Hierarchical Reinforcement Learning (HRL), Inverse Reinforcement Learning (IRL), Imitation Learning, Model-Based RL",
    "Medical and Life Sciences": "Medical and Biomedical research, genomics, or drug discovery projects involving machine learning or data analysis related to health or life sciences",
    "Mathematics and Science": "Numerical simulations, mathematical modeling, or scientific computing projects using mkl, oneMKL, tbb, or other libraries",
    "Tools & Development": "Compiler, optimization, or media libraries development projects, including oneMKL, oneDNN, oneDPL, or oneCCL, level zero",
    "Financial Services": "Projects involving financial data analysis, risk management, or trading algorithms Black-Scholes Model, Binomial Option Pricing, Monte Carlo Simulation, GARCH, ARIMA, VAR, Cointegration, CAPM, Fama-French Model, Time Series Analysis, Technical Analysis, Risk Metrics, Portfolio Optimization, Markov Chain, Machine Learning Models (e.g., SVM, Random Forest, Gradient Boosting, etc.), Neural Networks, Reinforcement Learning, Sentiment Analysis, Algorithmic Trading, Bayesian Networks",
    "Manufacturing": "Manufacturing process optimization, quality control, or factory automation projects",
    "Tutorials": "Guides, tutorials, or examples showcasing projects or libraries usage",
    "HPC": "Finite Element Method, Finite Difference Method, Finite Volume Method, Boundary Element Method, Lattice Boltzmann Method, Monte Carlo Simulations, Molecular Dynamics, Discrete Event Simulation, Fast Fourier Transform, Conjugate Gradient, Krylov Subspace Methods, Multigrid Methods, Discontinuous Galerkin Methods, Particle-in-Cell, Smoothed Particle Hydrodynamics, N-Body Simulations, High Performance Linpack, Graph Analytics, High-performance computing projects, including parallel computing, distributed systems, or GPGPU programming with SYCL or OpenCL, oneMKL, OpenMP, MPI ",
}

openai_embeddings_filename = "./embeddings/openai_embeddings.pkl"
transformer_embeddings_filename = "./embeddings/transformer_embeddings.pkl"
model_name = "all-MiniLM-L6-v2"
texts = list(category_examples.values())
tr_model = SentenceTransformer(model_name, device=device)


def save_and_load_embeddings(embeddings_generator, filename, *args, **kwargs):
    dir_name = os.path.dirname(filename)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    if os.path.exists(filename):
        with open(filename, "rb") as file:
            embeddings = pickle.load(file)
    else:
        embeddings = embeddings_generator(*args, **kwargs)
        with open(filename, "wb") as file:
            pickle.dump(embeddings, file)
    return normalize(embeddings)


def _truncate_tokens(text, max_chars=10000):
    """truncate text to 4096 tokens - 4096 * 4 == 16384 (16000 with buffer) chars"""
    return text[:max_chars]


def generate_openai_embeddings(texts, model="text-embedding-ada-002"):
    embeddings = []
    max_chars = 10000
    limiter.try_acquire("generate_openai_embeddings")
    for text in texts:
        try:
            text = _truncate_tokens(text)
            emb = openai.Embedding.create(input=[text], model=model)["data"][0][
                "embedding"
            ]
        except openai.InvalidRequestError:
            max_chars -= 1000
            text = _truncate_tokens(text, max_chars)
            emb = openai.Embedding.create(input=[text], model=model)["data"][0][
                "embedding"
            ]

        embeddings.append(emb)
    return embeddings


def generate_transformer_embeddings(
    texts, model_name="all-MiniLM-L6-v2", device=device, batch_size=8
):
    if tr_model is not None:
        model = tr_model
    else:
        model = SentenceTransformer(model_name, device=device)

    category_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        batch_embeddings = model.encode(batch)
        category_embeddings.extend(batch_embeddings)
    category_embeddings_normalized = normalize(category_embeddings)
    return category_embeddings_normalized


openai_normalized_categories = save_and_load_embeddings(
    generate_openai_embeddings, openai_embeddings_filename, texts
)

transformer_normalized_categories = save_and_load_embeddings(
    generate_transformer_embeddings,
    transformer_embeddings_filename,
    texts,
    model_name=model_name,
    device=device,
)
