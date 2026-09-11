# Graph Report - TerminalPersistente  (2026-09-11)

## Corpus Check
- 61 files · ~31,354 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 838 nodes · 1962 edges · 60 communities (49 shown, 11 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 405 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ae397a1b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TransportClosedError
- DeviceService
- Session
- SessionStatus
- handler.py
- Terminal Session Manager
- DeviceRepository
- test_mcp_server.py
- test_job.py
- Relatório — Etapa 6: MCP com FastMCP
- TerminalTransport
- Relatório — Etapa 0: Contrato e Esqueleto
- Relatório — Etapa 2: Persistência e Histórico
- Relatório — Etapa 1: Sessão Local Mínima
- FakeTransport
- LocalSession
- ._record_event
- main.py
- test_api_auth_and_errors.py
- JobService
- LocalProcessTransport
- terminal-session-manager
- Event
- Relatório — Etapa 3: Jobs Assíncronos
- SqliteStorage
- test_device_service.py
- Relatório — Etapa 5: API HTTP
- .transition_to
- .cancel_job
- Job
- terminal_session_manager/__init__.py
- SqliteEventRepository
- CredentialResolver
- rules/graphify.md
- workflows/graphify.md
- ProtectedLocalCredentialStore
- test_api_devices.py
- Device
- SqliteSessionRepository
- CredentialType
- CredentialRef
- ValidationError
- Relatório — Etapa 4: Dispositivos e Credenciais
- .start_in_thread
- test_api_sessions_events.py
- SqliteDeviceRepository
- test_contracts.py
- credential_store.py
- TransportNotOpenError
- job.py
- .remove
- test_api_docs.py
- test_service_restart_recovers_session_and_events
- job_service.py
- device_service.py
- test_device_resolution_and_session.py
- .list_devices
- .register_device
- .get_job
- .list_jobs

## God Nodes (most connected - your core abstractions)
1. `ValidationError` - 55 edges
2. `DeviceService` - 52 edges
3. `Session` - 49 edges
4. `SqliteStorage` - 48 edges
5. `Device` - 45 edges
6. `Job` - 44 edges
7. `JobService` - 43 edges
8. `LocalSession` - 42 edges
9. `Event` - 36 edges
10. `ProtectedLocalCredentialStore` - 36 edges

## Surprising Connections (you probably didn't know these)
- `test_device_deactivation()` --uses--> `Device`  [INFERRED]
  tests/test_device_and_credential.py → src/terminal_session_manager/models/device.py
- `test_api_authentication_enforcement()` --uses--> `APIServer`  [INFERRED]
  tests/test_api_auth_and_errors.py → src/terminal_session_manager/api/server.py
- `test_api_standardized_error_handling()` --uses--> `APIServer`  [INFERRED]
  tests/test_api_auth_and_errors.py → src/terminal_session_manager/api/server.py
- `test_device_crud_and_safe_resolution_api()` --uses--> `APIServer`  [INFERRED]
  tests/test_api_devices.py → src/terminal_session_manager/api/server.py
- `test_openapi_specification_endpoint()` --uses--> `APIServer`  [INFERRED]
  tests/test_api_docs.py → src/terminal_session_manager/api/server.py

## Import Cycles
- None detected.

## Communities (60 total, 11 thin omitted)

### Community 0 - "TransportClosedError"
Cohesion: 0.15
Nodes (9): Base exception for transport and process communication failures., Raised when attempting to write to or interact with a closed or terminated…, TransportClosedError, TransportError, Transport adapters package., _get_default_shell(), Local process terminal transport adapter., Returns platform-appropriate default interactive shell command. (+1 more)

### Community 1 - "DeviceService"
Cohesion: 0.11
Nodes (16): HTTP API package exposing Terminal Session Manager services., APIServer, HTTP server management for Terminal Session Manager., Encapsulates the standard library ThreadingHTTPServer lifecycle for TSM., Returns the bound host address., Returns the actual bound TCP port number., Returns base HTTP URL (e.g. http://127.0.0.1:54321)., Starts serving requests synchronously (blocking). (+8 more)

### Community 2 - "Session"
Cohesion: 0.05
Nodes (28): Row, Raised when a requested session is not found., SessionNotFoundError, Persists or updates a session., Retrieves a session by ID or returns None if not found., Lists all persisted sessions., Represents a persistent terminal session., Indicates whether the session is in an active/alive operational state. (+20 more)

### Community 3 - "SessionStatus"
Cohesion: 0.17
Nodes (12): Enum, str, Session domain model and state definitions., Conceptual states of a session., Transitions session to a new status if the transition is valid., SessionStatus, Tests for LocalSession controller and lifecycle integration., test_interactive_session_write_and_read() (+4 more)

### Community 4 - "handler.py"
Cohesion: 0.06
Nodes (53): BaseHTTPRequestHandler, FastMCP, device_to_dict(), event_to_dict(), _iso(), job_to_dict(), Any, datetime (+45 more)

### Community 5 - "Terminal Session Manager"
Cohesion: 0.05
Nodes (40): Estrutura do Projeto, Etapa 0 — Contrato e Esqueleto, Etapa 1 — Sessão Local Mínima, Etapa 2 — Persistência e Histórico, Etapa 3 — Jobs Assíncronos, Etapa 4 — Dispositivos e Credenciais, Etapa 5 — API HTTP, Etapa 6 — MCP com FastMCP (+32 more)

### Community 6 - "DeviceRepository"
Cohesion: 0.11
Nodes (10): DeviceRepository, Protocol, Contract for device catalog storage and queries., Registers a new device or updates an existing one., Retrieves a device by unique ID., Retrieves a device by unique name., Lists all active registered devices., Logically deactivates a device by ID. (+2 more)

### Community 7 - "test_mcp_server.py"
Cohesion: 0.29
Nodes (11): Tests for FastMCP server implementation in Terminal Session Manager., Helper to run async coroutines in synchronous pytest tests., _run(), test_mcp_device_inactive_rejection(), test_mcp_devices_and_secret_protection(), test_mcp_error_handling_unknown_entities(), test_mcp_events_cursor_pagination(), test_mcp_job_cancel() (+3 more)

### Community 8 - "test_job.py"
Cohesion: 0.20
Nodes (9): parametrize, Unit tests for Job model and lifecycle states., test_job_creation_defaults(), test_job_invalid_transitions_rejected(), test_job_lifecycle_to_cancelled(), test_job_lifecycle_to_completed(), test_job_lifecycle_to_failed(), test_job_lifecycle_to_timeout() (+1 more)

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

### Community 14 - "FakeTransport"
Cohesion: 0.20
Nodes (3): FakeTransport, Mock transport verifying pluggability and independence from OS processes., test_pluggable_transport_with_local_session()

### Community 15 - "LocalSession"
Cohesion: 0.11
Nodes (14): LocalSession, Any, Opens the transport and transitions session to RUNNING state. If transport…, Scans and redacts configured sensitive tokens from text., Writes data to the session transport channel and records STDIN event., Reads raw bytes from the session transport channel and records STDOUT event., Convenience method to read decoded text from the session., Resizes the terminal window dimensions. (+6 more)

### Community 16 - "._record_event"
Cohesion: 0.33
Nodes (4): Any, Reconciles interrupted jobs upon service restart. Scans repository for jobs in…, Atomically records a sequenced event associated with a session and job., Creates and launches an asynchronous job in a background worker.

### Community 17 - "main.py"
Cohesion: 0.50
Nodes (3): main(), Executable entry point for Terminal Session Manager., CLI entry point displaying version and skeleton status.

### Community 18 - "test_api_auth_and_errors.py"
Cohesion: 0.60
Nodes (4): http_request(), Tests for HTTP API authentication and standardized error handling., test_api_authentication_enforcement(), test_api_standardized_error_handling()

### Community 19 - "JobService"
Cohesion: 0.21
Nodes (18): JobStatus, str, Conceptual states of an asynchronous or synchronous job., JobService, Manages asynchronous job execution, monitoring, waiting, and cancellation. Jobs…, fixture, Unit and integration tests for asynchronous JobService., service() (+10 more)

### Community 20 - "LocalProcessTransport"
Cohesion: 0.14
Nodes (15): LocalProcessTransport, Records terminal dimensions., Terminates process cleanly and closes resources., TerminalTransport adapter backed by a local OS subprocess. Uses non-blocking…, Returns process returncode or None if still running., Continuously reads bytes from process stdout pipe into output queue., Tests for LocalProcessTransport adapter., test_command_not_found_raises_transport_error() (+7 more)

### Community 22 - "Event"
Cohesion: 0.13
Nodes (17): Appends a new event to the session/job stream., Retrieves an ordered stream of events for a session from a sequence cursor., Event, EventType, Enum, str, Event domain model with ordering and session/job linkage., Categorization of terminal and lifecycle events. (+9 more)

### Community 23 - "Relatório — Etapa 3: Jobs Assíncronos"
Cohesion: 0.20
Nodes (9): Critérios Verificados, Decisões Tomadas, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 4 — Dispositivos e Credenciais), Entregue, Relatório — Etapa 3: Jobs Assíncronos, Riscos e Decisões Pendentes, Status (+1 more)

### Community 24 - "SqliteStorage"
Cohesion: 0.10
Nodes (17): Connection, RLock, Path, Manages the SQLite database connection, initialization, and transactions., Returns the storage reentrant lock for synchronizing transactions., Returns the underlying sqlite connection., Closes the underlying database connection cleanly., SqliteStorage (+9 more)

### Community 25 - "test_device_service.py"
Cohesion: 0.16
Nodes (12): Device catalog interface definition., device_repo(), device_service(), fixture, Path, Tests for DeviceRepository and DeviceService CRUD, state transitions, and…, sqlite_storage(), test_device_crud_lifecycle() (+4 more)

### Community 26 - "Relatório — Etapa 5: API HTTP"
Cohesion: 0.20
Nodes (9): Critérios Verificados, Decisão Técnica HTTP e Documentação, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 6 — MCP), Entregue, Relatório — Etapa 5: API HTTP, Riscos e Decisões Pendentes, Status (+1 more)

### Community 28 - ".cancel_job"
Cohesion: 0.20
Nodes (6): Popen, Background worker thread executing the job process., Terminates a subprocess safely, escalating to kill if necessary., Waits for a job to complete execution and returns the finished Job., Cancels a running or created job., _terminate_proc()

### Community 29 - "Job"
Cohesion: 0.16
Nodes (10): JobRepository, Contract for job persistence., Persists or updates a job., Retrieves a job by ID or returns None if not found., Lists all jobs associated with a given session ID., Job, Represents an execution unit within a persistent session., InMemoryJobRepository (+2 more)

### Community 30 - "terminal_session_manager/__init__.py"
Cohesion: 0.12
Nodes (15): CredentialNotFoundError, DeviceInactiveError, DomainError, InvalidStateError, InvalidStateTransitionError, Exception, Domain exceptions for Terminal Session Manager., Raised when a blocking transport operation exceeds the specified timeout. (+7 more)

### Community 31 - "SqliteEventRepository"
Cohesion: 0.22
Nodes (7): Persistent EventRepository implementation with strict sequence uniqueness and…, Retrieves ordered event stream from a sequence cursor with optional limit., Returns the highest sequence number recorded for the session, or -1 if empty., SqliteEventRepository, auth_api_server(), fixture, Path

### Community 32 - "CredentialResolver"
Cohesion: 0.16
Nodes (12): CredentialResolver, ExternalCredentialProvider, Protocol, Credential abstraction and resolution interface., Internal contract to resolve secret references safely. This interface must only…, Resolves the raw secret string/bytes for a given credential reference ID., Contract for delegating credential resolution to an external provider., Resolves secret from external provider. Returns None if not handled. (+4 more)

### Community 35 - "ProtectedLocalCredentialStore"
Cohesion: 0.16
Nodes (15): CredentialResolutionError, Raised when resolving a credential secret fails or integrity check fails., ProtectedLocalCredentialStore, Decodes the secret in memory. Returns None if ref_id does not exist., Deletes credential from the protected store., Local credential storage protecting secrets at rest using authenticated…, local_cred_store(), fixture (+7 more)

### Community 36 - "test_api_devices.py"
Cohesion: 0.67
Nodes (3): http_request(), Tests for Devices HTTP API endpoints and safe nickname resolution., test_device_crud_and_safe_resolution_api()

### Community 37 - "Device"
Cohesion: 0.11
Nodes (10): Device, Represents an addressable device in the inventory., Deactivates device logically without deleting historical references., Deactivates a device logically., Logically marks a device as removed., Retrieves a device by ID., Retrieves a device by unique name/nickname., InMemoryDeviceRepository (+2 more)

### Community 38 - "SqliteSessionRepository"
Cohesion: 0.13
Nodes (14): Persistent SessionRepository implementation backed by SQLite., SqliteSessionRepository, api_server_with_creds(), fixture, Path, doc_api_server(), fixture, Path (+6 more)

### Community 39 - "CredentialType"
Cohesion: 0.15
Nodes (13): CredentialType, Enum, str, Credential reference model ensuring secret isolation., Supported types of credentials., Retrieves only non-sensitive metadata for the given credential reference ID., Unit tests for Device and CredentialRef models and security constraints., test_credential_ref_creation() (+5 more)

### Community 40 - "CredentialRef"
Cohesion: 0.16
Nodes (8): Retrieves only non-sensitive metadata for a credential reference., Retrieves metadata from external provider, or None if not handled., CredentialRef, Safe reference metadata for credentials. NOTE: This model strictly avoids…, Retrieves metadata from external provider first, then local store., InMemoryCredentialResolver, In-memory mock conforming to CredentialResolver protocol., test_credential_resolver_protocol()

### Community 41 - "ValidationError"
Cohesion: 0.13
Nodes (15): Raised when entity validation fails., ValidationError, Persistence package providing concrete repositories., _iso(), _parse_iso(), datetime, SQLite persistence implementation for sessions, jobs, and event history., Persists or updates a session entity. (+7 more)

### Community 42 - "Relatório — Etapa 4: Dispositivos e Credenciais"
Cohesion: 0.20
Nodes (9): Critérios Verificados, Decisões Tomadas, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 5 — API), Entregue, Relatório — Etapa 4: Dispositivos e Credenciais, Riscos e Decisões Pendentes, Status (+1 more)

### Community 44 - "test_api_sessions_events.py"
Cohesion: 0.47
Nodes (5): http_request(), Tests for Sessions and Events HTTP API endpoints., Helper to perform HTTP JSON requests using standard library urllib., test_events_cursor_pagination_api(), test_session_lifecycle_and_io_api()

### Community 45 - "SqliteDeviceRepository"
Cohesion: 0.14
Nodes (9): Persistent DeviceRepository implementation backed by SQLite., Persists or updates a device entity., Retrieves a device by ID., Retrieves a device by unique name., Lists all active and non-deleted registered devices., Logically deactivates a device by ID., Logically removes a device by ID., Lists all devices, optionally including logically deleted ones. (+1 more)

### Community 46 - "test_contracts.py"
Cohesion: 0.12
Nodes (7): InMemoryEventRepository, MockTerminalTransport, Unit tests for domain interfaces (Protocols) and mock in-memory implementations., In-memory implementation conforming to EventRepository protocol., In-memory mock conforming to TerminalTransport protocol., test_event_repository_protocol(), test_terminal_transport_protocol()

### Community 47 - "credential_store.py"
Cohesion: 0.29
Nodes (6): _crypt_keystream(), _derive_keys(), Protected credential storage and resolution services ensuring secrets are never…, Derives 32-byte encryption key and 32-byte MAC key using PBKDF2-HMAC-SHA256., Symmetric authenticated keystream XOR cipher (counter mode over HMAC-SHA256)., Encrypts the secret and persists non-sensitive metadata alongside ciphertext.

### Community 48 - "TransportNotOpenError"
Cohesion: 0.25
Nodes (5): Raised when attempting I/O operations on an unopened transport., TransportNotOpenError, Reads up to max_bytes from the process output stream., Writes byte data to the process stdin channel., Checks if the underlying process is currently running.

### Community 51 - "test_api_docs.py"
Cohesion: 0.47
Nodes (5): Tests for OpenAPI specification and Swagger UI documentation endpoints., Helper returning (status_code, content_type, body_text)., raw_http_get(), test_openapi_specification_endpoint(), test_swagger_ui_endpoint()

### Community 52 - "test_service_restart_recovers_session_and_events"
Cohesion: 0.47
Nodes (5): Path, Tests for persistence lifecycle: service restart, voluminous output, and secret…, test_sensitive_data_masking_in_history(), test_service_restart_recovers_session_and_events(), test_voluminous_output_cursor_pagination()

### Community 53 - "job_service.py"
Cohesion: 0.15
Nodes (12): Domain interfaces and contracts package., Protocol, Persistence interfaces for sessions, jobs, and events., Contract for session persistence., SessionRepository, Terminal and transport adapter interfaces., Asynchronous Job execution and lifecycle management service., Session lifecycle and interactive I/O coordinator service. (+4 more)

### Community 54 - "device_service.py"
Cohesion: 0.21
Nodes (6): Device catalog and safe internal connection resolution service., Resolves full connection details internally using a name or device ID. Enforces…, Internal connection metadata container. NOTE: The resolved secret exists…, ResolvedConnection, Session, job, device, and credential management services package., Local session controller binding Session lifecycle to TerminalTransport and…

### Community 55 - "test_device_resolution_and_session.py"
Cohesion: 0.20
Nodes (10): device_service_and_store(), fixture, Path, Tests for device resolution by nickname, error handling, session injection, and…, sqlite_storage(), test_resolve_connection_by_nickname(), test_resolve_connection_deactivated_or_deleted_device_fails(), test_resolve_connection_device_not_found() (+2 more)

## Knowledge Gaps
- **94 isolated node(s):** `terminal-session-manager`, `graphify`, `Workflow: graphify`, `Etapa 0 — Contrato e Esqueleto`, `Etapa 1 — Sessão Local Mínima` (+89 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 397 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ValidationError` connect `ValidationError` to `Session`, `SessionStatus`, `handler.py`, `test_job.py`, `._record_event`, `JobService`, `Event`, `SqliteStorage`, `test_device_service.py`, `.transition_to`, `Job`, `terminal_session_manager/__init__.py`, `SqliteEventRepository`, `ProtectedLocalCredentialStore`, `Device`, `SqliteSessionRepository`, `CredentialType`, `CredentialRef`, `SqliteDeviceRepository`, `credential_store.py`, `job.py`, `job_service.py`, `device_service.py`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `Device` connect `Device` to `DeviceService`, `handler.py`, `DeviceRepository`, `CredentialType`, `ValidationError`, `SqliteDeviceRepository`, `.remove`, `Event`, `device_service.py`, `.list_devices`, `test_device_service.py`, `.register_device`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `LocalSession` connect `LocalSession` to `TransportClosedError`, `DeviceService`, `Session`, `SessionStatus`, `TerminalTransport`, `FakeTransport`, `LocalProcessTransport`, `job_service.py`, `device_service.py`, `Event`, `test_device_resolution_and_session.py`, `test_service_restart_recovers_session_and_events`, `terminal_session_manager/__init__.py`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `ValidationError` (e.g. with `TSMRequestHandler` and `CredentialRef`) actually correct?**
  _`ValidationError` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `DeviceService` (e.g. with `APIServer` and `CredentialNotFoundError`) actually correct?**
  _`DeviceService` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `Session` (e.g. with `session_to_dict()` and `SessionRepository`) actually correct?**
  _`Session` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `SqliteStorage` (e.g. with `ProtectedLocalCredentialStore` and `auth_api_server()`) actually correct?**
  _`SqliteStorage` has 26 INFERRED edges - model-reasoned connections that need verification._