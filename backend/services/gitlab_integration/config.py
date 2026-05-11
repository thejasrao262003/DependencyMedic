from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "gitlab_integration"
    service_port: int = 8004
    mongo_uri: str = "mongodb://mongodb:27017/dependencymedic"
    redis_url: str = "redis://redis:6379"
    gitlab_url: str = "https://gitlab.com"
    gitlab_token: str = ""
    pipeline_poll_interval_seconds: float = 2.0
    pipeline_poll_max_seconds: float = 120.0
    log_level: str = "INFO"
    environment: str = "development"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
