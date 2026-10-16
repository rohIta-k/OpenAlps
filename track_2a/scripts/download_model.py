"""Download the multilingual sentence embedding model locally."""
from pathlib import Path

from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "models" / "paraphrase-multilingual-MiniLM-L12-v2"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main() -> None:
    if (MODEL_DIR / "modules.json").exists():
        print(f"Model already exists at: {MODEL_DIR}")
        return

    MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {MODEL_NAME}...")
    SentenceTransformer(MODEL_NAME).save(str(MODEL_DIR))
    print(f"Model downloaded successfully to: {MODEL_DIR}")


if __name__ == "__main__":
    main()
