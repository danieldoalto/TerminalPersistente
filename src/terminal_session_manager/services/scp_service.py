"""SCP file transfer service integrated with device inventory and job execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import io
import os
from pathlib import Path
import re
import socket
import threading
import time
from typing import Any, Callable, Sequence

import paramiko
import scp

from terminal_session_manager.config import SSHConfig
from terminal_session_manager.errors import (
    DeviceInactiveError,
    DeviceNotFoundError,
    JobNotFoundError,
    TransportError,
    TransportTimeoutError,
    ValidationError,
)
from terminal_session_manager.interfaces.persistence import (
    EventRepository,
    JobRepository,
    SessionRepository,
)
from terminal_session_manager.models.credential import CredentialType
from terminal_session_manager.models.device import ConnectionMethod
from terminal_session_manager.models.event import Event, EventType
from terminal_session_manager.models.job import Job, JobStatus
from terminal_session_manager.models.session import Session, SessionStatus
from terminal_session_manager.services.device_service import (
    DeviceService,
    ResolvedConnection,
)
from terminal_session_manager.transports.ssh import _load_private_key


class SCPTransferDirection(str, Enum):
    """Direction of an SCP transfer relative to the local TSM host."""

    UPLOAD = "upload"  # local_path -> remote_path
    DOWNLOAD = "download"  # remote_path -> local_path


class SCPService:
    """Manages secure, asynchronous SCP file transfers to/from remote SSH devices.

    Decoupled from interactive terminal transports, each transfer executes as an
    independent background Job, recording state changes, progress and audit events
    in SQLite, with strict credential isolation and host key verification.
    """

    def __init__(
        self,
        device_service: DeviceService,
        job_repo: JobRepository,
        event_repo: EventRepository,
        session_repo: SessionRepository | None = None,
        ssh_config: SSHConfig | None = None,
        client_factory: Any | None = None,
        scp_factory: Any | None = None,
    ) -> None:
        self.device_service = device_service
        self.job_repo = job_repo
        self.event_repo = event_repo
        self.session_repo = session_repo
        self.ssh_config = ssh_config
        self.client_factory = client_factory or paramiko.SSHClient
        self.scp_factory = scp_factory or scp.SCPClient

        self._active_clients: dict[str, paramiko.SSHClient] = {}
        self._active_scp_clients: dict[str, Any] = {}
        self._completion_events: dict[str, threading.Event] = {}
        self._cancel_flags: set[str] = set()
        self._lock = threading.Lock()

    def _record_event(
        self,
        session_id: str,
        job_id: str,
        event_type: EventType,
        payload: Any,
        is_masked: bool = False,
    ) -> None:
        """Atomically records a sequenced event in the audit trail."""
        with self._lock:
            if hasattr(self.event_repo, "get_latest_sequence"):
                seq = self.event_repo.get_latest_sequence(session_id) + 1
            else:
                seq = 0

            event = Event(
                sequence=seq,
                session_id=session_id,
                job_id=job_id,
                event_type=event_type,
                payload=payload,
                is_masked=is_masked,
            )
            self.event_repo.append(event)

    def _signal_completion(self, job_id: str) -> None:
        with self._lock:
            event = self._completion_events.get(job_id)
            if event:
                event.set()

    def submit_transfer(
        self,
        device_identifier: str,
        direction: SCPTransferDirection | str,
        local_path: str | Path,
        remote_path: str,
        session_id: str | None = None,
        timeout: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        """Submits an asynchronous SCP file transfer job."""
        if not device_identifier or not str(device_identifier).strip():
            raise ValidationError("device_identifier cannot be empty.")

        # Normalize direction
        if isinstance(direction, str):
            try:
                direction = SCPTransferDirection(direction.lower())
            except ValueError as err:
                raise ValidationError(f"Invalid transfer direction: '{direction}'. Must be 'upload' or 'download'.") from err

        # Validate paths
        if not remote_path or not str(remote_path).strip():
            raise ValidationError("remote_path cannot be empty.")

        local_path_obj = Path(local_path).expanduser().resolve()

        if direction == SCPTransferDirection.UPLOAD:
            if not local_path_obj.exists():
                raise ValidationError(f"Local file does not exist for upload: '{local_path_obj}'")
            if not local_path_obj.is_file():
                raise ValidationError(f"Local path is not a file: '{local_path_obj}'")
        elif direction == SCPTransferDirection.DOWNLOAD:
            dest_dir = local_path_obj.parent
            if not dest_dir.exists():
                raise ValidationError(f"Destination directory does not exist for download: '{dest_dir}'")

        # Resolve remote device and credential
        resolved_conn = self.device_service.resolve_connection(device_identifier)
        if resolved_conn.connection_method != ConnectionMethod.SSH:
            raise ValidationError(
                f"Device '{resolved_conn.device_name}' has connection method '{resolved_conn.connection_method.value}'. "
                "SCP file transfers require ConnectionMethod.SSH."
            )

        # Resolve or initialize session
        if not session_id:
            default_session_id = f"transfer-{resolved_conn.device_name}"
            if self.session_repo and self.session_repo.get_by_id(default_session_id) is None:
                sess = Session(
                    id=default_session_id,
                    name=f"scp-{resolved_conn.device_name}",
                    device_id=resolved_conn.device_id,
                    status=SessionStatus.RUNNING,
                )
                self.session_repo.save(sess)
            session_id = default_session_id
        elif self.session_repo:
            existing_session = self.session_repo.get_by_id(session_id)
            if existing_session is None:
                raise ValidationError(f"Specified session_id '{session_id}' not found.")

        cmd_repr = f"scp {direction.value} local='{local_path_obj.name}' remote='{remote_path}'"

        meta = {
            "type": "scp",
            "direction": direction.value,
            "device_name": resolved_conn.device_name,
            "local_path": str(local_path_obj),
            "remote_path": str(remote_path),
            "transferred_bytes": 0,
            **(metadata or {}),
        }

        job = Job(
            session_id=session_id,
            command=cmd_repr,
            device_id=resolved_conn.device_id,
            metadata=meta,
        )

        self.job_repo.save(job)
        self._record_event(
            session_id=session_id,
            job_id=job.id,
            event_type=EventType.STATE_CHANGE,
            payload={"status": JobStatus.CREATED.value, "command": cmd_repr, "metadata": meta},
        )

        completion_event = threading.Event()
        with self._lock:
            self._completion_events[job.id] = completion_event

        worker = threading.Thread(
            target=self._transfer_worker,
            args=(job, resolved_conn, direction, local_path_obj, str(remote_path), timeout),
            daemon=True,
            name=f"scp-worker-{job.id}",
        )
        worker.start()
        return job

    def cancel_transfer(self, job_id: str) -> Job:
        """Cancels an in-progress SCP transfer, closing its connection immediately."""
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundError(job_id)

        if job.is_finished():
            return job

        with self._lock:
            self._cancel_flags.add(job_id)
            scp_cli = self._active_scp_clients.get(job_id)
            client = self._active_clients.get(job_id)

        if scp_cli:
            try:
                scp_cli.close()
            except Exception:
                pass
        if client:
            try:
                client.close()
            except Exception:
                pass

        # Wait briefly for worker thread to persist CANCELLED status
        refreshed = self.wait_transfer(job_id, timeout=1.0)
        return refreshed

    def wait_transfer(self, job_id: str, timeout: float | None = None) -> Job:
        """Blocks until the transfer completes, times out, or is cancelled."""
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundError(job_id)

        with self._lock:
            event = self._completion_events.get(job_id)

        if event:
            event.wait(timeout=timeout)

        latest = self.job_repo.get_by_id(job_id)
        return latest if latest is not None else job

    def _transfer_worker(
        self,
        job: Job,
        conn: ResolvedConnection,
        direction: SCPTransferDirection,
        local_path: Path,
        remote_path: str,
        timeout: float | None,
    ) -> None:
        """Background thread worker executing the SCP file transfer."""
        # 1. Transition CREATED -> RUNNING
        job.transition_to(JobStatus.RUNNING)
        self.job_repo.save(job)
        self._record_event(
            session_id=job.session_id,
            job_id=job.id,
            event_type=EventType.STATE_CHANGE,
            payload={"status": JobStatus.RUNNING.value},
        )

        # 2. Extract and prepare credentials
        cred_type = conn.credential_ref.credential_type if conn.credential_ref else None
        password = None
        private_key = None
        secret = conn.secret
        if cred_type == CredentialType.PASSWORD:
            password = secret if isinstance(secret, str) else (secret.decode("utf-8", errors="ignore") if secret else None)
        elif cred_type == CredentialType.SSH_KEY:
            private_key = secret
        elif secret:
            sec_str = secret if isinstance(secret, str) else secret.decode("utf-8", errors="ignore")
            if "PRIVATE KEY" in sec_str:
                private_key = secret
            else:
                password = sec_str

        # 3. Connection & verification parameters
        known_hosts = self.ssh_config.known_hosts_path if self.ssh_config else None
        strict_checking = self.ssh_config.strict_host_key_checking if self.ssh_config else True
        conn_timeout = self.ssh_config.connect_timeout if self.ssh_config else 10.0

        opts = conn.options
        if "known_hosts_path" in opts:
            known_hosts = opts["known_hosts_path"]
        if "strict_host_key_checking" in opts:
            strict_checking = bool(opts["strict_host_key_checking"])
        if "connect_timeout" in opts:
            conn_timeout = float(opts["connect_timeout"])

        transfer_timeout = timeout if timeout is not None else conn_timeout

        # 4. Sensitive data token masking
        sensitive_tokens: list[str] = []
        if conn.secret:
            sec_val = conn.secret if isinstance(conn.secret, str) else conn.secret.decode("utf-8", errors="ignore")
            if sec_val:
                sensitive_tokens.append(sec_val)

        def mask(text: str) -> tuple[str, bool]:
            masked = text
            did_mask = False
            for tok in sensitive_tokens:
                if tok and tok in masked:
                    masked = masked.replace(tok, "[REDACTED]")
                    did_mask = True
            return masked, did_mask

        # Check early cancellation
        if job.id in self._cancel_flags:
            job.transition_to(JobStatus.CANCELLED, failure_reason="Transfer cancelled before connection.")
            job.exit_code = 130
            self.job_repo.save(job)
            self._signal_completion(job.id)
            return

        client = self.client_factory()
        with self._lock:
            self._active_clients[job.id] = client

        try:
            # 5. Host key verification policy
            if known_hosts and Path(known_hosts).is_file():
                client.load_host_keys(known_hosts)
            else:
                try:
                    client.load_system_host_keys()
                except Exception:
                    pass

            if strict_checking:
                client.set_missing_host_key_policy(paramiko.RejectPolicy())
            else:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # 6. Parse private key if provided
            pkey_obj = None
            if private_key is not None:
                pkey_obj = _load_private_key(private_key)

            # 7. Connect via SSH
            connect_kwargs: dict[str, Any] = {
                "hostname": conn.host,
                "port": conn.port,
                "username": conn.default_user,
                "timeout": conn_timeout,
                "banner_timeout": conn_timeout,
                "auth_timeout": conn_timeout,
                "allow_agent": False,
                "look_for_keys": False,
            }
            if password is not None:
                connect_kwargs["password"] = password
            if pkey_obj is not None:
                connect_kwargs["pkey"] = pkey_obj

            client.connect(**connect_kwargs)

            # Check cancellation after connect
            if job.id in self._cancel_flags:
                raise TransportError("Transfer cancelled by user.")

            # 8. Setup SCPClient with progress tracking
            transferred_bytes_holder = [0]
            total_bytes_holder = [local_path.stat().st_size if direction == SCPTransferDirection.UPLOAD and local_path.is_file() else 0]

            def on_progress(filename: Any, size: int, sent: int) -> None:
                transferred_bytes_holder[0] = sent
                if size > 0:
                    total_bytes_holder[0] = size

            transport = client.get_transport()
            if transport is None:
                raise TransportError("SSH transport could not be negotiated.")

            scp_cli = self.scp_factory(
                transport,
                socket_timeout=transfer_timeout,
                progress=on_progress,
                sanitize=lambda p: p,  # Paths are already validated
            )

            with self._lock:
                self._active_scp_clients[job.id] = scp_cli

            start_time = time.monotonic()

            # 9. Execute file transfer
            if direction == SCPTransferDirection.UPLOAD:
                scp_cli.put(str(local_path), remote_path=remote_path)
            else:
                scp_cli.get(remote_path, local_path=str(local_path))

            # Check if transfer was cancelled during put/get
            with self._lock:
                was_cancelled = job.id in self._cancel_flags

            if was_cancelled:
                raise TransportError("Transfer cancelled by user.")

            elapsed = time.monotonic() - start_time
            transferred = transferred_bytes_holder[0]
            if transferred == 0 and direction == SCPTransferDirection.UPLOAD and local_path.is_file():
                transferred = local_path.stat().st_size

            # 10. Mark success
            summary_msg = (
                f"Successfully {direction.value}ed '{local_path.name}' "
                f"({transferred} bytes in {elapsed:.2f}s) via SCP."
            )

            job.transition_to(JobStatus.COMPLETED)
            job.exit_code = 0
            job.stdout = summary_msg
            job.metadata["transferred_bytes"] = transferred
            job.metadata["elapsed_seconds"] = round(elapsed, 3)
            self.job_repo.save(job)

            self._record_event(
                session_id=job.session_id,
                job_id=job.id,
                event_type=EventType.STDOUT,
                payload=summary_msg,
            )
            self._record_event(
                session_id=job.session_id,
                job_id=job.id,
                event_type=EventType.STATE_CHANGE,
                payload={"status": JobStatus.COMPLETED.value, "exit_code": 0},
            )

        except (socket.timeout, TimeoutError) as err:
            with self._lock:
                was_cancelled = job.id in self._cancel_flags

            if was_cancelled:
                job.transition_to(JobStatus.CANCELLED, failure_reason="Transfer cancelled by user.")
                job.exit_code = 130
            else:
                job.transition_to(
                    JobStatus.TIMEOUT,
                    failure_reason=f"Transfer timed out after {transfer_timeout}s.",
                )
                job.exit_code = 124
            self.job_repo.save(job)
            self._record_event(
                session_id=job.session_id,
                job_id=job.id,
                event_type=EventType.STATE_CHANGE,
                payload={"status": job.status.value, "error": job.failure_reason},
            )

        except Exception as err:
            with self._lock:
                was_cancelled = job.id in self._cancel_flags

            if was_cancelled or "cancelled by user" in str(err).lower():
                job.transition_to(JobStatus.CANCELLED, failure_reason="Transfer cancelled by user.")
                job.exit_code = 130
                status_to_record = JobStatus.CANCELLED.value
            else:
                raw_err = str(err)
                masked_err, did_mask = mask(raw_err)
                job.transition_to(
                    JobStatus.FAILED,
                    failure_reason=f"SCP transfer failed: {masked_err}",
                )
                job.exit_code = 1
                job.stderr = masked_err
                status_to_record = JobStatus.FAILED.value
                job.stderr = masked_err
                status_to_record = JobStatus.FAILED.value

            self.job_repo.save(job)
            self._record_event(
                session_id=job.session_id,
                job_id=job.id,
                event_type=EventType.STATE_CHANGE,
                payload={"status": status_to_record, "error": job.failure_reason},
            )
            if job.stderr:
                self._record_event(
                    session_id=job.session_id,
                    job_id=job.id,
                    event_type=EventType.STDERR,
                    payload=job.stderr,
                    is_masked=True,
                )

        finally:
            with self._lock:
                scp_cli = self._active_scp_clients.pop(job.id, None)
                cli = self._active_clients.pop(job.id, None)
                self._cancel_flags.discard(job.id)

            if scp_cli:
                try:
                    scp_cli.close()
                except Exception:
                    pass
            if cli:
                try:
                    cli.close()
                except Exception:
                    pass

            self._signal_completion(job.id)
