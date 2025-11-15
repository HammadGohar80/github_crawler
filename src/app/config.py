from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # GitHub API
    GITHUB_API_URL: str = "https://api.github.com/graphql"
    GITHUB_ACCESS_TOKEN: str

    # Crawling
    BATCH_SIZE: int = 100
    MAX_RETRIES: int = 5
    RETRY_BACKOFF: int = 2
    MAX_WORKERS: int = 10
    TOTAL_REPOS: int = 100000
    STAR_STEP: int = 100

    # PostgreSQL DATABASE
    DATABASE_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()