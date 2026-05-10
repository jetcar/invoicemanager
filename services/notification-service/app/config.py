from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/notification_db"
    redis_url: str = "redis://localhost:6379/4"
    kafka_bootstrap_servers: str = "localhost:9092"
    secret_key: str = "supersecretkey"
    algorithm: str = "HS256"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@invoicemanager.local"
    firebase_credentials_json: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
