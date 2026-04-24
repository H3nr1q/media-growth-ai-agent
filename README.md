# Media Growth AI Agent - MVP

## 📋 Objetivo

MVP de um agente IA que responde perguntas sobre performance de canais de tráfego usando:
- **FastAPI** para API
- **LangGraph** para orquestração do agente
- **BigQuery** (dataset público thelook_ecommerce) para dados
- **OpenRouter/OpenAI** para LLM (com fallback mock para testes)

---

## 🚀 Instalação

1. **Clone o repositório**
2. **Crie um ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as credenciais do Google Cloud:**
   - Coloque o arquivo `credential_google.json` (Service Account) na **raiz do projeto**
   - Você pode verificar que está correto rodando:
     ```bash
     dir credential_google.json     # Windows
     ```

5. **Configure o arquivo `.env`:**
   
   Crie um arquivo `.env` na raiz do projeto (copie do exemplo):
   ```bash
   cp .env.example .env
   ```
   
   **Edite o `.env` com seus valores:**
   ```
   # LLM Configuration
   LLM_PROVIDER=openrouter  # openai|openrouter|mock

   OPENAI_API_KEY=  # Deixe vazio se usar OpenRouter

   OPENROUTER_API_KEY=  # Preencha com sua chave do OpenRouter
   OPENROUTER_MODEL=nvidia/nemotron-3-super-120b-a12b:free
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

   # Google Cloud / BigQuery
   GOOGLE_APPLICATION_CREDENTIALS=credential_google.json  # Caminho para o arquivo de credenciais
   GCP_PROJECT_ID=  # Seu GCP Project ID
   BQ_DATASET=bigquery-public-data.thelook_ecommerce  # Dataset público

   # API Configuration
   DEBUG=true
   LOG_LEVEL=INFO
   API_PORT=8000

   ```


---

## ⚙️ Execução

```bash
uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000/docs` (Swagger)

### 🤖 Provedores de LLM (2 Opções)

Este MVP foi **desenvolvido e validado com OpenRouter** (modelo 120B gratuito). Existem 2 provedores configuráveis:

| Provider | Modelo | Custo | Validado | Status |
|----------|--------|-------|----------|--------|
| **OpenRouter** | `nvidia/nemotron-3-super-120b-a12b:free` | 🆓 Grátis | ✅ SIM | **Validado em DEV** |
| OpenAI | `gpt-4o-mini` | ~$0.15/1M tokens | ✅ SIM | **Validado em PROD** |

**1. OpenRouter (Usado neste MVP) ✅**
- Modelo: `nvidia/nemotron-3-super-120b-a12b:free` (120B parameters)
- Custo: **$0 (totalmente gratuito)**
- Validado: ✅ Testado e funcionando
- Configure:
  ```
  LLM_PROVIDER=openrouter
  OPENROUTER_API_KEY=sk-or-v1-xxxxx
  ```

**2. OpenAI (Alternativa para Produção) ✅**
- Modelo: `gpt-4o-mini`
- Custo: ~$0.15 por 1M tokens
- Validado: ✅ Testado e funcionando
- Configure:
  ```
  LLM_PROVIDER=openai
  OPENAI_API_KEY=sk-xxxxx
  ```

**Por que 2 provedores no código?**
- 🎯 MVP validado com OpenRouter (gratuito + excelente qualidade)
- 🚀 OpenAI adicionado como fallback/alternativa para produção com SLA
- 💡 Código suporta múltiplos provedores para flexibilidade futura

---

## 📊 Fluxo do Agente (LangGraph Pipeline)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     User Input (Pergunta)                            │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │  1️⃣  PLANNER_NODE                     │
        │  • Detecta intenção                  │
        │  • Extrai datas e filtros           │
        │  • LLM faz parsing JSON             │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │  2️⃣  EXECUTOR_NODE                    │
        │  • Executa query no BigQuery         │
        │  • Retorna linhas de dados           │
        │  • Trata erros (timeout, permissão)  │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │  3️⃣  ANALYZER_NODE                    │
        │  • Calcula métricas                 │
        │  • Agrupa por canal                 │
        │  • Calcula percentuais              │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │  4️⃣  RESPONDER_NODE                   │
        │  • LLM gera resposta em PT-BR       │
        │  • Explica números com contexto     │
        │  • Dá recomendações                 │
        └──────────────┬───────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Response (Resposta Final)                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Detalhamento dos Nós

**planner_node** → Classifica pergunta e extrai parâmetros
**executor_node** → Consulta BigQuery com validação
**analyzer_node** → Calcula Revenue, CR, AOV
**responder_node** → Gera resposta em português com recomendações

---

## 🔌 Endpoints

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/health` | Status da API |
| POST | `/api/v1/chat` | Enviar pergunta ao agente |

**Exemplo (curl):**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Como foi o volume de usuários de Search no último mês?"}'
```

---

## ✅ Perguntas Suportadas

1. **"Qual foi o volume de usuários de Search no último mês?"**
2. **"Qual canal tem melhor performance e por quê?"**

**Fora do escopo:** Previsões, recomendações de produto, setup de ads

---

## 🧪 Testes

### Rodar Smoke Tests (Recomendado para validar setup)

**1. Ative o ambiente virtual:**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

**2. Execute os smoke tests:**
```bash
pytest tests/smoke/ -v
```

**Resultado esperado:**
```
tests/smoke/test_agent.py::TestAgentGraph::test_agent_graph_builds PASSED                                                                                                 [  2%]
tests/smoke/test_agent.py::TestAgentGraph::test_agent_graph_invokes_successfully PASSED                                                                                   [  5%]
tests/smoke/test_agent.py::TestAgentGraph::test_agent_graph_returns_agentstate PASSED                                                                                     [  8%]
tests/smoke/test_agent.py::TestAgentGraph::test_agent_graph_with_query_params PASSED                                                                                      [ 10%]
tests/smoke/test_agent.py::TestAgentNodes::test_planner_node_classifies_intention PASSED                                                                                  [ 13%]
tests/smoke/test_agent.py::TestAgentNodes::test_executor_node_handles_out_of_scope PASSED                                                                                 [ 16%]
tests/smoke/test_agent.py::TestAgentNodes::test_analyzer_node_handles_empty_results PASSED                                                                                [ 18%]
tests/smoke/test_agent.py::TestAgentNodes::test_responder_node_generates_response PASSED                                                                                  [ 21%]
tests/smoke/test_analytics.py::TestCalculateMetrics::test_calculate_metrics_empty_rows PASSED                                                                             [ 24%]
tests/smoke/test_analytics.py::TestCalculateMetrics::test_calculate_metrics_traffic_volume PASSED                                                                         [ 27%]
tests/smoke/test_analytics.py::TestCalculateMetrics::test_calculate_metrics_channel_performance PASSED                                                                    [ 29%]
tests/smoke/test_analytics.py::TestCalculateMetrics::test_calculate_metrics_channel_performance_single_channel PASSED                                                     [ 32%]
tests/smoke/test_analytics.py::TestCalculateMetrics::test_calculate_metrics_revenue_share PASSED                                                                          [ 35%]
tests/smoke/test_analytics.py::TestCalculateMetrics::test_calculate_metrics_zero_revenue PASSED                                                                           [ 37%]
tests/smoke/test_analytics.py::TestCalculateMetrics::test_calculate_metrics_null_handling PASSED                                                                          [ 40%]
tests/smoke/test_analytics.py::TestCalculateMetrics::test_calculate_metrics_returns_json_compatible PASSED                                                                [ 43%]
tests/smoke/test_analytics.py::TestCalculateMetrics::test_calculate_metrics_channel_metrics_type PASSED                                                                   [ 45%]
tests/smoke/test_bigquery.py::TestBigQueryClient::test_bigquery_client_connection PASSED                                                                                  [ 48%]
tests/smoke/test_bigquery.py::TestBigQueryClient::test_bigquery_client_singleton PASSED                                                                                   [ 51%]
tests/smoke/test_bigquery.py::TestBigQueryTool::test_bigquery_tool_input_validation PASSED                                                                                [ 54%]
tests/smoke/test_bigquery.py::TestBigQueryTool::test_bigquery_tool_input_invalid_metric PASSED                                                                            [ 56%]
tests/smoke/test_bigquery.py::TestBigQueryTool::test_bigquery_tool_structure PASSED                                                                                       [ 59%]
tests/smoke/test_bigquery.py::TestSQLTemplates::test_users_volume_template_exists PASSED                                                                                  [ 62%]
tests/smoke/test_bigquery.py::TestSQLTemplates::test_channel_performance_template_exists PASSED                                                                           [ 64%]
tests/smoke/test_bigquery.py::TestSQLTemplates::test_invalid_template_raises PASSED                                                                                       [ 67%]
tests/smoke/test_llm_providers.py::TestLLMProviders::test_get_llm_returns_object PASSED                                                                                   [ 70%]
tests/smoke/test_llm_providers.py::TestLLMProviders::test_get_llm_has_invoke_method PASSED                                                                                [ 72%]
tests/smoke/test_llm_providers.py::TestLLMProviders::test_mock_llm_invoke PASSED                                                                                          [ 75%]
tests/smoke/test_llm_providers.py::TestOpenRouterIntegration::test_openrouter_settings_loaded PASSED                                                                      [ 78%]
tests/smoke/test_llm_providers.py::TestOpenRouterIntegration::test_openrouter_api_key_format PASSED                                                                       [ 81%]
tests/smoke/test_llm_providers.py::TestOpenRouterIntegration::test_openrouter_model_is_mistral PASSED                                                                     [ 83%]
tests/smoke/test_llm_providers.py::TestOpenRouterIntegration::test_openrouter_provider_enum_exists PASSED                                                                 [ 86%]
tests/smoke/test_llm_providers.py::TestOpenRouterIntegration::test_openrouter_invoke_real PASSED                                                                          [ 89%]
tests/smoke/test_llm_providers.py::TestOpenRouterConfiguration::test_openrouter_base_url_correct PASSED                                                                   [ 91%]
tests/smoke/test_llm_providers.py::TestOpenRouterConfiguration::test_openrouter_api_key_not_empty PASSED                                                                  [ 94%]
tests/smoke/test_llm_providers.py::TestOpenRouterConfiguration::test_all_llm_providers_configured PASSED                                                                  [ 97%]
tests/smoke/test_llm_providers.py::TestOpenRouterConfiguration::test_llm_provider_is_valid PASSED                                                                         [100%]
...
======================== 37 passed in 2.34s ========================
```

**O que cada test valida:**
- ✅ Conexão ao BigQuery (credenciais, permissões)
- ✅ LLM provider funcionando (OpenRouter ou OpenAI)
- ✅ Agent respondendo às 2 perguntas principais
- ✅ Parsing JSON do LLM
- ✅ Cálculo de métricas
- ✅ Formatação de resposta em português

---



### Quick Validation (Sem pytest)

Se quiser testar rápido sem instalar pytest:
```bash
# 1. Inicie a API
uvicorn app.main:app --reload

# 2. Em outro terminal, faça uma requisição
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Como foi o volume de usuários de Search no último mês?"}'

# 3. Swagger

# 4. Postman
POST

URL: http://127.0.0.1:8000/api/v1/chat
HEADER: Content-Type : application/json
BODY: 
{
  "message": "Qual dos canais tem a melhor performance? E por que?"
}

```


**Status:** ✅ 37/37 smoke tests passing

---

## 🛠️ Estrutura

```
app/
  core/              # Config, logging, exceptions
  api/               # FastAPI routes
  llm/               # Agent, prompts, LLM providers
  schemas/           # Pydantic models
  services/          # BigQuery client
  tools/             # BigQueryTool, SQL templates, analytics
```

---

## 🎛️ Stack

- FastAPI 0.104+
- LangGraph 1.1.9
- BigQuery
- OpenRouter (120B Free) ou OpenAI gpt-4o-mini
- Pydantic v2.5+
- pytest 9.0.3

---

**Versão**: 0.1.0 (MVP) | **Status**: ✅ Pronto para uso