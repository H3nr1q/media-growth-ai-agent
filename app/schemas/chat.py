from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=5, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {"message": "Qual canal tem melhor performance no último mês e por quê?"}
        }


class ChatResponse(BaseModel):
    answer: str
    debug: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Search é o melhor canal com $50.000 em receita...",
                "debug": {"intention": "channel_performance", "execution_time_ms": 1234},
            }
        }


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None