import json
from datetime import date, timedelta

from langgraph.graph import StateGraph, END

from app.schemas.queries import AgentState, IntentionType
from app.core.logging import logger
from app.llm.providers import get_llm
from app.llm.prompts import SYSTEM_PROMPT, PLANNER_PROMPT, RESPONDER_PROMPT, OUT_OF_SCOPE_RESPONSE
from app.tools.bigquery_tool import BigQueryTool
from app.tools.analytics import calculate_metrics


def _llm_to_text(response) -> str:
    """Converte resposta do LLM (AIMessage ou string) para string pura"""
    if isinstance(response, str):
        return response
    if hasattr(response, "content"):
        content = response.content
        if isinstance(content, str):
            return content
        return str(content)
    return str(response)


def _last_30_days() -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=30)
    return start.isoformat(), end.isoformat()


def planner_node(state: AgentState) -> AgentState:
    """Classifica intenção e extrai parâmetros da pergunta do usuário"""
    try:
        llm = get_llm()
        today = date.today().isoformat()
        prompt = SYSTEM_PROMPT + "\n\n" + PLANNER_PROMPT.format(user_message=state.user_message, today=today)
        
        logger.info("planner_node: calling LLM to classify intention...")
        try:
            raw_msg = llm.invoke(prompt)
            raw = _llm_to_text(raw_msg)
        except TimeoutError as e:
            logger.error(f"LLM timeout: {str(e)}")
            state.error = "LLM API timeout - tente novamente"
            return state
        except Exception as e:
            # Captura erros de API (rate limit, conexão, etc)
            error_str = str(e).lower()
            if "rate" in error_str or "quota" in error_str:
                state.error = "LLM API rate limit excedido - tente mais tarde"
            elif "api" in error_str or "connection" in error_str:
                state.error = "Erro ao conectar com LLM API - verifique conexão"
            else:
                state.error = f"Erro ao chamar LLM: {str(e)}"
            
            logger.error(f"planner_node LLM error: {state.error}")
            return state

        # Tenta fazer parse do JSON
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: tenta extrair JSON do texto
            logger.warning("Failed to parse JSON directly, trying fallback...")
            if "{" in raw and "}" in raw:
                try:
                    parsed = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
                except json.JSONDecodeError:
                    logger.error(f"Failed to extract JSON from: {raw[:100]}")
                    state.intention = IntentionType.OUT_OF_SCOPE
                    state.debug_info = {"planner_raw": raw, "parse_error": "Could not extract JSON"}
                    return state
            else:
                logger.error("No JSON found in LLM response")
                state.intention = IntentionType.OUT_OF_SCOPE
                state.debug_info = {"planner_raw": raw, "parse_error": "No JSON in response"}
                return state

        # Extrai intenção
        intention = parsed.get("intention", "out_of_scope")
        try:
            state.intention = IntentionType(intention)
            logger.info(f"planner_node: intention detected = {intention}")
        except ValueError:
            logger.warning(f"Unknown intention: {intention}")
            state.intention = IntentionType.OUT_OF_SCOPE

        # Extrai parâmetros de data
        start_date = parsed.get("start_date")
        end_date = parsed.get("end_date")
        traffic_source = parsed.get("traffic_source")

        if not start_date or not end_date:
            start_date, end_date = _last_30_days()
            logger.info(f"Using default date range: {start_date} to {end_date}")

        state.query_params = {
            "start_date": start_date,
            "end_date": end_date,
            "traffic_source": traffic_source if traffic_source not in ("null", "", None) else None,
            "reason": parsed.get("reason"),
        }

        state.debug_info = state.debug_info or {}
        state.debug_info["planner_raw"] = raw
        state.debug_info["planner_parsed"] = parsed
        
        return state

    except Exception as e:
        logger.error("planner_node unexpected error", exc_info=True)
        state.intention = IntentionType.OUT_OF_SCOPE
        state.error = f"Erro ao processar sua pergunta: {str(e)}"
        state.debug_info = state.debug_info or {}
        state.debug_info["planner_error"] = str(e)
        return state


def executor_node(state: AgentState) -> AgentState:
    """Executa query no BigQuery baseado na intenção"""
    if state.error:
        return state
    if state.intention == IntentionType.OUT_OF_SCOPE:
        return state

    try:
        from app.tools.bigquery_tool import BigQueryToolInput
        
        tool = BigQueryTool()
        
        # Prepara parâmetros
        start_date = state.query_params.get("start_date")
        end_date = state.query_params.get("end_date")
        traffic_source = state.query_params.get("traffic_source")
        
        if state.intention == IntentionType.TRAFFIC_VOLUME:
            logger.info(f"executor_node: querying users_volume from {start_date} to {end_date}")
            tool_input = BigQueryToolInput(
                metric_type="users_volume",
                start_date=start_date,
                end_date=end_date,
                traffic_source=traffic_source or None,
            )
        else:  # CHANNEL_PERFORMANCE
            logger.info(f"executor_node: querying channel_performance from {start_date} to {end_date}")
            tool_input = BigQueryToolInput(
                metric_type="channel_performance",
                start_date=start_date,
                end_date=end_date,
                traffic_source=None,  # CHANNEL_PERFORMANCE não filtra por source
            )
        
        result = tool.run(tool_input)
        
        if result.get("success"):
            state.bigquery_result = result.get("rows", [])
            logger.info(f"executor_node: got {len(state.bigquery_result)} rows")
        else:
            state.error = f"BigQuery error: {result.get('error', 'Unknown error')}"
            logger.error(f"executor_node: {state.error}")
        
        return state
    
    except Exception as e:
        logger.error("executor_node failed", exc_info=True)
        state.error = str(e)
        return state


def analyzer_node(state: AgentState) -> AgentState:
    """Calcula métricas a partir dos resultados do BigQuery"""
    if state.error:
        return state
    if not state.bigquery_result:
        state.metrics = {"error": "Sem dados retornados do BigQuery"}
        return state

    try:
        logger.info(f"analyzer_node: processing {len(state.bigquery_result)} rows for {state.intention.value}")
        state.metrics = calculate_metrics(state.bigquery_result, state.intention)
        logger.info(f"analyzer_node: calculated metrics successfully")
        return state
    
    except Exception as e:
        logger.error("analyzer_node failed", exc_info=True)
        state.error = str(e)
        return state


def responder_node(state: AgentState) -> AgentState:
    """Gera resposta final com tratamento de erro informativo"""
    try:
        if state.error:
            # Trata erros específicos com mensagens amigáveis
            error = state.error
            
            if "autenticação" in error.lower() or "authentication" in error.lower():
                state.final_response = (
                    "❌ Erro de autenticação com BigQuery. "
                    "Verifique se o arquivo de credenciais está configurado corretamente no .env"
                )
            elif "timeout" in error.lower() or "deadline" in error.lower():
                state.final_response = (
                    "❌ A consulta demorou muito. Tente com um período menor "
                    "ou contate o administrador do sistema."
                )
            elif "não encontrado" in error.lower() or "not found" in error.lower():
                state.final_response = (
                    "❌ Não consegui encontrar os dados solicitados. "
                    "O dataset ou tabela pode estar indisponível."
                )
            elif "sem dados" in error.lower():
                state.final_response = (
                    "ℹ️ Nenhum dado encontrado para o período especificado. "
                    "Tente com um período mais recente ou um canal diferente."
                )
            else:
                state.final_response = f"❌ Erro ao processar sua pergunta: {error}"
            
            return state

        if state.intention == IntentionType.OUT_OF_SCOPE:
            state.final_response = OUT_OF_SCOPE_RESPONSE
            return state
        
        # Valida se há dados e métricas
        if not state.bigquery_result:
            state.final_response = (
                "ℹ️ Nenhum dado encontrado para consulta. "
                "Tente ajustar o período ou os filtros."
            )
            return state

        llm = get_llm()
        metrics_json = json.dumps(state.metrics or {}, ensure_ascii=False, indent=2)
        prompt = SYSTEM_PROMPT + "\n\n" + RESPONDER_PROMPT.format(
            intention=state.intention.value if state.intention else None,
            metrics_json=metrics_json,
        )
        answer_msg = llm.invoke(prompt)
        state.final_response = _llm_to_text(answer_msg)
        return state

    except Exception as e:
        logger.error("responder_node failed", exc_info=True)
        state.final_response = f"❌ Erro ao gerar resposta final: {str(e)}"
        return state


def should_analyze(state: AgentState) -> str:
    if state.error or state.intention == IntentionType.OUT_OF_SCOPE:
        return "responder"
    return "analyzer"


def build_agent_graph():
    """Constrói o grafo LangGraph"""
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("responder", responder_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "executor")

    graph.add_conditional_edges(
        "executor",
        should_analyze,
        {"analyzer": "analyzer", "responder": "responder"},
    )

    graph.add_edge("analyzer", "responder")
    graph.add_edge("responder", END)

    return graph.compile()