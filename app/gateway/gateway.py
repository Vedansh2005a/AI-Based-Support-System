from portkey_ai import Portkey
from app.config import settings
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
load_dotenv()
import os
import logfire
if not settings.PORTKEY_API_KEY:
    logfire.error("No API KEY FOUND FOR PORTKEY GATEWAY")
    raise ConnectionRefusedError
def create_llm(config_slug:str,model:str):
    return ChatOpenAI(model="openai/gpt-oss-20b",base_url="https://api.portkey.ai/v1",api_key=settings.PORTKEY_API_KEY,default_headers={"x-portkey-config":config_slug},temperature=0.2,max_retries=2,timeout=60)

main_llm=create_llm(config_slug=os.environ["MAIN_SLUG"],model="openai/gpt-oss-20b")
fallback_llm=create_llm(config_slug=os.environ["FALLBACK_SLUG"],model="openai/gpt-oss-20b")
def export_llm():
    return main_llm.with_fallbacks([fallback_llm])