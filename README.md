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

Para executar o ponto de entrada do esqueleto:

```bash
uv run terminal-session-manager
```

Ou através do módulo Python:

```bash
uv run python -m terminal_session_manager.main
```

Para verificar a versão instalada:

```bash
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
│   └── 03-persistencia-e-historico.md     # Relatório da Etapa 2
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
│       │   └── local_session.py           # LocalSession controller
│       └── persistence/                   # Repositórios duráveis (SQLite)
│           ├── __init__.py
│           └── sqlite.py                  # SqliteStorage, Repositories
└── tests/
    ├── test_contracts.py                  # Verificação dos protocolos em memória
    ├── test_device_and_credential.py      # Testes de Device e CredentialRef
    ├── test_event.py                      # Testes de Event e ordenação estrita
    ├── test_job.py                        # Testes de Job e transições de ciclo de vida
    ├── test_local_session.py              # Testes do controlador LocalSession
    ├── test_local_transport.py            # Testes do adaptador LocalProcessTransport
    ├── test_persistence_lifecycle.py      # Testes de reinício, saída volumosa e segredos
    ├── test_session.py                    # Testes de Session e máquina de estados
    └── test_sqlite_persistence.py         # Testes dos repositórios SQLite
```
