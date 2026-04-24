from enum import Enum
from typing import Optional
from pydantic_settings import BaseSettings


class LLMProvider(str, Enum):
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    MOCK = "mock"


class Settings(BaseSettings):
    # API
    debug: bool = True
    log_level: str = "INFO"
    api_port: int = 8000

    # LLM
    llm_provider: LLMProvider = LLMProvider.OPENROUTER
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "nvidia/nemotron-3-super-120b-a12b:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # BigQuery
    gcp_project_id: Optional[str] = None
    google_application_credentials: Optional[str] = None
    bq_dataset: str = "bigquery-public-data.thelook_ecommerce"

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",  # Ignora campos do .env que não estão definidos
    }

    def validate_at_startup(self) -> None:
        if self.llm_provider == LLMProvider.OPENAI and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY é obrigatório quando LLM_PROVIDER=openai")


settings = Settings()
settings.validate_at_startup()