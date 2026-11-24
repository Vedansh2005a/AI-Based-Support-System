import json
from pathlib import Path
import csv
from ragas.metrics.collections import AnswerRelevancy,Faithfulness
from ragas.llms import llm_factory
from ragas import SingleTurnSample
import instructor
import asyncio
from groq import AsyncGroq
from dotenv import load_dotenv
load_dotenv()

BASE_DIR=Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "results" / "generation_results.json"
OUTPUT_FILE = BASE_DIR / "results" / "generation_ragas_results.csv"

MAX_SAMPLE = 20

groq_clinet=AsyncGroq()


instructor_llm=instructor.from_groq(client=groq_clinet,mode=instructor.Mode.JSON)

ragas_llm=llm_factory(model="openai/gpt-oss-20b",provider="groq",client=instructor_llm,max_tokens=4096)
from ragas.embeddings import embedding_factory

embeddings_llm = embedding_factory(
    "huggingface",
    model="sentence-transformers/all-MiniLM-L6-v2"
)

faithful_metrics=Faithfulness(llm=ragas_llm)
answer_relevancy=AnswerRelevancy(llm=ragas_llm,embeddings=embeddings_llm,strictness=3)
def load_generation_result():
    with open(INPUT_FILE,"r",encoding="utf-8")as file:
        return json.load(file)

def filter_valid_record(records):
    filtered_records=[]
    for record in records:
        if record.get("flow_status")!="answered":
            continue
        if not record.get("response"):
            continue
        if not record.get("retrieved_contexts"):
            continue
        filtered_records.append(record)

    return filtered_records

def load_completed_ids():
    completed_ids = set()

    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                completed_ids.add(row["id"])

    return completed_ids

def save_result(result):
    file_exists = OUTPUT_FILE.exists()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "id",
                "category",
                "user_input",
                "faithfulness",
                "answer_relevancy"
            ]
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(result)

async def create_singleTurnSample(records):
    completed_ids = load_completed_ids()
    records = records[:MAX_SAMPLE]
    for record in records:
        record_id = record["id"]
        question = record["user_input"]
        response = record["response"]
        contexts = record["retrieved_contexts"]

        if record_id in completed_ids:
            print("\nSkipping")
            continue

        try:
            faithfulness_score = await faithful_metrics.ascore(
                user_input=question,
                response=response,
                retrieved_contexts=contexts,
            )
            answer_relevancy_score = await answer_relevancy.ascore(
                user_input=question,
                response=response,
            )
            result = {
                "id": record_id,
                "category": record["category"],
                "user_input": question,
                "faithfulness": faithfulness_score.value,
                "answer_relevancy": answer_relevancy_score.value,
            }
            save_result(result)
            completed_ids.add(record_id)

            print("\nQuestion:", question)
            print("Faithfulness:", faithfulness_score.value)
            print("Answer Relevancy:", answer_relevancy_score.value)
            print("Saved successfully!")

            await asyncio.sleep(3)
        except Exception as e:
            print("\nEvaluation failed for:", question)
            print("Error:", str(e))
            raise


if __name__ == "__main__":

    records = load_generation_result()

    valid_records = filter_valid_record(records)

    print("Total records:", len(records))
    print("Valid records:", len(valid_records))

    asyncio.run(create_singleTurnSample(valid_records))

    print("\nGeneration evaluation completed!")
    print("Results saved at:", OUTPUT_FILE)


  
    