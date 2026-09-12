# Graph Report - TerminalPersistente  (2026-09-12)

## Corpus Check
- 79 files · ~53,194 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1188 nodes · 2857 edges · 64 communities (56 shown, 7 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 625 edges (avg confidence: 0.95)
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
- TransportClosedError
- TSMRequestHandler
- DeviceService
- SqliteEventRepository
- MockSSHClient
- Session
- APIServer
- 3. Tool Reference
- CredentialType
- SqliteDeviceRepository
- credential_store.py
- 3. Tool Reference
- test_service_restart_recovers_session_and_events
- TerminalTransport
- device_service.py
- LocalSession
- LocalProcessTransport
- .save_credential
- Exemplos Práticos via `curl`
- Device
- DeviceNotFoundError
- SSHTransport
- TSMApplication
- DeviceRepository
- ValidationError
- api/__init__.py
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
- storage
- test_api_scp.py
- .save
- handler.py
- CredentialResolutionError
- SCPService
- Event
- SqliteStorage
- test_mcp_server.py
- errors.py
- CredentialRef
- test_contracts.py
- Relatório — Etapa 9: Transferência SCP
- CredentialNotFoundError
- rules/graphify.md
- workflows/graphify.md
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

## Communities (64 total, 7 thin omitted)

### Community 0 - "terminal_session_manager/__init__.py"
Cohesion: 0.07
Nodes (53): MonkeyPatch, Path, Central application container managing TSM services, storage, and lifecycle., Applies restrictive file system permissions on POSIX systems., _restrict_permissions(), ConfigurationError, HistoryConfig, JobsConfig (+45 more)

### Community 1 - "JobService"
Cohesion: 0.05
Nodes (48): Popen, JobNotFoundError, Raised when a requested job is not found., JobStatus, Enum, str, Conceptual states of an asynchronous or synchronous job., JobService (+40 more)

### Community 2 - "Terminal Session Manager"
Cohesion: 0.04
Nodes (43): Estrutura do Projeto, Etapa 0 — Contrato e Esqueleto, Etapa 1 — Sessão Local Mínima, Etapa 2 — Persistência e Histórico, Etapa 3 — Jobs Assíncronos, Etapa 4 — Dispositivos e Credenciais, Etapa 5 — API HTTP, Etapa 6 — MCP com FastMCP (+35 more)

### Community 3 - "Job"
Cohesion: 0.09
Nodes (23): Job, Represents an execution unit within a persistent session., Indicates whether the job has reached a terminal state., Transitions job to a new state and updates timestamps., Persistent JobRepository implementation backed by SQLite., Persists or updates a job entity., Retrieves a job by ID., Lists all jobs associated with a given session. (+15 more)

### Community 4 - "TransportClosedError"
Cohesion: 0.17
Nodes (9): Raised when a requested session is not found., Raised when attempting to write to or interact with a closed or terminated…, SessionNotFoundError, TransportClosedError, Writes data into an active session channel., Reads decoded text from an active session channel with automatic masking., Terminates an active session and updates its final status., Retrieves session metadata, synchronizing status if currently active. (+1 more)

### Community 5 - "TSMRequestHandler"
Cohesion: 0.16
Nodes (13): BaseHTTPRequestHandler, Exception, Processes HTTP API requests with token authentication and domain error…, Verifies Bearer token or X-API-Key against server configured token., Serializes and sends JSON response body with appropriate headers., Sends standardized JSON error response without internal leakages., Reads and parses JSON request payload safely., Handles HTTP POST requests. (+5 more)

### Community 6 - "DeviceService"
Cohesion: 0.08
Nodes (32): Any, HTTP server management for Terminal Session Manager., SSH transport connection and host key verification settings., SSHConfig, EventRepository, Protocol, Persistence interfaces for sessions, jobs, and events., Contract for session persistence. (+24 more)

### Community 7 - "SqliteEventRepository"
Cohesion: 0.16
Nodes (11): Persistent EventRepository implementation with strict sequence uniqueness and…, Retrieves ordered event stream from a sequence cursor with optional limit., Returns the highest sequence number recorded for the session, or -1 if empty., SqliteEventRepository, test_session_device_injection_and_output_masking(), Unit tests for SQLite persistence repositories and constraints., test_repositories_conform_to_protocols(), test_sqlite_event_repository_ordering_and_cursor() (+3 more)

### Community 8 - "MockSSHClient"
Cohesion: 0.06
Nodes (12): test_scp_auth_failure_masks_secret(), Verifies that non-zero exit code transitions remote job to FAILED., Verifies cancelling a running SSH job terminates channel cleanly., Helper to register a remote SSH device with protected credentials., _register_ssh_device(), test_job_execution_ssh_cancellation(), test_job_execution_ssh_failure_non_zero_exit_code(), MockChannel (+4 more)

### Community 9 - "Session"
Cohesion: 0.10
Nodes (26): Enum, str, Session domain model and state definitions., Conceptual states of a session., Represents a persistent terminal session., Indicates whether the session is in an active/alive operational state., Indicates whether the session has reached a closed terminal state., Session (+18 more)

### Community 10 - "APIServer"
Cohesion: 0.05
Nodes (39): APIServer, Encapsulates the standard library ThreadingHTTPServer lifecycle for TSM., Returns the bound host address., Returns the actual bound TCP port number., Returns base HTTP URL (e.g. http://127.0.0.1:54321)., Starts serving requests synchronously (blocking)., Starts server in a background daemon thread for testing or concurrent execution., Stops server and releases socket cleanly. (+31 more)

### Community 11 - "3. Tool Reference"
Cohesion: 0.11
Nodes (17): 1. Overview & Core Philosophy, 2. Server Configuration, 3.1. Devices (Inventory & Remote SSH), 3.2. Sessions (Interactive Terminal PTY), 3.3. Jobs (Asynchronous Background Execution), 3.4. History & Events, 3.5. File Transfers (SCP), 3. Tool Reference (+9 more)

### Community 12 - "CredentialType"
Cohesion: 0.17
Nodes (12): CredentialType, Enum, str, Credential reference model ensuring secret isolation., Supported types of credentials., Unit tests for Device and CredentialRef models and security constraints., test_credential_ref_creation(), test_credential_ref_validation() (+4 more)

### Community 13 - "SqliteDeviceRepository"
Cohesion: 0.12
Nodes (11): Persistent DeviceRepository implementation backed by SQLite., Retrieves a device by ID., Retrieves a device by unique name., Lists all active and non-deleted registered devices., Logically deactivates a device by ID., Logically removes a device by ID., Lists all devices, optionally including logically deleted ones., SqliteDeviceRepository (+3 more)

### Community 14 - "credential_store.py"
Cohesion: 0.16
Nodes (13): CredentialResolver, ExternalCredentialProvider, Protocol, Credential abstraction and resolution interface., Internal contract to resolve secret references safely. This interface must only…, Resolves the raw secret string/bytes for a given credential reference ID., Contract for delegating credential resolution to an external provider., Resolves secret from external provider. Returns None if not handled. (+5 more)

### Community 15 - "3. Tool Reference"
Cohesion: 0.11
Nodes (17): 1. Overview & Core Philosophy, 2. Server Configuration, 3.1. Devices (Inventory & Remote SSH), 3.2. Sessions (Interactive Terminal PTY), 3.3. Jobs (Asynchronous Background Execution), 3.4. History & Events, 3.5. File Transfers (SCP), 3. Tool Reference (+9 more)

### Community 16 - "test_service_restart_recovers_session_and_events"
Cohesion: 0.47
Nodes (5): Path, Tests for persistence lifecycle: service restart, voluminous output, and secret…, test_sensitive_data_masking_in_history(), test_service_restart_recovers_session_and_events(), test_voluminous_output_cursor_pagination()

### Community 17 - "TerminalTransport"
Cohesion: 0.10
Nodes (13): Domain interfaces and contracts package., Protocol, Terminal and transport adapter interfaces., Contract for low-level terminal/transport implementations (PTY, SSH, Serial,…, Initializes and opens the underlying transport channel., Reads up to max_bytes from the transport., Writes raw byte data to the transport channel and returns bytes written., Resizes the terminal dimensions if supported by the transport. (+5 more)

### Community 18 - "device_service.py"
Cohesion: 0.20
Nodes (8): Device catalog interface definition., Device catalog and safe internal connection resolution service., Tests for DeviceRepository and DeviceService CRUD, state transitions, and…, test_device_crud_lifecycle(), test_device_deactivation_and_logical_removal(), test_device_not_found_errors(), test_duplicate_device_name_rejected(), test_sqlite_device_repository_conforms_to_protocol()

### Community 19 - "LocalSession"
Cohesion: 0.09
Nodes (17): Resolves full connection details internally using a name or device ID. Enforces…, Internal connection metadata container. NOTE: The resolved secret exists…, ResolvedConnection, LocalSession, Any, Returns the session identifier., Returns current session status synchronized with the transport., Opens the transport and transitions session to RUNNING state. If transport… (+9 more)

### Community 20 - "LocalProcessTransport"
Cohesion: 0.08
Nodes (24): Raised when attempting I/O operations on an unopened transport., TransportNotOpenError, _get_default_shell(), LocalProcessTransport, Local process terminal transport adapter., Reads up to max_bytes from the process output stream., Writes byte data to the process stdin channel., Records terminal dimensions. (+16 more)

### Community 21 - ".save_credential"
Cohesion: 0.24
Nodes (7): _crypt_keystream(), _derive_keys(), Decodes the secret in memory. Returns None if ref_id does not exist., Re-encrypts all stored credentials with a new master key in a single atomic…, Derives 32-byte encryption key and 32-byte MAC key using PBKDF2-HMAC-SHA256., Symmetric authenticated keystream XOR cipher (counter mode over HMAC-SHA256)., Encrypts the secret and persists non-sensitive metadata alongside ciphertext.

### Community 22 - "Exemplos Práticos via `curl`"
Cohesion: 0.06
Nodes (35): 1. Criar uma Nova Sessão, 1. Instalação e Requisitos, 2. Configuração Centralizada, 2. Escrever um Comando na Sessão, 3.1. Validar a Configuração, 3.2. Exibir Status, 3.3. Iniciar a API HTTP REST, 3.4. Iniciar o Servidor MCP (Model Context Protocol) (+27 more)

### Community 23 - "Device"
Cohesion: 0.08
Nodes (13): Device, Represents an addressable device in the inventory., Deactivates device logically without deleting historical references., Marks device as logically removed without deleting historical references., Deactivates a device logically., Logically marks a device as removed., Lists registered devices., Registers a new device or updates an existing one. (+5 more)

### Community 24 - "DeviceNotFoundError"
Cohesion: 0.10
Nodes (13): DeviceInactiveError, DeviceNotFoundError, DomainError, EntityNotFoundError, InvalidStateError, Exception, Raised when an unrecognized or malformed state is encountered., Base exception for entity lookup failures. (+5 more)

### Community 25 - "SSHTransport"
Cohesion: 0.05
Nodes (42): PKey, Queue, Raised when a blocking transport operation exceeds the specified timeout., Base exception for transport and process communication failures., TransportError, TransportTimeoutError, Transport adapters package., _load_private_key() (+34 more)

### Community 26 - "TSMApplication"
Cohesion: 0.19
Nodes (22): add_device_interactive(), clean_path_input(), delete_device_interactive(), edit_device_interactive(), generate_ssh_key_interactive(), list_devices_view(), main(), print_header() (+14 more)

### Community 27 - "DeviceRepository"
Cohesion: 0.11
Nodes (10): DeviceRepository, Protocol, Contract for device catalog storage and queries., Registers a new device or updates an existing one., Retrieves a device by unique ID., Retrieves a device by unique name., Lists all active registered devices., Logically deactivates a device by ID. (+2 more)

### Community 28 - "ValidationError"
Cohesion: 0.11
Nodes (16): Row, Raised when entity validation fails., ValidationError, Persistence package providing concrete repositories., _iso(), _parse_iso(), datetime, SQLite persistence implementation for sessions, jobs, and event history. (+8 more)

### Community 29 - "api/__init__.py"
Cohesion: 0.20
Nodes (3): Suppresses default stderr server logging for quiet test execution., Sends HTML response body with appropriate headers., HTTP API package exposing Terminal Session Manager services.

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
Cohesion: 0.27
Nodes (8): FastMCP, FastMCP integration package for Terminal Session Manager., create_mcp_server(), main(), Any, FastMCP server implementation exposing Terminal Session Manager tools., CLI entrypoint for running the FastMCP server via stdio transport., Creates a configured FastMCP server exposing TSM capabilities to agents.

### Community 40 - "ProtectedLocalCredentialStore"
Cohesion: 0.20
Nodes (12): ProtectedLocalCredentialStore, Deletes credential from the protected store., Local credential storage protecting secrets at rest using authenticated…, device_service_and_store(), fixture, Path, Tests for device resolution by nickname, error handling, session injection, and…, sqlite_storage() (+4 more)

### Community 41 - "Relatório — Etapa 1: Sessão Local Mínima"
Cohesion: 0.22
Nodes (8): Critérios Verificados, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 2 — Persistência e Histórico), Entregue, Relatório — Etapa 1: Sessão Local Mínima, Riscos e Decisões Pendentes, Status, Testes e Resultados

### Community 43 - "Relatório — Etapa 7: Configuração e Endurecimento"
Cohesion: 0.25
Nodes (7): Dependências, Mudanças, Recomendação de Manutenção, Relatório — Etapa 7: Configuração e Endurecimento, Riscos Remanescentes, Status, Testes e Resultados

### Community 44 - "storage"
Cohesion: 0.67
Nodes (3): fixture, Fixture providing an in-memory SQLite storage., storage()

### Community 45 - "test_api_scp.py"
Cohesion: 0.17
Nodes (11): http_request(), Path, Tests for SCP HTTP API and FastMCP tools., test_api_scp_download(), test_api_scp_upload(), test_api_scp_validations(), test_mcp_scp_tools_registered_and_callable(), MockSCPClient (+3 more)

### Community 47 - "handler.py"
Cohesion: 0.21
Nodes (15): device_to_dict(), event_to_dict(), _iso(), job_to_dict(), Any, datetime, HTTP request handler implementing REST API for sessions, jobs, events, and…, Handles HTTP GET requests. (+7 more)

### Community 48 - "CredentialResolutionError"
Cohesion: 0.20
Nodes (11): CredentialResolutionError, Raised when resolving a credential secret fails or integrity check fails., local_cred_store(), fixture, Path, Tests for protected credential persistence, encryption at rest, tampering…, sqlite_storage(), test_credential_store_conforms_to_protocol() (+3 more)

### Community 49 - "SCPService"
Cohesion: 0.14
Nodes (12): JobRepository, Contract for job persistence., Persists or updates a job., Retrieves a job by ID or returns None if not found., Lists all jobs associated with a given session ID., Any, Path, Submits an asynchronous SCP file transfer job. (+4 more)

### Community 50 - "Event"
Cohesion: 0.13
Nodes (18): Event, EventType, Enum, str, Event domain model with ordering and session/job linkage., Categorization of terminal and lifecycle events., Represents an observable, ordered event within a session or job stream., Enables natural sorting of events by sequence number and timestamp. (+10 more)

### Community 51 - "SqliteStorage"
Cohesion: 0.17
Nodes (6): Path, Manages the SQLite database connection, initialization, and transactions., Closes the underlying database connection cleanly., SqliteStorage, Path, sqlite_storage()

### Community 52 - "test_mcp_server.py"
Cohesion: 0.29
Nodes (11): Tests for FastMCP server implementation in Terminal Session Manager., Helper to run async coroutines in synchronous pytest tests., _run(), test_mcp_device_inactive_rejection(), test_mcp_devices_and_secret_protection(), test_mcp_error_handling_unknown_entities(), test_mcp_events_cursor_pagination(), test_mcp_job_cancel() (+3 more)

### Community 53 - "errors.py"
Cohesion: 0.13
Nodes (13): InvalidStateTransitionError, Domain exceptions for Terminal Session Manager., Raised when an illegal state transition is attempted., Job domain model and lifecycle states., Transitions session to a new status if the transition is valid., fixture, Integration tests for remote SSH Sessions and asynchronous Jobs via…, Verifies asynchronous job execution on a remote SSH host via nickname. (+5 more)

### Community 55 - "CredentialRef"
Cohesion: 0.19
Nodes (7): Retrieves only non-sensitive metadata for a credential reference., Retrieves metadata from external provider, or None if not handled., CredentialRef, Safe reference metadata for credentials. NOTE: This model strictly avoids…, InMemoryCredentialResolver, In-memory mock conforming to CredentialResolver protocol., test_credential_resolver_protocol()

### Community 56 - "test_contracts.py"
Cohesion: 0.18
Nodes (4): MockTerminalTransport, Unit tests for domain interfaces (Protocols) and mock in-memory implementations., In-memory mock conforming to TerminalTransport protocol., test_terminal_transport_protocol()

### Community 57 - "Relatório — Etapa 9: Transferência SCP"
Cohesion: 0.20
Nodes (9): Biblioteca Escolhida, Decisões de Arquitetura, Entrada Recomendada para a Próxima Etapa, Entregue, Limitações Conhecidas, Relatório — Etapa 9: Transferência SCP, Resultado da Suíte Completa:, Status (+1 more)

### Community 64 - "CredentialNotFoundError"
Cohesion: 0.29
Nodes (4): CredentialNotFoundError, Raised when a requested credential reference is not found., Rotates an existing credential secret with fresh cryptographic parameters., Retrieves metadata from external provider first, then local store.

### Community 70 - "ConnectionMethod"
Cohesion: 0.18
Nodes (13): ConnectionMethod, DeviceType, Enum, str, Device inventory model and connection metadata., Categorization of managed devices., Supported transport/connection mechanisms for devices., Any (+5 more)

### Community 71 - "api_server_with_creds"
Cohesion: 0.33
Nodes (6): api_server_with_creds(), http_request(), fixture, Path, Tests for Devices HTTP API endpoints and safe nickname resolution., test_device_crud_and_safe_resolution_api()

## Knowledge Gaps
- **171 isolated node(s):** `terminal-session-manager`, `graphify`, `1. Overview & Core Philosophy`, `Cursor / Antigravity (`.agents/mcp_config.json` or global config)`, `Claude Desktop (`claude_desktop_config.json`)` (+166 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 586 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DeviceService` connect `DeviceService` to `terminal_session_manager/__init__.py`, `JobService`, `SqliteEventRepository`, `APIServer`, `SqliteDeviceRepository`, `credential_store.py`, `device_service.py`, `LocalSession`, `Device`, `DeviceNotFoundError`, `TSMApplication`, `DeviceRepository`, `mcp/server.py`, `ProtectedLocalCredentialStore`, `test_api_scp.py`, `SCPService`, `test_mcp_server.py`, `errors.py`, `CredentialRef`, `CredentialNotFoundError`, `ConnectionMethod`, `api_server_with_creds`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `Device` connect `Device` to `JobService`, `ConnectionMethod`, `DeviceService`, `MockSSHClient`, `CredentialType`, `SqliteDeviceRepository`, `test_api_scp.py`, `handler.py`, `device_service.py`, `Event`, `TSMApplication`, `DeviceRepository`, `ValidationError`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `LocalSession` connect `LocalSession` to `terminal_session_manager/__init__.py`, `TransportClosedError`, `DeviceService`, `ConnectionMethod`, `SqliteEventRepository`, `Session`, `CredentialType`, `test_service_restart_recovers_session_and_events`, `TerminalTransport`, `Event`, `LocalProcessTransport`, `SSHTransport`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `DeviceService` (e.g. with `APIServer` and `TSMApplication`) actually correct?**
  _`DeviceService` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `ValidationError` (e.g. with `TSMRequestHandler` and `CredentialRef`) actually correct?**
  _`ValidationError` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `SqliteStorage` (e.g. with `TSMApplication` and `ProtectedLocalCredentialStore`) actually correct?**
  _`SqliteStorage` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `JobService` (e.g. with `APIServer` and `TSMApplication`) actually correct?**
  _`JobService` has 34 INFERRED edges - model-reasoned connections that need verification._