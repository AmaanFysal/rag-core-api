from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    CHUNK_SIZE_TOKENS: int = 500
    CHUNK_OVERLAP_TOKENS: int = 80
    TOKENIZER_MODEL: str = "text-embedding-3-small"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60
    USERS_SEED: str = ""  # "alice:pass1,bob:pass2"

    class Config:
        env_file = ".env"

settings = Settings()