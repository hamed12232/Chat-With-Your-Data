from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = ""

    # Chroma
    chroma_persist_dir: str = "./chroma_data"
    collection_name: str = "rag_documents"

    # Indexing pipeline
    index_chunk_size: int = 500
    index_chunk_overlap: int = 50

    # Chat / retrieval pipeline
    chat_retrieval_top_k: int = 4
    chat_llm_temperature: float = 0.1

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
