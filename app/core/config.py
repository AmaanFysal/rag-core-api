from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    CHUNK_SIZE_TOKENS: int = 500
    CHUNK_OVERLAP_TOKENS: int = 80
    TOKENIZER_MODEL: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"
        
settings = Settings()