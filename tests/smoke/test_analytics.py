"""Smoke tests para cálculo de métricas e analytics"""
import pytest
from app.tools.analytics import calculate_metrics
from app.schemas.queries import IntentionType, ChannelMetrics


class TestCalculateMetrics:
    """Testes para função calculate_metrics"""

    def test_calculate_metrics_empty_rows(self):
        """Testa calculate_metrics com lista vazia"""
        result = calculate_metrics([], IntentionType.TRAFFIC_VOLUME)
        assert "error" in result
        assert result["error"] == "Sem dados para o período"

    def test_calculate_metrics_traffic_volume(self):
        """Testa TRAFFIC_VOLUME metrics calculation"""
        rows = [
            {"traffic_source": "Search", "users": 150, "first_user": "2026-03-24", "last_user": "2026-04-23"},
            {"traffic_source": "Facebook", "users": 100, "first_user": "2026-03-24", "last_user": "2026-04-23"},
        ]
        result = calculate_metrics(rows, IntentionType.TRAFFIC_VOLUME)
        
        assert "channels" in result
        assert len(result["channels"]) == 2
        assert result["channels"][0]["traffic_source"] == "Search"
        assert result["channels"][0]["users"] == 150

    def test_calculate_metrics_channel_performance(self):
        """Testa CHANNEL_PERFORMANCE metrics calculation"""
        rows = [
            {
                "channel": "Search",
                "users": 150,
                "orders": 15,
                "revenue": 5000.0,
                "conversion_rate": 0.10,
                "aov": 333.33,
            },
            {
                "channel": "Facebook",
                "users": 100,
                "orders": 5,
                "revenue": 1500.0,
                "conversion_rate": 0.05,
                "aov": 300.0,
            },
        ]
        result = calculate_metrics(rows, IntentionType.CHANNEL_PERFORMANCE)
        
        assert result["best_channel"] == "Search"
        assert result["total_revenue"] == 6500.0
        assert result["total_users"] == 250
        assert result["total_orders"] == 20
        assert len(result["channels"]) == 2

    def test_calculate_metrics_channel_performance_single_channel(self):
        """Testa CHANNEL_PERFORMANCE com um único canal"""
        rows = [
            {
                "channel": "Organic",
                "users": 200,
                "orders": 20,
                "revenue": 3000.0,
                "conversion_rate": 0.10,
                "aov": 150.0,
            },
        ]
        result = calculate_metrics(rows, IntentionType.CHANNEL_PERFORMANCE)
        
        assert result["best_channel"] == "Organic"
        assert result["total_revenue"] == 3000.0

    def test_calculate_metrics_revenue_share(self):
        """Testa cálculo de revenue_share"""
        rows = [
            {
                "channel": "Search",
                "users": 100,
                "orders": 10,
                "revenue": 4000.0,
                "conversion_rate": 0.10,
                "aov": 400.0,
            },
            {
                "channel": "Facebook",
                "users": 100,
                "orders": 10,
                "revenue": 1000.0,
                "conversion_rate": 0.10,
                "aov": 100.0,
            },
        ]
        result = calculate_metrics(rows, IntentionType.CHANNEL_PERFORMANCE)
        
        # Search deve ter 80% do revenue (4000/5000)
        search_channel = next((c for c in result["channels"] if c["name"] == "Search"), None)
        assert search_channel is not None
        assert abs(search_channel["revenue_share"] - 0.8) < 0.01

    def test_calculate_metrics_zero_revenue(self):
        """Testa cálculo com revenue zero"""
        rows = [
            {
                "channel": "Test",
                "users": 100,
                "orders": 0,
                "revenue": 0.0,
                "conversion_rate": 0.0,
                "aov": 0.0,
            },
        ]
        result = calculate_metrics(rows, IntentionType.CHANNEL_PERFORMANCE)
        
        assert result["total_revenue"] == 0.0
        assert result["channels"][0]["revenue_share"] == 0.0

    def test_calculate_metrics_null_handling(self):
        """Testa tratamento de valores None"""
        rows = [
            {
                "channel": "Search",
                "users": 100,
                "orders": 5,
                "revenue": None,
                "conversion_rate": 0.05,
                "aov": None,
            },
        ]
        result = calculate_metrics(rows, IntentionType.CHANNEL_PERFORMANCE)
        
        # Deve converter None para 0 ou valor padrão
        assert result["total_revenue"] == 0.0
        assert "channels" in result

    def test_calculate_metrics_returns_json_compatible(self):
        """Testa se resultado é JSON-compatível"""
        import json
        
        rows = [
            {
                "channel": "Search",
                "users": 100,
                "orders": 10,
                "revenue": 2000.0,
                "conversion_rate": 0.10,
                "aov": 200.0,
            },
        ]
        result = calculate_metrics(rows, IntentionType.CHANNEL_PERFORMANCE)
        
        # Deve ser serializável a JSON
        json_str = json.dumps(result, ensure_ascii=False)
        assert json_str is not None
        assert len(json_str) > 0

    def test_calculate_metrics_channel_metrics_type(self):
        """Testa se channels contêm ChannelMetrics válidos"""
        rows = [
            {
                "channel": "Search",
                "users": 100,
                "orders": 10,
                "revenue": 2000.0,
                "conversion_rate": 0.10,
                "aov": 200.0,
            },
        ]
        result = calculate_metrics(rows, IntentionType.CHANNEL_PERFORMANCE)
        
        # Channels devem ser dicts (convertidos de ChannelMetrics)
        assert isinstance(result["channels"], list)
        assert isinstance(result["channels"][0], dict)
        assert "name" in result["channels"][0]
        assert "revenue" in result["channels"][0]
