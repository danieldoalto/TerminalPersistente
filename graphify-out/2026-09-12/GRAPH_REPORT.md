# Graph Report - TerminalPersistente  (2026-09-12)

## Corpus Check
- 79 files · ~52,223 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1186 nodes · 2846 edges · 73 communities (65 shown, 7 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 622 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `93540541`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- terminal_session_manager/__init__.py
- JobService
- Terminal Session Manager
- Job
- SessionService
- TSMRequestHandler
- scp_service.py
- SqliteStorage
- MockChannel
- Session
- APIServer
- 3. Tool Reference
- CredentialType
- SqliteDeviceRepository
- credential_store.py
- 3. Tool Reference
- local_session.py
- TerminalTransport
- test_device_service.py
- LocalSession
- LocalProcessTransport
- ._row_to_device
- Exemplos Práticos via `curl`
- Device
- DeviceNotFoundError
- SSHTransport
- TSMApplication
- DeviceRepository
- ValidationError
- TransportNotOpenError
- ._record_event
- Relatório — Etapa 0: Contrato e Esqueleto
- Relatório — Etapa 8: Transporte SSH
- .cancel_job
- Relatório — Etapa 2: Persistência e Histórico
- Relatório — Etapa 3: Jobs Assíncronos
- Relatório — Etapa 4: Dispositivos e Credenciais
- Relatório — Etapa 5: API HTTP
- Relatório — Etapa 6: MCP com FastMCP
- mcp/server.py
- DeviceService
- Relatório — Etapa 1: Sessão Local Mínima
- FakeTransport
- Relatório — Etapa 7: Configuração e Endurecimento
- MockSSHClient
- scp_api_server
- test_scp_service.py
- handler.py
- ProtectedLocalCredentialStore
- ._transfer_worker
- Event
- sqlite.py
- test_mcp_server.py
- test_ssh_session_and_jobs.py
- api_server
- CredentialRef
- test_contracts.py
- Relatório — Etapa 9: Transferência SCP
- errors.py
- job_service.py
- test_hardening_lifecycle.py
- doc_api_server
- JobNotFoundError
- device_service.py
- test_api_scp.py
- rules/graphify.md
- workflows/graphify.md
- _get_default_shell
- .transition_to
- ConnectionMethod
- api_server_with_creds
- terminal-session-manager

## God Nodes (most connected - your core abstractions)
1. `DeviceService` - 65 edges
2. `ValidationError` - 62 edges
3. `SqliteStorage` - 59 edges
4. `JobService` - 57 edges
5. `Device` - 53 edges
6. `Job` - 53 edges
7. `Session` - 53 edges
8. `ProtectedLocalCredentialStore` - 48 edges
9. `LocalSession` - 46 edges
10. `JobStatus` - 45 edges

## Surprising Connections (you probably didn't know these)
- `test_scp_non_existent_device()` --uses--> `DeviceNotFoundError`  [INFERRED]
  tests/test_scp_service.py → src/terminal_session_manager/errors.py
- `test_scp_inactive_device()` --uses--> `DeviceInactiveError`  [INFERRED]
  tests/test_scp_service.py → src/terminal_session_manager/errors.py
- `test_scp_download_invalid_destination_dir()` --uses--> `ValidationError`  [INFERRED]
  tests/test_scp_service.py → src/terminal_session_manager/errors.py
- `test_scp_upload_file_not_found()` --uses--> `ValidationError`  [INFERRED]
  tests/test_scp_service.py → src/terminal_session_manager/errors.py
- `test_device_deactivation()` --uses--> `Device`  [INFERRED]
  tests/test_device_and_credential.py → src/terminal_session_manager/models/device.py

## Import Cycles
- None detected.

## Communities (73 total, 7 thin omitted)

### Community 0 - "terminal_session_manager/__init__.py"
Cohesion: 0.09
Nodes (41): MonkeyPatch, ConfigurationError, HistoryConfig, JobsConfig, load_config(), _parse_bool(), Any, Path (+33 more)

### Community 1 - "JobService"
Cohesion: 0.16
Nodes (18): JobStatus, str, Conceptual states of an asynchronous or synchronous job., Lists all persisted jobs, optionally filtered by status., JobService, Manages asynchronous job execution, monitoring, waiting, and cancellation. Jobs…, Retrieves current job status from persistent repository., Lists all jobs registered for a session. (+10 more)

### Community 2 - "Terminal Session Manager"
Cohesion: 0.04
Nodes (43): Estrutura do Projeto, Etapa 0 — Contrato e Esqueleto, Etapa 1 — Sessão Local Mínima, Etapa 2 — Persistência e Histórico, Etapa 3 — Jobs Assíncronos, Etapa 4 — Dispositivos e Credenciais, Etapa 5 — API HTTP, Etapa 6 — MCP com FastMCP (+35 more)

### Community 3 - "Job"
Cohesion: 0.09
Nodes (19): Persists or updates a job., Retrieves a job by ID or returns None if not found., Lists all jobs associated with a given session ID., Job, Represents an execution unit within a persistent session., Retrieves a job by ID., Lists all jobs associated with a given session., InMemoryJobRepository (+11 more)

### Community 4 - "SessionService"
Cohesion: 0.11
Nodes (12): Any, Raised when a requested session is not found., SessionNotFoundError, Writes data into an active session channel., Reads decoded text from an active session channel with automatic masking., Terminates an active session and updates its final status., Terminates all active sessions during shutdown., Coordinates interactive terminal sessions, persistence, and active processes. (+4 more)

### Community 5 - "TSMRequestHandler"
Cohesion: 0.14
Nodes (15): BaseHTTPRequestHandler, Exception, Processes HTTP API requests with token authentication and domain error…, Verifies Bearer token or X-API-Key against server configured token., Sends HTML response body with appropriate headers., Serializes and sends JSON response body with appropriate headers., Sends standardized JSON error response without internal leakages., Reads and parses JSON request payload safely. (+7 more)

### Community 6 - "scp_service.py"
Cohesion: 0.17
Nodes (16): SSH transport connection and host key verification settings., SSHConfig, Domain interfaces and contracts package., EventRepository, JobRepository, Protocol, Persistence interfaces for sessions, jobs, and events., Contract for session persistence. (+8 more)

### Community 7 - "SqliteStorage"
Cohesion: 0.08
Nodes (27): Connection, RLock, Path, Manages the SQLite database connection, initialization, and transactions., Returns the storage reentrant lock for synchronizing transactions., Returns the underlying sqlite connection., Closes the underlying database connection cleanly., Persistent EventRepository implementation with strict sequence uniqueness and… (+19 more)

### Community 9 - "Session"
Cohesion: 0.08
Nodes (20): Persists or updates a session., Retrieves a session by ID or returns None if not found., Lists all persisted sessions., Represents a persistent terminal session., Indicates whether the session is in an active/alive operational state., Indicates whether the session has reached a closed terminal state., Session, Retrieves a session by ID. (+12 more)

### Community 10 - "APIServer"
Cohesion: 0.10
Nodes (16): APIServer, Encapsulates the standard library ThreadingHTTPServer lifecycle for TSM., Returns the bound host address., Returns the actual bound TCP port number., Returns base HTTP URL (e.g. http://127.0.0.1:54321)., Starts serving requests synchronously (blocking)., Starts server in a background daemon thread for testing or concurrent execution., Stops server and releases socket cleanly. (+8 more)

### Community 11 - "3. Tool Reference"
Cohesion: 0.11
Nodes (17): 1. Overview & Core Philosophy, 2. Server Configuration, 3.1. Devices (Inventory & Remote SSH), 3.2. Sessions (Interactive Terminal PTY), 3.3. Jobs (Asynchronous Background Execution), 3.4. History & Events, 3.5. File Transfers (SCP), 3. Tool Reference (+9 more)

### Community 12 - "CredentialType"
Cohesion: 0.15
Nodes (14): CredentialType, Enum, str, Credential reference model ensuring secret isolation., Supported types of credentials., http_request(), Tests for Devices HTTP API endpoints and safe nickname resolution., test_device_crud_and_safe_resolution_api() (+6 more)

### Community 13 - "SqliteDeviceRepository"
Cohesion: 0.14
Nodes (11): Persistent DeviceRepository implementation backed by SQLite., Logically deactivates a device by ID., Logically removes a device by ID., SqliteDeviceRepository, api_server(), fixture, Path, device_repo() (+3 more)

### Community 14 - "credential_store.py"
Cohesion: 0.14
Nodes (14): CredentialResolver, ExternalCredentialProvider, Protocol, Credential abstraction and resolution interface., Internal contract to resolve secret references safely. This interface must only…, Resolves the raw secret string/bytes for a given credential reference ID., Contract for delegating credential resolution to an external provider., Resolves secret from external provider. Returns None if not handled. (+6 more)

### Community 15 - "3. Tool Reference"
Cohesion: 0.11
Nodes (17): 1. Overview & Core Philosophy, 2. Server Configuration, 3.1. Devices (Inventory & Remote SSH), 3.2. Sessions (Interactive Terminal PTY), 3.3. Jobs (Asynchronous Background Execution), 3.4. History & Events, 3.5. File Transfers (SCP), 3. Tool Reference (+9 more)

### Community 16 - "local_session.py"
Cohesion: 0.14
Nodes (15): Enum, str, Session domain model and state definitions., Conceptual states of a session., Transitions session to a new status if the transition is valid., SessionStatus, Local session controller binding Session lifecycle to TerminalTransport and…, Tests for LocalSession controller and lifecycle integration. (+7 more)

### Community 17 - "TerminalTransport"
Cohesion: 0.11
Nodes (11): Protocol, Contract for low-level terminal/transport implementations (PTY, SSH, Serial,…, Initializes and opens the underlying transport channel., Reads up to max_bytes from the transport., Writes raw byte data to the transport channel and returns bytes written., Resizes the terminal dimensions if supported by the transport., Closes the transport channel cleanly., Checks if the underlying process/connection is currently active. (+3 more)

### Community 18 - "test_device_service.py"
Cohesion: 0.20
Nodes (10): device_service(), fixture, Path, Tests for DeviceRepository and DeviceService CRUD, state transitions, and…, sqlite_storage(), test_device_crud_lifecycle(), test_device_deactivation_and_logical_removal(), test_device_not_found_errors() (+2 more)

### Community 19 - "LocalSession"
Cohesion: 0.13
Nodes (13): LocalSession, Any, Returns the session identifier., Returns current session status synchronized with the transport., Opens the transport and transitions session to RUNNING state. If transport…, Scans and redacts configured sensitive tokens from text., Writes data to the session transport channel and records STDIN event., Reads raw bytes from the session transport channel and records STDOUT event. (+5 more)

### Community 20 - "LocalProcessTransport"
Cohesion: 0.12
Nodes (16): LocalProcessTransport, Records terminal dimensions., Terminates process cleanly and closes resources., TerminalTransport adapter backed by a local OS subprocess. Uses non-blocking…, Returns process returncode or None if still running., Starts the underlying local process and reader thread., Continuously reads bytes from process stdout pipe into output queue., Tests for LocalProcessTransport adapter. (+8 more)

### Community 21 - "._row_to_device"
Cohesion: 0.22
Nodes (4): Retrieves a device by ID., Retrieves a device by unique name., Lists all active and non-deleted registered devices., Lists all devices, optionally including logically deleted ones.

### Community 22 - "Exemplos Práticos via `curl`"
Cohesion: 0.06
Nodes (34): 1. Criar uma Nova Sessão, 1. Instalação e Requisitos, 2. Configuração Centralizada, 2. Escrever um Comando na Sessão, 3.1. Validar a Configuração, 3.2. Exibir Status, 3.3. Iniciar a API HTTP REST, 3.4. Iniciar o Servidor MCP (Model Context Protocol) (+26 more)

### Community 23 - "Device"
Cohesion: 0.12
Nodes (9): Device, Represents an addressable device in the inventory., Deactivates device logically without deleting historical references., Marks device as logically removed without deleting historical references., Deactivates a device logically., Registers a new device or updates an existing one., InMemoryDeviceRepository, In-memory implementation conforming to DeviceRepository protocol. (+1 more)

### Community 24 - "DeviceNotFoundError"
Cohesion: 0.12
Nodes (11): DeviceNotFoundError, DomainError, EntityNotFoundError, InvalidStateError, InvalidStateTransitionError, Exception, Raised when an unrecognized or malformed state is encountered., Raised when an illegal state transition is attempted. (+3 more)

### Community 25 - "SSHTransport"
Cohesion: 0.10
Nodes (20): Any, Returns remote exit code or None if channel is still active., Reads stdout and stderr streams from the SSH channel into queues., Resizes the remote terminal dimensions., TerminalTransport adapter backed by an SSH connection using Paramiko. Supports…, SSHTransport, SSHClient, Unit tests for SSHTransport using mocked Paramiko client and channel. (+12 more)

### Community 26 - "TSMApplication"
Cohesion: 0.18
Nodes (21): add_device_interactive(), clean_path_input(), delete_device_interactive(), edit_device_interactive(), generate_ssh_key_interactive(), list_devices_view(), main(), print_header() (+13 more)

### Community 27 - "DeviceRepository"
Cohesion: 0.11
Nodes (10): DeviceRepository, Protocol, Contract for device catalog storage and queries., Registers a new device or updates an existing one., Retrieves a device by unique ID., Retrieves a device by unique name., Lists all active registered devices., Logically deactivates a device by ID. (+2 more)

### Community 28 - "ValidationError"
Cohesion: 0.16
Nodes (11): Row, Raised when entity validation fails., ValidationError, _iso(), _parse_iso(), datetime, Persists or updates a session entity., Persists or updates a job entity. (+3 more)

### Community 29 - "TransportNotOpenError"
Cohesion: 0.13
Nodes (10): Queue, Raised when attempting I/O operations on an unopened transport., TransportNotOpenError, Reads up to max_bytes from the process output stream., Writes byte data to the process stdin channel., Checks if the underlying process is currently running., Reads up to max_bytes from the SSH stdout stream., Reads up to max_bytes from the SSH stderr stream. (+2 more)

### Community 30 - "._record_event"
Cohesion: 0.21
Nodes (6): Any, Creates and launches an asynchronous job in a background worker., Background worker thread executing the job process., Executes a job remotely over SSH, streaming events and capturing output., Reconciles interrupted jobs upon service restart. Scans repository for jobs in…, Atomically records a sequenced event associated with a session and job.

### Community 31 - "Relatório — Etapa 0: Contrato e Esqueleto"
Cohesion: 0.18
Nodes (10): Decisões Tomadas, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 1 — Sessão Local Mínima), Entregue, Estrutura do Projeto, Relatório — Etapa 0: Contrato e Esqueleto, Requisitos Atendidos, Riscos e Decisões Pendentes (+2 more)

### Community 32 - "Relatório — Etapa 8: Transporte SSH"
Cohesion: 0.20
Nodes (9): Biblioteca Escolhida, Configuração, Critérios Verificados, Entregue, Limitações, Recomendação de Manutenção, Relatório — Etapa 8: Transporte SSH, Status (+1 more)

### Community 33 - ".cancel_job"
Cohesion: 0.29
Nodes (5): Popen, Terminates a subprocess safely, escalating to kill if necessary., Waits for a job to complete execution and returns the finished Job., Cancels a running or created job., _terminate_proc()

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

### Community 39 - "mcp/server.py"
Cohesion: 0.20
Nodes (15): FastMCP, device_to_dict(), event_to_dict(), _iso(), job_to_dict(), Any, Suppresses default stderr server logging for quiet test execution., session_to_dict() (+7 more)

### Community 40 - "DeviceService"
Cohesion: 0.11
Nodes (18): DeviceInactiveError, Raised when an operation targets a deactivated or removed device., DeviceService, Logically marks a device as removed., Lists registered devices., Resolves full connection details internally using a name or device ID. Enforces…, Manages the device inventory and handles secure connection resolution., Retrieves a device by ID. (+10 more)

### Community 41 - "Relatório — Etapa 1: Sessão Local Mínima"
Cohesion: 0.22
Nodes (8): Critérios Verificados, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 2 — Persistência e Histórico), Entregue, Relatório — Etapa 1: Sessão Local Mínima, Riscos e Decisões Pendentes, Status, Testes e Resultados

### Community 43 - "Relatório — Etapa 7: Configuração e Endurecimento"
Cohesion: 0.25
Nodes (7): Dependências, Mudanças, Recomendação de Manutenção, Relatório — Etapa 7: Configuração e Endurecimento, Riscos Remanescentes, Status, Testes e Resultados

### Community 44 - "MockSSHClient"
Cohesion: 0.12
Nodes (10): test_scp_auth_failure_masks_secret(), MockSSHClient, Any, Mock Paramiko SSHClient., Verifies private key loading and connection kwargs., Verifies that strict_host_key_checking uses RejectPolicy and never…, Verifies command execution mode capturing exit code and stderr., test_ssh_transport_command_exec_and_exit_code() (+2 more)

### Community 45 - "scp_api_server"
Cohesion: 0.15
Nodes (11): fixture, Path, scp_api_server(), test_mcp_scp_tools_registered_and_callable(), MockSCPClient, Any, fixture, Path (+3 more)

### Community 46 - "test_scp_service.py"
Cohesion: 0.14
Nodes (12): Unit and integration tests for SCP file transfer service., test_scp_cancel_transfer(), test_scp_concurrency(), test_scp_download_invalid_destination_dir(), test_scp_download_success(), test_scp_inactive_device(), test_scp_non_existent_device(), test_scp_non_ssh_device() (+4 more)

### Community 47 - "handler.py"
Cohesion: 0.18
Nodes (10): datetime, HTTP request handler implementing REST API for sessions, jobs, events, and…, HTTP API package exposing Terminal Session Manager services., get_openapi_spec(), get_swagger_ui_html(), Any, OpenAPI 3.0 specification and Swagger UI HTML generator for Terminal Session…, Returns standalone Swagger UI v5 HTML loading assets via CDN (zero… (+2 more)

### Community 48 - "ProtectedLocalCredentialStore"
Cohesion: 0.11
Nodes (22): CredentialResolutionError, Raised when resolving a credential secret fails or integrity check fails., _crypt_keystream(), _derive_keys(), ProtectedLocalCredentialStore, Decodes the secret in memory. Returns None if ref_id does not exist., Deletes credential from the protected store., Rotates an existing credential secret with fresh cryptographic parameters. (+14 more)

### Community 49 - "._transfer_worker"
Cohesion: 0.20
Nodes (8): Any, Enum, Path, str, Submits an asynchronous SCP file transfer job., Background thread worker executing the SCP file transfer., Direction of an SCP transfer relative to the local TSM host., SCPTransferDirection

### Community 50 - "Event"
Cohesion: 0.09
Nodes (22): Appends a new event to the session/job stream., Retrieves an ordered stream of events for a session from a sequence cursor., Event, EventType, Enum, str, Event domain model with ordering and session/job linkage., Categorization of terminal and lifecycle events. (+14 more)

### Community 51 - "sqlite.py"
Cohesion: 0.18
Nodes (10): Path, Central application container managing TSM services, storage, and lifecycle., Applies restrictive file system permissions on POSIX systems., _restrict_permissions(), Persistence package providing concrete repositories., SQLite persistence implementation for sessions, jobs, and event history., Persistent SessionRepository implementation backed by SQLite., Persistent JobRepository implementation backed by SQLite. (+2 more)

### Community 52 - "test_mcp_server.py"
Cohesion: 0.29
Nodes (11): Tests for FastMCP server implementation in Terminal Session Manager., Helper to run async coroutines in synchronous pytest tests., _run(), test_mcp_device_inactive_rejection(), test_mcp_devices_and_secret_protection(), test_mcp_error_handling_unknown_entities(), test_mcp_events_cursor_pagination(), test_mcp_job_cancel() (+3 more)

### Community 53 - "test_ssh_session_and_jobs.py"
Cohesion: 0.20
Nodes (13): Integration tests for remote SSH Sessions and asynchronous Jobs via…, Verifies asynchronous job execution on a remote SSH host via nickname., Verifies that non-zero exit code transitions remote job to FAILED., Verifies cancelling a running SSH job terminates channel cleanly., Verifies that non-existent or deactivated SSH devices are rejected., Helper to register a remote SSH device with protected credentials., Verifies creating an interactive session targeting an SSH device by nickname., _register_ssh_device() (+5 more)

### Community 54 - "api_server"
Cohesion: 0.28
Nodes (8): api_server(), http_request(), fixture, Path, Tests for Sessions and Events HTTP API endpoints., Helper to perform HTTP JSON requests using standard library urllib., test_events_cursor_pagination_api(), test_session_lifecycle_and_io_api()

### Community 55 - "CredentialRef"
Cohesion: 0.16
Nodes (8): Retrieves only non-sensitive metadata for a credential reference., Retrieves metadata from external provider, or None if not handled., CredentialRef, Safe reference metadata for credentials. NOTE: This model strictly avoids…, Retrieves metadata from external provider first, then local store., InMemoryCredentialResolver, In-memory mock conforming to CredentialResolver protocol., test_credential_resolver_protocol()

### Community 56 - "test_contracts.py"
Cohesion: 0.18
Nodes (4): MockTerminalTransport, Unit tests for domain interfaces (Protocols) and mock in-memory implementations., In-memory mock conforming to TerminalTransport protocol., test_terminal_transport_protocol()

### Community 57 - "Relatório — Etapa 9: Transferência SCP"
Cohesion: 0.20
Nodes (9): Biblioteca Escolhida, Decisões de Arquitetura, Entrada Recomendada para a Próxima Etapa, Entregue, Limitações Conhecidas, Relatório — Etapa 9: Transferência SCP, Resultado da Suíte Completa:, Status (+1 more)

### Community 58 - "errors.py"
Cohesion: 0.15
Nodes (15): PKey, Domain exceptions for Terminal Session Manager., Raised when a blocking transport operation exceeds the specified timeout., Base exception for transport and process communication failures., Raised when attempting to write to or interact with a closed or terminated…, TransportClosedError, TransportError, TransportTimeoutError (+7 more)

### Community 59 - "job_service.py"
Cohesion: 0.27
Nodes (7): Enum, Job domain model and lifecycle states., Asynchronous Job execution and lifecycle management service., http_request(), Tests for Jobs HTTP API endpoints., test_job_cancellation_api(), test_job_submit_wait_and_query_api()

### Community 61 - "test_hardening_lifecycle.py"
Cohesion: 0.33
Nodes (9): Path, Tests for lifecycle hardening, graceful shutdown, credential rotation, and…, _run(), test_api_and_mcp_share_same_database_and_configuration(), test_clean_installation_creates_db_directory(), test_credential_store_rotate_credential(), test_credential_store_rotate_master_key(), test_graceful_shutdown_closes_active_sessions() (+1 more)

### Community 62 - "doc_api_server"
Cohesion: 0.28
Nodes (8): doc_api_server(), fixture, Path, Tests for OpenAPI specification and Swagger UI documentation endpoints., Helper returning (status_code, content_type, body_text)., raw_http_get(), test_openapi_specification_endpoint(), test_swagger_ui_endpoint()

### Community 63 - "JobNotFoundError"
Cohesion: 0.33
Nodes (4): JobNotFoundError, Raised when a requested job is not found., Cancels an in-progress SCP transfer, closing its connection immediately., Blocks until the transfer completes, times out, or is cancelled.

### Community 64 - "device_service.py"
Cohesion: 0.20
Nodes (7): CredentialNotFoundError, Raised when a requested credential reference is not found., Device catalog interface definition., Device catalog and safe internal connection resolution service., Internal connection metadata container. NOTE: The resolved secret exists…, ResolvedConnection, test_resolve_connection_by_nickname()

### Community 65 - "test_api_scp.py"
Cohesion: 0.53
Nodes (5): http_request(), Tests for SCP HTTP API and FastMCP tools., test_api_scp_download(), test_api_scp_upload(), test_api_scp_validations()

### Community 70 - "ConnectionMethod"
Cohesion: 0.19
Nodes (12): ConnectionMethod, DeviceType, Enum, str, Device inventory model and connection metadata., Categorization of managed devices., Supported transport/connection mechanisms for devices., Domain models package for Terminal Session Manager. (+4 more)

### Community 71 - "api_server_with_creds"
Cohesion: 0.67
Nodes (3): api_server_with_creds(), fixture, Path

## Knowledge Gaps
- **170 isolated node(s):** `terminal-session-manager`, `graphify`, `1. Overview & Core Philosophy`, `Cursor / Antigravity (`.agents/mcp_config.json` or global config)`, `Claude Desktop (`claude_desktop_config.json`)` (+165 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 586 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DeviceService` connect `DeviceService` to `terminal_session_manager/__init__.py`, `JobService`, `SessionService`, `scp_service.py`, `APIServer`, `SqliteDeviceRepository`, `credential_store.py`, `local_session.py`, `test_device_service.py`, `LocalSession`, `Device`, `DeviceNotFoundError`, `TSMApplication`, `DeviceRepository`, `mcp/server.py`, `scp_api_server`, `handler.py`, `sqlite.py`, `test_mcp_server.py`, `api_server`, `CredentialRef`, `job_service.py`, `doc_api_server`, `device_service.py`, `ConnectionMethod`, `api_server_with_creds`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `Device` connect `Device` to `device_service.py`, `ConnectionMethod`, `mcp/server.py`, `DeviceService`, `CredentialType`, `SqliteDeviceRepository`, `scp_api_server`, `handler.py`, `test_scp_service.py`, `sqlite.py`, `._row_to_device`, `test_ssh_session_and_jobs.py`, `TSMApplication`, `DeviceRepository`, `ValidationError`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `LocalSession` connect `LocalSession` to `terminal_session_manager/__init__.py`, `device_service.py`, `SessionService`, `scp_service.py`, `ConnectionMethod`, `DeviceService`, `Session`, `SqliteStorage`, `CredentialType`, `credential_store.py`, `local_session.py`, `TerminalTransport`, `Event`, `LocalProcessTransport`, `SSHTransport`, `errors.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `DeviceService` (e.g. with `APIServer` and `TSMApplication`) actually correct?**
  _`DeviceService` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `ValidationError` (e.g. with `TSMRequestHandler` and `CredentialRef`) actually correct?**
  _`ValidationError` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `SqliteStorage` (e.g. with `TSMApplication` and `ProtectedLocalCredentialStore`) actually correct?**
  _`SqliteStorage` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `JobService` (e.g. with `APIServer` and `TSMApplication`) actually correct?**
  _`JobService` has 34 INFERRED edges - model-reasoned connections that need verification._