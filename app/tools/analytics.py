from typing import List, Dict, Any
from app.schemas.queries import IntentionType, ChannelMetrics
import json


def calculate_metrics(rows: List[Dict[str, Any]], intention: IntentionType) -> Dict[str, Any]:
    """
    Calcula métricas a partir de dados do BigQuery.
    
    Args:
        rows: Lista de dicts do BigQuery
        intention: TRAFFIC_VOLUME ou CHANNEL_PERFORMANCE
    
    Returns:
        Dict com métricas agregadas
    """
    if not rows:
        return {"error": "Sem dados para o período", "channels": [], "best_channel": None}

    # traffic_volume query tem traffic_source/users
    if intention == IntentionType.TRAFFIC_VOLUME:
        # normaliza para o mesmo shape (sem revenue etc)
        normalized = []
        for r in rows:
            normalized.append(
                {
                    "traffic_source": r.get("traffic_source"),
                    "users": int(r.get("users", 0)),
                    "first_user": str(r.get("first_user", "")),
                    "last_user": str(r.get("last_user", "")),
                }
            )
        return {"channels": normalized}

    # channel_performance query tem channel/users/orders/revenue/conversion_rate/aov
    channels: List[ChannelMetrics] = []
    total_revenue = 0.0
    total_users = 0
    total_orders = 0

    for r in rows:
        cm = ChannelMetrics(
            name=str(r.get("channel", "")),
            revenue=float(r.get("revenue", 0) or 0),
            users=int(r.get("users", 0) or 0),
            orders=int(r.get("orders", 0) or 0),
            conversion_rate=float(r.get("conversion_rate", 0) or 0),
            aov=float(r.get("aov", 0) or 0),
            revenue_share=0.0,
        )
        channels.append(cm)
        total_revenue += cm.revenue
        total_users += cm.users
        total_orders += cm.orders

    for c in channels:
        c.revenue_share = (c.revenue / total_revenue) if total_revenue > 0 else 0.0

    best_channel = max(channels, key=lambda c: c.revenue).name if channels else None
    best_conversion_channel = max(channels, key=lambda c: c.conversion_rate).name if channels else None
    best_aov_channel = max(channels, key=lambda c: c.aov).name if channels else None

    avg_conversion_rate = (
        sum(c.conversion_rate for c in channels) / len(channels)
        if channels
        else 0.0
    )

    return {
        "total_revenue": total_revenue,
        "total_users": total_users,
        "total_orders": total_orders,
        "avg_conversion_rate": avg_conversion_rate,
        "best_channel": best_channel,
        "best_conversion_channel": best_conversion_channel,
        "best_aov_channel": best_aov_channel,
        "channels": [json.loads(c.model_dump_json()) for c in channels],
    }
