import os
import json
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest, DeadlineExceeded, Unauthenticated, PermissionDenied
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import (
    BigQueryConnectionError,
    BigQueryQueryError,
    BigQueryTimeoutError,
    BigQueryException,
)


_bigquery_client = None


def get_bigquery_client():
    """Inicializa cliente BigQuery com tratamento de erro"""
    global _bigquery_client
    if _bigquery_client is None:
        try:
            # Garante que a variável de ambiente está setada para autenticação Google
            if settings.google_application_credentials and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
            
            _bigquery_client = bigquery.Client(project=settings.gcp_project_id)
            logger.info(f"✅ BigQuery client initialized for project {settings.gcp_project_id}")
        except (Unauthenticated, PermissionDenied) as e:
            logger.error(f"❌ BigQuery authentication failed: {str(e)}")
            raise BigQueryConnectionError(
                f"Não consegui autenticar com BigQuery. Verifique GOOGLE_APPLICATION_CREDENTIALS e permissões.\nErro: {str(e)}"
            )
        except Exception as e:
            logger.error(f"❌ BigQuery connection failed: {str(e)}")
            raise BigQueryConnectionError(f"Erro ao conectar com BigQuery: {str(e)}")
    
    return _bigquery_client


class BigQueryService:
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Executa query no BigQuery com tratamento completo de erros
        
        Raises:
            BigQueryConnectionError: Se não conseguir conectar
            BigQueryTimeoutError: Se timeout
            BigQueryQueryError: Se erro na query ou nos dados
        """
        try:
            client = get_bigquery_client()
            job_config = bigquery.QueryJobConfig()

            query_params = []
            parameters = parameters or {}

            # Passamos como STRING e fazemos CAST no SQL (simples e robusto)
            for k, v in parameters.items():
                query_params.append(bigquery.ScalarQueryParameter(k, "STRING", None if v is None else str(v)))

            job_config.query_parameters = query_params
            
            logger.info(f"Executing BigQuery query with {len(query_params)} parameters...")
            
            job = client.query(query, job_config=job_config, timeout=30)
            results = job.result(timeout=30)

            rows = [dict(r) for r in results]
            logger.info(f"✅ BigQuery returned {len(rows)} rows")
            return rows
        
        except DeadlineExceeded as e:
            logger.error(f"❌ BigQuery query timeout: {str(e)}")
            raise BigQueryTimeoutError(
                "A query no BigQuery demorou muito. Tente com um período menor ou contate o administrador."
            )
        
        except BadRequest as e:
            logger.error(f"❌ BigQuery query syntax error: {str(e)}")
            raise BigQueryQueryError(
                f"Erro na query SQL. Verifique sintaxe ou campos.\nDetalhes: {str(e)}"
            )
        
        except NotFound as e:
            logger.error(f"❌ BigQuery resource not found: {str(e)}")
            raise BigQueryQueryError(
                f"Tabela ou dataset não encontrado. Verifique BQ_DATASET.\nDetalhes: {str(e)}"
            )
        
        except (Unauthenticated, PermissionDenied) as e:
            logger.error(f"❌ BigQuery permission denied: {str(e)}")
            raise BigQueryConnectionError(
                f"Sem permissão para acessar BigQuery. Verifique credenciais.\nDetalhes: {str(e)}"
            )
        
        except Exception as e:
            logger.error(f"❌ Unexpected BigQuery error: {type(e).__name__}: {str(e)}")
            raise BigQueryQueryError(
                f"Erro inesperado ao consultar BigQuery: {str(e)}"
            )


bigquery_service = BigQueryService()


bigquery_service = BigQueryService()