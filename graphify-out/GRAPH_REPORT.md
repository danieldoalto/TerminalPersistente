# Graph Report - TerminalPersistente  (2026-09-11)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 469 nodes · 943 edges · 22 communities (17 shown, 5 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 179 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Event
- terminal_session_manager/__init__.py
- Session
- CredentialRef
- ValidationError
- Terminal Session Manager — Especificação do Projeto
- Device
- LocalSession
- test_contracts.py
- persistence.py
- TerminalTransport
- Relatório — Etapa 0: Contrato e Esqueleto
- Relatório — Etapa 2: Persistência e Histórico
- Relatório — Etapa 1: Sessão Local Mínima
- FakeTransport
- test_local_session.py
- local_session.py
- main.py
- .id
- .resize
- .exit_code
- terminal-session-manager

## God Nodes (most connected - your core abstractions)
1. `Session` - 40 edges
2. `ValidationError` - 38 edges
3. `LocalSession` - 34 edges
4. `LocalProcessTransport` - 33 edges
5. `Job` - 32 edges
6. `Event` - 31 edges
7. `SessionStatus` - 26 edges
8. `EventType` - 24 edges
9. `Device` - 22 edges
10. `SqliteStorage` - 20 edges

## Surprising Connections (you probably didn't know these)
- `test_device_deactivation()` --uses--> `Device`  [INFERRED]
  tests/test_device_and_credential.py → src/terminal_session_manager/models/device.py
- `test_sqlite_job_repository_crud()` --uses--> `SqliteStorage`  [INFERRED]
  tests/test_sqlite_persistence.py → src/terminal_session_manager/persistence/sqlite.py
- `test_write_to_closed_session_raises()` --uses--> `TransportClosedError`  [INFERRED]
  tests/test_local_session.py → src/terminal_session_manager/errors.py
- `test_session_start_failure_transitions_to_failed()` --uses--> `TransportError`  [INFERRED]
  tests/test_local_session.py → src/terminal_session_manager/errors.py
- `test_interactive_session_write_and_read()` --uses--> `LocalProcessTransport`  [INFERRED]
  tests/test_local_session.py → src/terminal_session_manager/transports/local_process.py

## Import Cycles
- None detected.

## Communities (22 total, 5 thin omitted)

### Community 0 - "Event"
Cohesion: 0.05
Nodes (51): Connection, datetime, fixture, Row, Event, EventType, Enum, str (+43 more)

### Community 1 - "terminal_session_manager/__init__.py"
Cohesion: 0.05
Nodes (47): Exception, CredentialNotFoundError, DeviceNotFoundError, DomainError, EntityNotFoundError, InvalidStateError, JobNotFoundError, Domain exceptions for Terminal Session Manager. (+39 more)

### Community 2 - "Session"
Cohesion: 0.07
Nodes (27): InvalidStateTransitionError, Raised when an illegal state transition is attempted., Persists or updates a session., Retrieves a session by ID or returns None if not found., Domain models package for Terminal Session Manager., Enum, str, Session domain model and state definitions. (+19 more)

### Community 3 - "CredentialRef"
Cohesion: 0.08
Nodes (30): CredentialResolver, Protocol, Credential abstraction and resolution interface., Internal contract to resolve secret references safely. This interface must only…, Resolves the raw secret string/bytes for a given credential reference ID., Retrieves only non-sensitive metadata for a credential reference., CredentialRef, CredentialType (+22 more)

### Community 4 - "ValidationError"
Cohesion: 0.09
Nodes (29): Raised when entity validation fails., ValidationError, Persists or updates a job., Retrieves a job by ID or returns None if not found., Lists all jobs associated with a given session ID., Job, JobStatus, Enum (+21 more)

### Community 5 - "Terminal Session Manager — Especificação do Projeto"
Cohesion: 0.06
Nodes (34): Estrutura do Projeto, Etapa 0 — Contrato e Esqueleto, Etapa 1 — Sessão Local Mínima, Etapa 2 — Persistência e Histórico, Execução, Instalação, Requisitos, Terminal Session Manager (+26 more)

### Community 6 - "Device"
Cohesion: 0.10
Nodes (15): DeviceRepository, Protocol, Device catalog interface definition., Contract for device catalog storage and queries., Registers a new device or updates an existing one., Retrieves a device by unique ID., Retrieves a device by unique name., Lists all active registered devices. (+7 more)

### Community 7 - "LocalSession"
Cohesion: 0.18
Nodes (10): Any, LocalSession, Writes data to the session transport channel and records STDIN event., Reads raw bytes from the session transport channel and records STDOUT event., Convenience method to read decoded text from the session., Terminates transport cleanly and transitions session to CLOSED state., Inspects transport liveness and synchronizes session state., Orchestrates an interactive local terminal session. Connects the high-level… (+2 more)

### Community 8 - "test_contracts.py"
Cohesion: 0.12
Nodes (7): InMemoryJobRepository, MockTerminalTransport, Unit tests for domain interfaces (Protocols) and mock in-memory implementations., In-memory implementation conforming to JobRepository protocol., In-memory mock conforming to TerminalTransport protocol., test_job_repository_protocol(), test_terminal_transport_protocol()

### Community 9 - "persistence.py"
Cohesion: 0.17
Nodes (11): Domain interfaces and contracts package., EventRepository, JobRepository, Protocol, Persistence interfaces for sessions, jobs, and events., Contract for session persistence., Contract for job persistence., Contract for event stream persistence and cursor-based retrieval. (+3 more)

### Community 10 - "TerminalTransport"
Cohesion: 0.13
Nodes (9): Protocol, Contract for low-level terminal/transport implementations (PTY, SSH, Serial,…, Initializes and opens the underlying transport channel., Reads up to max_bytes from the transport., Writes raw byte data to the transport channel and returns bytes written., Resizes the terminal dimensions if supported by the transport., Closes the transport channel cleanly., Checks if the underlying process/connection is currently active. (+1 more)

### Community 11 - "Relatório — Etapa 0: Contrato e Esqueleto"
Cohesion: 0.18
Nodes (10): Decisões Tomadas, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 1 — Sessão Local Mínima), Entregue, Estrutura do Projeto, Relatório — Etapa 0: Contrato e Esqueleto, Requisitos Atendidos, Riscos e Decisões Pendentes (+2 more)

### Community 12 - "Relatório — Etapa 2: Persistência e Histórico"
Cohesion: 0.20
Nodes (9): Critérios Verificados, Decisão de Armazenamento, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 3 — Jobs Assíncronos), Entregue, Relatório — Etapa 2: Persistência e Histórico, Riscos e Decisões Pendentes, Status (+1 more)

### Community 13 - "Relatório — Etapa 1: Sessão Local Mínima"
Cohesion: 0.22
Nodes (8): Critérios Verificados, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 2 — Persistência e Histórico), Entregue, Relatório — Etapa 1: Sessão Local Mínima, Riscos e Decisões Pendentes, Status, Testes e Resultados

### Community 15 - "test_local_session.py"
Cohesion: 0.25
Nodes (7): Tests for LocalSession controller and lifecycle integration., test_interactive_session_write_and_read(), test_pluggable_transport_with_local_session(), test_session_failure_on_non_zero_exit(), test_session_start_failure_transitions_to_failed(), test_session_successful_lifecycle(), test_write_to_closed_session_raises()

### Community 16 - "local_session.py"
Cohesion: 0.33
Nodes (3): Terminal and transport adapter interfaces., Session management services package., Local session controller binding Session lifecycle to TerminalTransport and…

### Community 17 - "main.py"
Cohesion: 0.50
Nodes (3): main(), Executable entry point for Terminal Session Manager., CLI entry point displaying version and skeleton status.

## Knowledge Gaps
- **55 isolated node(s):** `Decisões Tomadas`, `Desvios e Limitações`, `Entrada Recomendada para a Próxima Etapa (Etapa 1 — Sessão Local Mínima)`, `Entregue`, `Estrutura do Projeto` (+50 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 223 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ValidationError` connect `ValidationError` to `Event`, `terminal_session_manager/__init__.py`, `Session`, `CredentialRef`, `Device`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Why does `LocalSession` connect `LocalSession` to `Event`, `terminal_session_manager/__init__.py`, `Session`, `persistence.py`, `TerminalTransport`, `test_local_session.py`, `local_session.py`, `.id`, `.resize`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `Session` connect `Session` to `Event`, `ValidationError`, `LocalSession`, `persistence.py`, `test_local_session.py`, `local_session.py`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `Session` (e.g. with `SessionRepository` and `InvalidStateTransitionError`) actually correct?**
  _`Session` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `ValidationError` (e.g. with `CredentialRef` and `Device`) actually correct?**
  _`ValidationError` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `LocalSession` (e.g. with `TransportClosedError` and `TransportError`) actually correct?**
  _`LocalSession` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `LocalProcessTransport` (e.g. with `LocalSession` and `TransportClosedError`) actually correct?**
  _`LocalProcessTransport` has 18 INFERRED edges - model-reasoned connections that need verification._