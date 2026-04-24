"""
Exceções customizadas para o agente
"""


class AgentException(Exception):
    """Exceção base para o agente"""
    pass


class BigQueryException(AgentException):
    """Exceção para erros do BigQuery"""
    pass


class BigQueryConnectionError(BigQueryException):
    """Erro ao conectar no BigQuery"""
    pass


class BigQueryQueryError(BigQueryException):
    """Erro ao executar query no BigQuery"""
    pass


class BigQueryTimeoutError(BigQueryException):
    """Timeout ao executar query no BigQuery"""
    pass


class LLMException(AgentException):
    """Exceção para erros do LLM"""
    pass


class LLMAPIError(LLMException):
    """Erro ao chamar API do LLM"""
    pass


class LLMTimeoutError(LLMException):
    """Timeout ao chamar LLM"""
    pass


class LLMRateLimitError(LLMException):
    """Rate limit excedido no LLM"""
    pass


class IntentionDetectionError(AgentException):
    """Não conseguiu detectar intenção da pergunta"""
    pass
