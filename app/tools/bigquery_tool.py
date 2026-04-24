from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.bigquery import bigquery_service
from app.tools.templates import get_template
from app.core.logging import logger
from app.core.exceptions import (
    BigQueryException,
    BigQueryConnectionError,
    BigQueryTimeoutError,
    BigQueryQueryError,
)


class BigQueryToolInput(BaseModel):
    metric_type: str  # "users_volume" | "channel_performance"
    start_date: str
    end_date: str
    traffic_source: Optional[str] = None


class BigQueryTool:
    def run(self, tool_input: BigQueryToolInput) -> Dict[str, Any]:
        """
        Executa ferramenta BigQuery com tratamento de erros
        """
        try:
            # Validação de entrada
            if tool_input.metric_type not in ("users_volume", "channel_performance"):
                error_msg = f"Tipo de métrica inválido: {tool_input.metric_type}. Use 'users_volume' ou 'channel_performance'"
                logger.warning(error_msg)
                return {
                    "success": False,
                    "rows": [],
                    "row_count": 0,
                    "error": error_msg
                }

            # Recupera template SQL
            try:
                sql = get_template(tool_input.metric_type)
            except Exception as e:
                error_msg = f"Erro ao carregar template SQL: {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "rows": [],
                    "row_count": 0,
                    "error": error_msg
                }

            # Prepara parâmetros
            params = {
                "start_date": tool_input.start_date,
                "end_date": tool_input.end_date,
                "traffic_source": tool_input.traffic_source,
            }

            logger.info(f"BigQueryTool executing {tool_input.metric_type} with params: {params}")
            
            # Executa query
            rows = bigquery_service.execute_query(sql, params)
            
            # Validação de resultado
            if not rows:
                logger.warning(f"BigQueryTool returned 0 rows for {tool_input.metric_type}")
                return {
                    "success": True,
                    "rows": [],
                    "row_count": 0,
                    "error": None,
                    "warning": "Nenhum dado encontrado para o período especificado"
                }
            
            logger.info(f"✅ BigQueryTool successfully returned {len(rows)} rows")
            return {
                "success": True,
                "rows": rows,
                "row_count": len(rows),
                "error": None
            }
        
        except BigQueryConnectionError as e:
            error_msg = f"❌ Erro de conexão BigQuery: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "rows": [],
                "row_count": 0,
                "error": error_msg
            }
        
        except BigQueryTimeoutError as e:
            error_msg = f"❌ Timeout ao consultar BigQuery: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "rows": [],
                "row_count": 0,
                "error": error_msg
            }
        
        except BigQueryQueryError as e:
            error_msg = f"❌ Erro na query BigQuery: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "rows": [],
                "row_count": 0,
                "error": error_msg
            }
        
        except BigQueryException as e:
            error_msg = f"❌ Erro BigQuery: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "rows": [],
                "row_count": 0,
                "error": error_msg
            }
        
        except Exception as e:
            error_msg = f"❌ Erro inesperado na ferramenta BigQuery: {type(e).__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "rows": [],
                "row_count": 0,
                "error": error_msg
            }


bigquery_tool = BigQueryTool()


bigquery_tool = BigQueryTool()