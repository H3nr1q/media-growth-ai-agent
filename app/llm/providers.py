from typing import Any
from langchain_openai import ChatOpenAI
from langchain_community.llms.fake import FakeListLLM
from app.core.config import settings, LLMProvider
from app.core.logging import logger


def get_llm() -> Any:
    """
    Retorna um objeto com método .invoke(prompt: str) -> str.
    """
    if settings.llm_provider == LLMProvider.OPENAI:
        logger.info("Using OpenAI LLM (gpt-4o-mini)")
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model="gpt-4o-mini",
            temperature=0.3,
        )

    if settings.llm_provider == LLMProvider.OPENROUTER:
        logger.info(f"Using OpenRouter LLM ({settings.openrouter_model})")
        return ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            temperature=0.3,
        )

    # MOCK: respostas determinísticas para testes offline
    logger.info("Using MOCK LLM for offline testing")
    return FakeListLLM(
        responses=[
            '{"intention":"channel_performance","start_date":"2026-03-24","end_date":"2026-04-23","traffic_source":null,"reason":"mock"}',
            "Search é o melhor canal (mock). Receita maior, boa conversão e AOV alto. Recomendação: priorizar Search.",
        ]
    )