"""Application configuration.
The single door for environment-dependent values: nothing outside this
module reads os.environ. Settings are validated once at startup (the app
refuses to boot on invalid config) and are immutable afterwards.
"""

from enum import StrEnum
from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, PostgresDsn, RedisDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT= "development"
    TEST="test"
    PRODUCTION="production"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RAGX_",
        env_file=".env",
        frozen=True,
        extra="forbid",
        env_file_encoding="utf-8",
    )

    app_name : str = "ragx"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    database_url: PostgresDsn = Field(
            default="postgresql+asyncpg://ragx:ragx@localhost:5432/ragx",  # type: ignore[assignment]
            description="Async SQLAlchemy DSN. Dev default matches docker-compose.",
        )

    redis_url: RedisDsn = Field(
            default="redis://localhost:6379/0",  # type: ignore[assignment]
            description="Broker/cache. Dev default matches docker-compose.",
        )


    '''model validator checks the whole condition is true or false'''
    @model_validator(mode="after")
    def production_must_not_debug(self) -> Self:
        if self.environment is Environment.PRODUCTION and self.debug:
            raise ValueError("debug=True is forbidden in production")
        return self


'''memoize the function thatwhy lru_cache'''
@lru_cache
def get_settings() -> Settings:
    return Settings()

