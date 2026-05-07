import sys
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def setup_logging():
    """Inicia o sistema de logs padronizado."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(BASE_DIR / "sincronizacao.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

# gera dados falsos para o projeto
LIMITE_TESTE = 50 # Quantidade de dados falsos gerados por tabela
BITRIX_URL = "https://mock-api-portfolio.bitrix24.com.br/rest/1/mock-token/"

# Banco de dados local para o Portfólio
DB_PATH = BASE_DIR / "portfolio_database.sqlite"