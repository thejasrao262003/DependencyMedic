from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "api_gateway"
    service_port: int = 8000
    mongo_uri: str = "mongodb://mongodb:27017/dependencymedic"
    redis_url: str = "redis://redis:6379"
    api_key: str = "dev-api-key-change-me"
    remediation_engine_url: str = "http://remediation_engine:8003"
    gitlab_integration_url: str = "http://gitlab_integration:8004"
    log_level: str = "INFO"
    environment: str = "development"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
