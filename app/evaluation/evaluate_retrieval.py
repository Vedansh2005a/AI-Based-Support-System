
import json
import os
from pathlib import Path
import asyncio
import csv
import instructor
from groq import AsyncGroq
from dotenv import load_dotenv

from ragas import SingleTurnSample, EvaluationDataset, evaluate
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    ContextPrecisionWithReference,
    ContextRecall,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "results" / "retrieval_results.json"
RESULT_DIR = BASE_DIR / "results"

MAX_SAMPLE = 20


def load_retrieval_results():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def build_ragas_dataset(records):

    samples = []

    for record in records:
        sample = SingleTurnSample(
            user_input=record["user_input"],
            retrieved_contexts=record["retrieved_contexts"],
            reference=record["reference"],
        )

        samples.append(sample)

    return EvaluationDataset(samples=samples)


def create_evaluator_llm():
    groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    instructor_client = instructor.from_groq(
        groq_client,
        mode=instructor.Mode.JSON
    )

    evaluator_llm = llm_factory(
        model="openai/gpt-oss-20b",
        provider="groq",
        client=instructor_client,
        max_tokens=4096
    )

    return evaluator_llm



def load_completed_questions(output_file):
    completed = set()

    if output_file.exists():
        with open(output_file, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                completed.add(row["question"])

    return completed


def save_result(output_file, result):
    file_exists = output_file.exists() and output_file.stat().st_size > 0

    with open(output_file, "a", newline="", encoding="utf-8") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "question",
                "context_precision",
                "context_recall",
            ],
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(result)
        file.flush()


async def run_evaluation(dataset, context_precision, context_recall, output_file):

    completed_questions = load_completed_questions(output_file)

    for sample in dataset.samples:

        # Skip questions that have already been evaluated
        if sample.user_input in completed_questions:
            print("\nSkipping already evaluated question:", sample.user_input)
            continue

        try:
            # Context Precision
            precision_result = await context_precision.ascore(
                user_input=sample.user_input,
                reference=sample.reference,
                retrieved_contexts=sample.retrieved_contexts,
            )

            await asyncio.sleep(3)

            # Context Recall
            recall_result = await context_recall.ascore(
                user_input=sample.user_input,
                reference=sample.reference,
                retrieved_contexts=sample.retrieved_contexts,
            )

            result = {
                "question": sample.user_input,
                "context_precision": precision_result.value,
                "context_recall": recall_result.value,
            }

            # Save immediately after both metrics succeed
            save_result(output_file, result)

            completed_questions.add(sample.user_input)

            print("\nQuestion:", sample.user_input)
            print("Context Precision:", precision_result.value)
            print("Context Recall:", recall_result.value)
            print("Result saved successfully!")

            await asyncio.sleep(3)

        except Exception as e:
            print("\nEvaluation failed for:", sample.user_input)
            print("Error:", str(e))
            raise


if __name__ == "__main__":

    records = load_retrieval_results()
    records = records[:MAX_SAMPLE]

    dataset = build_ragas_dataset(records)

    evaluator_llm = create_evaluator_llm()

    context_precision = ContextPrecisionWithReference(
        llm=evaluator_llm
    )

    context_recall = ContextRecall(
        llm=evaluator_llm
    )

    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = RESULT_DIR / "ragas_results.csv"

    asyncio.run(
        run_evaluation(
            dataset,
            context_precision,
            context_recall,
            output_file
        )
    )

    print("\nEvaluation completed!")
    print("Results saved at:", output_file)