from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone,ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import settings

def load_data_from_path(path:str):
    loader=TextLoader(path)
    documents=loader.load()
    return documents
def chunking_docs(docs):
 splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=150)
 chunks=splitter.split_documents(docs)
 return chunks

pinecone=Pinecone(api_key=settings.PINECONE_API_KEY)
embd_model=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def create_index(INDEX:str,NAMESPACE:str):
      pinecone.create_index(name=INDEX, spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
    ),metric="cosine",dimension=384)
   
   
    





def PineConeIntegration(INDEX: str, NAMESPACE: str, path: str):
    existing_list = pinecone.list_indexes().names()

    if INDEX not in existing_list:
        create_index(INDEX, NAMESPACE)

    print(f"Index requested: {INDEX!r}")
    print(f"Source file: {path}")

    docs = load_data_from_path(path)
    chunks = chunking_docs(docs)

    if not chunks:
        raise ValueError(f"No chunks generated from {path}")

    # Explicitly select the Pinecone index
    index_object = pinecone.Index(INDEX)

    vectorstore = PineconeVectorStore(
        index=index_object,
        embedding=embd_model,
        namespace=NAMESPACE or None,
    )

    vectorstore.add_documents(documents=chunks)

    print(f"SUCCESS: {path}")
    print(f"Chunks ingested: {len(chunks)}")

    return vectorstore



def get_data_from_pinecone(
    INDEX: str,
    query: str,
    NAMESPACE: str = "",
):
    index_object = pinecone.Index(INDEX)

    vectorstore = PineconeVectorStore(
        index=index_object,
        embedding=embd_model,
        namespace=NAMESPACE or None,
    )

    results = vectorstore.similarity_search(
        query=query,
        k=5,
    )

    return "\n\n".join(
        doc.page_content for doc in results
    )
##introducted for evalution
def get_retrieved_documents(
    INDEX: str,
    query: str,
    NAMESPACE: str = "",
    k: int = 5,
):
    index_object = pinecone.Index(INDEX)

    vectorstore = PineconeVectorStore(
        index=index_object,
        embedding=embd_model,
        namespace=NAMESPACE or None,
    )

    documents = vectorstore.similarity_search(
        query=query,
        k=k,
    )

    return documents



