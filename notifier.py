import logging

def enviar_alerta_email_global(mensagem):
    """
    Simula o envio de um e-mail de alerta.
    No ambiente real, este módulo usava SMTP para notificar a equipe.
    """
    logging.info("📧 [MOCK EMAIL ENVIADO] Para: equipe-dados@empresa.com")
    logging.info(f"Assunto: Falha no ETL (Bitrix -> Banco de Dados)")
    logging.info(f"Corpo da Mensagem:\n{mensagem}")