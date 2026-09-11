"""Unit tests for domain interfaces (Protocols) and mock in-memory implementations."""

from typing import Any

from terminal_session_manager.interfaces.credentials import CredentialResolver
from terminal_session_manager.interfaces.device import DeviceRepository
from terminal_session_manager.interfaces.persistence import (
    EventRepository,
    JobRepository,
    SessionRepository,
)
from terminal_session_manager.interfaces.transport import TerminalTransport
from terminal_session_manager.models.credential import CredentialRef, CredentialType
from terminal_session_manager.models.device import Device
from terminal_session_manager.models.event import Event, EventType
from terminal_session_manager.models.job import Job
from terminal_session_manager.models.session import Session


class InMemorySessionRepository:
    """In-memory implementation conforming to SessionRepository protocol."""

    def __init__(self) -> None:
        self._storage: dict[str, Session] = {}

    def save(self, session: Session) -> None:
        self._storage[session.id] = session

    def get_by_id(self, session_id: str) -> Session | None:
        return self._storage.get(session_id)

    def list_all(self) -> list[Session]:
        return list(self._storage.values())


class InMemoryJobRepository:
    """In-memory implementation conforming to JobRepository protocol."""

    def __init__(self) -> None:
        self._storage: dict[str, Job] = {}

    def save(self, job: Job) -> None:
        self._storage[job.id] = job

    def get_by_id(self, job_id: str) -> Job | None:
        return self._storage.get(job_id)

    def list_by_session(self, session_id: str) -> list[Job]:
        return [job for job in self._storage.values() if job.session_id == session_id]


class InMemoryEventRepository:
    """In-memory implementation conforming to EventRepository protocol."""

    def __init__(self) -> None:
        self._events: list[Event] = []

    def append(self, event: Event) -> None:
        self._events.append(event)

    def get_events(
        self,
        session_id: str,
        since_sequence: int = 0,
        limit: int | None = None,
    ) -> list[Event]:
        matching = [
            e
            for e in sorted(self._events)
            if e.session_id == session_id and e.sequence >= since_sequence
        ]
        if limit is not None:
            return matching[:limit]
        return matching


class MockTerminalTransport:
    """In-memory mock conforming to TerminalTransport protocol."""

    def __init__(self) -> None:
        self._open = False
        self._buffer: list[bytes] = []

    def open(self) -> None:
        self._open = True

    def read(self, max_bytes: int = 4096, timeout: float | None = None) -> bytes:
        if not self._buffer:
            return b""
        data = self._buffer.pop(0)
        return data[:max_bytes]

    def write(self, data: bytes) -> int:
        self._buffer.append(data)
        return len(data)

    def resize(self, rows: int, cols: int) -> None:
        pass

    def close(self) -> None:
        self._open = False

    def is_alive(self) -> bool:
        return self._open


class InMemoryDeviceRepository:
    """In-memory implementation conforming to DeviceRepository protocol."""

    def __init__(self) -> None:
        self._devices: dict[str, Device] = {}

    def register(self, device: Device) -> None:
        self._devices[device.id] = device

    def get_by_id(self, device_id: str) -> Device | None:
        return self._devices.get(device_id)

    def get_by_name(self, name: str) -> Device | None:
        for d in self._devices.values():
            if d.name == name:
                return d
        return None

    def list_active(self) -> list[Device]:
        return [d for d in self._devices.values() if d.is_active]

    def deactivate(self, device_id: str) -> None:
        device = self._devices.get(device_id)
        if device is not None:
            device.deactivate()


class InMemoryCredentialResolver:
    """In-memory mock conforming to CredentialResolver protocol."""

    def __init__(self) -> None:
        self._refs: dict[str, CredentialRef] = {}
        self._secrets: dict[str, str | bytes] = {}

    def register_credential(
        self, ref: CredentialRef, secret: str | bytes
    ) -> None:
        self._refs[ref.id] = ref
        self._secrets[ref.id] = secret

    def resolve(self, ref_id: str) -> str | bytes | None:
        return self._secrets.get(ref_id)

    def get_ref(self, ref_id: str) -> CredentialRef | None:
        return self._refs.get(ref_id)


def test_session_repository_protocol() -> None:
    repo = InMemorySessionRepository()
    assert isinstance(repo, SessionRepository)

    session = Session(name="sess-test")
    repo.save(session)
    retrieved = repo.get_by_id(session.id)
    assert retrieved is not None
    assert retrieved.name == "sess-test"
    assert len(repo.list_all()) == 1


def test_job_repository_protocol() -> None:
    repo = InMemoryJobRepository()
    assert isinstance(repo, JobRepository)

    job1 = Job(session_id="s1", command="cmd1")
    job2 = Job(session_id="s1", command="cmd2")
    job3 = Job(session_id="s2", command="cmd3")

    repo.save(job1)
    repo.save(job2)
    repo.save(job3)

    assert repo.get_by_id(job1.id) == job1
    assert len(repo.list_by_session("s1")) == 2
    assert len(repo.list_by_session("s2")) == 1


def test_event_repository_protocol() -> None:
    repo = InMemoryEventRepository()
    assert isinstance(repo, EventRepository)

    e0 = Event(sequence=0, session_id="s1", event_type=EventType.SYSTEM, payload="start")
    e1 = Event(sequence=1, session_id="s1", event_type=EventType.STDOUT, payload="out")
    e2 = Event(sequence=2, session_id="s1", event_type=EventType.STATE_CHANGE, payload="end")

    repo.append(e2)
    repo.append(e0)
    repo.append(e1)

    events = repo.get_events(session_id="s1", since_sequence=1, limit=1)
    assert len(events) == 1
    assert events[0].sequence == 1


def test_terminal_transport_protocol() -> None:
    transport = MockTerminalTransport()
    assert isinstance(transport, TerminalTransport)

    assert transport.is_alive() is False
    transport.open()
    assert transport.is_alive() is True

    written = transport.write(b"ls\n")
    assert written == 3
    assert transport.read() == b"ls\n"

    transport.close()
    assert transport.is_alive() is False


def test_device_repository_protocol() -> None:
    repo = InMemoryDeviceRepository()
    assert isinstance(repo, DeviceRepository)

    device = Device(name="switch-01", host="10.1.1.1")
    repo.register(device)

    assert repo.get_by_name("switch-01") == device
    assert repo.get_by_id(device.id) == device
    assert len(repo.list_active()) == 1

    repo.deactivate(device.id)
    assert len(repo.list_active()) == 0


def test_credential_resolver_protocol() -> None:
    resolver = InMemoryCredentialResolver()
    assert isinstance(resolver, CredentialResolver)

    ref = CredentialRef(name="api-token", credential_type=CredentialType.TOKEN)
    resolver.register_credential(ref, secret="super-secret-token")

    assert resolver.get_ref(ref.id) == ref
    assert resolver.resolve(ref.id) == "super-secret-token"
