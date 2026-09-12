# Graph Report - TerminalPersistente  (2026-09-12)

## Corpus Check
- 79 files · ~53,505 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1189 nodes · 2858 edges · 90 communities (67 shown, 22 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 625 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `19b7dd9c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- terminal_session_manager/__init__.py
- JobService
- Terminal Session Manager
- test_job.py
- SessionNotFoundError
- TSMRequestHandler
- DeviceService
- SqliteEventRepository
- MockChannel
- scp_service.py
- APIServer
- 3. Tool Reference
- CredentialType
- SqliteDeviceRepository
- credential_store.py
- 3. Tool Reference
- test_service_restart_recovers_session_and_events
- TerminalTransport
- test_device_service.py
- LocalSession
- LocalProcessTransport
- CredentialResolutionError
- Exemplos Práticos via `curl`
- Device
- JobNotFoundError
- SSHTransport
- TSMApplication
- DeviceRepository
- ._row_to_session
- .log_message
- .connection
- Relatório — Etapa 0: Contrato e Esqueleto
- Relatório — Etapa 8: Transporte SSH
- .lock
- Relatório — Etapa 2: Persistência e Histórico
- Relatório — Etapa 3: Jobs Assíncronos
- Relatório — Etapa 4: Dispositivos e Credenciais
- Relatório — Etapa 5: API HTTP
- Relatório — Etapa 6: MCP com FastMCP
- mcp/server.py
- ProtectedLocalCredentialStore
- Relatório — Etapa 1: Sessão Local Mínima
- FakeTransport
- Relatório — Etapa 7: Configuração e Endurecimento
- Event
- MockSCPClient
- .save
- handler.py
- test_credential_protection.py
- ._transfer_worker
- EventType
- SqliteStorage
- test_mcp_server.py
- errors.py
- TransportClosedError
- CredentialRef
- MockTerminalTransport
- Relatório — Etapa 9: Transferência SCP
- Job
- TransportError
- test_scp_service.py
- ._record_event
- MockSSHClient
- .rotate_credential
- Session
- rules/graphify.md
- workflows/graphify.md
- _register_ssh_device
- DomainError
- ValidationError
- doc_api_server
- api_server
- test_session.py
- api_server
- terminal-session-manager
- .cancel_job
- test_api_scp.py
- .transition_to
- .cancel_transfer
- ._send_html
- api/__init__.py
- .get_by_id
- .list_all
- .is_active
- .is_terminal
- .transition_to
- .save
- .save
- .list_sessions

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

## Communities (90 total, 22 thin omitted)

### Community 0 - "terminal_session_manager/__init__.py"
Cohesion: 0.08
Nodes (49): MonkeyPatch, ConfigurationError, HistoryConfig, JobsConfig, load_config(), _parse_bool(), Any, Path (+41 more)

### Community 1 - "JobService"
Cohesion: 0.21
Nodes (18): JobStatus, str, Conceptual states of an asynchronous or synchronous job., JobService, Manages asynchronous job execution, monitoring, waiting, and cancellation. Jobs…, fixture, Unit and integration tests for asynchronous JobService., service() (+10 more)

### Community 2 - "Terminal Session Manager"
Cohesion: 0.04
Nodes (43): Estrutura do Projeto, Etapa 0 — Contrato e Esqueleto, Etapa 1 — Sessão Local Mínima, Etapa 2 — Persistência e Histórico, Etapa 3 — Jobs Assíncronos, Etapa 4 — Dispositivos e Credenciais, Etapa 5 — API HTTP, Etapa 6 — MCP com FastMCP (+35 more)

### Community 3 - "test_job.py"
Cohesion: 0.20
Nodes (9): parametrize, Unit tests for Job model and lifecycle states., test_job_creation_defaults(), test_job_invalid_transitions_rejected(), test_job_lifecycle_to_cancelled(), test_job_lifecycle_to_completed(), test_job_lifecycle_to_failed(), test_job_lifecycle_to_timeout() (+1 more)

### Community 4 - "SessionNotFoundError"
Cohesion: 0.18
Nodes (6): Raised when a requested session is not found., SessionNotFoundError, Writes data into an active session channel., Reads decoded text from an active session channel with automatic masking., Terminates an active session and updates its final status., Retrieves session metadata, synchronizing status if currently active.

### Community 5 - "TSMRequestHandler"
Cohesion: 0.16
Nodes (13): BaseHTTPRequestHandler, Exception, Processes HTTP API requests with token authentication and domain error…, Verifies Bearer token or X-API-Key against server configured token., Serializes and sends JSON response body with appropriate headers., Sends standardized JSON error response without internal leakages., Reads and parses JSON request payload safely., Handles HTTP POST requests. (+5 more)

### Community 6 - "DeviceService"
Cohesion: 0.12
Nodes (28): HTTP server management for Terminal Session Manager., SSH transport connection and host key verification settings., SSHConfig, EventRepository, JobRepository, Protocol, Persistence interfaces for sessions, jobs, and events., Contract for session persistence. (+20 more)

### Community 7 - "SqliteEventRepository"
Cohesion: 0.09
Nodes (24): Path, Central application container managing TSM services, storage, and lifecycle., Applies restrictive file system permissions on POSIX systems., _restrict_permissions(), Persistence package providing concrete repositories., Persistent SessionRepository implementation backed by SQLite., Persistent JobRepository implementation backed by SQLite., Retrieves a job by ID. (+16 more)

### Community 9 - "scp_service.py"
Cohesion: 0.18
Nodes (13): Enum, str, Session domain model and state definitions., Conceptual states of a session., SessionStatus, Local session controller binding Session lifecycle to TerminalTransport and…, SCP file transfer service integrated with device inventory and job execution., Tests for LocalSession controller and lifecycle integration. (+5 more)

### Community 10 - "APIServer"
Cohesion: 0.09
Nodes (17): APIServer, Any, Encapsulates the standard library ThreadingHTTPServer lifecycle for TSM., Returns the bound host address., Returns the actual bound TCP port number., Returns base HTTP URL (e.g. http://127.0.0.1:54321)., Starts serving requests synchronously (blocking)., Starts server in a background daemon thread for testing or concurrent execution. (+9 more)

### Community 11 - "3. Tool Reference"
Cohesion: 0.11
Nodes (17): 1. Overview & Core Philosophy, 2. Server Configuration, 3.1. Devices (Inventory & Remote SSH), 3.2. Sessions (Interactive Terminal PTY), 3.3. Jobs (Asynchronous Background Execution), 3.4. History & Events, 3.5. File Transfers (SCP), 3. Tool Reference (+9 more)

### Community 12 - "CredentialType"
Cohesion: 0.19
Nodes (10): CredentialType, Enum, str, Credential reference model ensuring secret isolation., Supported types of credentials., Domain models package for Terminal Session Manager., http_request(), Tests for Devices HTTP API endpoints and safe nickname resolution. (+2 more)

### Community 13 - "SqliteDeviceRepository"
Cohesion: 0.17
Nodes (10): Persistent DeviceRepository implementation backed by SQLite., Persists or updates a device entity., Retrieves a device by ID., Retrieves a device by unique name., Lists all active and non-deleted registered devices., Lists all devices, optionally including logically deleted ones., SqliteDeviceRepository, device_repo() (+2 more)

### Community 14 - "credential_store.py"
Cohesion: 0.15
Nodes (14): CredentialResolver, ExternalCredentialProvider, Protocol, Credential abstraction and resolution interface., Internal contract to resolve secret references safely. This interface must only…, Resolves the raw secret string/bytes for a given credential reference ID., Contract for delegating credential resolution to an external provider., Resolves secret from external provider. Returns None if not handled. (+6 more)

### Community 15 - "3. Tool Reference"
Cohesion: 0.11
Nodes (17): 1. Overview & Core Philosophy, 2. Server Configuration, 3.1. Devices (Inventory & Remote SSH), 3.2. Sessions (Interactive Terminal PTY), 3.3. Jobs (Asynchronous Background Execution), 3.4. History & Events, 3.5. File Transfers (SCP), 3. Tool Reference (+9 more)

### Community 16 - "test_service_restart_recovers_session_and_events"
Cohesion: 0.47
Nodes (5): Path, Tests for persistence lifecycle: service restart, voluminous output, and secret…, test_sensitive_data_masking_in_history(), test_service_restart_recovers_session_and_events(), test_voluminous_output_cursor_pagination()

### Community 17 - "TerminalTransport"
Cohesion: 0.10
Nodes (12): Protocol, Terminal and transport adapter interfaces., Contract for low-level terminal/transport implementations (PTY, SSH, Serial,…, Initializes and opens the underlying transport channel., Reads up to max_bytes from the transport., Writes raw byte data to the transport channel and returns bytes written., Resizes the terminal dimensions if supported by the transport., Closes the transport channel cleanly. (+4 more)

### Community 18 - "test_device_service.py"
Cohesion: 0.22
Nodes (8): Path, Tests for DeviceRepository and DeviceService CRUD, state transitions, and…, sqlite_storage(), test_device_crud_lifecycle(), test_device_deactivation_and_logical_removal(), test_device_not_found_errors(), test_duplicate_device_name_rejected(), test_sqlite_device_repository_conforms_to_protocol()

### Community 19 - "LocalSession"
Cohesion: 0.11
Nodes (14): LocalSession, Any, Returns the session identifier., Returns current session status synchronized with the transport., Opens the transport and transitions session to RUNNING state. If transport…, Scans and redacts configured sensitive tokens from text., Writes data to the session transport channel and records STDIN event., Reads raw bytes from the session transport channel and records STDOUT event. (+6 more)

### Community 20 - "LocalProcessTransport"
Cohesion: 0.10
Nodes (18): LocalProcessTransport, Reads up to max_bytes from the process output stream., Writes byte data to the process stdin channel., Records terminal dimensions., Terminates process cleanly and closes resources., Checks if the underlying process is currently running., TerminalTransport adapter backed by a local OS subprocess. Uses non-blocking…, Returns process returncode or None if still running. (+10 more)

### Community 21 - "CredentialResolutionError"
Cohesion: 0.14
Nodes (13): CredentialResolutionError, Raised when resolving a credential secret fails or integrity check fails., _iso(), Logically deactivates a device by ID., Logically removes a device by ID., _crypt_keystream(), _derive_keys(), Decodes the secret in memory. Returns None if ref_id does not exist. (+5 more)

### Community 22 - "Exemplos Práticos via `curl`"
Cohesion: 0.05
Nodes (36): 1. Criar uma Nova Sessão, 1. Instalação e Requisitos, 2. Configuração Centralizada, 2. Escrever um Comando na Sessão, 3.1. Validar a Configuração, 3.2. Exibir Status, 3.3. Iniciar a API HTTP REST, 3.4. Iniciar o Servidor MCP (Model Context Protocol) (+28 more)

### Community 23 - "Device"
Cohesion: 0.10
Nodes (11): Device, Represents an addressable device in the inventory., Deactivates device logically without deleting historical references., Marks device as logically removed without deleting historical references., Lists registered devices., Registers a new device or updates an existing one., Retrieves a device by ID., Retrieves a device by unique name/nickname. (+3 more)

### Community 24 - "JobNotFoundError"
Cohesion: 0.13
Nodes (9): CredentialNotFoundError, DeviceInactiveError, EntityNotFoundError, JobNotFoundError, Base exception for entity lookup failures., Raised when a requested job is not found., Raised when a requested credential reference is not found., Raised when an operation targets a deactivated or removed device. (+1 more)

### Community 25 - "SSHTransport"
Cohesion: 0.07
Nodes (30): Transport adapters package., Any, Returns remote exit code or None if channel is still active., Reads stdout and stderr streams from the SSH channel into queues., Resizes the remote terminal dimensions., Closes channel, underlying SSH client, and joins reader worker., TerminalTransport adapter backed by an SSH connection using Paramiko. Supports…, SSHTransport (+22 more)

### Community 26 - "TSMApplication"
Cohesion: 0.19
Nodes (22): add_device_interactive(), clean_path_input(), delete_device_interactive(), edit_device_interactive(), generate_ssh_key_interactive(), list_devices_view(), main(), print_header() (+14 more)

### Community 27 - "DeviceRepository"
Cohesion: 0.11
Nodes (10): DeviceRepository, Protocol, Contract for device catalog storage and queries., Registers a new device or updates an existing one., Retrieves a device by unique ID., Retrieves a device by unique name., Lists all active registered devices., Logically deactivates a device by ID. (+2 more)

### Community 28 - "._row_to_session"
Cohesion: 0.33
Nodes (3): Row, Retrieves a session by ID., Lists all persisted sessions.

### Community 31 - "Relatório — Etapa 0: Contrato e Esqueleto"
Cohesion: 0.18
Nodes (10): Decisões Tomadas, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 1 — Sessão Local Mínima), Entregue, Estrutura do Projeto, Relatório — Etapa 0: Contrato e Esqueleto, Requisitos Atendidos, Riscos e Decisões Pendentes (+2 more)

### Community 32 - "Relatório — Etapa 8: Transporte SSH"
Cohesion: 0.20
Nodes (9): Biblioteca Escolhida, Configuração, Critérios Verificados, Entregue, Limitações, Recomendação de Manutenção, Relatório — Etapa 8: Transporte SSH, Status (+1 more)

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
Cohesion: 0.16
Nodes (12): FastMCP, DeviceNotFoundError, Raised when a requested device is not found., FastMCP integration package for Terminal Session Manager., create_mcp_server(), main(), Any, FastMCP server implementation exposing Terminal Session Manager tools. (+4 more)

### Community 40 - "ProtectedLocalCredentialStore"
Cohesion: 0.19
Nodes (13): ProtectedLocalCredentialStore, Deletes credential from the protected store., Local credential storage protecting secrets at rest using authenticated…, device_service_and_store(), fixture, Path, Tests for device resolution by nickname, error handling, session injection, and…, sqlite_storage() (+5 more)

### Community 41 - "Relatório — Etapa 1: Sessão Local Mínima"
Cohesion: 0.22
Nodes (8): Critérios Verificados, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 2 — Persistência e Histórico), Entregue, Relatório — Etapa 1: Sessão Local Mínima, Riscos e Decisões Pendentes, Status, Testes e Resultados

### Community 43 - "Relatório — Etapa 7: Configuração e Endurecimento"
Cohesion: 0.25
Nodes (7): Dependências, Mudanças, Recomendação de Manutenção, Relatório — Etapa 7: Configuração e Endurecimento, Riscos Remanescentes, Status, Testes e Resultados

### Community 44 - "Event"
Cohesion: 0.10
Nodes (11): Appends a new event to the session/job stream., Retrieves an ordered stream of events for a session from a sequence cursor., Event, Represents an observable, ordered event within a session or job stream., Enables natural sorting of events by sequence number and timestamp., Appends an event ensuring strict sequence order and rejecting duplicates., Retrieves ordered event stream from a sequence cursor with optional limit., Reconciles interrupted sessions upon service restart. Scans repository for… (+3 more)

### Community 45 - "MockSCPClient"
Cohesion: 0.29
Nodes (4): MockSCPClient, Any, Path, Simulates scp.SCPClient operations in memory with progress callbacks.

### Community 47 - "handler.py"
Cohesion: 0.21
Nodes (15): device_to_dict(), event_to_dict(), _iso(), job_to_dict(), Any, datetime, HTTP request handler implementing REST API for sessions, jobs, events, and…, Handles HTTP GET requests. (+7 more)

### Community 48 - "test_credential_protection.py"
Cohesion: 0.22
Nodes (9): local_cred_store(), fixture, Path, Tests for protected credential persistence, encryption at rest, tampering…, sqlite_storage(), test_credential_store_conforms_to_protocol(), test_protected_at_rest_persistence_never_plaintext(), test_tampering_detection() (+1 more)

### Community 49 - "._transfer_worker"
Cohesion: 0.19
Nodes (9): Any, Enum, Path, str, Submits an asynchronous SCP file transfer job., Background thread worker executing the SCP file transfer., Direction of an SCP transfer relative to the local TSM host., Atomically records a sequenced event in the audit trail. (+1 more)

### Community 50 - "EventType"
Cohesion: 0.23
Nodes (11): EventType, Enum, str, Event domain model with ordering and session/job linkage., Categorization of terminal and lifecycle events., Unit tests for Event model, ordering, and session/job correlation., test_event_creation_and_defaults(), test_event_linked_to_job() (+3 more)

### Community 51 - "SqliteStorage"
Cohesion: 0.12
Nodes (12): Path, Manages the SQLite database connection, initialization, and transactions., Closes the underlying database connection cleanly., SqliteStorage, fixture, Unit tests for SQLite persistence repositories and constraints., Fixture providing an in-memory SQLite storage., storage() (+4 more)

### Community 52 - "test_mcp_server.py"
Cohesion: 0.29
Nodes (11): Tests for FastMCP server implementation in Terminal Session Manager., Helper to run async coroutines in synchronous pytest tests., _run(), test_mcp_device_inactive_rejection(), test_mcp_devices_and_secret_protection(), test_mcp_error_handling_unknown_entities(), test_mcp_events_cursor_pagination(), test_mcp_job_cancel() (+3 more)

### Community 53 - "errors.py"
Cohesion: 0.15
Nodes (14): Domain exceptions for Terminal Session Manager., Device catalog interface definition., DeviceType, Enum, Device inventory model and connection metadata., Categorization of managed devices., Enum, Job domain model and lifecycle states. (+6 more)

### Community 54 - "TransportClosedError"
Cohesion: 0.12
Nodes (13): Queue, Raised when attempting I/O operations on an unopened transport., Raised when attempting to write to or interact with a closed or terminated…, TransportClosedError, TransportNotOpenError, _get_default_shell(), Local process terminal transport adapter., Returns platform-appropriate default interactive shell command. (+5 more)

### Community 55 - "CredentialRef"
Cohesion: 0.16
Nodes (8): Retrieves only non-sensitive metadata for a credential reference., Retrieves metadata from external provider, or None if not handled., CredentialRef, Safe reference metadata for credentials. NOTE: This model strictly avoids…, Retrieves only non-sensitive metadata for the given credential reference ID., InMemoryCredentialResolver, In-memory mock conforming to CredentialResolver protocol., test_credential_resolver_protocol()

### Community 56 - "MockTerminalTransport"
Cohesion: 0.20
Nodes (3): MockTerminalTransport, In-memory mock conforming to TerminalTransport protocol., test_terminal_transport_protocol()

### Community 57 - "Relatório — Etapa 9: Transferência SCP"
Cohesion: 0.20
Nodes (9): Biblioteca Escolhida, Decisões de Arquitetura, Entrada Recomendada para a Próxima Etapa, Entregue, Limitações Conhecidas, Relatório — Etapa 9: Transferência SCP, Resultado da Suíte Completa:, Status (+1 more)

### Community 58 - "Job"
Cohesion: 0.12
Nodes (10): Persists or updates a job., Retrieves a job by ID or returns None if not found., Lists all jobs associated with a given session ID., Job, Represents an execution unit within a persistent session., Retrieves current job status from persistent repository., Lists all jobs registered for a session., InMemoryJobRepository (+2 more)

### Community 59 - "TransportError"
Cohesion: 0.21
Nodes (10): PKey, Raised when a blocking transport operation exceeds the specified timeout., Base exception for transport and process communication failures., TransportError, TransportTimeoutError, Starts the underlying local process and reader thread., _load_private_key(), SSH terminal and command execution transport adapter. (+2 more)

### Community 61 - "test_scp_service.py"
Cohesion: 0.15
Nodes (11): Unit and integration tests for SCP file transfer service., test_scp_cancel_transfer(), test_scp_concurrency(), test_scp_download_invalid_destination_dir(), test_scp_download_success(), test_scp_inactive_device(), test_scp_non_existent_device(), test_scp_orphan_recovery() (+3 more)

### Community 62 - "._record_event"
Cohesion: 0.21
Nodes (6): Any, Creates and launches an asynchronous job in a background worker., Background worker thread executing the job process., Executes a job remotely over SSH, streaming events and capturing output., Reconciles interrupted jobs upon service restart. Scans repository for jobs in…, Atomically records a sequenced event associated with a session and job.

### Community 63 - "MockSSHClient"
Cohesion: 0.18
Nodes (4): test_scp_auth_failure_masks_secret(), MockSSHClient, Any, Mock Paramiko SSHClient.

### Community 65 - "Session"
Cohesion: 0.29
Nodes (5): Represents a persistent terminal session., Session, InMemorySessionRepository, In-memory implementation conforming to SessionRepository protocol., test_session_repository_protocol()

### Community 68 - "_register_ssh_device"
Cohesion: 0.20
Nodes (10): Verifies asynchronous job execution on a remote SSH host via nickname., Verifies that non-zero exit code transitions remote job to FAILED., Verifies cancelling a running SSH job terminates channel cleanly., Verifies that non-existent or deactivated SSH devices are rejected., Helper to register a remote SSH device with protected credentials., _register_ssh_device(), test_job_execution_on_ssh_device_by_nickname(), test_job_execution_ssh_cancellation() (+2 more)

### Community 69 - "DomainError"
Cohesion: 0.22
Nodes (7): DomainError, InvalidStateError, InvalidStateTransitionError, Exception, Raised when an unrecognized or malformed state is encountered., Raised when an illegal state transition is attempted., Base exception for all domain-level errors.

### Community 70 - "ValidationError"
Cohesion: 0.13
Nodes (15): Raised when entity validation fails., ValidationError, ConnectionMethod, str, Supported transport/connection mechanisms for devices., Any, Updates attributes of an existing device., Creates, persists, and returns a new Device. (+7 more)

### Community 71 - "doc_api_server"
Cohesion: 0.28
Nodes (8): doc_api_server(), fixture, Path, Tests for OpenAPI specification and Swagger UI documentation endpoints., Helper returning (status_code, content_type, body_text)., raw_http_get(), test_openapi_specification_endpoint(), test_swagger_ui_endpoint()

### Community 72 - "api_server"
Cohesion: 0.28
Nodes (8): api_server(), http_request(), fixture, Path, Tests for Sessions and Events HTTP API endpoints., Helper to perform HTTP JSON requests using standard library urllib., test_events_cursor_pagination_api(), test_session_lifecycle_and_io_api()

### Community 73 - "test_session.py"
Cohesion: 0.22
Nodes (8): parametrize, Unit tests for Session model and lifecycle transitions., test_invalid_transitions_rejected(), test_session_creation_defaults(), test_session_empty_id_raises(), test_session_invalid_status(), test_transition_idempotent_when_same_state(), test_valid_transitions()

### Community 74 - "api_server"
Cohesion: 0.32
Nodes (7): api_server(), http_request(), fixture, Path, Tests for Jobs HTTP API endpoints., test_job_cancellation_api(), test_job_submit_wait_and_query_api()

### Community 76 - ".cancel_job"
Cohesion: 0.29
Nodes (5): Popen, Terminates a subprocess safely, escalating to kill if necessary., Waits for a job to complete execution and returns the finished Job., Cancels a running or created job., _terminate_proc()

### Community 77 - "test_api_scp.py"
Cohesion: 0.53
Nodes (5): http_request(), Tests for SCP HTTP API and FastMCP tools., test_api_scp_download(), test_api_scp_upload(), test_api_scp_validations()

## Knowledge Gaps
- **172 isolated node(s):** `terminal-session-manager`, `graphify`, `1. Overview & Core Philosophy`, `Cursor / Antigravity (`.agents/mcp_config.json` or global config)`, `Claude Desktop (`claude_desktop_config.json`)` (+167 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 587 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DeviceService` connect `DeviceService` to `terminal_session_manager/__init__.py`, `JobService`, `SqliteEventRepository`, `scp_service.py`, `APIServer`, `SqliteDeviceRepository`, `credential_store.py`, `test_device_service.py`, `LocalSession`, `Device`, `JobNotFoundError`, `TSMApplication`, `DeviceRepository`, `mcp/server.py`, `ProtectedLocalCredentialStore`, `test_mcp_server.py`, `errors.py`, `CredentialRef`, `ValidationError`, `doc_api_server`, `api_server`, `api_server`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `Device` connect `Device` to `_register_ssh_device`, `ValidationError`, `DeviceService`, `mcp/server.py`, `SqliteEventRepository`, `CredentialType`, `SqliteDeviceRepository`, `handler.py`, `errors.py`, `TSMApplication`, `DeviceRepository`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `LocalSession` connect `LocalSession` to `terminal_session_manager/__init__.py`, `Session`, `DeviceService`, `ValidationError`, `ProtectedLocalCredentialStore`, `scp_service.py`, `CredentialType`, `Event`, `test_service_restart_recovers_session_and_events`, `TerminalTransport`, `EventType`, `LocalProcessTransport`, `TransportClosedError`, `SSHTransport`, `TransportError`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `DeviceService` (e.g. with `APIServer` and `TSMApplication`) actually correct?**
  _`DeviceService` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `ValidationError` (e.g. with `TSMRequestHandler` and `CredentialRef`) actually correct?**
  _`ValidationError` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `SqliteStorage` (e.g. with `TSMApplication` and `ProtectedLocalCredentialStore`) actually correct?**
  _`SqliteStorage` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `JobService` (e.g. with `APIServer` and `TSMApplication`) actually correct?**
  _`JobService` has 34 INFERRED edges - model-reasoned connections that need verification._