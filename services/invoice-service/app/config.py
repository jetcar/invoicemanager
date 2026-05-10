from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/invoice_db"
    redis_url: str = "redis://localhost:6379/2"
    kafka_bootstrap_servers: str = "localhost:9092"
    secret_key: str = "supersecretkey"
    algorithm: str = "HS256"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
