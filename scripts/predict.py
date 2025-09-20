# scripts/predict.py
# =========================================
ART_DIR    = r"Apply-Machine-Learning-to-Classify-Scientific-Paper-Based-on-Abstracts-\artifacts"
MODEL_NAME = "decision_tree"   # "knn" | "decision_tree" | "mlp" | "kmeans" | "transformer"
TEXTS = [
    """State-of-the-art computer vision systems are trained to predict a fixed set of predetermined object categories. This restricted form of supervision limits their generality and usability since additional labeled data is needed to specify any other visual concept. Learning directly from raw text about images is a promising alternative which leverages a much broader source of supervision. We demonstrate that the simple pre-training task of predicting which caption goes with which image is an efficient and scalable way to learn SOTA image representations from scratch on a dataset of 400 million (image, text) pairs collected from the internet. After pre-training, natural language is used to reference learned visual concepts (or describe new ones) enabling zero-shot transfer of the model to downstream tasks. We study the performance of this approach by benchmarking on over 30 different existing computer vision datasets, spanning tasks such as OCR, action recognition in videos, geo-localization, and many types of fine-grained object classification. The model transfers non-trivially to most tasks and is often competitive with a fully supervised baseline without the need for any dataset specific training. For instance, we match the accuracy of the original ResNet-50 on ImageNet zero-shot without needing to use any of the 1.28 million training examples it was trained on. We release our code and pre-trained model weights at"""
]
# =========================================

import os, sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from joblib import load
from pathlib import Path

def _embed_sbert(texts, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    from sentence_transformers import SentenceTransformer
    from sklearn.preprocessing import normalize
    model = SentenceTransformer(model_name)
    X = model.encode(list(texts), batch_size=64, show_progress_bar=False,
                     convert_to_numpy=True, normalize_embeddings=False)
    return normalize(X)
def main():
    model_path = Path(ART_DIR) / f"{MODEL_NAME}.joblib"
    mlb_path   = Path(ART_DIR) / f"{MODEL_NAME}.mlb.joblib"

    arts = load(model_path)   # FitArtifacts(pipeline=..., mlb=...)
    pipe = arts.pipeline
    mlb  = arts.mlb or (load(mlb_path) if mlb_path.exists() else None)

    try:
        # Works for KNN/DT/MLP/KMeans that have SBERT inside the pipeline
        y_pred_bin = pipe.predict(TEXTS)
    except ValueError:
        # Transformer artifact = classifier only → embed first, then predict
        X = _embed_sbert(TEXTS)  # default to all-MiniLM-L6-v2
        y_pred_bin = pipe.predict(X)

    if mlb is not None:
        labels = [list(lbls) for lbls in mlb.inverse_transform(y_pred_bin)]
    else:
        labels = [[str(x)] if not isinstance(x, (list, tuple)) else list(map(str, x)) for x in y_pred_bin]

    for t, labs in zip(TEXTS, labels):
        print("\n---")
        print("Text:", t[:120].replace("\n", " ") + ("..." if len(t) > 120 else ""))
        print("Predicted labels:", labs)

if __name__ == "__main__":
    main()
