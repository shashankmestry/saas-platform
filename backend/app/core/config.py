from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="SaaS Platform API", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        alias="APP_ENV",
    )
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/saas_platform",
        alias="DATABASE_URL",
    )
    cors_allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        alias="CORS_ALLOWED_ORIGINS",
    )
    trusted_hosts: Annotated[list[str], NoDecode] = Field(
        default_factory=list,
        alias="TRUSTED_HOSTS",
    )

    @field_validator("cors_allowed_origins", "trusted_hosts", mode="before")
    @classmethod
    def parse_list_env(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]

        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
