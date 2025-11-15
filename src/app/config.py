from pydantic import BaseSettings

class Settings(BaseSettings):
    GITHUB_API_URL: str = "https://api.github.com/graphql"
    BATCH_SIZE: int = 50
    MAX_RETRIES: int = 5
    RETRY_BACKOFF: int = 2
    POSTGRES_URL: str = "postgresql://postgres:postgres@localhost:5432/github"

settings = Settings()