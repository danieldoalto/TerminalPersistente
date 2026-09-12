"""Asynchronous Job execution and lifecycle management service."""

from __future__ import annotations

from datetime import datetime, timezone
import subprocess
import sys
import threading
import time
from typing import Any, Sequence

from terminal_session_manager.config import SSHConfig
from terminal_session_manager.errors import JobNotFoundError, ValidationError
from terminal_session_manager.interfaces.persistence import (
    EventRepository,
    JobRepository,
    SessionRepository,
)
from terminal_session_manager.models.credential import CredentialType
from terminal_session_manager.models.device import ConnectionMethod
from terminal_session_manager.models.event import Event, EventType
from terminal_session_manager.models.job import Job, JobStatus
from terminal_session_manager.services.device_service import (
    DeviceService,
    ResolvedConnection,
)
from terminal_session_manager.transports.ssh import SSHTransport


def _terminate_proc(proc: subprocess.Popen[bytes]) -> None:
    """Terminates a subprocess safely, escalating to kill if necessary."""
    try:
        proc.terminate()
        proc.wait(timeout=1.0)
    except (subprocess.TimeoutExpired, OSError):
        try:
            proc.kill()
            proc.wait(timeout=1.0)
        except OSError:
            pass


class JobService:
    """Manages asynchronous job execution, monitoring, waiting, and cancellation.

    Jobs run in background threads decoupled from the client's connection.
    State, inputs, stdout, stderr, errors, and terminal status are persisted
    continuously to SQLite.
    """

    def __init__(
        self,
        job_repo: JobRepository,
        event_repo: EventRepository,
        session_repo: SessionRepository | None = None,
        device_service: DeviceService | None = None,
        ssh_config: SSHConfig | None = None,
        scp_service: Any | None = None,
    ) -> None:
        self.job_repo = job_repo
        self.event_repo = event_repo
        self.session_repo = session_repo
        self.device_service = device_service
        self.ssh_config = ssh_config
        self.scp_service = scp_service

        self._active_processes: dict[str, subprocess.Popen[bytes]] = {}
        self._active_transports: dict[str, SSHTransport] = {}
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
        """Atomically records a sequenced event associated with a session and job."""
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

    def submit_job(
        self,
        session_id: str,
        command: Sequence[str] | str,
        inputs: list[str] | None = None,
        timeout: float | None = None,
        device_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        """Creates and launches an asynchronous job in a background worker."""
        if not session_id:
            raise ValidationError("session_id cannot be empty.")
        if not command:
            raise ValidationError("command cannot be empty.")

        # If device_id not specified, inherit from session if available
        if device_id is None and self.session_repo:
            sess = self.session_repo.get_by_id(session_id)
            if sess and sess.device_id:
                device_id = sess.device_id

        cmd_str = command if isinstance(command, str) else " ".join(command)
        job = Job(
            session_id=session_id,
            command=cmd_str,
            device_id=device_id,
            inputs=inputs or [],
            metadata=metadata or {},
        )

        self.job_repo.save(job)
        self._record_event(
            session_id=session_id,
            job_id=job.id,
            event_type=EventType.STATE_CHANGE,
            payload={"status": JobStatus.CREATED.value, "command": cmd_str},
        )

        completion_event = threading.Event()
        with self._lock:
            self._completion_events[job.id] = completion_event

        worker = threading.Thread(
            target=self._job_worker,
            args=(job, command, inputs, timeout),
            daemon=True,
            name=f"job-worker-{job.id}",
        )
        worker.start()
        return job

    def _job_worker(
        self,
        job: Job,
        command: Sequence[str] | str,
        inputs: list[str] | None,
        timeout: float | None,
    ) -> None:
        """Background worker thread executing the job process."""
        # 1. Transition CREATED -> RUNNING
        job.transition_to(JobStatus.RUNNING)
        self.job_repo.save(job)
        self._record_event(
            session_id=job.session_id,
            job_id=job.id,
            event_type=EventType.STATE_CHANGE,
            payload={"status": JobStatus.RUNNING.value},
        )

        # Check if execution should be routed to an SSH remote device
        resolved_conn: ResolvedConnection | None = None
        if job.device_id and self.device_service:
            try:
                resolved_conn = self.device_service.resolve_connection(job.device_id)
            except Exception as err:
                job.transition_to(
                    JobStatus.FAILED,
                    failure_reason=f"Failed to resolve device for job: {err}",
                )
                self.job_repo.save(job)
                self._record_event(
                    session_id=job.session_id,
                    job_id=job.id,
                    event_type=EventType.STATE_CHANGE,
                    payload={"status": JobStatus.FAILED.value, "error": str(err)},
                )
                self._signal_completion(job.id)
                return

        if resolved_conn and resolved_conn.connection_method == ConnectionMethod.SSH:
            self._ssh_job_worker(job, command, inputs, timeout, resolved_conn)
            return

        # 2. Spawn local process
        try:
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=isinstance(command, str),
                bufsize=0,
            )
        except Exception as err:
            job.transition_to(
                JobStatus.FAILED,
                failure_reason=f"Failed to spawn process: {err}",
            )
            self.job_repo.save(job)
            self._record_event(
                session_id=job.session_id,
                job_id=job.id,
                event_type=EventType.STATE_CHANGE,
                payload={"status": JobStatus.FAILED.value, "error": str(err)},
            )
            self._signal_completion(job.id)
            return

        with self._lock:
            self._active_processes[job.id] = proc

        # 3. Handle initial inputs
        if inputs and proc.stdin:
            try:
                for item in inputs:
                    line = item if item.endswith("\n") else f"{item}\n"
                    proc.stdin.write(line.encode("utf-8"))
                    self._record_event(
                        session_id=job.session_id,
                        job_id=job.id,
                        event_type=EventType.STDIN,
                        payload=item,
                    )
                proc.stdin.flush()
                proc.stdin.close()
            except OSError:
                pass

        # 4. Stream readers for stdout and stderr
        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []

        def read_stream(stream, chunks: list[str], event_type: EventType) -> None:
            try:
                for line_bytes in iter(stream.readline, b""):
                    text = line_bytes.decode("utf-8", errors="replace")
                    chunks.append(text)
                    self._record_event(
                        session_id=job.session_id,
                        job_id=job.id,
                        event_type=event_type,
                        payload=text,
                    )
                stream.close()
            except Exception:
                pass

        stdout_thread = threading.Thread(
            target=read_stream,
            args=(proc.stdout, stdout_chunks, EventType.STDOUT),
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=read_stream,
            args=(proc.stderr, stderr_chunks, EventType.STDERR),
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()

        # 5. Monitor execution, cancellation and timeout
        start_time = time.monotonic()
        timed_out = False
        cancelled = False

        while proc.poll() is None:
            with self._lock:
                if job.id in self._cancel_flags:
                    cancelled = True
                    break

            if timeout is not None and (time.monotonic() - start_time) >= timeout:
                timed_out = True
                break

            time.sleep(0.05)

        with self._lock:
            if job.id in self._cancel_flags:
                cancelled = True

        # 6. Finalize process state
        if cancelled:
            _terminate_proc(proc)
            job.transition_to(JobStatus.CANCELLED, failure_reason="Cancelled by user")
        elif timed_out:
            _terminate_proc(proc)
            job.transition_to(
                JobStatus.TIMEOUT,
                failure_reason=f"Execution timed out after {timeout}s",
            )
        else:
            try:
                proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                _terminate_proc(proc)

            exit_code = proc.returncode
            if exit_code == 0:
                job.transition_to(JobStatus.COMPLETED, exit_code=0)
            else:
                job.transition_to(
                    JobStatus.FAILED,
                    exit_code=exit_code,
                    failure_reason=f"Process exited with code {exit_code}",
                )

        stdout_thread.join(timeout=0.5)
        stderr_thread.join(timeout=0.5)

        job.stdout = "".join(stdout_chunks)
        job.stderr = "".join(stderr_chunks)

        try:
            self.job_repo.save(job)
            self._record_event(
                session_id=job.session_id,
                job_id=job.id,
                event_type=EventType.STATE_CHANGE,
                payload={
                    "status": job.status.value,
                    "exit_code": job.exit_code,
                    "failure_reason": job.failure_reason,
                },
            )
        except Exception:
            pass

        with self._lock:
            self._active_processes.pop(job.id, None)
            self._cancel_flags.discard(job.id)

        self._signal_completion(job.id)

    def _ssh_job_worker(
        self,
        job: Job,
        command: Sequence[str] | str,
        inputs: list[str] | None,
        timeout: float | None,
        conn: ResolvedConnection,
    ) -> None:
        """Executes a job remotely over SSH, streaming events and capturing output."""
        # 1. Prepare credentials and transport
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

        transport = SSHTransport(
            host=conn.host,
            port=conn.port,
            username=conn.default_user,
            password=password,
            private_key=private_key,
            known_hosts_path=known_hosts,
            strict_host_key_checking=strict_checking,
            connect_timeout=conn_timeout,
            command=command,
            options=opts,
        )

        try:
            transport.open()
        except Exception as err:
            job.transition_to(
                JobStatus.FAILED,
                failure_reason=f"Failed to establish SSH connection: {err}",
            )
            self.job_repo.save(job)
            self._record_event(
                session_id=job.session_id,
                job_id=job.id,
                event_type=EventType.STATE_CHANGE,
                payload={"status": JobStatus.FAILED.value, "error": str(err)},
            )
            self._signal_completion(job.id)
            return

        with self._lock:
            self._active_transports[job.id] = transport

        # 2. Handle initial inputs
        if inputs:
            try:
                for item in inputs:
                    line = item if item.endswith("\n") else f"{item}\n"
                    transport.write(line.encode("utf-8"))
                    masked_input, was_masked = mask(item)
                    self._record_event(
                        session_id=job.session_id,
                        job_id=job.id,
                        event_type=EventType.STDIN,
                        payload=masked_input,
                        is_masked=was_masked,
                    )
            except Exception:
                pass

        # 3. Stream readers for stdout and stderr
        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []
        start_time = time.monotonic()
        timed_out = False
        cancelled = False

        while transport.is_alive():
            with self._lock:
                if job.id in self._cancel_flags:
                    cancelled = True
                    break

            if timeout is not None and (time.monotonic() - start_time) >= timeout:
                timed_out = True
                break

            out_chunk = transport.read(4096, timeout=0.05)
            if out_chunk:
                raw_text = out_chunk.decode("utf-8", errors="replace")
                masked_text, was_masked = mask(raw_text)
                stdout_chunks.append(masked_text)
                self._record_event(
                    session_id=job.session_id,
                    job_id=job.id,
                    event_type=EventType.STDOUT,
                    payload=masked_text,
                    is_masked=was_masked,
                )

            err_chunk = transport.read_stderr(4096, timeout=0.05)
            if err_chunk:
                raw_err = err_chunk.decode("utf-8", errors="replace")
                masked_err, was_masked = mask(raw_err)
                stderr_chunks.append(masked_err)
                self._record_event(
                    session_id=job.session_id,
                    job_id=job.id,
                    event_type=EventType.STDERR,
                    payload=masked_err,
                    is_masked=was_masked,
                )

        # Drain remaining output
        while True:
            out_chunk = transport.read(4096, timeout=0.05)
            if not out_chunk:
                break
            raw_text = out_chunk.decode("utf-8", errors="replace")
            masked_text, was_masked = mask(raw_text)
            stdout_chunks.append(masked_text)
            self._record_event(
                session_id=job.session_id,
                job_id=job.id,
                event_type=EventType.STDOUT,
                payload=masked_text,
                is_masked=was_masked,
            )

        while True:
            err_chunk = transport.read_stderr(4096, timeout=0.05)
            if not err_chunk:
                break
            raw_err = err_chunk.decode("utf-8", errors="replace")
            masked_err, was_masked = mask(raw_err)
            stderr_chunks.append(masked_err)
            self._record_event(
                session_id=job.session_id,
                job_id=job.id,
                event_type=EventType.STDERR,
                payload=masked_err,
                is_masked=was_masked,
            )

        exit_code = transport.exit_code
        transport.close()

        with self._lock:
            if job.id in self._cancel_flags:
                cancelled = True

        if cancelled:
            job.transition_to(JobStatus.CANCELLED, failure_reason="Cancelled by user")
        elif timed_out:
            job.transition_to(
                JobStatus.TIMEOUT,
                failure_reason=f"Execution timed out after {timeout}s",
            )
        else:
            job.exit_code = exit_code if exit_code is not None else 0
            if job.exit_code == 0:
                job.transition_to(JobStatus.COMPLETED)
            else:
                job.transition_to(
                    JobStatus.FAILED,
                    failure_reason=f"Remote process exited with non-zero status: {job.exit_code}",
                )

        job.stdout = "".join(stdout_chunks)
        job.stderr = "".join(stderr_chunks)
        self.job_repo.save(job)

        self._record_event(
            session_id=job.session_id,
            job_id=job.id,
            event_type=EventType.STATE_CHANGE,
            payload={
                "status": job.status.value,
                "exit_code": job.exit_code,
                "failure_reason": job.failure_reason,
            },
        )

        with self._lock:
            self._active_transports.pop(job.id, None)
            self._cancel_flags.discard(job.id)

        self._signal_completion(job.id)

    def get_job(self, job_id: str) -> Job | None:
        """Retrieves current job status from persistent repository."""
        return self.job_repo.get_by_id(job_id)

    def list_jobs(self, session_id: str) -> list[Job]:
        """Lists all jobs registered for a session."""
        return self.job_repo.list_by_session(session_id)

    def wait_job(self, job_id: str, timeout: float | None = None) -> Job:
        """Waits for a job to complete execution and returns the finished Job."""
        job = self.job_repo.get_by_id(job_id)
        if job is None:
            raise JobNotFoundError(job_id)

        if job.is_finished():
            return job

        with self._lock:
            event = self._completion_events.get(job_id)

        if event:
            event.wait(timeout=timeout)

        refreshed = self.job_repo.get_by_id(job_id)
        return refreshed if refreshed is not None else job

    def cancel_job(self, job_id: str, reason: str = "Cancelled by user") -> Job:
        """Cancels a running or created job."""
        job = self.job_repo.get_by_id(job_id)
        if job is None:
            raise JobNotFoundError(job_id)

        if job.is_finished():
            return job

        with self._lock:
            self._cancel_flags.add(job_id)
            proc = self._active_processes.get(job_id)
            transport = self._active_transports.get(job_id)

        if proc:
            _terminate_proc(proc)
        if transport:
            transport.close()
        if self.scp_service:
            try:
                self.scp_service.cancel_transfer(job_id)
            except Exception:
                pass

        # Wait briefly for worker thread to persist CANCELLED status
        refreshed = self.wait_job(job_id, timeout=1.0)
        return refreshed

    def recover_orphaned_jobs(self) -> int:
        """Reconciles interrupted jobs upon service restart.

        Scans repository for jobs in CREATED or RUNNING state that have no
        active process in the current service runtime and marks them as FAILED.
        """
        if not hasattr(self.job_repo, "list_all"):
            return 0

        unresolved = [
            j
            for j in self.job_repo.list_all()
            if j.status in {JobStatus.CREATED, JobStatus.RUNNING}
        ]

        recovered_count = 0
        for job in unresolved:
            with self._lock:
                if job.id in self._active_processes or job.id in self._active_transports:
                    continue

            job.transition_to(
                JobStatus.FAILED,
                failure_reason="Process interrupted by service restart",
            )
            self.job_repo.save(job)
            self._record_event(
                session_id=job.session_id,
                job_id=job.id,
                event_type=EventType.STATE_CHANGE,
                payload={
                    "status": JobStatus.FAILED.value,
                    "reason": "service_restart_recovery",
                },
            )
            recovered_count += 1

        return recovered_count
