"""Unit and integration tests for asynchronous JobService."""

import sys
import time

import pytest

from terminal_session_manager.errors import JobNotFoundError, ValidationError
from terminal_session_manager.models.event import EventType
from terminal_session_manager.models.job import Job, JobStatus
from terminal_session_manager.persistence.sqlite import (
    SqliteEventRepository,
    SqliteJobRepository,
    SqliteSessionRepository,
    SqliteStorage,
)
from terminal_session_manager.services.job_service import JobService


@pytest.fixture
def storage() -> SqliteStorage:
    s = SqliteStorage(":memory:")
    yield s
    s.close()


@pytest.fixture
def service(storage: SqliteStorage) -> JobService:
    job_repo = SqliteJobRepository(storage)
    event_repo = SqliteEventRepository(storage)
    session_repo = SqliteSessionRepository(storage)
    return JobService(job_repo=job_repo, event_repo=event_repo, session_repo=session_repo)


def test_submit_and_wait_job_success(service: JobService, storage: SqliteStorage) -> None:
    job = service.submit_job(
        session_id="session-1",
        command=[
            sys.executable,
            "-c",
            "import sys; print('ASYNC_JOB_OK'); sys.stdout.flush()",
        ],
    )
    assert job.id is not None
    assert job.status in {JobStatus.CREATED, JobStatus.RUNNING}

    finished = service.wait_job(job.id, timeout=5.0)
    assert finished.status == JobStatus.COMPLETED
    assert finished.exit_code == 0
    assert "ASYNC_JOB_OK" in finished.stdout

    # Verify persistent repository
    persisted = service.get_job(job.id)
    assert persisted is not None
    assert persisted.status == JobStatus.COMPLETED

    # Verify event history
    events = service.event_repo.get_events("session-1")
    event_types = [e.event_type for e in events]
    assert EventType.STATE_CHANGE in event_types
    assert EventType.STDOUT in event_types
    assert any("ASYNC_JOB_OK" in str(e.payload) for e in events if e.event_type == EventType.STDOUT)


def test_job_autonomous_execution_without_client_waiting(service: JobService) -> None:
    # Submitting a job and letting it run independently in the background
    job = service.submit_job(
        session_id="session-bg",
        command=[
            sys.executable,
            "-c",
            "import time, sys; time.sleep(0.3); print('BACKGROUND_FINISHED'); sys.stdout.flush()",
        ],
    )

    # Client checks immediately; job should be running or created
    initial = service.get_job(job.id)
    assert initial is not None
    assert not initial.is_finished()

    # Client "disconnects" / does other work, then returns after job completes
    refreshed = None
    for _ in range(30):
        refreshed = service.get_job(job.id)
        if refreshed is not None and refreshed.is_finished():
            break
        time.sleep(0.1)

    assert refreshed is not None
    assert refreshed.status == JobStatus.COMPLETED
    assert "BACKGROUND_FINISHED" in refreshed.stdout


def test_job_failure_with_exit_code(service: JobService) -> None:
    job = service.submit_job(
        session_id="session-err",
        command=[
            sys.executable,
            "-c",
            "import sys; sys.stderr.write('FATAL_INTERNAL_ERROR'); sys.exit(42)",
        ],
    )

    finished = service.wait_job(job.id, timeout=5.0)
    assert finished.status == JobStatus.FAILED
    assert finished.exit_code == 42
    assert "FATAL_INTERNAL_ERROR" in finished.stderr
    assert "42" in (finished.failure_reason or "")


def test_job_cancellation(service: JobService) -> None:
    # Long running job that will be cancelled
    job = service.submit_job(
        session_id="session-cancel",
        command=[sys.executable, "-c", "import time; time.sleep(60)"],
    )

    time.sleep(0.2)
    cancelled = service.cancel_job(job.id, reason="User requested termination")

    assert cancelled.status == JobStatus.CANCELLED
    assert cancelled.failure_reason == "Cancelled by user"
    assert cancelled.is_finished() is True


def test_job_timeout_handling(service: JobService) -> None:
    # Job configured with 0.3s timeout running a command that takes 5s
    job = service.submit_job(
        session_id="session-timeout",
        command=[sys.executable, "-c", "import time; time.sleep(5)"],
        timeout=0.3,
    )

    finished = service.wait_job(job.id, timeout=5.0)
    assert finished.status == JobStatus.TIMEOUT
    assert "timed out" in (finished.failure_reason or "").lower()
    assert finished.is_finished() is True


def test_job_inputs_and_multiple_outputs(service: JobService) -> None:
    script = (
        "import sys\n"
        "for line in sys.stdin:\n"
        "    sys.stdout.write(f'PROCESSED: {line}')\n"
        "    sys.stdout.flush()\n"
    )
    job = service.submit_job(
        session_id="session-io",
        command=[sys.executable, "-u", "-c", script],
        inputs=["alpha", "beta"],
    )

    finished = service.wait_job(job.id, timeout=5.0)
    assert finished.status == JobStatus.COMPLETED
    assert "PROCESSED: alpha" in finished.stdout
    assert "PROCESSED: beta" in finished.stdout

    events = service.event_repo.get_events("session-io")
    stdin_events = [e for e in events if e.event_type == EventType.STDIN]
    assert len(stdin_events) == 2
    assert stdin_events[0].payload == "alpha"
    assert stdin_events[1].payload == "beta"


def test_concurrent_jobs_execution(service: JobService) -> None:
    job_ids = []
    for i in range(4):
        job = service.submit_job(
            session_id=f"concurrent-sess-{i % 2}",
            command=[
                sys.executable,
                "-c",
                f"import time; time.sleep(0.1); print('WORKER_{i}')",
            ],
        )
        job_ids.append(job.id)

    # Wait for all jobs to complete concurrently
    completed_jobs = [service.wait_job(jid, timeout=5.0) for jid in job_ids]

    for idx, j in enumerate(completed_jobs):
        assert j.status == JobStatus.COMPLETED
        assert j.exit_code == 0
        assert f"WORKER_{idx}" in j.stdout


def test_recover_orphaned_jobs_on_service_restart(storage: SqliteStorage) -> None:
    job_repo = SqliteJobRepository(storage)
    event_repo = SqliteEventRepository(storage)

    # Simulate an orphaned job left in RUNNING status in the DB due to abrupt shutdown
    orphaned_job = Job(
        session_id="sess-orphan",
        command="long_running_server_task",
        status=JobStatus.RUNNING,
    )
    job_repo.save(orphaned_job)

    # Start a new JobService instance simulating service recovery
    new_service = JobService(job_repo=job_repo, event_repo=event_repo)

    recovered = new_service.recover_orphaned_jobs()
    assert recovered == 1

    reconciled = job_repo.get_by_id(orphaned_job.id)
    assert reconciled is not None
    assert reconciled.status == JobStatus.FAILED
    assert "service restart" in (reconciled.failure_reason or "").lower()

    # Verify event was recorded
    events = event_repo.get_events("sess-orphan")
    assert any(
        e.event_type == EventType.STATE_CHANGE and e.payload.get("status") == "failed"
        for e in events
    )


def test_validation_and_not_found(service: JobService) -> None:
    with pytest.raises(ValidationError):
        service.submit_job(session_id="", command="ls")

    with pytest.raises(ValidationError):
        service.submit_job(session_id="s1", command="")

    with pytest.raises(JobNotFoundError):
        service.wait_job("non-existent-job-id")

    with pytest.raises(JobNotFoundError):
        service.cancel_job("non-existent-job-id")
