# Graph Report - TerminalPersistente  (2026-09-11)

## Corpus Check
- 66 files · ~35,523 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 920 nodes · 2200 edges · 53 communities (46 shown, 7 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 459 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ae397a1b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- SessionService
- APIServer
- Session
- TSMApplication
- TSMRequestHandler
- Terminal Session Manager
- DeviceRepository
- test_mcp_server.py
- JobStatus
- Relatório — Etapa 6: MCP com FastMCP
- TerminalTransport
- Relatório — Etapa 0: Contrato e Esqueleto
- Relatório — Etapa 2: Persistência e Histórico
- Relatório — Etapa 1: Sessão Local Mínima
- FakeTransport
- LocalSession
- ._record_event
- load_config
- handler.py
- JobService
- LocalProcessTransport
- terminal-session-manager
- sqlite.py
- Relatório — Etapa 3: Jobs Assíncronos
- SqliteStorage
- terminal_session_manager/__init__.py
- Relatório — Etapa 5: API HTTP
- TSMConfig
- job_service.py
- Job
- errors.py
- ValidationError
- CredentialResolver
- rules/graphify.md
- workflows/graphify.md
- test_credential_protection.py
- device_service.py
- Device
- SqliteSessionRepository
- CredentialType
- CredentialRef
- SqliteJobRepository
- Relatório — Etapa 4: Dispositivos e Credenciais
- mcp/server.py
- Relatório — Etapa 7: Configuração e Endurecimento
- SqliteDeviceRepository
- api_server
- ProtectedLocalCredentialStore
- .log_message
- ._send_html
- api/__init__.py
- local_session.py
- DeviceService

## God Nodes (most connected - your core abstractions)
1. `ValidationError` - 56 edges
2. `SqliteStorage` - 55 edges
3. `DeviceService` - 55 edges
4. `Session` - 50 edges
5. `JobService` - 46 edges
6. `Device` - 45 edges
7. `Job` - 45 edges
8. `ProtectedLocalCredentialStore` - 44 edges
9. `LocalSession` - 42 edges
10. `Event` - 39 edges

## Surprising Connections (you probably didn't know these)
- `test_device_deactivation()` --uses--> `Device`  [INFERRED]
  tests/test_device_and_credential.py → src/terminal_session_manager/models/device.py
- `test_device_crud_and_safe_resolution_api()` --uses--> `APIServer`  [INFERRED]
  tests/test_api_devices.py → src/terminal_session_manager/api/server.py
- `test_job_cancellation_api()` --uses--> `APIServer`  [INFERRED]
  tests/test_api_jobs.py → src/terminal_session_manager/api/server.py
- `test_job_submit_wait_and_query_api()` --uses--> `APIServer`  [INFERRED]
  tests/test_api_jobs.py → src/terminal_session_manager/api/server.py
- `test_validation_invalid_host()` --uses--> `ServerConfig`  [INFERRED]
  tests/test_config.py → src/terminal_session_manager/config.py

## Import Cycles
- None detected.

## Communities (53 total, 7 thin omitted)

### Community 0 - "SessionService"
Cohesion: 0.10
Nodes (17): Any, HTTP server management for Terminal Session Manager., Raised when a requested session is not found., Raised when attempting to write to or interact with a closed or terminated…, SessionNotFoundError, TransportClosedError, Session, job, device, and credential management services package., Session lifecycle and interactive I/O coordinator service. (+9 more)

### Community 1 - "APIServer"
Cohesion: 0.06
Nodes (33): APIServer, Encapsulates the standard library ThreadingHTTPServer lifecycle for TSM., Returns the bound host address., Returns the actual bound TCP port number., Returns base HTTP URL (e.g. http://127.0.0.1:54321)., Starts serving requests synchronously (blocking)., Starts server in a background daemon thread for testing or concurrent execution., Stops server and releases socket cleanly. (+25 more)

### Community 2 - "Session"
Cohesion: 0.07
Nodes (21): Persists or updates a session., Retrieves a session by ID or returns None if not found., Lists all persisted sessions., Represents a persistent terminal session., Indicates whether the session is in an active/alive operational state., Indicates whether the session has reached a closed terminal state., Transitions session to a new status if the transition is valid., Session (+13 more)

### Community 3 - "TSMApplication"
Cohesion: 0.16
Nodes (15): Any, Instantiates the FastMCP server with configured services and storage., Root application container unifying configuration, services, and lifecycle., Runs startup initialization, reconciling orphaned sessions and jobs., Executes graceful shutdown: closes active sessions, terminates jobs, closes DB., TSMApplication, Path, Tests for lifecycle hardening, graceful shutdown, credential rotation, and… (+7 more)

### Community 4 - "TSMRequestHandler"
Cohesion: 0.16
Nodes (13): BaseHTTPRequestHandler, Exception, Processes HTTP API requests with token authentication and domain error…, Verifies Bearer token or X-API-Key against server configured token., Serializes and sends JSON response body with appropriate headers., Sends standardized JSON error response without internal leakages., Reads and parses JSON request payload safely., Handles HTTP POST requests. (+5 more)

### Community 5 - "Terminal Session Manager"
Cohesion: 0.05
Nodes (41): Estrutura do Projeto, Etapa 0 — Contrato e Esqueleto, Etapa 1 — Sessão Local Mínima, Etapa 2 — Persistência e Histórico, Etapa 3 — Jobs Assíncronos, Etapa 4 — Dispositivos e Credenciais, Etapa 5 — API HTTP, Etapa 6 — MCP com FastMCP (+33 more)

### Community 6 - "DeviceRepository"
Cohesion: 0.11
Nodes (10): DeviceRepository, Protocol, Contract for device catalog storage and queries., Registers a new device or updates an existing one., Retrieves a device by unique ID., Retrieves a device by unique name., Lists all active registered devices., Logically deactivates a device by ID. (+2 more)

### Community 7 - "test_mcp_server.py"
Cohesion: 0.29
Nodes (11): Tests for FastMCP server implementation in Terminal Session Manager., Helper to run async coroutines in synchronous pytest tests., _run(), test_mcp_device_inactive_rejection(), test_mcp_devices_and_secret_protection(), test_mcp_error_handling_unknown_entities(), test_mcp_events_cursor_pagination(), test_mcp_job_cancel() (+3 more)

### Community 8 - "JobStatus"
Cohesion: 0.17
Nodes (14): JobStatus, Enum, str, Job domain model and lifecycle states., Conceptual states of an asynchronous or synchronous job., parametrize, Unit tests for Job model and lifecycle states., test_job_creation_defaults() (+6 more)

### Community 9 - "Relatório — Etapa 6: MCP com FastMCP"
Cohesion: 0.20
Nodes (9): 1. Início via CLI, 2. Configuração em Clientes MCP (Claude Desktop, Cursor, Antigravity), Como Iniciar e Conectar um Cliente MCP, Decisões Técnicas, Entregue, Próximos Passos Recomendados, Relatório — Etapa 6: MCP com FastMCP, Status (+1 more)

### Community 10 - "TerminalTransport"
Cohesion: 0.11
Nodes (11): Protocol, Contract for low-level terminal/transport implementations (PTY, SSH, Serial,…, Initializes and opens the underlying transport channel., Reads up to max_bytes from the transport., Writes raw byte data to the transport channel and returns bytes written., Resizes the terminal dimensions if supported by the transport., Closes the transport channel cleanly., Checks if the underlying process/connection is currently active. (+3 more)

### Community 11 - "Relatório — Etapa 0: Contrato e Esqueleto"
Cohesion: 0.18
Nodes (10): Decisões Tomadas, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 1 — Sessão Local Mínima), Entregue, Estrutura do Projeto, Relatório — Etapa 0: Contrato e Esqueleto, Requisitos Atendidos, Riscos e Decisões Pendentes (+2 more)

### Community 12 - "Relatório — Etapa 2: Persistência e Histórico"
Cohesion: 0.20
Nodes (9): Critérios Verificados, Decisão de Armazenamento, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 3 — Jobs Assíncronos), Entregue, Relatório — Etapa 2: Persistência e Histórico, Riscos e Decisões Pendentes, Status (+1 more)

### Community 13 - "Relatório — Etapa 1: Sessão Local Mínima"
Cohesion: 0.22
Nodes (8): Critérios Verificados, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 2 — Persistência e Histórico), Entregue, Relatório — Etapa 1: Sessão Local Mínima, Riscos e Decisões Pendentes, Status, Testes e Resultados

### Community 15 - "LocalSession"
Cohesion: 0.09
Nodes (25): Enum, str, Session domain model and state definitions., Conceptual states of a session., SessionStatus, LocalSession, Any, Opens the transport and transitions session to RUNNING state. If transport… (+17 more)

### Community 16 - "._record_event"
Cohesion: 0.33
Nodes (4): Any, Reconciles interrupted jobs upon service restart. Scans repository for jobs in…, Atomically records a sequenced event associated with a session and job., Creates and launches an asynchronous job in a background worker.

### Community 17 - "load_config"
Cohesion: 0.18
Nodes (14): MonkeyPatch, load_config(), _parse_bool(), Any, Path, Converts common boolean string representations to boolean., Loads configuration from defaults, YAML file, and environment overrides.…, main() (+6 more)

### Community 18 - "handler.py"
Cohesion: 0.21
Nodes (15): device_to_dict(), event_to_dict(), _iso(), job_to_dict(), Any, datetime, HTTP request handler implementing REST API for sessions, jobs, events, and…, Handles HTTP GET requests. (+7 more)

### Community 19 - "JobService"
Cohesion: 0.21
Nodes (15): JobService, Manages asynchronous job execution, monitoring, waiting, and cancellation. Jobs…, fixture, Unit and integration tests for asynchronous JobService., service(), storage(), test_concurrent_jobs_execution(), test_job_autonomous_execution_without_client_waiting() (+7 more)

### Community 20 - "LocalProcessTransport"
Cohesion: 0.08
Nodes (27): Base exception for transport and process communication failures., Raised when attempting I/O operations on an unopened transport., TransportError, TransportNotOpenError, Transport adapters package., _get_default_shell(), LocalProcessTransport, Local process terminal transport adapter. (+19 more)

### Community 22 - "sqlite.py"
Cohesion: 0.05
Nodes (38): Appends a new event to the session/job stream., Retrieves an ordered stream of events for a session from a sequence cursor., Event, EventType, Enum, str, Event domain model with ordering and session/job linkage., Categorization of terminal and lifecycle events. (+30 more)

### Community 23 - "Relatório — Etapa 3: Jobs Assíncronos"
Cohesion: 0.20
Nodes (9): Critérios Verificados, Decisões Tomadas, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 4 — Dispositivos e Credenciais), Entregue, Relatório — Etapa 3: Jobs Assíncronos, Riscos e Decisões Pendentes, Status (+1 more)

### Community 24 - "SqliteStorage"
Cohesion: 0.11
Nodes (11): Connection, RLock, Path, Manages the SQLite database connection, initialization, and transactions., Returns the storage reentrant lock for synchronizing transactions., Returns the underlying sqlite connection., Closes the underlying database connection cleanly., SqliteStorage (+3 more)

### Community 25 - "terminal_session_manager/__init__.py"
Cohesion: 0.17
Nodes (14): HistoryConfig, JobsConfig, Centralized configuration loading, validation, and environment overrides for…, HTTP API server network and authorization parameters., Durability and database persistence parameters., Cryptography, credential protection, and authorization policies., Interactive terminal session constraints., Asynchronous job execution policies. (+6 more)

### Community 26 - "Relatório — Etapa 5: API HTTP"
Cohesion: 0.20
Nodes (9): Critérios Verificados, Decisão Técnica HTTP e Documentação, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 6 — MCP), Entregue, Relatório — Etapa 5: API HTTP, Riscos e Decisões Pendentes, Status (+1 more)

### Community 27 - "TSMConfig"
Cohesion: 0.33
Nodes (13): ConfigurationError, Raised when configuration values are missing, invalid, or conflicting., Aggregated configuration root for Terminal Session Manager., Enforces correctness constraints and security invariants on configuration., TSMConfig, validate_config(), Tests for centralized configuration loading, environment overrides, and…, test_validation_invalid_db_path() (+5 more)

### Community 28 - "job_service.py"
Cohesion: 0.17
Nodes (7): Popen, Asynchronous Job execution and lifecycle management service., Background worker thread executing the job process., Terminates a subprocess safely, escalating to kill if necessary., Waits for a job to complete execution and returns the finished Job., Cancels a running or created job., _terminate_proc()

### Community 29 - "Job"
Cohesion: 0.11
Nodes (12): Persists or updates a job., Retrieves a job by ID or returns None if not found., Lists all jobs associated with a given session ID., Job, Represents an execution unit within a persistent session., Indicates whether the job has reached a terminal state., Transitions job to a new state and updates timestamps., Retrieves current job status from persistent repository. (+4 more)

### Community 30 - "errors.py"
Cohesion: 0.09
Nodes (19): CredentialNotFoundError, DeviceInactiveError, DomainError, EntityNotFoundError, InvalidStateError, InvalidStateTransitionError, JobNotFoundError, Exception (+11 more)

### Community 31 - "ValidationError"
Cohesion: 0.15
Nodes (8): Raised when entity validation fails., ValidationError, _parse_iso(), datetime, Persists or updates a session entity., Appends an event ensuring strict sequence order and rejecting duplicates., Persists or updates a device entity., Retrieves only non-sensitive metadata for the given credential reference ID.

### Community 32 - "CredentialResolver"
Cohesion: 0.16
Nodes (12): CredentialResolver, ExternalCredentialProvider, Protocol, Credential abstraction and resolution interface., Internal contract to resolve secret references safely. This interface must only…, Resolves the raw secret string/bytes for a given credential reference ID., Contract for delegating credential resolution to an external provider., Resolves secret from external provider. Returns None if not handled. (+4 more)

### Community 35 - "test_credential_protection.py"
Cohesion: 0.22
Nodes (9): local_cred_store(), fixture, Path, Tests for protected credential persistence, encryption at rest, tampering…, sqlite_storage(), test_credential_store_conforms_to_protocol(), test_protected_at_rest_persistence_never_plaintext(), test_tampering_detection() (+1 more)

### Community 36 - "device_service.py"
Cohesion: 0.13
Nodes (18): Device catalog interface definition., ConnectionMethod, DeviceType, Enum, str, Device inventory model and connection metadata., Categorization of managed devices., Supported transport/connection mechanisms for devices. (+10 more)

### Community 37 - "Device"
Cohesion: 0.14
Nodes (8): Device, Represents an addressable device in the inventory., Deactivates device logically without deleting historical references., Marks device as logically removed without deleting historical references., Retrieves a device by unique name/nickname., InMemoryDeviceRepository, In-memory implementation conforming to DeviceRepository protocol., test_device_repository_protocol()

### Community 38 - "SqliteSessionRepository"
Cohesion: 0.18
Nodes (10): Path, Central application container managing TSM services, storage, and lifecycle., Applies restrictive file system permissions on POSIX systems., _restrict_permissions(), Persistent SessionRepository implementation backed by SQLite., SqliteSessionRepository, api_server_with_creds(), fixture (+2 more)

### Community 39 - "CredentialType"
Cohesion: 0.19
Nodes (11): CredentialType, Enum, str, Credential reference model ensuring secret isolation., Supported types of credentials., Unit tests for Device and CredentialRef models and security constraints., test_credential_ref_creation(), test_credential_ref_validation() (+3 more)

### Community 40 - "CredentialRef"
Cohesion: 0.16
Nodes (8): Retrieves only non-sensitive metadata for a credential reference., Retrieves metadata from external provider, or None if not handled., CredentialRef, Safe reference metadata for credentials. NOTE: This model strictly avoids…, Retrieves metadata from external provider first, then local store., InMemoryCredentialResolver, In-memory mock conforming to CredentialResolver protocol., test_credential_resolver_protocol()

### Community 41 - "SqliteJobRepository"
Cohesion: 0.21
Nodes (7): Persistent JobRepository implementation backed by SQLite., Persists or updates a job entity., Retrieves a job by ID., Lists all jobs associated with a given session., Lists all persisted jobs, optionally filtered by status., SqliteJobRepository, test_sqlite_job_repository_crud()

### Community 42 - "Relatório — Etapa 4: Dispositivos e Credenciais"
Cohesion: 0.20
Nodes (9): Critérios Verificados, Decisões Tomadas, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 5 — API), Entregue, Relatório — Etapa 4: Dispositivos e Credenciais, Riscos e Decisões Pendentes, Status (+1 more)

### Community 43 - "mcp/server.py"
Cohesion: 0.25
Nodes (9): FastMCP, DeviceNotFoundError, Raised when a requested device is not found., FastMCP integration package for Terminal Session Manager., create_mcp_server(), main(), FastMCP server implementation exposing Terminal Session Manager tools., CLI entrypoint for running the FastMCP server via stdio transport. (+1 more)

### Community 44 - "Relatório — Etapa 7: Configuração e Endurecimento"
Cohesion: 0.25
Nodes (7): Dependências, Mudanças, Recomendação de Manutenção, Relatório — Etapa 7: Configuração e Endurecimento, Riscos Remanescentes, Status, Testes e Resultados

### Community 45 - "SqliteDeviceRepository"
Cohesion: 0.09
Nodes (20): Row, Persistent DeviceRepository implementation backed by SQLite., Retrieves a device by ID., Retrieves a device by unique name., Lists all active and non-deleted registered devices., Logically deactivates a device by ID., Logically removes a device by ID., Lists all devices, optionally including logically deleted ones. (+12 more)

### Community 46 - "api_server"
Cohesion: 0.32
Nodes (7): api_server(), http_request(), fixture, Path, Tests for Jobs HTTP API endpoints., test_job_cancellation_api(), test_job_submit_wait_and_query_api()

### Community 47 - "ProtectedLocalCredentialStore"
Cohesion: 0.15
Nodes (15): CredentialResolutionError, Raised when resolving a credential secret fails or integrity check fails., _iso(), _crypt_keystream(), _derive_keys(), ProtectedLocalCredentialStore, Protected credential storage and resolution services ensuring secrets are never…, Decodes the secret in memory. Returns None if ref_id does not exist. (+7 more)

### Community 53 - "local_session.py"
Cohesion: 0.16
Nodes (14): Domain interfaces and contracts package., EventRepository, JobRepository, Protocol, Persistence interfaces for sessions, jobs, and events., Contract for session persistence., Contract for job persistence., Contract for event stream persistence and cursor-based retrieval. (+6 more)

### Community 55 - "DeviceService"
Cohesion: 0.11
Nodes (16): DeviceService, Deactivates a device logically., Logically marks a device as removed., Lists registered devices., Manages the device inventory and handles secure connection resolution., Registers a new device or updates an existing one., Retrieves a device by ID., device_service_and_store() (+8 more)

## Knowledge Gaps
- **101 isolated node(s):** `terminal-session-manager`, `graphify`, `Workflow: graphify`, `Etapa 0 — Contrato e Esqueleto`, `Etapa 1 — Sessão Local Mínima` (+96 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 433 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ValidationError` connect `ValidationError` to `Session`, `TSMRequestHandler`, `JobStatus`, `LocalSession`, `._record_event`, `handler.py`, `JobService`, `sqlite.py`, `terminal_session_manager/__init__.py`, `job_service.py`, `Job`, `errors.py`, `device_service.py`, `Device`, `SqliteSessionRepository`, `CredentialType`, `CredentialRef`, `SqliteJobRepository`, `SqliteDeviceRepository`, `ProtectedLocalCredentialStore`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `DeviceService` connect `DeviceService` to `SessionService`, `APIServer`, `CredentialResolver`, `TSMApplication`, `device_service.py`, `Device`, `SqliteSessionRepository`, `DeviceRepository`, `CredentialRef`, `CredentialType`, `test_mcp_server.py`, `mcp/server.py`, `SqliteDeviceRepository`, `api_server`, `LocalSession`, `local_session.py`, `terminal_session_manager/__init__.py`, `errors.py`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `SqliteStorage` connect `SqliteStorage` to `APIServer`, `TSMApplication`, `test_credential_protection.py`, `SqliteSessionRepository`, `test_mcp_server.py`, `SqliteJobRepository`, `mcp/server.py`, `SqliteDeviceRepository`, `api_server`, `ProtectedLocalCredentialStore`, `JobService`, `local_session.py`, `sqlite.py`, `DeviceService`, `terminal_session_manager/__init__.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `ValidationError` (e.g. with `TSMRequestHandler` and `CredentialRef`) actually correct?**
  _`ValidationError` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `SqliteStorage` (e.g. with `TSMApplication` and `ProtectedLocalCredentialStore`) actually correct?**
  _`SqliteStorage` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `DeviceService` (e.g. with `APIServer` and `TSMApplication`) actually correct?**
  _`DeviceService` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `Session` (e.g. with `session_to_dict()` and `SessionRepository`) actually correct?**
  _`Session` has 22 INFERRED edges - model-reasoned connections that need verification._