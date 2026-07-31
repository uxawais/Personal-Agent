from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Chorus Agent"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_SECRET_KEY: str = "change-me"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql+asyncpg://chorus:chorus@localhost:5432/chorus"
    REDIS_URL: str = "redis://localhost:6379/0"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_CHEAP_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "anthropic/claude-sonnet-4"
    OPENROUTER_CHEAP_MODEL: str = "openai/gpt-4o-mini"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    BEDROCK_MODEL: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    DEFAULT_PROVIDER: str = "openai"
    ROUTING_STRATEGY: str = "smart"

    SLACK_BOT_TOKEN: str = ""
    SLACK_APP_TOKEN: str = ""
    SLACK_SIGNING_SECRET: str = ""
    SLACK_ALLOWED_USER_IDS: str = ""

    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_ALLOWED_PHONE_NUMBERS: str = ""

    SERPER_API_KEY: str = ""
    EXA_API_KEY: str = ""

    DASHBOARD_URL: str = "http://localhost:3000"

    @property
    def slack_allowed_user_ids_list(self) -> list[str]:
        return [uid.strip() for uid in self.SLACK_ALLOWED_USER_IDS.split(",") if uid.strip()]

    @property
    def whatsapp_allowed_numbers_list(self) -> list[str]:
        return [n.strip() for n in self.WHATSAPP_ALLOWED_PHONE_NUMBERS.split(",") if n.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
