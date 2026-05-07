import copy
import time
import logging
import sqlite3
import random
from datetime import datetime, timedelta
from config import DB_PATH, LIMITE_TESTE
from notifier import enviar_alerta_email_global
from faker import Faker

# Inicializa o gerador de dados falsos em PT-BR
fake = Faker('pt_BR')

class DBConfig:
    TABLES = {
        "deals": "deals",
        "tasks": "tasks",
        "users": "users",     
        "leads": "leads",
        "contacts": "contacts",
        "groups": "grupos_trabalho", # Evitando palavra reservada no SQLite
        "departments": "departments"
    }

class BitrixSync:
    def __init__(self):
        # Conecta ao SQLite local (cria o arquivo se não existir)
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        logging.info("Conexão com Banco de Dados SQLite (Portfólio) OK.")
        self._create_tables_if_not_exist()
        
    def _create_tables_if_not_exist(self):
        """Cria as tabelas dinamicamente para que o avaliador não precise configurar banco."""
        query = """
        CREATE TABLE IF NOT EXISTS users (bitrix_id INTEGER PRIMARY KEY, nome TEXT, sobrenome TEXT, email TEXT, ativo BOOLEAN, departamento_id INTEGER, cargo TEXT, telefone TEXT, tipo_usuario TEXT, data_registro TEXT, ultimo_login TEXT, ultima_sincronizacao TEXT);
        CREATE TABLE IF NOT EXISTS departments (bitrix_id INTEGER PRIMARY KEY, nome TEXT, pai_id INTEGER, ultima_sincronizacao TEXT);
        CREATE TABLE IF NOT EXISTS grupos_trabalho (bitrix_id INTEGER PRIMARY KEY, nome TEXT, ativo BOOLEAN, ultima_sincronizacao TEXT);
        CREATE TABLE IF NOT EXISTS tasks (bitrix_id INTEGER PRIMARY KEY, titulo TEXT, descricao TEXT, responsavel_id INTEGER, criado_por INTEGER, data_criacao TEXT, data_alteracao TEXT, status INTEGER, prazo TEXT, data_conclusao TEXT, grupo_id INTEGER, tempo_estimado INTEGER, tempo_gasto INTEGER, prioridade INTEGER);
        CREATE TABLE IF NOT EXISTS leads (bitrix_id INTEGER PRIMARY KEY, titulo TEXT, status_id TEXT, oportunidade REAL, moeda TEXT, data_criacao TEXT, data_alteracao TEXT, telefone TEXT, email TEXT);
        CREATE TABLE IF NOT EXISTS contacts (bitrix_id INTEGER PRIMARY KEY, nome TEXT, sobrenome TEXT, tipo_contato TEXT, data_criacao TEXT, data_alteracao TEXT, telefone TEXT, email TEXT);
        CREATE TABLE IF NOT EXISTS deals (bitrix_id INTEGER PRIMARY KEY, titulo TEXT, tipo_id TEXT, estagio_id TEXT, categoria_id INTEGER, valor REAL, moeda TEXT, probabilidade REAL, empresa_id INTEGER, contato_id INTEGER, responsavel_id INTEGER, criado_por_id INTEGER, data_criacao TEXT, data_alteracao TEXT, fechado BOOLEAN, ultima_sincronizacao TEXT);
        """
        self.cursor.executescript(query)
        self.conn.commit()

    # MÉTODOS MOCK DE API (PORTFÓLIO)
 
    def _make_request(self, endpoint, payload, retries=3):
        logging.info(f"Mock da API ativado para: [{endpoint}]")
        time.sleep(random.uniform(0.05, 0.2)) # Simula latência de rede
        
        start = payload.get("start", 0)
        if start > 0:
            if endpoint == "tasks.task.list": return {"result": {"tasks": []}}
            return {"result": []}

        return self._generate_mock_data(endpoint)
        
    def _generate_mock_data(self, endpoint):
        data = []
        qtd = LIMITE_TESTE or 25
        
        if endpoint == "user.get":
            for _ in range(qtd): data.append({"ID": str(fake.unique.random_number(digits=4)), "NAME": fake.first_name(), "LAST_NAME": fake.last_name(), "EMAIL": fake.company_email(), "ACTIVE": True, "WORK_POSITION": fake.job(), "PERSONAL_MOBILE": fake.cellphone_number()})
            return {"result": data}
        elif endpoint == "crm.lead.list":
            for _ in range(qtd): data.append({"ID": str(fake.unique.random_number(digits=5)), "TITLE": f"Lead - {fake.company()}", "STATUS_ID": "NEW", "OPPORTUNITY": str(round(random.uniform(1000, 50000), 2)), "CURRENCY_ID": "BRL", "DATE_CREATE": fake.iso8601()})
            return {"result": data}
        elif endpoint == "crm.deal.list":
            for _ in range(qtd): data.append({"ID": str(fake.unique.random_number(digits=5)), "TITLE": f"Venda - {fake.company()}", "STAGE_ID": "WON", "OPPORTUNITY": str(round(random.uniform(5000, 100000), 2)), "CURRENCY_ID": "BRL", "PROBABILITY": "100", "DATE_CREATE": fake.iso8601(), "CLOSED": "Y"})
            return {"result": data}
        elif endpoint == "crm.contact.list":
            for _ in range(qtd): data.append({"ID": str(fake.unique.random_number(digits=5)), "NAME": fake.first_name(), "LAST_NAME": fake.last_name(), "TYPE_ID": "CLIENT", "DATE_CREATE": fake.iso8601(), "PHONE": [{"VALUE": fake.cellphone_number()}], "EMAIL": [{"VALUE": fake.free_email()}]})
            return {"result": data}
        elif endpoint == "department.get":
            for i in range(1, 6): data.append({"ID": str(i), "NAME": f"Dep. de {fake.job().split()[0]}", "PARENT": "0"})
            return {"result": data}
        elif endpoint == "sonet_group.get":
            for _ in range(5): data.append({"ID": str(fake.unique.random_number(digits=3)), "NAME": f"Projeto {fake.bs().title()}", "ACTIVE": True})
            return {"result": data}
        elif endpoint == "tasks.task.list":
            for _ in range(qtd): data.append({"id": str(fake.unique.random_number(digits=4)), "title": fake.catch_phrase(), "description": fake.text(), "responsibleId": "1", "createdBy": "1", "createdDate": fake.iso8601(), "changedDate": fake.iso8601(), "status": "2", "priority": "1"})
            return {"result": {"tasks": data}}
        return {"result": []}

    def _fetch_paginated(self, endpoint, base_params=None, data_key=None):
        if base_params is None: base_params = {}
        start = 0
        total_processado = 0
        while True:
            if LIMITE_TESTE and total_processado >= LIMITE_TESTE: break
            params = copy.deepcopy(base_params)
            params["start"] = start
            res = self._make_request(endpoint, params)
            data = res.get("result", [])
            items = data.get(data_key, []) if data_key and isinstance(data, dict) else data
            if not items: break
            for item in items:
                if LIMITE_TESTE and total_processado >= LIMITE_TESTE: break
                yield item
                total_processado += 1
            if len(items) < 50: break
            start += 50

    def _bulk_upsert(self, query, buffer, entity_name):
        if not buffer: return
        try:
            self.cursor.executemany(query, buffer)
            self.conn.commit()
            logging.info(f"{entity_name}: {len(buffer)} registros salvos com sucesso!")
        except Exception as db_err:
            self.conn.rollback()
            raise Exception(f"Erro ao salvar {entity_name}: {db_err}")
 
    def get_last_update(self, table, column="data_alteracao"):
        try:
            self.cursor.execute(f"SELECT MAX({column}) FROM {table}")
            res = self.cursor.fetchone()
            return res[0] if res and res[0] else "2010-01-01T00:00:00+00:00"
        except: return "2010-01-01T00:00:00+00:00"
 
    def _extract_primary_contact(self, contact_list):
        if not contact_list: return None
        if isinstance(contact_list, list) and len(contact_list) > 0: return contact_list[0].get("VALUE")
        if isinstance(contact_list, dict): return contact_list.get("VALUE")
        return None
 
    def _to_int_or_none(self, val): return int(val) if val not in [None, "", "0"] else None
    
    def _ajustar_fuso_horario(self, date_str):
        if not date_str or str(date_str).strip() == "": return None
        try:
            dt = datetime.fromisoformat(date_str[:19]) + timedelta(hours=-3)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except: return None
 
    def _sync_entity(self, entity_name, table_name, endpoint, data_mapper, upsert_query, is_incremental=True, date_field="DATE_MODIFY", extra_params=None, data_key=None):
        params = copy.deepcopy(extra_params) if extra_params else {}
        if is_incremental:
            params.setdefault("filter", {})[f">={date_field}"] = self.get_last_update(table_name, "data_alteracao")
        buffer_dict = {}
        for item in self._fetch_paginated(endpoint, params, data_key=data_key):
            mapped = data_mapper(item)
            if mapped: buffer_dict[mapped[0]] = mapped
        self._bulk_upsert(upsert_query, list(buffer_dict.values()), entity_name)
 
    # REGRAS DE NEGÓCIO E MAPEAMENTO SQL
 
    def sync_users(self):
        query = f"INSERT INTO {DBConfig.TABLES['users']} (bitrix_id, nome, sobrenome, email, ativo, departamento_id, cargo, telefone, tipo_usuario, data_registro, ultimo_login) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (bitrix_id) DO UPDATE SET nome=EXCLUDED.nome, sobrenome=EXCLUDED.sobrenome, email=EXCLUDED.email, ativo=EXCLUDED.ativo, departamento_id=EXCLUDED.departamento_id, cargo=EXCLUDED.cargo, telefone=EXCLUDED.telefone, tipo_usuario=EXCLUDED.tipo_usuario, data_registro=EXCLUDED.data_registro, ultimo_login=EXCLUDED.ultimo_login, ultima_sincronizacao=datetime('now', 'localtime')"
        self._sync_entity("Usuarios", DBConfig.TABLES['users'], "user.get", lambda u: (int(u["ID"]), u.get("NAME"), u.get("LAST_NAME"), u.get("EMAIL"), u.get("ACTIVE") in [True, "Y", "true", "1"], (u.get("UF_DEPARTMENT") or [None])[0], u.get("WORK_POSITION"), u.get("PERSONAL_MOBILE") or u.get("WORK_PHONE"), u.get("USER_TYPE") or "employee", u.get("DATE_REGISTER") or None, u.get("LAST_LOGIN") or None), query, is_incremental=False)
 
    def sync_departments(self):
        query = f"INSERT INTO {DBConfig.TABLES['departments']} (bitrix_id, nome, pai_id) VALUES (?, ?, ?) ON CONFLICT (bitrix_id) DO UPDATE SET nome=EXCLUDED.nome, pai_id=EXCLUDED.pai_id, ultima_sincronizacao=datetime('now', 'localtime')"
        res = self._make_request("department.get", {})
        buffer = [(int(d["ID"]), d.get("NAME"), int(d.get("PARENT") or 0)) for d in res.get("result", [])]
        self._bulk_upsert(query, buffer, "Departamentos")
 
    def sync_groups(self):
        query = f"INSERT INTO {DBConfig.TABLES['groups']} (bitrix_id, nome, ativo) VALUES (?, ?, ?) ON CONFLICT (bitrix_id) DO UPDATE SET nome=EXCLUDED.nome, ativo=EXCLUDED.ativo, ultima_sincronizacao=datetime('now', 'localtime')"
        self._sync_entity("Grupos", DBConfig.TABLES['groups'], "sonet_group.get", lambda g: (int(g["ID"]), g.get("NAME"), g.get("ACTIVE") in [True, "Y", "true", "1"]), query, is_incremental=False)
 
    def sync_tasks(self):
        query = f"INSERT INTO {DBConfig.TABLES['tasks']} (bitrix_id, titulo, descricao, responsavel_id, criado_por, data_criacao, data_alteracao, status, prazo, data_conclusao, grupo_id, tempo_estimado, tempo_gasto, prioridade) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (bitrix_id) DO UPDATE SET titulo=EXCLUDED.titulo, descricao=EXCLUDED.descricao, responsavel_id=EXCLUDED.responsavel_id, criado_por=EXCLUDED.criado_por, data_alteracao=EXCLUDED.data_alteracao, status=EXCLUDED.status, prazo=EXCLUDED.prazo, data_conclusao=EXCLUDED.data_conclusao, grupo_id=EXCLUDED.grupo_id, tempo_estimado=EXCLUDED.tempo_estimado, tempo_gasto=EXCLUDED.tempo_gasto, prioridade=EXCLUDED.prioridade"
        self._sync_entity("Tasks", DBConfig.TABLES['tasks'], "tasks.task.list", lambda t: (int(t["id"]), t.get("title"), t.get("description"), int(t.get("responsibleId") or 0), int(t.get("createdBy") or 0), self._ajustar_fuso_horario(t.get("createdDate")), self._ajustar_fuso_horario(t.get("changedDate")), int(t.get("status") or 0), self._ajustar_fuso_horario(t.get("deadline")), self._ajustar_fuso_horario(t.get("closedDate")), int(t.get("groupId") or 0), int(t.get("timeEstimate") or 0), int(t.get("timeSpentInLogs") or 0), int(t.get("priority") or 2)), query, data_key="tasks")
 
    def sync_leads(self):
        query = f"INSERT INTO {DBConfig.TABLES['leads']} (bitrix_id, titulo, status_id, oportunidade, moeda, data_criacao, data_alteracao, telefone, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (bitrix_id) DO UPDATE SET titulo=EXCLUDED.titulo, status_id=EXCLUDED.status_id, oportunidade=EXCLUDED.oportunidade, data_alteracao=EXCLUDED.data_alteracao, telefone=EXCLUDED.telefone, email=EXCLUDED.email"
        self._sync_entity("Leads", DBConfig.TABLES['leads'], "crm.lead.list", lambda l: (int(l["ID"]), l.get("TITLE"), l.get("STATUS_ID"), float(l.get("OPPORTUNITY") or 0), l.get("CURRENCY_ID"), self._ajustar_fuso_horario(l.get("DATE_CREATE")), self._ajustar_fuso_horario(l.get("DATE_MODIFY") or l.get("DATE_CREATE")), self._extract_primary_contact(l.get("PHONE")), self._extract_primary_contact(l.get("EMAIL"))), query)
 
    def sync_contacts(self):
        query = f"INSERT INTO {DBConfig.TABLES['contacts']} (bitrix_id, nome, sobrenome, tipo_contato, data_criacao, data_alteracao, telefone, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (bitrix_id) DO UPDATE SET nome=EXCLUDED.nome, sobrenome=EXCLUDED.sobrenome, data_alteracao=EXCLUDED.data_alteracao, telefone=EXCLUDED.telefone, email=EXCLUDED.email"
        self._sync_entity("Contatos", DBConfig.TABLES['contacts'], "crm.contact.list", lambda c: (int(c["ID"]), c.get("NAME"), c.get("LAST_NAME"), c.get("TYPE_ID", "CLIENT"), self._ajustar_fuso_horario(c.get("DATE_CREATE")), self._ajustar_fuso_horario(c.get("DATE_MODIFY") or c.get("DATE_CREATE")), self._extract_primary_contact(c.get("PHONE")), self._extract_primary_contact(c.get("EMAIL"))), query)
 
    def sync_deals(self):
        query = f"INSERT INTO {DBConfig.TABLES['deals']} (bitrix_id, titulo, tipo_id, estagio_id, categoria_id, valor, moeda, probabilidade, empresa_id, contato_id, responsavel_id, criado_por_id, data_criacao, data_alteracao, fechado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (bitrix_id) DO UPDATE SET titulo=EXCLUDED.titulo, tipo_id=EXCLUDED.tipo_id, estagio_id=EXCLUDED.estagio_id, categoria_id=EXCLUDED.categoria_id, valor=EXCLUDED.valor, moeda=EXCLUDED.moeda, probabilidade=EXCLUDED.probabilidade, empresa_id=EXCLUDED.empresa_id, contato_id=EXCLUDED.contato_id, responsavel_id=EXCLUDED.responsavel_id, criado_por_id=EXCLUDED.criado_por_id, data_alteracao=EXCLUDED.data_alteracao, fechado=EXCLUDED.fechado, ultima_sincronizacao=datetime('now', 'localtime')"
        self._sync_entity("Negocios", DBConfig.TABLES['deals'], "crm.deal.list", lambda d: (int(d["ID"]), d.get("TITLE"), d.get("TYPE_ID"), d.get("STAGE_ID"), self._to_int_or_none(d.get("CATEGORY_ID")), float(d.get("OPPORTUNITY") or 0), d.get("CURRENCY_ID"), float(d.get("PROBABILITY") or 0), self._to_int_or_none(d.get("COMPANY_ID")), self._to_int_or_none(d.get("CONTACT_ID")), self._to_int_or_none(d.get("ASSIGNED_BY_ID")), self._to_int_or_none(d.get("CREATED_BY_ID")), self._ajustar_fuso_horario(d.get("DATE_CREATE")), self._ajustar_fuso_horario(d.get("DATE_MODIFY") or d.get("DATE_CREATE")), d.get("CLOSED") in ["Y", "true", True, "1"]), query)
 
    def close(self):
        if hasattr(self, "cursor") and self.cursor: self.cursor.close()
        if hasattr(self, "conn") and self.conn: self.conn.close()
 
    def run_all(self):
        for nome, rotina in [("Usuarios", self.sync_users), ("Departamentos", self.sync_departments), ("Grupos", self.sync_groups), ("Tasks", self.sync_tasks), ("Leads", self.sync_leads), ("Contatos", self.sync_contacts), ("Negocios", self.sync_deals)]:
            try:
                logging.info(f"--- Iniciando módulo: {nome} ---")
                rotina()
            except Exception as e:
                msg_erro = f"Erro no módulo {nome}:\n{e}"
                logging.error(msg_erro)
                enviar_alerta_email_global(msg_erro)
        logging.info("Sincronização Geral Finalizada!")