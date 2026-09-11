# Graph Report - TerminalPersistente  (2026-09-11)

## Corpus Check
- 35 files · ~13,046 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 470 nodes · 943 edges · 20 communities (18 shown, 2 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 179 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- terminal_session_manager/__init__.py
- test_contracts.py
- Session
- Job
- LocalSession
- Terminal Session Manager — Especificação do Projeto
- Device
- SqliteStorage
- TerminalTransport
- sqlite.py
- EventType
- Event
- Relatório — Etapa 0: Contrato e Esqueleto
- SqliteEventRepository
- Relatório — Etapa 2: Persistência e Histórico
- ValidationError
- Relatório — Etapa 1: Sessão Local Mínima
- FakeTransport
- main.py
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
- `test_invalid_transitions_rejected()` --uses--> `InvalidStateTransitionError`  [INFERRED]
  tests/test_session.py → src/terminal_session_manager/errors.py
- `test_credential_ref_validation()` --uses--> `ValidationError`  [INFERRED]
  tests/test_device_and_credential.py → src/terminal_session_manager/errors.py
- `test_device_validation_errors()` --uses--> `ValidationError`  [INFERRED]
  tests/test_device_and_credential.py → src/terminal_session_manager/errors.py
- `test_event_validation_errors()` --uses--> `ValidationError`  [INFERRED]
  tests/test_event.py → src/terminal_session_manager/errors.py

## Import Cycles
- None detected.

## Communities (20 total, 2 thin omitted)

### Community 0 - "terminal_session_manager/__init__.py"
Cohesion: 0.05
Nodes (47): Exception, CredentialNotFoundError, DeviceNotFoundError, DomainError, EntityNotFoundError, InvalidStateError, JobNotFoundError, Domain exceptions for Terminal Session Manager. (+39 more)

### Community 1 - "test_contracts.py"
Cohesion: 0.06
Nodes (35): CredentialResolver, Protocol, Credential abstraction and resolution interface., Internal contract to resolve secret references safely. This interface must only…, Resolves the raw secret string/bytes for a given credential reference ID., Retrieves only non-sensitive metadata for a credential reference., CredentialRef, CredentialType (+27 more)

### Community 2 - "Session"
Cohesion: 0.06
Nodes (31): Domain interfaces and contracts package., EventRepository, JobRepository, Protocol, Persistence interfaces for sessions, jobs, and events., Contract for session persistence., Persists or updates a session., Retrieves a session by ID or returns None if not found. (+23 more)

### Community 3 - "Job"
Cohesion: 0.08
Nodes (31): InvalidStateTransitionError, Raised when an illegal state transition is attempted., Retrieves a job by ID or returns None if not found., Lists all jobs associated with a given session ID., Job, JobStatus, Enum, str (+23 more)

### Community 4 - "LocalSession"
Cohesion: 0.08
Nodes (27): Any, Enum, str, Session domain model and state definitions., Conceptual states of a session., SessionStatus, Session management services package., LocalSession (+19 more)

### Community 5 - "Terminal Session Manager — Especificação do Projeto"
Cohesion: 0.06
Nodes (34): Estrutura do Projeto, Etapa 0 — Contrato e Esqueleto, Etapa 1 — Sessão Local Mínima, Etapa 2 — Persistência e Histórico, Execução, Instalação, Requisitos, Terminal Session Manager (+26 more)

### Community 6 - "Device"
Cohesion: 0.10
Nodes (15): DeviceRepository, Protocol, Device catalog interface definition., Contract for device catalog storage and queries., Registers a new device or updates an existing one., Retrieves a device by unique ID., Retrieves a device by unique name., Lists all active registered devices. (+7 more)

### Community 7 - "SqliteStorage"
Cohesion: 0.13
Nodes (13): Connection, fixture, Path, Returns the underlying sqlite connection., Closes the underlying database connection cleanly., Manages the SQLite database connection, initialization, and transactions., SqliteStorage, Unit tests for SQLite persistence repositories and constraints. (+5 more)

### Community 8 - "TerminalTransport"
Cohesion: 0.12
Nodes (10): Protocol, Terminal and transport adapter interfaces., Contract for low-level terminal/transport implementations (PTY, SSH, Serial,…, Initializes and opens the underlying transport channel., Reads up to max_bytes from the transport., Writes raw byte data to the transport channel and returns bytes written., Resizes the terminal dimensions if supported by the transport., Closes the transport channel cleanly. (+2 more)

### Community 9 - "sqlite.py"
Cohesion: 0.18
Nodes (8): Row, Persistence package providing concrete repositories., _parse_iso(), SQLite persistence implementation for sessions, jobs, and event history., Persistent SessionRepository implementation backed by SQLite., Retrieves a session by ID., Lists all persisted sessions., SqliteSessionRepository

### Community 10 - "EventType"
Cohesion: 0.23
Nodes (12): datetime, EventType, Enum, str, Event domain model with ordering and session/job linkage., Categorization of terminal and lifecycle events., Unit tests for Event model, ordering, and session/job correlation., test_event_creation_and_defaults() (+4 more)

### Community 11 - "Event"
Cohesion: 0.19
Nodes (7): Event, Represents an observable, ordered event within a session or job stream., Enables natural sorting of events by sequence number and timestamp., Retrieves ordered event stream from a sequence cursor with optional limit., InMemoryEventRepository, In-memory implementation conforming to EventRepository protocol., test_event_repository_protocol()

### Community 12 - "Relatório — Etapa 0: Contrato e Esqueleto"
Cohesion: 0.18
Nodes (10): Decisões Tomadas, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 1 — Sessão Local Mínima), Entregue, Estrutura do Projeto, Relatório — Etapa 0: Contrato e Esqueleto, Requisitos Atendidos, Riscos e Decisões Pendentes (+2 more)

### Community 13 - "SqliteEventRepository"
Cohesion: 0.25
Nodes (8): Persistent EventRepository implementation with strict sequence uniqueness and…, Returns the highest sequence number recorded for the session, or -1 if empty., SqliteEventRepository, Path, Tests for persistence lifecycle: service restart, voluminous output, and secret…, test_sensitive_data_masking_in_history(), test_service_restart_recovers_session_and_events(), test_voluminous_output_cursor_pagination()

### Community 14 - "Relatório — Etapa 2: Persistência e Histórico"
Cohesion: 0.20
Nodes (9): Critérios Verificados, Decisão de Armazenamento, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 3 — Jobs Assíncronos), Entregue, Relatório — Etapa 2: Persistência e Histórico, Riscos e Decisões Pendentes, Status (+1 more)

### Community 15 - "ValidationError"
Cohesion: 0.24
Nodes (6): Raised when entity validation fails., ValidationError, _iso(), Persists or updates a session entity., Persists or updates a job entity., Appends an event ensuring strict sequence order and rejecting duplicates.

### Community 16 - "Relatório — Etapa 1: Sessão Local Mínima"
Cohesion: 0.22
Nodes (8): Critérios Verificados, Desvios e Limitações, Entrada Recomendada para a Próxima Etapa (Etapa 2 — Persistência e Histórico), Entregue, Relatório — Etapa 1: Sessão Local Mínima, Riscos e Decisões Pendentes, Status, Testes e Resultados

### Community 18 - "main.py"
Cohesion: 0.50
Nodes (3): main(), Executable entry point for Terminal Session Manager., CLI entry point displaying version and skeleton status.

## Knowledge Gaps
- **55 isolated node(s):** `terminal-session-manager`, `Etapa 0 — Contrato e Esqueleto`, `Etapa 1 — Sessão Local Mínima`, `Etapa 2 — Persistência e Histórico`, `Requisitos` (+50 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 225 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ValidationError` connect `ValidationError` to `terminal_session_manager/__init__.py`, `test_contracts.py`, `Session`, `Job`, `LocalSession`, `Device`, `SqliteStorage`, `sqlite.py`, `EventType`, `Event`, `SqliteEventRepository`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Why does `LocalSession` connect `LocalSession` to `terminal_session_manager/__init__.py`, `Session`, `TerminalTransport`, `EventType`, `Event`, `SqliteEventRepository`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `Session` connect `Session` to `test_contracts.py`, `Job`, `LocalSession`, `SqliteStorage`, `sqlite.py`, `SqliteEventRepository`, `ValidationError`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `Session` (e.g. with `SessionRepository` and `InvalidStateTransitionError`) actually correct?**
  _`Session` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `ValidationError` (e.g. with `CredentialRef` and `Device`) actually correct?**
  _`ValidationError` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `LocalSession` (e.g. with `TransportClosedError` and `TransportError`) actually correct?**
  _`LocalSession` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `LocalProcessTransport` (e.g. with `LocalSession` and `TransportClosedError`) actually correct?**
  _`LocalProcessTransport` has 18 INFERRED edges - model-reasoned connections that need verification._