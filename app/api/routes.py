from fastapi import APIRouter, HTTPException
import time

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.queries import AgentState
from app.core.config import settings
from app.core.logging import logger
from app.llm.agent import build_agent_graph

router = APIRouter()
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_agent_graph()
        logger.info("Agent graph built and cached")
    return _graph


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    try:
        start = time.time()

        graph = get_graph()
        initial_state = AgentState(user_message=req.message)
        result_dict = graph.invoke(initial_state.model_dump())
        result = AgentState(**result_dict)

        elapsed_ms = (time.time() - start) * 1000.0

        answer = result.final_response or "Não consegui gerar resposta."
        debug = None
        if settings.debug:
            debug = {
                "intention": str(result.intention) if result.intention else None,
                "execution_time_ms": elapsed_ms,
                "error": result.error,
                "bigquery_rows": len(result.bigquery_result or []),
            }

        return ChatResponse(answer=answer, debug=debug)

    except Exception as e:
        logger.error("Chat error", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))