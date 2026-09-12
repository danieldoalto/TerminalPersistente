# Graph Report - TerminalPersistente  (2026-09-11)

## Corpus Check
- 75 files · ~46,108 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1110 nodes · 2577 edges · 61 communities (55 shown, 5 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 534 edges (avg confidence: 0.95)
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
- SessionNotFoundError
- handler.py
- SessionService
- SqliteStorage
- MockChannel
- Session
- APIServer
- Terminal Session Manager (TSM) — MCP Agent Skill
- CredentialType
- device_service.py
- CredentialResolver
- Terminal Session Manager (TSM) — MCP Agent Skill
- errors.py
- TerminalTransport
- DeviceService
- LocalSession
- LocalProcessTransport
- SqliteDeviceRepository
- Exemplos Práticos via `curl`
- Device
- test_api_devices.py
- SSHTransport
- TSMApplication
- DeviceRepository
- ValidationError
- TransportNotOpenError
- ._record_event
- Relatório — Etapa 0: Contrato e Esqueleto
- Relatório — Etapa 8: Transporte SSH
- job_service.py
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
- credential_store.py
- Event
- test_mcp_server.py
- test_ssh_session_and_jobs.py
- api_server
- CredentialRef
- test_contracts.py
- auth_api_server
- TransportError
- api_server
- doc_api_server
- api/server.py
- rules/graphify.md
- workflows/graphify.md
- ConnectionMethod
- terminal-session-manager

## God Nodes (most connected - your core abstractions)
1. `DeviceService` - 59 edges
2. `ValidationError` - 56 edges
3. `SqliteStorage` - 56 edges
4. `JobService` - 54 edges
5. `Session` - 50 edges
6. `Device` - 48 edges
7. `Job` - 46 edges
8. `LocalSession` - 46 edges
9. `ProtectedLocalCredentialStore` - 45 edges
10. `CredentialRef` - 41 edges

## Surprising Connections (you probably didn't know these)
- `test_device_deactivation()` --uses--> `Device`  [INFERRED]
  tests/test_device_and_credential.py → src/terminal_session_manager/models/device.py
- `list_devices_view()` --uses--> `Device`  [INFERRED]
  scripts/manage_devices.py → src/terminal_session_manager/models/device.py
- `add_device_interactive()` --uses--> `CredentialRef`  [INFERRED]
  scripts/manage_devices.py → src/terminal_session_manager/models/credential.py
- `add_device_interactive()` --uses--> `CredentialType`  [INFERRED]
  scripts/manage_devices.py → src/terminal_session_manager/models/credential.py
- `add_device_interactive()` --uses--> `ConnectionMethod`  [INFERRED]
  scripts/manage_devices.py → src/terminal_session_manager/models/device.py

## Import Cycles
- None detected.

## Communities (61 total, 5 thin omitted)

### Community 0 - "terminal_session_manager/__init__.py"
Cohesion: 0.08
Nodes (47): MonkeyPatch, Central application container managing TSM services, storage, and lifecycle., ConfigurationError, HistoryConfig, JobsConfig, load_config(), _parse_bool(), Any (+39 more)

### Community 1 - "JobService"
Cohesion: 0.21
Nodes (18): JobStatus, str, Conceptual states of an asynchronous or synchronous job., JobService, Manages asynchronous job execution, monitoring, waiting, and cancellation. Jobs…, fixture, Unit and integration tests for asynchronous JobService., service() (+10 more)

### Community 2 - "Terminal Session Manager"
Cohesion: 0.05
Nodes (42): Estrutura do Projeto, Etapa 0 — Contrato e Esqueleto, Etapa 1 — Sessão Local Mínima, Etapa 2 — Persistência e Histórico, Etapa 3 — Jobs Assíncronos, Etapa 4 — Dispositivos e Credenciais, Etapa 5 — API HTTP, Etapa 6 — MCP com FastMCP (+34 more)

### Community 3 - "Job"
Cohesion: 0.09
Nodes (23): InvalidStateTransitionError, Raised when an illegal state transition is attempted., Job, Enum, Job domain model and lifecycle states., Represents an execution unit within a persistent session., Indicates whether the job has reached a terminal state., Transitions job to a new state and updates timestamps. (+15 more)

### Community 4 - "SessionNotFoundError"
Cohesion: 0.09
Nodes (8): EntityNotFoundError, Base exception for entity lookup failures., Raised when a requested session is not found., SessionNotFoundError, Writes data into an active session channel., Reads decoded text from an active session channel with automatic masking., Terminates an active session and updates its final status., Retrieves session metadata, synchronizing status if currently active.

### Community 5 - "handler.py"
Cohesion: 0.09
Nodes (30): BaseHTTPRequestHandler, device_to_dict(), event_to_dict(), _iso(), job_to_dict(), Any, datetime, Exception (+22 more)

### Community 6 - "SessionService"
Cohesion: 0.12
Nodes (12): Any, SSH transport connection and host key verification settings., SSHConfig, EventRepository, Contract for event stream persistence and cursor-based retrieval., Appends a new event to the session/job stream., Retrieves an ordered stream of events for a session from a sequence cursor., Terminates all active sessions during shutdown. (+4 more)

### Community 7 - "SqliteStorage"
Cohesion: 0.05
Nodes (45): Connection, RLock, Path, Applies restrictive file system permissions on POSIX systems., _restrict_permissions(), Persistence package providing concrete repositories., Path, Manages the SQLite database connection, initialization, and transactions. (+37 more)

### Community 8 - "MockChannel"
Cohesion: 0.08
Nodes (5): MockChannel, MockSSHClient, Any, Mock Paramiko SSHClient., Simulates a Paramiko Channel with in-memory streams and exit status.

### Community 9 - "Session"
Cohesion: 0.05
Nodes (31): Domain interfaces and contracts package., JobRepository, Protocol, Persistence interfaces for sessions, jobs, and events., Contract for session persistence., Persists or updates a session., Retrieves a session by ID or returns None if not found., Lists all persisted sessions. (+23 more)

### Community 10 - "APIServer"
Cohesion: 0.13
Nodes (9): APIServer, Encapsulates the standard library ThreadingHTTPServer lifecycle for TSM., Returns the bound host address., Returns the actual bound TCP port number., Returns base HTTP URL (e.g. http://127.0.0.1:54321)., Starts serving requests synchronously (blocking)., Starts server in a background daemon thread for testing or concurrent execution., Stops server and releases socket cleanly. (+1 more)

### Community 11 - "Terminal Session Manager (TSM) — MCP Agent Skill"
Cohesion: 0.12
Nodes (15): 1. Overview & Core Philosophy, 2. Server Configuration, 3.1. Devices (Inventory & Remote SSH), 3.2. Sessions (Interactive Terminal PTY), 3.3. Jobs (Asynchronous Background Execution), 3.4. History & Events, 3. Tool Reference, 4. Standard Agent Interaction Patterns (+7 more)

### Community 12 - "CredentialType"
Cohesion: 0.17
Nodes (12): CredentialType, Enum, str, Credential reference model ensuring secret isolation., Supported types of credentials., Unit tests for Device and CredentialRef models and security constraints., test_credential_ref_creation(), test_credential_ref_validation() (+4 more)

### Community 13 - "device_service.py"
Cohesion: 0.15
Nodes (10): DeviceInactiveError, Raised when an operation targets a deactivated or removed device., Device catalog interface definition., Device catalog and safe internal connection resolution service., Resolves full connection details internally using a name or device ID. Enforces…, Internal connection metadata container. NOTE: The resolved secret exists…, ResolvedConnection, Session, job, device, and credential management services package. (+2 more)

### Community 14 - "CredentialResolver"
Cohesion: 0.18
Nodes (11): CredentialResolver, ExternalCredentialProvider, Protocol, Internal contract to resolve secret references safely. This interface must only…, Resolves the raw secret string/bytes for a given credential reference ID., Contract for delegating credential resolution to an external provider., Resolves secret from external provider. Returns None if not handled., DelegatingCredentialResolver (+3 more)

### Community 15 - "Terminal Session Manager (TSM) — MCP Agent Skill"
Cohesion: 0.12
Nodes (15): 1. Overview & Core Philosophy, 2. Server Configuration, 3.1. Devices (Inventory & Remote SSH), 3.2. Sessions (Interactive Terminal PTY), 3.3. Jobs (Asynchronous Background Execution), 3.4. History & Events, 3. Tool Reference, 4. Standard Agent Interaction Patterns (+7 more)

### Community 16 - "errors.py"
Cohesion: 0.23
Nodes (8): Domain exceptions for Terminal Session Manager., Raised when attempting to write to or interact with a closed or terminated…, TransportClosedError, Terminal and transport adapter interfaces., Enum, Session domain model and state definitions., Local session controller binding Session lifecycle to TerminalTransport and…, Session lifecycle and interactive I/O coordinator service.

### Community 17 - "TerminalTransport"
Cohesion: 0.11
Nodes (11): Protocol, Contract for low-level terminal/transport implementations (PTY, SSH, Serial,…, Initializes and opens the underlying transport channel., Reads up to max_bytes from the transport., Writes raw byte data to the transport channel and returns bytes written., Resizes the terminal dimensions if supported by the transport., Closes the transport channel cleanly., Checks if the underlying process/connection is currently active. (+3 more)

### Community 18 - "DeviceService"
Cohesion: 0.17
Nodes (14): DeviceService, Manages the device inventory and handles secure connection resolution., Retrieves a device by ID., device_repo(), device_service(), fixture, Path, Tests for DeviceRepository and DeviceService CRUD, state transitions, and… (+6 more)

### Community 19 - "LocalSession"
Cohesion: 0.09
Nodes (23): str, Conceptual states of a session., SessionStatus, LocalSession, Any, Returns the session identifier., Returns current session status synchronized with the transport., Opens the transport and transitions session to RUNNING state. If transport… (+15 more)

### Community 20 - "LocalProcessTransport"
Cohesion: 0.09
Nodes (23): Transport adapters package., _get_default_shell(), LocalProcessTransport, Local process terminal transport adapter., Records terminal dimensions., Terminates process cleanly and closes resources., Returns platform-appropriate default interactive shell command., TerminalTransport adapter backed by a local OS subprocess. Uses non-blocking… (+15 more)

### Community 21 - "SqliteDeviceRepository"
Cohesion: 0.13
Nodes (8): Persistent DeviceRepository implementation backed by SQLite., Retrieves a device by ID., Retrieves a device by unique name., Lists all active and non-deleted registered devices., Logically deactivates a device by ID., Logically removes a device by ID., Lists all devices, optionally including logically deleted ones., SqliteDeviceRepository

### Community 22 - "Exemplos Práticos via `curl`"
Cohesion: 0.06
Nodes (33): 1. Criar uma Nova Sessão, 1. Instalação e Requisitos, 2. Configuração Centralizada, 2. Escrever um Comando na Sessão, 3.1. Validar a Configuração, 3.2. Exibir Status, 3.3. Iniciar a API HTTP REST, 3.4. Iniciar o Servidor MCP (Model Context Protocol) (+25 more)

### Community 23 - "Device"
Cohesion: 0.11
Nodes (10): Device, Represents an addressable device in the inventory., Deactivates device logically without deleting historical references., Marks device as logically removed without deleting historical references., Lists registered devices., Registers a new device or updates an existing one., Retrieves a device by unique name/nickname., InMemoryDeviceRepository (+2 more)

### Community 24 - "test_api_devices.py"
Cohesion: 0.67
Nodes (3): http_request(), Tests for Devices HTTP API endpoints and safe nickname resolution., test_device_crud_and_safe_resolution_api()

### Community 25 - "SSHTransport"
Cohesion: 0.08
Nodes (26): Any, Returns remote exit code or None if channel is still active., Reads stdout and stderr streams from the SSH channel into queues., Resizes the remote terminal dimensions., TerminalTransport adapter backed by an SSH connection using Paramiko. Supports…, SSHTransport, SSHClient, Unit tests for SSHTransport using mocked Paramiko client and channel. (+18 more)

### Community 26 - "TSMApplication"
Cohesion: 0.18
Nodes (20): add_device_interactive(), clean_path_input(), delete_device_interactive(), generate_ssh_key_interactive(), list_devices_view(), main(), print_header(), Path (+12 more)

### Community 27 - "DeviceRepository"
Cohesion: 0.11
Nodes (10): DeviceRepository, Protocol, Contract for device catalog storage and queries., Registers a new device or updates an existing one., Retrieves a device by unique ID., Retrieves a device by unique name., Lists all active registered devices., Logically deactivates a device by ID. (+2 more)

### Community 28 - "ValidationError"
Cohesion: 0.09
Nodes (19): Row, Raised when entity validation fails., ValidationError, _iso(), _parse_iso(), datetime, SQLite persistence implementation for sessions, jobs, and event history., Persists or updates a session entity. (+11 more)

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

### Community 33 - "job_service.py"
Cohesion: 0.22
Nodes (8): Popen, JobNotFoundError, Raised when a requested job is not found., Asynchronous Job execution and lifecycle management service., Terminates a subprocess safely, escalating to kill if necessary., Waits for a job to complete execution and returns the finished Job., Cancels a running or created job., _terminate_proc()

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
Cohesion: 0.17
Nodes (11): FastMCP, DeviceNotFoundError, Raised when a requested device is not found., FastMCP integration package for Terminal Session Manager., create_mcp_server(), main(), FastMCP server implementation exposing Terminal Session Manager tools., CLI entrypoint for running the FastMCP server via stdio transport. (+3 more)

### Community 40 - "ProtectedLocalCredentialStore"
Cohesion: 0.14
Nodes (17): CredentialNotFoundError, Raised when a requested credential reference is not found., ProtectedLocalCredentialStore, Deletes credential from the protected store., Rotates an existing credential secret with fresh cryptographic parameters., Local credential storage protecting secrets at rest using authenticated…, Encrypts the secret and persists non-sensitive metadata alongside ciphertext., device_service_and_store() (+9 more)

### Community 41 - "Relatório — Etapa 1: Sessão Local Mínima"
Cohesion: 0.22
Nodes (8): Critérios Verificados, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 2 — Persistência e Histórico), Entregue, Relatório — Etapa 1: Sessão Local Mínima, Riscos e Decisões Pendentes, Status, Testes e Resultados

### Community 43 - "Relatório — Etapa 7: Configuração e Endurecimento"
Cohesion: 0.25
Nodes (7): Dependências, Mudanças, Recomendação de Manutenção, Relatório — Etapa 7: Configuração e Endurecimento, Riscos Remanescentes, Status, Testes e Resultados

### Community 48 - "credential_store.py"
Cohesion: 0.14
Nodes (15): CredentialResolutionError, Raised when resolving a credential secret fails or integrity check fails., Credential abstraction and resolution interface., _crypt_keystream(), _derive_keys(), Protected credential storage and resolution services ensuring secrets are never…, Decodes the secret in memory. Returns None if ref_id does not exist., Re-encrypts all stored credentials with a new master key in a single atomic… (+7 more)

### Community 50 - "Event"
Cohesion: 0.13
Nodes (18): Event, EventType, Enum, str, Event domain model with ordering and session/job linkage., Categorization of terminal and lifecycle events., Represents an observable, ordered event within a session or job stream., Enables natural sorting of events by sequence number and timestamp. (+10 more)

### Community 52 - "test_mcp_server.py"
Cohesion: 0.29
Nodes (11): Tests for FastMCP server implementation in Terminal Session Manager., Helper to run async coroutines in synchronous pytest tests., _run(), test_mcp_device_inactive_rejection(), test_mcp_devices_and_secret_protection(), test_mcp_error_handling_unknown_entities(), test_mcp_events_cursor_pagination(), test_mcp_job_cancel() (+3 more)

### Community 53 - "test_ssh_session_and_jobs.py"
Cohesion: 0.23
Nodes (11): Integration tests for remote SSH Sessions and asynchronous Jobs via…, Verifies asynchronous job execution on a remote SSH host via nickname., Verifies that non-zero exit code transitions remote job to FAILED., Verifies cancelling a running SSH job terminates channel cleanly., Helper to register a remote SSH device with protected credentials., Verifies creating an interactive session targeting an SSH device by nickname., _register_ssh_device(), test_job_execution_on_ssh_device_by_nickname() (+3 more)

### Community 54 - "api_server"
Cohesion: 0.28
Nodes (8): api_server(), http_request(), fixture, Path, Tests for Sessions and Events HTTP API endpoints., Helper to perform HTTP JSON requests using standard library urllib., test_events_cursor_pagination_api(), test_session_lifecycle_and_io_api()

### Community 55 - "CredentialRef"
Cohesion: 0.16
Nodes (8): Retrieves only non-sensitive metadata for a credential reference., Retrieves metadata from external provider, or None if not handled., CredentialRef, Safe reference metadata for credentials. NOTE: This model strictly avoids…, Retrieves metadata from external provider first, then local store., InMemoryCredentialResolver, In-memory mock conforming to CredentialResolver protocol., test_credential_resolver_protocol()

### Community 56 - "test_contracts.py"
Cohesion: 0.18
Nodes (4): MockTerminalTransport, Unit tests for domain interfaces (Protocols) and mock in-memory implementations., In-memory mock conforming to TerminalTransport protocol., test_terminal_transport_protocol()

### Community 57 - "auth_api_server"
Cohesion: 0.32
Nodes (7): auth_api_server(), http_request(), fixture, Path, Tests for HTTP API authentication and standardized error handling., test_api_authentication_enforcement(), test_api_standardized_error_handling()

### Community 58 - "TransportError"
Cohesion: 0.17
Nodes (11): PKey, Raised when a blocking transport operation exceeds the specified timeout., Base exception for transport and process communication failures., TransportError, TransportTimeoutError, Starts the underlying local process and reader thread., _load_private_key(), SSH terminal and command execution transport adapter. (+3 more)

### Community 59 - "api_server"
Cohesion: 0.32
Nodes (7): api_server(), http_request(), fixture, Path, Tests for Jobs HTTP API endpoints., test_job_cancellation_api(), test_job_submit_wait_and_query_api()

### Community 61 - "doc_api_server"
Cohesion: 0.28
Nodes (8): doc_api_server(), fixture, Path, Tests for OpenAPI specification and Swagger UI documentation endpoints., Helper returning (status_code, content_type, body_text)., raw_http_get(), test_openapi_specification_endpoint(), test_swagger_ui_endpoint()

### Community 70 - "ConnectionMethod"
Cohesion: 0.22
Nodes (10): ConnectionMethod, DeviceType, Enum, str, Device inventory model and connection metadata., Categorization of managed devices., Supported transport/connection mechanisms for devices., Any (+2 more)

## Knowledge Gaps
- **157 isolated node(s):** `terminal-session-manager`, `graphify`, `1. Overview & Core Philosophy`, `Cursor / Antigravity (`.agents/mcp_config.json` or global config)`, `Claude Desktop (`claude_desktop_config.json`)` (+152 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 553 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DeviceService` connect `DeviceService` to `terminal_session_manager/__init__.py`, `JobService`, `SessionService`, `SqliteStorage`, `APIServer`, `device_service.py`, `CredentialResolver`, `errors.py`, `LocalSession`, `Device`, `TSMApplication`, `DeviceRepository`, `job_service.py`, `mcp/server.py`, `ProtectedLocalCredentialStore`, `test_mcp_server.py`, `api_server`, `CredentialRef`, `auth_api_server`, `api_server`, `doc_api_server`, `api/server.py`, `ConnectionMethod`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `ValidationError` connect `ValidationError` to `terminal_session_manager/__init__.py`, `JobService`, `Job`, `handler.py`, `SqliteStorage`, `Session`, `CredentialType`, `device_service.py`, `errors.py`, `DeviceService`, `SqliteDeviceRepository`, `Device`, `._record_event`, `job_service.py`, `ProtectedLocalCredentialStore`, `credential_store.py`, `Event`, `CredentialRef`, `ConnectionMethod`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `JobService` connect `JobService` to `terminal_session_manager/__init__.py`, `Job`, `SessionService`, `SqliteStorage`, `Session`, `APIServer`, `CredentialType`, `device_service.py`, `DeviceService`, `SSHTransport`, `TSMApplication`, `ValidationError`, `._record_event`, `job_service.py`, `mcp/server.py`, `Event`, `api_server`, `auth_api_server`, `api_server`, `doc_api_server`, `api/server.py`, `ConnectionMethod`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `DeviceService` (e.g. with `APIServer` and `TSMApplication`) actually correct?**
  _`DeviceService` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `ValidationError` (e.g. with `TSMRequestHandler` and `CredentialRef`) actually correct?**
  _`ValidationError` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `SqliteStorage` (e.g. with `TSMApplication` and `ProtectedLocalCredentialStore`) actually correct?**
  _`SqliteStorage` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `JobService` (e.g. with `APIServer` and `TSMApplication`) actually correct?**
  _`JobService` has 31 INFERRED edges - model-reasoned connections that need verification._