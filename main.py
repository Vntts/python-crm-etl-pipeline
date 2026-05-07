import logging
from config import setup_logging
from notifier import enviar_alerta_email_global
from bitrix_sync import BitrixSync

if __name__ == "__main__":
    # 1. Inicia as configuracoes de Log
    setup_logging()
    
    sync = None
    try:
        # 2. Inicia o robo
        sync = BitrixSync()
        
        # 3. Executa todas as tarefas
        sync.run_all()
        
    except Exception as e:
        msg_fatal = f"Erro fatal no ETL:\n{e}"
        logging.error(msg_fatal)
        enviar_alerta_email_global(msg_fatal)
        
    finally:
        # 4. Encerra com segurança
        if sync:
            sync.close()