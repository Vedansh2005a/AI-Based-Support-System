
import json
from pathlib import Path

from app.ingestion.loading_data import get_retrieved_documents
from app.config import settings

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "dataset" / "support_questions.json"
OUTPUT_FILE = BASE_DIR / "results" / "retrieval_results.json"

MAX_SAMPLE = None

INDEX_NAME = settings.INDEX_NAME
NAMESPACE = settings.NAMESPACE


def load_dataset():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def export_retrieval_results():

    records = load_dataset()[:MAX_SAMPLE]

    results = []

    for record in records:

        question = record["user_input"]

        print(f"\nRetrieving: {question}")

        documents = get_retrieved_documents(
            INDEX=INDEX_NAME,
            NAMESPACE=NAMESPACE,
            query=question,
            k=5,
        )

        retrieved_contexts = [
            doc.page_content
            for doc in documents
            if doc.page_content and doc.page_content.strip()
        ]

        results.append({
            **record,
            "retrieved_contexts": retrieved_contexts,
        })

        print("Retrieved documents:", len(retrieved_contexts))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4, ensure_ascii=False)

    print("\nRetrieval export completed!")
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    export_retrieval_results()
