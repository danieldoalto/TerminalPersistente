"""SQLite persistence implementation for sessions, jobs, and event history."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import threading
from typing import Any

from terminal_session_manager.errors import ValidationError
from terminal_session_manager.models.device import ConnectionMethod, Device, DeviceType
from terminal_session_manager.models.event import Event, EventType
from terminal_session_manager.models.job import Job, JobStatus
from terminal_session_manager.models.session import Session, SessionStatus


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    device_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    closed_at TEXT,
    metadata TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    command TEXT NOT NULL,
    status TEXT NOT NULL,
    device_id TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    exit_code INTEGER,
    inputs TEXT NOT NULL,
    stdout TEXT NOT NULL,
    stderr TEXT NOT NULL,
    failure_reason TEXT,
    metadata TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    sequence INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    job_id TEXT,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    is_masked INTEGER NOT NULL DEFAULT 0,
    metadata TEXT NOT NULL,
    UNIQUE (session_id, sequence)
);

CREATE INDEX IF NOT EXISTS idx_events_session_seq
ON events (session_id, sequence ASC);

CREATE INDEX IF NOT EXISTS idx_jobs_session
ON jobs (session_id);

CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    host TEXT NOT NULL,
    port INTEGER NOT NULL,
    device_type TEXT NOT NULL,
    connection_method TEXT NOT NULL,
    default_user TEXT,
    options TEXT NOT NULL,
    credential_ref_id TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_devices_name
ON devices (name);

CREATE TABLE IF NOT EXISTS credential_secrets (
    ref_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    credential_type TEXT NOT NULL,
    description TEXT NOT NULL,
    ciphertext TEXT NOT NULL,
    salt TEXT NOT NULL,
    nonce TEXT NOT NULL,
    auth_tag TEXT NOT NULL,
    metadata TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""



def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class SqliteStorage:
    """Manages the SQLite database connection, initialization, and transactions."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()
        self._conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0,
        )
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self._lock, self._conn:
            self._conn.execute("PRAGMA foreign_keys = ON;")
            if self.db_path != ":memory:":
                self._conn.execute("PRAGMA journal_mode = WAL;")
            self._conn.executescript(SCHEMA_SQL)

    @property
    def lock(self) -> threading.RLock:
        """Returns the storage reentrant lock for synchronizing transactions."""
        return self._lock

    @property
    def connection(self) -> sqlite3.Connection:
        """Returns the underlying sqlite connection."""
        return self._conn

    def close(self) -> None:
        """Closes the underlying database connection cleanly."""
        self._conn.close()


class SqliteSessionRepository:
    """Persistent SessionRepository implementation backed by SQLite."""

    def __init__(self, storage: SqliteStorage) -> None:
        self.storage = storage

    def save(self, session: Session) -> None:
        """Persists or updates a session entity."""
        query = """
        INSERT INTO sessions (
            id, name, status, device_id, created_at, updated_at, closed_at, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            status = excluded.status,
            device_id = excluded.device_id,
            updated_at = excluded.updated_at,
            closed_at = excluded.closed_at,
            metadata = excluded.metadata;
        """
        try:
            with self.storage.lock, self.storage.connection:
                self.storage.connection.execute(
                    query,
                    (
                        session.id,
                        session.name,
                        session.status.value,
                        session.device_id,
                        _iso(session.created_at),
                        _iso(session.updated_at),
                        _iso(session.closed_at),
                        json.dumps(session.metadata),
                    ),
                )
        except sqlite3.Error as err:
            raise ValidationError(f"Failed to persist session {session.id}: {err}") from err

    def get_by_id(self, session_id: str) -> Session | None:
        """Retrieves a session by ID."""
        with self.storage.lock:
            cursor = self.storage.connection.execute(
                "SELECT * FROM sessions WHERE id = ?;", (session_id,)
            )
            row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_session(row)

    def list_all(self) -> list[Session]:
        """Lists all persisted sessions."""
        with self.storage.lock:
            cursor = self.storage.connection.execute(
                "SELECT * FROM sessions ORDER BY created_at DESC;"
            )
            rows = cursor.fetchall()
        return [self._row_to_session(r) for r in rows]

    def _row_to_session(self, row: sqlite3.Row) -> Session:
        try:
            created_at = _parse_iso(row["created_at"]) or datetime.now(timezone.utc)
            updated_at = _parse_iso(row["updated_at"]) or datetime.now(timezone.utc)
            closed_at = _parse_iso(row["closed_at"])
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}

            return Session(
                id=row["id"],
                name=row["name"],
                status=SessionStatus(row["status"]),
                device_id=row["device_id"],
                created_at=created_at,
                updated_at=updated_at,
                closed_at=closed_at,
                metadata=metadata,
            )
        except Exception as err:
            raise ValidationError(f"Corrupt session record in database: {err}") from err


class SqliteJobRepository:
    """Persistent JobRepository implementation backed by SQLite."""

    def __init__(self, storage: SqliteStorage) -> None:
        self.storage = storage

    def save(self, job: Job) -> None:
        """Persists or updates a job entity."""
        query = """
        INSERT INTO jobs (
            id, session_id, command, status, device_id, created_at,
            started_at, finished_at, exit_code, inputs, stdout, stderr,
            failure_reason, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            status = excluded.status,
            started_at = excluded.started_at,
            finished_at = excluded.finished_at,
            exit_code = excluded.exit_code,
            inputs = excluded.inputs,
            stdout = excluded.stdout,
            stderr = excluded.stderr,
            failure_reason = excluded.failure_reason,
            metadata = excluded.metadata;
        """
        try:
            with self.storage.lock, self.storage.connection:
                self.storage.connection.execute(
                    query,
                    (
                        job.id,
                        job.session_id,
                        job.command,
                        job.status.value,
                        job.device_id,
                        _iso(job.created_at),
                        _iso(job.started_at),
                        _iso(job.finished_at),
                        job.exit_code,
                        json.dumps(job.inputs),
                        job.stdout,
                        job.stderr,
                        job.failure_reason,
                        json.dumps(job.metadata),
                    ),
                )
        except sqlite3.Error as err:
            raise ValidationError(f"Failed to persist job {job.id}: {err}") from err

    def get_by_id(self, job_id: str) -> Job | None:
        """Retrieves a job by ID."""
        with self.storage.lock:
            cursor = self.storage.connection.execute(
                "SELECT * FROM jobs WHERE id = ?;", (job_id,)
            )
            row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_job(row)

    def list_by_session(self, session_id: str) -> list[Job]:
        """Lists all jobs associated with a given session."""
        with self.storage.lock:
            cursor = self.storage.connection.execute(
                "SELECT * FROM jobs WHERE session_id = ? ORDER BY created_at ASC;",
                (session_id,),
            )
            rows = cursor.fetchall()
        return [self._row_to_job(r) for r in rows]

    def list_all(self, status: JobStatus | None = None) -> list[Job]:
        """Lists all persisted jobs, optionally filtered by status."""
        with self.storage.lock:
            if status is not None:
                cursor = self.storage.connection.execute(
                    "SELECT * FROM jobs WHERE status = ? ORDER BY created_at ASC;",
                    (status.value,),
                )
            else:
                cursor = self.storage.connection.execute(
                    "SELECT * FROM jobs ORDER BY created_at ASC;"
                )
            rows = cursor.fetchall()
        return [self._row_to_job(r) for r in rows]

    def _row_to_job(self, row: sqlite3.Row) -> Job:
        try:
            created_at = _parse_iso(row["created_at"]) or datetime.now(timezone.utc)
            started_at = _parse_iso(row["started_at"])
            finished_at = _parse_iso(row["finished_at"])
            inputs = json.loads(row["inputs"]) if row["inputs"] else []
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}

            return Job(
                id=row["id"],
                session_id=row["session_id"],
                command=row["command"],
                status=JobStatus(row["status"]),
                device_id=row["device_id"],
                created_at=created_at,
                started_at=started_at,
                finished_at=finished_at,
                exit_code=row["exit_code"],
                inputs=inputs,
                stdout=row["stdout"],
                stderr=row["stderr"],
                failure_reason=row["failure_reason"],
                metadata=metadata,
            )
        except Exception as err:
            raise ValidationError(f"Corrupt job record in database: {err}") from err


class SqliteEventRepository:
    """Persistent EventRepository implementation with strict sequence uniqueness and cursor queries."""

    def __init__(self, storage: SqliteStorage) -> None:
        self.storage = storage

    def append(self, event: Event) -> None:
        """Appends an event ensuring strict sequence order and rejecting duplicates."""
        query = """
        INSERT INTO events (
            id, sequence, session_id, job_id, event_type, payload,
            timestamp, is_masked, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        payload_data = (
            json.dumps(event.payload)
            if isinstance(event.payload, (dict, list))
            else str(event.payload)
        )
        try:
            with self.storage.lock, self.storage.connection:
                self.storage.connection.execute(
                    query,
                    (
                        event.id,
                        event.sequence,
                        event.session_id,
                        event.job_id,
                        event.event_type.value,
                        payload_data,
                        _iso(event.timestamp),
                        1 if event.is_masked else 0,
                        json.dumps(event.metadata),
                    ),
                )
        except sqlite3.IntegrityError as err:
            raise ValidationError(
                f"Duplicate sequence {event.sequence} for session '{event.session_id}' or duplicate ID: {err}"
            ) from err
        except sqlite3.Error as err:
            raise ValidationError(f"Failed to append event {event.id}: {err}") from err

    def get_events(
        self,
        session_id: str,
        since_sequence: int = 0,
        limit: int | None = None,
    ) -> list[Event]:
        """Retrieves ordered event stream from a sequence cursor with optional limit."""
        if limit is not None:
            query = """
            SELECT * FROM events
            WHERE session_id = ? AND sequence >= ?
            ORDER BY sequence ASC
            LIMIT ?;
            """
            params: tuple[Any, ...] = (session_id, since_sequence, limit)
        else:
            query = """
            SELECT * FROM events
            WHERE session_id = ? AND sequence >= ?
            ORDER BY sequence ASC;
            """
            params = (session_id, since_sequence)

        with self.storage.lock:
            cursor = self.storage.connection.execute(query, params)
            rows = cursor.fetchall()
        return [self._row_to_event(r) for r in rows]

    def get_latest_sequence(self, session_id: str) -> int:
        """Returns the highest sequence number recorded for the session, or -1 if empty."""
        with self.storage.lock:
            cursor = self.storage.connection.execute(
                "SELECT MAX(sequence) as max_seq FROM events WHERE session_id = ?;",
                (session_id,),
            )
            row = cursor.fetchone()
        if row and row["max_seq"] is not None:
            return int(row["max_seq"])
        return -1

    def _row_to_event(self, row: sqlite3.Row) -> Event:
        try:
            timestamp = _parse_iso(row["timestamp"]) or datetime.now(timezone.utc)
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            raw_payload = row["payload"]
            try:
                payload = json.loads(raw_payload)
            except (json.JSONDecodeError, TypeError):
                payload = raw_payload

            return Event(
                id=row["id"],
                sequence=row["sequence"],
                session_id=row["session_id"],
                job_id=row["job_id"],
                event_type=EventType(row["event_type"]),
                payload=payload,
                timestamp=timestamp,
                is_masked=bool(row["is_masked"]),
                metadata=metadata,
            )
        except Exception as err:
            raise ValidationError(f"Corrupt event record in database: {err}") from err


class SqliteDeviceRepository:
    """Persistent DeviceRepository implementation backed by SQLite."""

    def __init__(self, storage: SqliteStorage) -> None:
        self.storage = storage

    def register(self, device: Device) -> None:
        """Persists or updates a device entity."""
        query = """
        INSERT INTO devices (
            id, name, host, port, device_type, connection_method,
            default_user, options, credential_ref_id, is_active,
            is_deleted, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            host = excluded.host,
            port = excluded.port,
            device_type = excluded.device_type,
            connection_method = excluded.connection_method,
            default_user = excluded.default_user,
            options = excluded.options,
            credential_ref_id = excluded.credential_ref_id,
            is_active = excluded.is_active,
            is_deleted = excluded.is_deleted,
            updated_at = excluded.updated_at;
        """
        try:
            with self.storage.lock, self.storage.connection:
                self.storage.connection.execute(
                    query,
                    (
                        device.id,
                        device.name,
                        device.host,
                        device.port,
                        device.device_type.value,
                        device.connection_method.value,
                        device.default_user,
                        json.dumps(device.options),
                        device.credential_ref_id,
                        1 if device.is_active else 0,
                        1 if device.is_deleted else 0,
                        _iso(device.created_at),
                        _iso(device.updated_at),
                    ),
                )
        except sqlite3.IntegrityError as err:
            raise ValidationError(
                f"Device with name '{device.name}' or ID '{device.id}' conflict: {err}"
            ) from err
        except sqlite3.Error as err:
            raise ValidationError(f"Failed to persist device {device.id}: {err}") from err

    def get_by_id(self, device_id: str) -> Device | None:
        """Retrieves a device by ID."""
        with self.storage.lock:
            cursor = self.storage.connection.execute(
                "SELECT * FROM devices WHERE id = ?;", (device_id,)
            )
            row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_device(row)

    def get_by_name(self, name: str) -> Device | None:
        """Retrieves a device by unique name."""
        with self.storage.lock:
            cursor = self.storage.connection.execute(
                "SELECT * FROM devices WHERE name = ?;", (name,)
            )
            row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_device(row)

    def list_active(self) -> list[Device]:
        """Lists all active and non-deleted registered devices."""
        with self.storage.lock:
            cursor = self.storage.connection.execute(
                "SELECT * FROM devices WHERE is_active = 1 AND is_deleted = 0 ORDER BY name ASC;"
            )
            rows = cursor.fetchall()
        return [self._row_to_device(r) for r in rows]

    def deactivate(self, device_id: str) -> None:
        """Logically deactivates a device by ID."""
        now_str = _iso(datetime.now(timezone.utc))
        with self.storage.lock, self.storage.connection:
            cursor = self.storage.connection.execute(
                "UPDATE devices SET is_active = 0, updated_at = ? WHERE id = ?;",
                (now_str, device_id),
            )
            if cursor.rowcount == 0:
                pass

    def remove(self, device_id: str) -> None:
        """Logically removes a device by ID."""
        now_str = _iso(datetime.now(timezone.utc))
        with self.storage.lock, self.storage.connection:
            self.storage.connection.execute(
                "UPDATE devices SET is_deleted = 1, is_active = 0, updated_at = ? WHERE id = ?;",
                (now_str, device_id),
            )

    def list_all(self, include_deleted: bool = False) -> list[Device]:
        """Lists all devices, optionally including logically deleted ones."""
        with self.storage.lock:
            if include_deleted:
                cursor = self.storage.connection.execute(
                    "SELECT * FROM devices ORDER BY name ASC;"
                )
            else:
                cursor = self.storage.connection.execute(
                    "SELECT * FROM devices WHERE is_deleted = 0 ORDER BY name ASC;"
                )
            rows = cursor.fetchall()
        return [self._row_to_device(r) for r in rows]

    def _row_to_device(self, row: sqlite3.Row) -> Device:
        try:
            created_at = _parse_iso(row["created_at"]) or datetime.now(timezone.utc)
            updated_at = _parse_iso(row["updated_at"]) or datetime.now(timezone.utc)
            options = json.loads(row["options"]) if row["options"] else {}

            return Device(
                id=row["id"],
                name=row["name"],
                host=row["host"],
                port=row["port"],
                device_type=DeviceType(row["device_type"]),
                connection_method=ConnectionMethod(row["connection_method"]),
                default_user=row["default_user"],
                options=options,
                credential_ref_id=row["credential_ref_id"],
                is_active=bool(row["is_active"]),
                is_deleted=bool(row["is_deleted"]),
                created_at=created_at,
                updated_at=updated_at,
            )
        except Exception as err:
            raise ValidationError(f"Corrupt device record in database: {err}") from err

