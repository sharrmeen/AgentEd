from langchain_huggingface import HuggingFaceEmbeddings

# Singleton model (loaded once)
_embedding_model = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-large"
)

def embed_query(text: str) -> list[float]:

    return _embedding_model.embed_query(f"query: {text.strip()}")

def embed_passage(text: str) -> list[float]:

    return _embedding_model.embed_documents([f"passage: {text.strip()}"])[0]

def get_embedding_model():

    return _embedding_model
