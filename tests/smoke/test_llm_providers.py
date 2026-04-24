"""Smoke tests para LLM providers"""
import pytest
import os
from app.llm.providers import get_llm
from app.core.config import settings, LLMProvider


class TestLLMProviders:
    """Testes para diferentes providers de LLM"""

    def test_get_llm_returns_object(self):
        """Testa se get_llm retorna um objeto válido"""
        llm = get_llm()
        assert llm is not None
        assert hasattr(llm, "invoke")

    def test_get_llm_has_invoke_method(self):
        """Testa se objeto tem método invoke"""
        llm = get_llm()
        assert callable(getattr(llm, "invoke", None))

    def test_mock_llm_invoke(self):
        """Testa invocação com MOCK LLM"""
        os.environ['LLM_PROVIDER'] = 'mock'
        # Reload config
        import importlib
        import app.core.config
        importlib.reload(app.core.config)
        
        llm = get_llm()
        response = llm.invoke("Test prompt")
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


class TestOpenRouterIntegration:
    """Testes para integração com OpenRouter"""

    def test_openrouter_settings_loaded(self):
        """Testa se settings do OpenRouter estão carregadas"""
        assert settings.openrouter_api_key is not None
        assert settings.openrouter_model is not None
        assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"

    def test_openrouter_api_key_format(self):
        """Testa se API key tem formato válido"""
        api_key = settings.openrouter_api_key
        assert api_key.startswith("sk-or-v1-")

    def test_openrouter_model_is_mistral(self):
        """Testa se modelo configurado é gratuito"""
        assert ":free" in settings.openrouter_model.lower()

    def test_openrouter_provider_enum_exists(self):
        """Testa se OPENROUTER existe no enum"""
        assert hasattr(LLMProvider, 'OPENROUTER')
        assert LLMProvider.OPENROUTER.value == "openrouter"

    def test_openrouter_invoke_real(self):
        """Teste REAL de invocação OpenRouter com API real"""
        from app.llm.providers import get_llm
        from app.core.config import LLMProvider
        
        llm = get_llm()
        
        # Teste com prompt simples
        response = llm.invoke("Responda em uma frase: Qual é a capital da França?")
        assert response is not None
        assert len(response) > 0
        print(f"\n✅ OpenRouter respondeu: {response}")


class TestOpenRouterConfiguration:
    """Testes para configuração do OpenRouter"""

    def test_openrouter_base_url_correct(self):
        """Testa se base URL está correta"""
        assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"

    def test_openrouter_api_key_not_empty(self):
        """Testa se API key não está vazia"""
        assert settings.openrouter_api_key
        assert len(settings.openrouter_api_key) > 20

    def test_all_llm_providers_configured(self):
        """Testa se todos os providers têm configuração"""
        assert settings.openai_api_key is not None or settings.openai_api_key == ""
        assert settings.openrouter_api_key is not None

    def test_llm_provider_is_valid(self):
        """Testa se provider atual é válido"""
        assert settings.llm_provider in [
            LLMProvider.OPENAI,
            LLMProvider.OPENROUTER,
            LLMProvider.MOCK,
        ]
