from dotenv import load_dotenv
load_dotenv()
import os
class Settings():
    GROQ_API_KEY=os.getenv('GROQ_API_KEY')
    GEMINI_API_KEY=os.getenv('GEMINI_API_KEY')
    LOGFIRE_API_KEY=os.getenv('LOGFIRE_API_KEY')
    MAIN_MODEL=os.getenv('MODEL')
    OTHER_MODEL=os.getenv('MODEL2')
    PORTKEY_API_KEY=os.getenv('PORTKEY_API_KEY')
    PINECONE_API_KEY=os.getenv('PINECONE_API_KEY')
    SLUG=os.getenv('MAIN_SLUG')
    FALLBACK_SLUG=os.getenv('FALLBACK_SLUG')
    INDEX_NAME="knowledge-base-customer-assistant"
    NAMESPACE="support-docs"

settings=Settings()
