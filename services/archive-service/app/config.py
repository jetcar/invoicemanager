from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/archive_db"
    redis_url: str = "redis://localhost:6379/6"
    kafka_bootstrap_servers: str = "localhost:9092"
    secret_key: str = "supersecretkey"
    algorithm: str = "HS256"
    archive_threshold_days: int = 365

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
