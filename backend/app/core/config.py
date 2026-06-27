from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Gemini / Google API Key
    google_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("google_api_key", "gemini_api_key", "gemnai_key"),
    )

    # Chroma
    chroma_persist_dir: str = "./chroma_data"
    collection_name: str = "rag_documents"

    # Server-side PDF documents directory for indexing.
    # Change this path to point to the managed PDF folder on the server.
    server_documents_dir: str = "backend/assets/Hamed_Ahmed_Hamed__Resume_Updated.pdf"

    # Indexing pipeline
    index_chunk_size: int = 500
    index_chunk_overlap: int = 50
    index_embedding_model: str = "intfloat/multilingual-e5-base"

    # Chat / retrieval pipeline
    chat_retrieval_top_k: int = 4

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
