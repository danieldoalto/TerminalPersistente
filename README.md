# Terminal Session Manager

Terminal Session Manager minimalista, modular e orientado a agentes. O sistema mantém sessões de terminal persistentes independentemente do agente que as iniciou, gerencia execução de jobs, preserva histórico ordenado de eventos e opera dispositivos cadastrados sem expor credenciais em texto puro.

Este repositório implementa a arquitetura incremental descrita em [`spec.md`](spec.md).

---

## Etapa 0 — Contrato e Esqueleto

Nesta etapa inicial foi construído o esqueleto executável e os contratos fundamentais de domínio, sem acoplamento a integrações de rede ou bibliotecas externas no núcleo:

- **Modelos de Domínio:**
  - `Session` e `SessionStatus` (`created`, `running`, `waiting`, `completed`, `failed`, `closed`, `lost`) com máquina de estados e validação estrita de transições.
  - `Job` e `JobStatus` (`created`, `running`, `completed`, `failed`, `cancelled`, `timeout`) com controle de ciclo de vida, códigos de saída e timestamps.
  - `Device`, `DeviceType` e `ConnectionMethod` para catálogo de inventário e parametrização segura de conexões.
  - `CredentialRef` e `CredentialType` com garantia estrutural de não armazenar nem vazar segredos ao agente ou histórico.
  - `Event` e `EventType` (`stdin`, `stdout`, `stderr`, `state_change`, `system`) com suporte a ordenação estrita (`sequence`, `timestamp`) e flags para mascaramento de dados sensíveis.
- **Interfaces e Contratos (`typing.Protocol`):**
  - `SessionRepository`, `JobRepository`, `EventRepository` (persistência).
  - `TerminalTransport` (adaptadores de transporte/PTY).
  - `DeviceRepository` (catálogo de dispositivos).
  - `CredentialResolver` (resolução interna de segredos para adaptadores).
- **Erros de Domínio:**
  - `DomainError`, `InvalidStateTransitionError`, `InvalidStateError`, `EntityNotFoundError`, `SessionNotFoundError`, `JobNotFoundError`, `DeviceNotFoundError`, `CredentialNotFoundError` e `ValidationError`.

---

## Etapa 1 — Sessão Local Mínima

Implementa um adaptador concreto de terminal/processo local e um orquestrador de sessão conectado ao ciclo de vida de `Session`:

- **`LocalProcessTransport` (`transports/local_process.py`):**
  - Implementa o protocolo `TerminalTransport` sobre subprocessos do sistema operacional.
  - Leitura não-bloqueante multithread com suporte a timeout real e isolamento cross-platform (Windows e Linux).
  - Operações de `open`, `read`, `write`, `resize` e `close` com liberação limpa de recursos.
- **`LocalSession` (`services/local_session.py`):**
  - Orquestra sessões de terminal acopladas a transportes via injeção de dependências (pluggable).
  - Sincroniza o ciclo de vida da entidade `Session` (`CREATED -> RUNNING -> COMPLETED / FAILED / CLOSED`) com o estado real do transporte.
  - Métodos de conveniência como `read_text()` e `write()`.

---

## Etapa 2 — Persistência e Histórico

Implementa persistência durável em SQLite (`sqlite3` da biblioteca padrão) para sessões, jobs e histórico sequencial de eventos:

- **Repositórios SQLite (`persistence/sqlite.py`):**
  - `SqliteSessionRepository`: CRUD e upsert de metadados e ciclo de vida de sessões.
  - `SqliteJobRepository`: CRUD e vinculação de jobs com comandos e resultados.
  - `SqliteEventRepository`: persistência com unicidade estrita `(session_id, sequence)`, ordenação e paginação por cursor (`since_sequence`, `limit`).
- **Histórico e Proteção de Segredos (`services/local_session.py`):**
  - Emissão e persistência automática de eventos `STDIN`, `STDOUT`, `STDERR` e `STATE_CHANGE`.
  - Suporte a `write(..., is_sensitive=True)` registrando eventos com `is_masked=True` e payload mascarado `"[REDACTED]"`, impedindo vazamento de segredos para a base durável.
  - Recuperação completa de estado e histórico após reinício do serviço.

---

## Etapa 3 — Jobs Assíncronos

Implementa execução, espera, cancelamento e monitoramento de jobs desacoplados da conexão contínua do cliente:

- **Serviço de Jobs (`JobService` em `services/job_service.py`):**
  - Submissão não-bloqueante (`submit_job`) com execução em thread dedicada e subprocesso isolado.
  - Vínculo a `session_id` e persistência contínua de eventos (`STATE_CHANGE`, `STDIN`, `STDOUT`, `STDERR`).
  - Espera com bloqueio sincronizado (`wait_job`) e cancelamento forçado com terminação de processo (`cancel_job`).
  - Controle de timeout por job com transição para `TIMEOUT` e encerramento de processo.
  - Reconciliação em reinício (`recover_orphaned_jobs`): jobs interrompidos por crash/reinício do serviço são detectados e marcados como `FAILED`, garantindo que nenhuma falha seja silenciosa.

---

## Etapa 4 — Dispositivos e Credenciais

Implementa o catálogo persistente de dispositivos e a resolução segura de credenciais:

- **Catálogo de Dispositivos (`persistence/sqlite.py` e `services/device_service.py`):**
  - `SqliteDeviceRepository`: persistência durável de metadados não-secretos no SQLite (`devices`), com garantia de unicidade de nome/nickname e exclusão lógica (`is_deleted`).
  - `DeviceService`: gerenciamento completo de ciclo de vida (criação, consulta, atualização, desativação e remoção lógica) e resolução interna de dados de conexão (`resolve_connection`).
- **Resolução Segura e Proteção em Repouso (`services/credential_store.py`):**
  - `ProtectedLocalCredentialStore`: armazenamento local cifrado em SQLite (`credential_secrets`) usando derivação de chaves PBKDF2-HMAC-SHA256, cifra de fluxo autenticada e tags HMAC contra adulteração, mantendo zero dependências externas no runtime e nunca persistindo segredos em texto puro.
  - `DelegatingCredentialResolver`: resolução com delegação a provedores externos (`ExternalCredentialProvider`) e fallback local.
  - `ResolvedConnection`: objeto de trânsito em memória estrita, ocultando segredos em representações (`__repr__`) e inacessível a agentes.
- **Integração à Sessão e Mascaramento de Saídas (`services/local_session.py`):**
  - Associação injetável da resolução de dispositivo no fluxo de `LocalSession`.
  - Mascaramento dinâmico em saídas de terminal: qualquer eco ou saída contendo o segredo resolvido é redigido para `[REDACTED]` antes da persistência de eventos no histórico.

---

## Etapa 5 — API HTTP

Expõe por HTTP os serviços essenciais do Terminal Session Manager através de uma arquitetura leve, minimalista e sem dependências externas:

- **Coordenação de Sessões (`SessionService` em `services/session_service.py`):**
  - Gerencia instâncias de sessões interativas em memória (`LocalSession`), integrando-as com `SqliteSessionRepository`, `EventRepository` e `DeviceService`.
  - Suporte à escrita (`write_session`) e leitura mascarada (`read_session`).
- **Servidor HTTP e Roteador (`APIServer` e `TSMRequestHandler` em `api/`):**
  - Servidor multi-threaded baseado em `http.server.ThreadingHTTPServer` da biblioteca padrão do Python.
  - Autenticação local configurável via Bearer token (`Authorization: Bearer <token>`) ou `X-API-Key`.
  - Mapeamento uniforme e sanitizado de exceções de domínio para códigos HTTP (`400`, `401`, `404`, `409`, `500`).
  - **Endpoints Disponíveis:**
    - `POST /sessions`: Cria e inicia nova sessão.
    - `GET /sessions`: Lista todas as sessões cadastradas.
    - `GET /sessions/{id}`: Consulta metadados da sessão.
    - `POST /sessions/{id}/write`: Escreve dados na sessão ativa (com flag `is_sensitive`).
    - `POST /sessions/{id}/read`: Lê dados do canal de saída da sessão.
    - `POST /sessions/{id}/close`: Encerra o canal de transporte da sessão.
    - `GET /sessions/{id}/events?since_sequence=...&limit=...`: Consulta paginada do histórico por cursor sequencial.
    - `POST /sessions/{id}/jobs` e `POST /jobs`: Submete um job assíncrono.
    - `GET /jobs/{id}`: Consulta status, exit_code e saídas do job.
    - `GET /sessions/{id}/jobs`: Lista jobs associados a uma sessão.
    - `POST /jobs/{id}/wait`: Aguarda conclusão com timeout.
    - `POST /jobs/{id}/cancel`: Cancela execução de um job em andamento.
    - `POST /devices`: Cadastra novo dispositivo no catálogo.
    - `GET /devices`: Lista dispositivos registrados (`?only_active=true`).
    - `GET /devices/{id_or_name}`: Consulta detalhes do dispositivo.
    - `PATCH /devices/{id}`: Atualiza parâmetros do dispositivo.
    - `POST /devices/{id}/deactivate`: Desativa logicamente um dispositivo.
    - `GET /devices/{id_or_name}/resolve`: Resolve parâmetros de conexão por nickname **sem expor segredos** (`has_credential: true/false`).

---

## Etapa 6 — MCP com FastMCP

Expõe as capacidades essenciais do Terminal Session Manager para agentes de inteligência artificial através do protocolo **Model Context Protocol (MCP)**, utilizando a biblioteca **FastMCP**:

- **Servidor FastMCP (`terminal_session_manager.mcp.server`):**
  - Execução via transporte padrão `stdio`, compatível com Claude Desktop, Cursor, Antigravity e clientes MCP em geral.
  - Reutiliza diretamente as instâncias de domínio (`SessionService`, `JobService`, `DeviceService`, `SqliteEventRepository`), garantindo paridade total com a API HTTP.
- **Ferramentas MCP Expostas (15 Tools):**
  - **Sessões:** `create_session`, `get_session`, `list_sessions`, `write_session`, `read_session`, `close_session`.
  - **Histórico de Eventos:** `get_events` (paginação por cursor com `since_sequence` e `limit`).
  - **Jobs em Segundo Plano:** `submit_job`, `get_job`, `list_jobs`, `wait_job`, `cancel_job`.
  - **Catálogo e Resolução de Dispositivos:** `list_devices`, `get_device`, `resolve_device`.
- **Garantias de Segurança:**
  - `resolve_device` resolve internamente parâmetros de conexão, validando existência e atividade do dispositivo, indicando `has_credential: true/false`, mas **omite estritamente segredos, senhas e chaves privadas** da resposta ao agente.
- **Configuração em Clientes MCP:**

Adicione a configuração abaixo ao seu cliente MCP (por exemplo, `claude_desktop_config.json` ou arquivo de settings do IDE):

```json
{
  "mcpServers": {
    "terminal-session-manager": {
      "command": "uv",
      "args": [
        "--directory",
        "d:/Projetos/TerminalPersistente",
        "run",
        "terminal-session-manager-mcp"
      ],
      "env": {
        "TSM_DB_PATH": ".tsm/tsm.db"
      }
    }
  }
}
```

---

## Etapa 7 — Configuração e Endurecimento

Consolida a configuração centralizada, ciclo de vida operacional, reconciliação de recursos órfãos e rotação de credenciais protegidas:

- **Configuração Centralizada (`config.yml` e `config.py`):**
  - Carregamento declarativo via `config.yml` com defaults seguros para servidor, armazenamento, sessões, jobs e limites de eventos.
  - Sobrescrita estrita via variáveis de ambiente com prefixo `TSM_`:
    - `TSM_CONFIG_PATH`: Caminho alternativo para o arquivo de configuração.
    - `TSM_SERVER_HOST`: Endereço de escuta da API (padrão: `127.0.0.1`).
    - `TSM_SERVER_PORT`: Porta TCP da API HTTP (padrão: `8000`).
    - `TSM_API_TOKEN`: Token de autenticação da API HTTP.
    - `TSM_DB_PATH`: Caminho do banco SQLite (padrão: `.tsm/tsm.db`).
    - `TSM_MASTER_KEY`: Chave mestra criptográfica para proteção em repouso.
    - `TSM_REQUIRE_AUTH`: Obrigatoriedade de autenticação HTTP (`true`/`false`).
  - **Validação Antecipada na Inicialização:** Portas inválidas, timeouts nulos ou negativos, limites invertidos ou ativação de `require_auth` sem token informado levantam `ConfigurationError` imediato e abortam a execução com erro claro.
  - **Segredos Fora do YAML:** Nenhuma credencial ou chave secreta é persistida em texto puro no arquivo `config.yml`.
- **Endurecimento de Ciclo de Vida e Reconciliação (`app.py`):**
  - `TSMApplication`: Container central que injeta a mesma configuração e banco entre API, MCP e serviços.
  - `startup()`: Executa reconciliação de recursos interrompidos:
    - Jobs em execução durante falhas/reinícios são marcados como `FAILED`.
    - Sessões ativas em banco sem processo no runtime são marcadas como `LOST`.
  - `shutdown()`: Encerramento gracioso que fecha todas as sessões ativas (`close_all()`), cancela processos em segundo plano e fecha conexões SQLite de maneira determinística.
- **Segurança e Rotação do Armazenamento de Credenciais:**
  - `rotate_master_key(new_master_key)`: Re-criptografa todas as credenciais sob uma nova chave mestra em transação atômica única no SQLite.
  - `rotate_credential(ref_id, new_secret)`: Atualiza o segredo de uma credencial gerando novo sal, nonce e tag de autenticação HMAC.
  - Restrição de permissões de arquivo em sistemas POSIX (`0o600` para banco e `0o700` para diretório).

---

## Requisitos

- Python >= 3.11
- [`uv`](https://docs.astral.sh/uv/) (gerenciador de dependências e ambientes)

---

## Instalação

Clone o repositório e sincronize o ambiente virtual com `uv`:

```bash
uv sync
```

---

## Execução

O utilitário CLI unificado `terminal-session-manager` oferece controle sobre todos os serviços e operações:

```bash
# Validar arquivo de configuração e banco de dados
uv run terminal-session-manager validate

# Iniciar o servidor HTTP REST API (com documentação Swagger em /docs)
uv run terminal-session-manager api

# Iniciar o servidor MCP (transporte stdio para Claude Desktop / Cursor / Antigravity)
uv run terminal-session-manager mcp

# Exibir status e visão geral
uv run terminal-session-manager status

# Ponto de entrada direto do MCP
uv run terminal-session-manager-mcp

# Verificar versão instalada
uv run terminal-session-manager --version
```

---

## Testes

A suíte de testes unitários valida modelos, transições de estado permitidas e rejeitadas, ordenação de eventos e conformidade dos contratos:

```bash
uv run pytest -v
```

Todos os testes são autossuficientes e executam sem qualquer dependência de rede, processos externos ou banco de dados.

---

## Estrutura do Projeto

```text
.
├── pyproject.toml                         # Configuração uv e dependências
├── README.md                              # Documentação de uso e instalação
├── spec.md                                # Especificação completa do produto
├── reports/
│   ├── 01-contrato-e-esqueleto.md         # Relatório da Etapa 0
│   ├── 02-sessao-local.md                 # Relatório da Etapa 1
│   ├── 03-persistencia-e-historico.md     # Relatório da Etapa 2
│   └── 04-jobs-assincronos.md             # Relatório da Etapa 3
├── src/
│   └── terminal_session_manager/
│       ├── __init__.py                    # Exportações públicas de domínio
│       ├── errors.py                      # Exceções de domínio e transporte
│       ├── main.py                        # Ponto de entrada CLI
│       ├── models/                        # Entidades e máquinas de estado
│       │   ├── __init__.py
│       │   ├── credential.py              # CredentialRef, CredentialType
│       │   ├── device.py                  # Device, DeviceType, ConnectionMethod
│       │   ├── event.py                   # Event, EventType
│       │   ├── job.py                     # Job, JobStatus, JOB_TRANSITIONS
│       │   └── session.py                 # Session, SessionStatus, SESSION_TRANSITIONS
│       ├── interfaces/                    # Contratos estruturais (Protocols)
│       │   ├── __init__.py
│       │   ├── credentials.py             # CredentialResolver
│       │   ├── device.py                  # DeviceRepository
│       │   ├── persistence.py             # SessionRepository, JobRepository, EventRepository
│       │   └── transport.py               # TerminalTransport
│       ├── transports/                    # Adaptadores de transporte
│       │   ├── __init__.py
│       │   └── local_process.py           # LocalProcessTransport (subprocess + non-blocking queue)
│       ├── services/                      # Orquestradores de alto nível
│       │   ├── __init__.py
│       │   ├── job_service.py             # JobService (execução assíncrona em background)
│       │   └── local_session.py           # LocalSession controller
│       └── persistence/                   # Repositórios duráveis (SQLite)
│           ├── __init__.py
│           └── sqlite.py                  # SqliteStorage, Repositories
└── tests/
    ├── test_contracts.py                  # Verificação dos protocolos em memória
    ├── test_device_and_credential.py      # Testes de Device e CredentialRef
    ├── test_event.py                      # Testes de Event e ordenação estrita
    ├── test_job.py                        # Testes de Job e transições de ciclo de vida
    ├── test_job_service.py                # Testes de JobService assíncrono
    ├── test_local_session.py              # Testes do controlador LocalSession
    ├── test_local_transport.py            # Testes do adaptador LocalProcessTransport
    ├── test_persistence_lifecycle.py      # Testes de reinício, saída volumosa e segredos
    ├── test_session.py                    # Testes de Session e máquina de estados
    └── test_sqlite_persistence.py         # Testes dos repositórios SQLite
```
