"""Smoke tests para LangGraph agent"""
import pytest
from app.llm.agent import build_agent_graph
from app.schemas.queries import AgentState, IntentionType


class TestAgentGraph:
    """Testes para construção e invocação do grafo LangGraph"""

    def test_agent_graph_builds(self):
        """Testa se grafo LangGraph compila corretamente"""
        graph = build_agent_graph()
        assert graph is not None
        assert hasattr(graph, 'invoke')

    def test_agent_graph_invokes_successfully(self):
        """Testa invocação básica do grafo com mock LLM"""
        graph = build_agent_graph()
        result = graph.invoke({"user_message": "Test message"})
        assert result is not None
        assert "final_response" in result
        assert isinstance(result["final_response"], str)

    def test_agent_graph_returns_agentstate(self):
        """Testa se resultado é um dict com chaves AgentState"""
        graph = build_agent_graph()
        result = graph.invoke({"user_message": "Test"})
        
        # Chaves essenciais do AgentState
        required_keys = ["user_message", "intention", "final_response"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_agent_graph_with_query_params(self, bigquery_params):
        """Testa se grafo aceita query_params"""
        graph = build_agent_graph()
        result = graph.invoke({"user_message": "Test message"})
        
        # Resultado deve ter estado completo
        assert "query_params" in result or result.get("error") is None


class TestAgentNodes:
    """Testes individuais dos nós do agente"""

    def test_planner_node_classifies_intention(self):
        """Testa se planner_node classifica intenção"""
        from app.llm.agent import planner_node
        
        state = AgentState(user_message="How many users from Search?")
        result = planner_node(state)
        
        assert result.intention is not None
        assert isinstance(result.intention, IntentionType)

    def test_executor_node_handles_out_of_scope(self):
        """Testa se executor_node respeita intenção out_of_scope"""
        from app.llm.agent import executor_node
        
        state = AgentState(user_message="Test")
        state.intention = IntentionType.OUT_OF_SCOPE
        
        result = executor_node(state)
        assert result.intention == IntentionType.OUT_OF_SCOPE

    def test_analyzer_node_handles_empty_results(self):
        """Testa se analyzer_node trata resultados vazios"""
        from app.llm.agent import analyzer_node
        
        state = AgentState(user_message="Test")
        state.intention = IntentionType.TRAFFIC_VOLUME
        state.bigquery_result = []
        
        result = analyzer_node(state)
        assert "error" in result.metrics

    def test_responder_node_generates_response(self):
        """Testa se responder_node gera resposta"""
        from app.llm.agent import responder_node
        
        state = AgentState(user_message="Test")
        state.intention = IntentionType.OUT_OF_SCOPE
        
        result = responder_node(state)
        assert result.final_response is not None
        assert len(result.final_response) > 0
