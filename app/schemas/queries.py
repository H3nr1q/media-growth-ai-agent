from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum


class IntentionType(str, Enum):
    TRAFFIC_VOLUME = "traffic_volume"
    CHANNEL_PERFORMANCE = "channel_performance"
    OUT_OF_SCOPE = "out_of_scope"


class AgentState(BaseModel):
    user_message: str
    intention: Optional[IntentionType] = None
    query_params: Optional[Dict[str, Any]] = None
    bigquery_result: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[Dict[str, Any]] = None
    final_response: Optional[str] = None
    error: Optional[str] = None
    debug_info: Optional[Dict[str, Any]] = None


class ChannelMetrics(BaseModel):
    name: str
    revenue: float
    users: int
    orders: int
    conversion_rate: float
    aov: float
    revenue_share: float