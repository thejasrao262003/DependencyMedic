from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "vuln_intelligence"
    service_port: int = 8001
    mongo_uri: str = "mongodb://mongodb:27017/dependencymedic"
    redis_url: str = "redis://redis:6379"
    gitlab_url: str = "https://gitlab.com"
    gitlab_token: str = ""
    gemini_api_key: str = ""
    log_level: str = "INFO"
    environment: str = "development"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
