from app.guardrails.service import process_support_message_for_evaluation
import json
import asyncio
from pathlib import Path

BASE_DIR=Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "results" / "retrieval_results.json"
OUTPUT_FILE = BASE_DIR / "results" / "generation_results.json"

MAX_SAMPLE = 20

def load_retrieval_result():
    with open(INPUT_FILE,"r",encoding="utf-8")as f:
        return json.load(f)

def load_completed_questions():
    completed = set()

    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)

            for record in records:
                if record.get("flow_status") in (
                    "answered", "refused", "handoff"
                ):
                    completed.add(record["id"])

    return completed

def save_result(records):
   OUTPUT_FILE.parent.mkdir(parents=True,exist_ok=True)
   with open(OUTPUT_FILE,"w",encoding="utf-8")as file:
      json.dump(records,file,indent=4,ensure_ascii=False)

async def generate_response(records):

    completed_questions = load_completed_questions()

    existing_records = []

    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
            existing_records = json.load(file)

    for record in records:

        question = record["user_input"]

        if record["id"] in completed_questions:
            print("Skipping:", question)
            continue

        try:
            result = await process_support_message_for_evaluation(question)

            chatbot_result = result["result"]
            trace = result["trace"]

            generated_record = {
                "id": record["id"],
                "category": record["category"],
                "user_input": question,
                "retrieved_contexts": trace["retrieved_contexts"],
                "reference_contexts": record["reference_contexts"],
                "response": chatbot_result["response"],
                "reference": record["reference"],
                "flow_status": trace["flow_status"],
            }

            existing_records.append(generated_record)

            save_result(existing_records)

            completed_questions.add(record["id"])

            print("\nQuestion:", question)
            print("Response:", chatbot_result["response"])
            print("Flow status:", trace["flow_status"])
            print("Saved successfully!")

            await asyncio.sleep(3)

        except Exception as e:
            print("\nGeneration failed for:", question)
            print("Error:", str(e))
            raise

if __name__ == "__main__":

    print("Script started!")

    print("Input file:", INPUT_FILE)
    print("Input exists:", INPUT_FILE.exists())

    print("Output file:", OUTPUT_FILE)
    print("Output directory:", OUTPUT_FILE.parent)

    records = load_retrieval_result()

    print("Total records loaded:", len(records))

    records = records[:MAX_SAMPLE]

    asyncio.run(generate_response(records))

    print("\nGeneration completed!")
    print("Results saved at:", OUTPUT_FILE)
