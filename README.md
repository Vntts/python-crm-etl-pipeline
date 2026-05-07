# 🚀 Pipeline ETL: Bitrix24 to SQL (Portfolio Edition)

Este é um projeto de **Engenharia de Dados / Integração** que demonstra a construção de um pipeline ETL (Extract, Transform, Load) robusto em Python. O objetivo principal do script é extrair dados de um CRM (Bitrix24), tratá-los e carregá-los em um Banco de Dados Relacional, lidando com paginação, limites de requisição (rate limit) e atualizações incrementais.

> **Nota:** Esta é uma versão adaptada para portfólio. A infraestrutura original utilizava **PostgreSQL (Supabase)** e **Notificações SMTP reais**. Para facilitar a avaliação por recrutadores e engenheiros, esta versão foi adaptada para rodar localmente com **SQLite** e gera dados fictícios usando a biblioteca `Faker` (Mock API), permitindo testar a arquitetura com um simples comando "plug and play".

> **Nota de performance e escalabilidade:** A arquitetura original deste pipeline foi validada e estressada com uma carga superior a 700.000 registros, servindo como base de dados para dashboards analíticos de BI. Para fins de portfólio, esta versão mock está configurada por padrão para processar 50 registros (ajustável em config.py), garantindo uma execução instantânea e facilitando a auditoria do código sem a necessidade de grandes volumes de armazenamento local.
<br>
<img width="1264" height="900" alt="code" src="https://github.com/user-attachments/assets/c12ea745-ee31-4906-8c28-6487061c7fc9" />


## 🧠 Desafios Técnicos Resolvidos

Neste projeto, apliquei boas práticas de desenvolvimento e arquitetura de dados para garantir performance e resiliência:

* **Controle de Paginação Inteligente (Generator):** Uso de `yield` para lidar com a paginação da API sem sobrecarregar a memória (RAM) durante a extração de grandes volumes de dados.
* **Controle de Rate Limit (Backoff Exponencial):** Tratamento automático de falhas e sobrecarga da API usando tentativas com esperas progressivas.
* **Inserção em Lote (Batching & Upsert):** Os dados não são salvos um a um. Eles são armazenados em um buffer e inseridos em lotes (ex: a cada 1000 registros), utilizando `ON CONFLICT DO UPDATE` para garantir idempotência (Upsert) de forma extremamente rápida.
* **Sincronização Incremental:** O código busca a data da última alteração no banco de dados e consome da API apenas os registros que foram criados ou modificados após essa data, economizando recursos e tempo.
* **Orientação a Objetos (POO):** Estrutura de classes bem definida, tornando a manutenção do código mais simples e modular.

## 🛠️ Tecnologias Utilizadas

* **Python 3.x**
* **SQLite** (Adaptável facilmente para PostgreSQL, MySQL, etc.)
* **Faker** (Para geração de dados mock)
* **Logging** (Para rastreabilidade e observabilidade)

## ⚙️ Como Executar Localmente

Como esta versão utiliza SQLite local e Mocks, o processo de execução é extremamente simples. Nenhuma configuração de variável de ambiente (`.env`) é necessária!

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
   cd seu-repositorio
