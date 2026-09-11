# Graph Report - TerminalPersistente  (2026-09-11)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 946 nodes · 2020 edges · 78 communities (61 shown, 17 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 376 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c7041a6b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- terminal_session_manager/__init__.py
- JobService
- Terminal Session Manager
- test_contracts.py
- errors.py
- TSMRequestHandler
- SessionService
- SqliteStorage
- handler.py
- Session
- APIServer
- Event
- ValidationError
- ConnectionMethod
- CredentialResolver
- Job
- persistence.py
- TerminalTransport
- ProtectedLocalCredentialStore
- LocalSession
- LocalProcessTransport
- SqliteDeviceRepository
- .poll_status
- Device
- device_service.py
- SqliteEventRepository
- SqliteJobRepository
- DeviceRepository
- credential_store.py
- DeviceService
- test_mcp_server.py
- Relatório — Etapa 0: Contrato e Esqueleto
- .do_GET
- app.py
- Relatório — Etapa 2: Persistência e Histórico
- Relatório — Etapa 3: Jobs Assíncronos
- Relatório — Etapa 4: Dispositivos e Credenciais
- Relatório — Etapa 5: API HTTP
- Relatório — Etapa 6: MCP com FastMCP
- SqliteSessionRepository
- test_device_resolution_and_session.py
- Relatório — Etapa 1: Sessão Local Mínima
- FakeTransport
- Relatório — Etapa 7: Configuração e Endurecimento
- InvalidStateTransitionError
- TransportNotOpenError
- SessionRepository
- auth_api_server
- CredentialNotFoundError
- local_process.py
- TransportClosedError
- sqlite.py
- .read
- test_api_docs.py
- test_service_restart_recovers_session_and_events
- .get_ref
- .__init__
- .__init__
- TransportError
- .lock
- .deactivate
- .get_by_name
- .remove
- api_server_with_creds
- api_server
- api_server
- rules/graphify.md
- workflows/graphify.md
- .deactivate
- .remove
- .deactivate_device
- .get_device_by_name
- .remove_device
- ._reader_worker
- .resize
- terminal-session-manager
- Enum
- str

## God Nodes (most connected - your core abstractions)
1. `ValidationError` - 56 edges
2. `SqliteStorage` - 55 edges
3. `DeviceService` - 54 edges
4. `Device` - 45 edges
5. `ProtectedLocalCredentialStore` - 42 edges
6. `JobService` - 39 edges
7. `LocalSession` - 34 edges
8. `SqliteDeviceRepository` - 33 edges
9. `APIServer` - 32 edges
10. `TSMRequestHandler` - 32 edges

## Surprising Connections (you probably didn't know these)
- `test_device_deactivation()` --uses--> `Device`  [INFERRED]
  tests/test_device_and_credential.py → src/terminal_session_manager/models/device.py
- `auth_api_server()` --uses--> `JobService`  [INFERRED]
  tests/test_api_auth_and_errors.py → src/terminal_session_manager/services/job_service.py
- `api_server_with_creds()` --uses--> `JobService`  [INFERRED]
  tests/test_api_devices.py → src/terminal_session_manager/services/job_service.py
- `doc_api_server()` --uses--> `JobService`  [INFERRED]
  tests/test_api_docs.py → src/terminal_session_manager/services/job_service.py
- `api_server()` --uses--> `JobService`  [INFERRED]
  tests/test_api_jobs.py → src/terminal_session_manager/services/job_service.py

## Import Cycles
- None detected.

## Communities (78 total, 17 thin omitted)

### Community 0 - "terminal_session_manager/__init__.py"
Cohesion: 0.06
Nodes (57): MonkeyPatch, Any, Instantiates the HTTP API server bound to configured host, port, and token., Instantiates the FastMCP server with configured services and storage., Root application container unifying configuration, services, and lifecycle., Runs startup initialization, reconciling orphaned sessions and jobs., Executes graceful shutdown: closes active sessions, terminates jobs, closes DB., TSMApplication (+49 more)

### Community 1 - "JobService"
Cohesion: 0.07
Nodes (33): JobRepository, Popen, JobService, Any, EventRepository, EventType, Job, SessionRepository (+25 more)

### Community 2 - "Terminal Session Manager"
Cohesion: 0.05
Nodes (41): Estrutura do Projeto, Etapa 0 — Contrato e Esqueleto, Etapa 1 — Sessão Local Mínima, Etapa 2 — Persistência e Histórico, Etapa 3 — Jobs Assíncronos, Etapa 4 — Dispositivos e Credenciais, Etapa 5 — API HTTP, Etapa 6 — MCP com FastMCP (+33 more)

### Community 3 - "test_contracts.py"
Cohesion: 0.06
Nodes (20): InMemoryCredentialResolver, InMemoryEventRepository, InMemoryJobRepository, InMemorySessionRepository, MockTerminalTransport, CredentialRef, Event, Job (+12 more)

### Community 4 - "errors.py"
Cohesion: 0.09
Nodes (18): DeviceInactiveError, DeviceNotFoundError, DomainError, EntityNotFoundError, InvalidStateError, JobNotFoundError, Exception, Domain exceptions for Terminal Session Manager. (+10 more)

### Community 5 - "TSMRequestHandler"
Cohesion: 0.13
Nodes (15): BaseHTTPRequestHandler, Exception, Processes HTTP API requests with token authentication and domain error…, Suppresses default stderr server logging for quiet test execution., Verifies Bearer token or X-API-Key against server configured token., Serializes and sends JSON response body with appropriate headers., Sends standardized JSON error response without internal leakages., Reads and parses JSON request payload safely. (+7 more)

### Community 6 - "SessionService"
Cohesion: 0.10
Nodes (15): Any, EventRepository, Any, EventRepository, Session, SessionRepository, TerminalTransport, Terminates an active session and updates its final status. (+7 more)

### Community 7 - "SqliteStorage"
Cohesion: 0.12
Nodes (15): Connection, Path, Manages the SQLite database connection, initialization, and transactions., Returns the underlying sqlite connection., Closes the underlying database connection cleanly., SqliteStorage, fixture, Unit tests for SQLite persistence repositories and constraints. (+7 more)

### Community 8 - "handler.py"
Cohesion: 0.17
Nodes (19): FastMCP, device_to_dict(), event_to_dict(), _iso(), job_to_dict(), Any, datetime, Event (+11 more)

### Community 9 - "Session"
Cohesion: 0.14
Nodes (17): Enum, str, Session domain model and state definitions., Conceptual states of a session., Represents a persistent terminal session., Indicates whether the session is in an active/alive operational state., Indicates whether the session has reached a closed terminal state., Session (+9 more)

### Community 10 - "APIServer"
Cohesion: 0.11
Nodes (14): APIServer, Encapsulates the standard library ThreadingHTTPServer lifecycle for TSM., Returns the bound host address., Returns the actual bound TCP port number., Returns base HTTP URL (e.g. http://127.0.0.1:54321)., Starts serving requests synchronously (blocking)., Starts server in a background daemon thread for testing or concurrent execution., Stops server and releases socket cleanly. (+6 more)

### Community 11 - "Event"
Cohesion: 0.16
Nodes (15): Event, EventType, Enum, str, Event domain model with ordering and session/job linkage., Categorization of terminal and lifecycle events., Represents an observable, ordered event within a session or job stream., Enables natural sorting of events by sequence number and timestamp. (+7 more)

### Community 12 - "ValidationError"
Cohesion: 0.17
Nodes (16): Raised when entity validation fails., ValidationError, CredentialRef, CredentialType, Enum, str, Credential reference model ensuring secret isolation., Supported types of credentials. (+8 more)

### Community 13 - "ConnectionMethod"
Cohesion: 0.17
Nodes (14): Enum, ConnectionMethod, DeviceType, Device inventory model and connection metadata., Categorization of managed devices., Supported transport/connection mechanisms for devices., Any, Updates attributes of an existing device. (+6 more)

### Community 14 - "CredentialResolver"
Cohesion: 0.15
Nodes (13): CredentialResolver, ExternalCredentialProvider, Protocol, Credential abstraction and resolution interface., Internal contract to resolve secret references safely. This interface must only…, Resolves the raw secret string/bytes for a given credential reference ID., Contract for delegating credential resolution to an external provider., Resolves secret from external provider. Returns None if not handled. (+5 more)

### Community 15 - "Job"
Cohesion: 0.19
Nodes (16): Job, JobStatus, Enum, str, Job domain model and lifecycle states., Conceptual states of an asynchronous or synchronous job., Represents an execution unit within a persistent session., parametrize (+8 more)

### Community 16 - "persistence.py"
Cohesion: 0.12
Nodes (11): EventRepository, JobRepository, Protocol, Persistence interfaces for sessions, jobs, and events., Contract for job persistence., Persists or updates a job., Retrieves a job by ID or returns None if not found., Lists all jobs associated with a given session ID. (+3 more)

### Community 17 - "TerminalTransport"
Cohesion: 0.12
Nodes (10): Protocol, Terminal and transport adapter interfaces., Contract for low-level terminal/transport implementations (PTY, SSH, Serial,…, Initializes and opens the underlying transport channel., Reads up to max_bytes from the transport., Writes raw byte data to the transport channel and returns bytes written., Resizes the terminal dimensions if supported by the transport., Closes the transport channel cleanly. (+2 more)

### Community 18 - "ProtectedLocalCredentialStore"
Cohesion: 0.18
Nodes (14): CredentialResolutionError, Raised when resolving a credential secret fails or integrity check fails., ProtectedLocalCredentialStore, Deletes credential from the protected store., Local credential storage protecting secrets at rest using authenticated…, local_cred_store(), fixture, Path (+6 more)

### Community 19 - "LocalSession"
Cohesion: 0.17
Nodes (12): LocalSession, Resizes the terminal window dimensions., Orchestrates an interactive local terminal session. Connects the high-level…, Returns the session identifier., Returns the in-memory active LocalSession if open, else None., Tests for LocalSession controller and lifecycle integration., test_interactive_session_write_and_read(), test_pluggable_transport_with_local_session() (+4 more)

### Community 20 - "LocalProcessTransport"
Cohesion: 0.18
Nodes (13): LocalProcessTransport, Terminates process cleanly and closes resources., TerminalTransport adapter backed by a local OS subprocess. Uses non-blocking…, Returns process returncode or None if still running., Tests for LocalProcessTransport adapter., test_command_not_found_raises_transport_error(), test_conforms_to_terminal_transport_protocol(), test_interactive_io() (+5 more)

### Community 21 - "SqliteDeviceRepository"
Cohesion: 0.16
Nodes (8): Row, Persistent DeviceRepository implementation backed by SQLite., Persists or updates a device entity., Retrieves a device by ID., Lists all active and non-deleted registered devices., Lists all devices, optionally including logically deleted ones., SqliteDeviceRepository, test_sqlite_device_repository_conforms_to_protocol()

### Community 22 - ".poll_status"
Cohesion: 0.17
Nodes (8): SessionStatus, Any, EventType, Opens the transport and transitions session to RUNNING state. If transport…, Writes data to the session transport channel and records STDIN event., Terminates transport cleanly and transitions session to CLOSED state., Inspects transport liveness and synchronizes session state., Returns current session status synchronized with the transport.

### Community 23 - "Device"
Cohesion: 0.19
Nodes (6): Device, Represents an addressable device in the inventory., Lists registered devices., InMemoryDeviceRepository, In-memory implementation conforming to DeviceRepository protocol., test_device_repository_protocol()

### Community 24 - "device_service.py"
Cohesion: 0.18
Nodes (8): Device catalog interface definition., Device catalog and safe internal connection resolution service., Resolves full connection details internally using a name or device ID. Enforces…, Internal connection metadata container. NOTE: The resolved secret exists…, ResolvedConnection, Session, job, device, and credential management services package., Local session controller binding Session lifecycle to TerminalTransport and…, test_resolve_connection_by_nickname()

### Community 25 - "SqliteEventRepository"
Cohesion: 0.18
Nodes (9): Event, Persistent EventRepository implementation with strict sequence uniqueness and…, Appends an event ensuring strict sequence order and rejecting duplicates., Retrieves ordered event stream from a sequence cursor with optional limit., Returns the highest sequence number recorded for the session, or -1 if empty., SqliteEventRepository, doc_api_server(), fixture (+1 more)

### Community 26 - "SqliteJobRepository"
Cohesion: 0.26
Nodes (8): JobStatus, Job, Persistent JobRepository implementation backed by SQLite., Persists or updates a job entity., Retrieves a job by ID., Lists all jobs associated with a given session., Lists all persisted jobs, optionally filtered by status., SqliteJobRepository

### Community 27 - "DeviceRepository"
Cohesion: 0.15
Nodes (7): DeviceRepository, Protocol, Contract for device catalog storage and queries., Registers a new device or updates an existing one., Retrieves a device by unique ID., Lists all active registered devices., Lists all registered devices, optionally including deleted ones.

### Community 28 - "credential_store.py"
Cohesion: 0.22
Nodes (9): _iso(), _crypt_keystream(), _derive_keys(), Protected credential storage and resolution services ensuring secrets are never…, Decodes the secret in memory. Returns None if ref_id does not exist., Re-encrypts all stored credentials with a new master key in a single atomic…, Derives 32-byte encryption key and 32-byte MAC key using PBKDF2-HMAC-SHA256., Symmetric authenticated keystream XOR cipher (counter mode over HMAC-SHA256). (+1 more)

### Community 29 - "DeviceService"
Cohesion: 0.23
Nodes (12): DeviceService, Manages the device inventory and handles secure connection resolution., device_repo(), device_service(), fixture, Path, Tests for DeviceRepository and DeviceService CRUD, state transitions, and…, sqlite_storage() (+4 more)

### Community 30 - "test_mcp_server.py"
Cohesion: 0.29
Nodes (11): Tests for FastMCP server implementation in Terminal Session Manager., Helper to run async coroutines in synchronous pytest tests., _run(), test_mcp_device_inactive_rejection(), test_mcp_devices_and_secret_protection(), test_mcp_error_handling_unknown_entities(), test_mcp_events_cursor_pagination(), test_mcp_job_cancel() (+3 more)

### Community 31 - "Relatório — Etapa 0: Contrato e Esqueleto"
Cohesion: 0.18
Nodes (10): Decisões Tomadas, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 1 — Sessão Local Mínima), Entregue, Estrutura do Projeto, Relatório — Etapa 0: Contrato e Esqueleto, Requisitos Atendidos, Riscos e Decisões Pendentes (+2 more)

### Community 32 - ".do_GET"
Cohesion: 0.20
Nodes (8): Sends HTML response body with appropriate headers., Handles HTTP GET requests., get_openapi_spec(), get_swagger_ui_html(), Any, OpenAPI 3.0 specification and Swagger UI HTML generator for Terminal Session…, Returns standalone Swagger UI v5 HTML loading assets via CDN (zero…, Generates the OpenAPI 3.0.3 schema for Terminal Session Manager HTTP API.

### Community 33 - "app.py"
Cohesion: 0.25
Nodes (7): HTTP server management for Terminal Session Manager., Central application container managing TSM services, storage, and lifecycle., Session lifecycle and interactive I/O coordinator service., http_request(), Tests for Jobs HTTP API endpoints., test_job_cancellation_api(), test_job_submit_wait_and_query_api()

### Community 34 - "Relatório — Etapa 2: Persistência e Histórico"
Cohesion: 0.20
Nodes (9): Critérios Verificados, Decisão de Armazenamento, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 3 — Jobs Assíncronos), Entregue, Relatório — Etapa 2: Persistência e Histórico, Riscos e Decisões Pendentes, Status (+1 more)

### Community 35 - "Relatório — Etapa 3: Jobs Assíncronos"
Cohesion: 0.20
Nodes (9): Critérios Verificados, Decisões Tomadas, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 4 — Dispositivos e Credenciais), Entregue, Relatório — Etapa 3: Jobs Assíncronos, Riscos e Decisões Pendentes, Status (+1 more)

### Community 36 - "Relatório — Etapa 4: Dispositivos e Credenciais"
Cohesion: 0.20
Nodes (9): Critérios Verificados, Decisões Tomadas, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 5 — API), Entregue, Relatório — Etapa 4: Dispositivos e Credenciais, Riscos e Decisões Pendentes, Status (+1 more)

### Community 37 - "Relatório — Etapa 5: API HTTP"
Cohesion: 0.20
Nodes (9): Critérios Verificados, Decisão Técnica HTTP e Documentação, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 6 — MCP), Entregue, Relatório — Etapa 5: API HTTP, Riscos e Decisões Pendentes, Status (+1 more)

### Community 38 - "Relatório — Etapa 6: MCP com FastMCP"
Cohesion: 0.20
Nodes (9): 1. Início via CLI, 2. Configuração em Clientes MCP (Claude Desktop, Cursor, Antigravity), Como Iniciar e Conectar um Cliente MCP, Decisões Técnicas, Entregue, Próximos Passos Recomendados, Relatório — Etapa 6: MCP com FastMCP, Status (+1 more)

### Community 39 - "SqliteSessionRepository"
Cohesion: 0.31
Nodes (5): Session, Persistent SessionRepository implementation backed by SQLite., Persists or updates a session entity., Retrieves a session by ID., SqliteSessionRepository

### Community 40 - "test_device_resolution_and_session.py"
Cohesion: 0.22
Nodes (9): device_service_and_store(), fixture, Path, Tests for device resolution by nickname, error handling, session injection, and…, sqlite_storage(), test_resolve_connection_deactivated_or_deleted_device_fails(), test_resolve_connection_device_not_found(), test_resolve_connection_missing_credential_reference() (+1 more)

### Community 41 - "Relatório — Etapa 1: Sessão Local Mínima"
Cohesion: 0.22
Nodes (8): Critérios Verificados, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 2 — Persistência e Histórico), Entregue, Relatório — Etapa 1: Sessão Local Mínima, Riscos e Decisões Pendentes, Status, Testes e Resultados

### Community 43 - "Relatório — Etapa 7: Configuração e Endurecimento"
Cohesion: 0.25
Nodes (7): Dependências, Mudanças, Recomendação de Manutenção, Relatório — Etapa 7: Configuração e Endurecimento, Riscos Remanescentes, Status, Testes e Resultados

### Community 44 - "InvalidStateTransitionError"
Cohesion: 0.25
Nodes (5): InvalidStateTransitionError, Raised when an illegal state transition is attempted., Indicates whether the job has reached a terminal state., Transitions job to a new state and updates timestamps., Transitions session to a new status if the transition is valid.

### Community 45 - "TransportNotOpenError"
Cohesion: 0.29
Nodes (5): Raised when attempting I/O operations on an unopened transport., TransportNotOpenError, Reads up to max_bytes from the process output stream., Writes byte data to the process stdin channel., Checks if the underlying process is currently running.

### Community 46 - "SessionRepository"
Cohesion: 0.25
Nodes (5): Contract for session persistence., Persists or updates a session., Retrieves a session by ID or returns None if not found., Lists all persisted sessions., SessionRepository

### Community 47 - "auth_api_server"
Cohesion: 0.32
Nodes (7): auth_api_server(), http_request(), fixture, Path, Tests for HTTP API authentication and standardized error handling., test_api_authentication_enforcement(), test_api_standardized_error_handling()

### Community 48 - "CredentialNotFoundError"
Cohesion: 0.29
Nodes (5): CredentialNotFoundError, Raised when a requested credential reference is not found., CredentialRef, Rotates an existing credential secret with fresh cryptographic parameters., Retrieves metadata from external provider first, then local store.

### Community 49 - "local_process.py"
Cohesion: 0.29
Nodes (4): Transport adapters package., _get_default_shell(), Local process terminal transport adapter., Returns platform-appropriate default interactive shell command.

### Community 50 - "TransportClosedError"
Cohesion: 0.33
Nodes (4): Raised when attempting to write to or interact with a closed or terminated…, TransportClosedError, Reads decoded text from an active session channel with automatic masking., Writes data into an active session channel.

### Community 51 - "sqlite.py"
Cohesion: 0.40
Nodes (4): Persistence package providing concrete repositories., _parse_iso(), datetime, SQLite persistence implementation for sessions, jobs, and event history.

### Community 52 - ".read"
Cohesion: 0.33
Nodes (3): Scans and redacts configured sensitive tokens from text., Reads raw bytes from the session transport channel and records STDOUT event., Convenience method to read decoded text from the session.

### Community 53 - "test_api_docs.py"
Cohesion: 0.47
Nodes (5): Tests for OpenAPI specification and Swagger UI documentation endpoints., Helper returning (status_code, content_type, body_text)., raw_http_get(), test_openapi_specification_endpoint(), test_swagger_ui_endpoint()

### Community 54 - "test_service_restart_recovers_session_and_events"
Cohesion: 0.47
Nodes (5): Path, Tests for persistence lifecycle: service restart, voluminous output, and secret…, test_sensitive_data_masking_in_history(), test_service_restart_recovers_session_and_events(), test_voluminous_output_cursor_pagination()

### Community 55 - ".get_ref"
Cohesion: 0.40
Nodes (3): CredentialRef, Retrieves only non-sensitive metadata for a credential reference., Retrieves metadata from external provider, or None if not handled.

### Community 56 - ".__init__"
Cohesion: 0.40
Nodes (4): EventRepository, Session, SessionRepository, TerminalTransport

### Community 57 - ".__init__"
Cohesion: 0.67
Nodes (3): Path, Applies restrictive file system permissions on POSIX systems., _restrict_permissions()

### Community 58 - "TransportError"
Cohesion: 0.50
Nodes (3): Base exception for transport and process communication failures., TransportError, Starts the underlying local process and reader thread.

### Community 63 - "api_server_with_creds"
Cohesion: 0.67
Nodes (3): api_server_with_creds(), fixture, Path

### Community 64 - "api_server"
Cohesion: 0.67
Nodes (3): api_server(), fixture, Path

### Community 65 - "api_server"
Cohesion: 0.67
Nodes (3): api_server(), fixture, Path

## Knowledge Gaps
- **101 isolated node(s):** `Estrutura do Projeto`, `Etapa 0 — Contrato e Esqueleto`, `Etapa 1 — Sessão Local Mínima`, `Etapa 2 — Persistência e Histórico`, `Etapa 3 — Jobs Assíncronos` (+96 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 440 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ValidationError` connect `ValidationError` to `terminal_session_manager/__init__.py`, `JobService`, `errors.py`, `TSMRequestHandler`, `SqliteStorage`, `handler.py`, `Session`, `Event`, `ConnectionMethod`, `Job`, `ProtectedLocalCredentialStore`, `SqliteDeviceRepository`, `Device`, `device_service.py`, `SqliteEventRepository`, `SqliteJobRepository`, `credential_store.py`, `DeviceService`, `SqliteSessionRepository`, `InvalidStateTransitionError`, `sqlite.py`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Why does `DeviceService` connect `DeviceService` to `terminal_session_manager/__init__.py`, `errors.py`, `SessionService`, `handler.py`, `APIServer`, `ConnectionMethod`, `CredentialResolver`, `LocalSession`, `SqliteDeviceRepository`, `Device`, `device_service.py`, `SqliteEventRepository`, `DeviceRepository`, `test_mcp_server.py`, `app.py`, `test_device_resolution_and_session.py`, `auth_api_server`, `CredentialNotFoundError`, `.__init__`, `.__init__`, `api_server_with_creds`, `api_server`, `api_server`, `.deactivate_device`, `.get_device_by_name`, `.remove_device`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `SqliteStorage` connect `SqliteStorage` to `terminal_session_manager/__init__.py`, `JobService`, `handler.py`, `ProtectedLocalCredentialStore`, `SqliteDeviceRepository`, `SqliteEventRepository`, `credential_store.py`, `DeviceService`, `test_mcp_server.py`, `app.py`, `SqliteSessionRepository`, `test_device_resolution_and_session.py`, `auth_api_server`, `sqlite.py`, `test_service_restart_recovers_session_and_events`, `.__init__`, `.lock`, `api_server_with_creds`, `api_server`, `api_server`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `ValidationError` (e.g. with `TSMRequestHandler` and `CredentialRef`) actually correct?**
  _`ValidationError` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `SqliteStorage` (e.g. with `TSMApplication` and `ProtectedLocalCredentialStore`) actually correct?**
  _`SqliteStorage` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `DeviceService` (e.g. with `APIServer` and `TSMApplication`) actually correct?**
  _`DeviceService` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `Device` (e.g. with `device_to_dict()` and `DeviceRepository`) actually correct?**
  _`Device` has 10 INFERRED edges - model-reasoned connections that need verification._