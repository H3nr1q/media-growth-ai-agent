"""Pytest configuration and fixtures"""
import os
import pytest

# Usar LLM mock para testes
os.environ['LLM_PROVIDER'] = 'mock'


@pytest.fixture
def agent_state():
    """Fixture para AgentState inicial"""
    from app.schemas.queries import AgentState
    return AgentState(user_message="Test message")


@pytest.fixture
def bigquery_params():
    """Fixture para parâmetros de BigQuery"""
    return {
        "start_date": "2026-03-24",
        "end_date": "2026-04-23",
        "traffic_source": None,
    }
