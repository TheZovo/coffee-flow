from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DATABASE_URL: str = "postgresql+asyncpg://coffee:coffee@db:5432/coffee"
    APP_TIMEZONE: str = "Europe/Minsk"

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BARISTA_BOT_TOKEN: str = ""
    PUBLIC_BASE_URL: str = "http://localhost:8000"
    TELEGRAM_MINIAPP_URL: str = ""
    CUSTOMER_BOT_ENABLED: bool = True
    BARISTA_BOT_ENABLED: bool = True
    TELEGRAM_POLL_RETRY_SECONDS: int = 20

    BARISTA_CHAT_ID: int | None = None
    BARISTA_SECRET: str = "coffee-barista-secret"

    INITDATA_TTL_SECONDS: int = 86400
    SESSION_TTL_SECONDS: int = 2592000
    SESSION_SECRET: str = "change-me-coffee-session-secret"
    DEBUG_ALLOW_FAKE_INITDATA: bool = False
    DEFAULT_PICKUP_ETA_MINUTES: int = 7
    AUTO_SEED: bool = True

    @property
    def MINIAPP_URL(self) -> str:
        if self.TELEGRAM_MINIAPP_URL.strip():
            return self.TELEGRAM_MINIAPP_URL.strip()
        return f"{self.PUBLIC_BASE_URL.rstrip('/')}/miniapp"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
