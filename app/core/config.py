from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AIDP Meta/Taxonomy Async API"
    database_url: str = "sqlite+aiosqlite:///./test.db"
    debug: bool = True

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()
