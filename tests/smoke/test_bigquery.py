"""Smoke tests para BigQuery connectivity e tools"""
import pytest
from app.services.bigquery import get_bigquery_client
from app.tools.bigquery_tool import BigQueryTool, BigQueryToolInput
from app.tools.templates import get_template


class TestBigQueryClient:
    """Testes de conexão com BigQuery"""

    def test_bigquery_client_connection(self):
        """Testa se cliente BigQuery inicializa corretamente"""
        client = get_bigquery_client()
        assert client is not None
        assert client.project == "pushnotification-a29e1"

    def test_bigquery_client_singleton(self):
        """Testa se cliente é singleton (mesma instância)"""
        client1 = get_bigquery_client()
        client2 = get_bigquery_client()
        assert client1 is client2


class TestBigQueryTool:
    """Testes para BigQueryTool"""

    def test_bigquery_tool_input_validation(self):
        """Testa validação do BigQueryToolInput"""
        input_data = BigQueryToolInput(
            metric_type="users_volume",
            start_date="2026-03-24",
            end_date="2026-04-23",
            traffic_source=None,
        )
        assert input_data.metric_type == "users_volume"
        assert input_data.start_date == "2026-03-24"

    def test_bigquery_tool_input_invalid_metric(self):
        """Testa rejeição de metric_type inválido"""
        tool = BigQueryTool()
        input_data = BigQueryToolInput(
            metric_type="invalid_metric",
            start_date="2026-03-24",
            end_date="2026-04-23",
        )
        result = tool.run(input_data)
        assert not result["success"]
        assert "métrica inválido" in result["error"] or "Unknown metric_type" in result["error"]

    def test_bigquery_tool_structure(self):
        """Testa estrutura de resposta do tool"""
        tool = BigQueryTool()
        # Teste com metric inválido pra não precisa de credenciais reais
        result = tool.run(
            BigQueryToolInput(
                metric_type="invalid",
                start_date="2026-03-24",
                end_date="2026-04-23",
            )
        )
        assert isinstance(result, dict)
        assert "success" in result
        assert "rows" in result
        assert "row_count" in result
        assert "error" in result


class TestSQLTemplates:
    """Testes para templates SQL"""

    def test_users_volume_template_exists(self):
        """Testa se template users_volume existe"""
        template = get_template("users_volume")
        assert template is not None
        assert "traffic_source" in template
        assert "@start_date" in template
        assert "@end_date" in template

    def test_channel_performance_template_exists(self):
        """Testa se template channel_performance existe"""
        template = get_template("channel_performance")
        assert template is not None
        assert "channel" in template
        assert "SAFE_DIVIDE" in template

    def test_invalid_template_raises(self):
        """Testa se template inválido lança erro"""
        with pytest.raises(KeyError):
            get_template("invalid_template")
