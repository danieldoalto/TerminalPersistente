"""Unit tests for Job model and lifecycle states."""

import pytest

from terminal_session_manager.errors import InvalidStateTransitionError, ValidationError
from terminal_session_manager.models.job import Job, JobStatus


def test_job_creation_defaults() -> None:
    job = Job(session_id="sess-123", command="echo hello")
    assert job.id is not None
    assert job.session_id == "sess-123"
    assert job.command == "echo hello"
    assert job.status == JobStatus.CREATED
    assert job.is_finished() is False
    assert job.started_at is None
    assert job.finished_at is None
    assert job.exit_code is None


def test_job_validation() -> None:
    with pytest.raises(ValidationError, match="session_id"):
        Job(session_id="", command="ls")

    with pytest.raises(ValidationError, match="command"):
        Job(session_id="sess-1", command="")

    with pytest.raises(ValidationError, match="Invalid job status"):
        Job(session_id="sess-1", command="ls", status="unknown")  # type: ignore[arg-type]


def test_job_lifecycle_to_completed() -> None:
    job = Job(session_id="sess-1", command="pytest")

    # CREATED -> RUNNING
    job.transition_to(JobStatus.RUNNING)
    assert job.status == JobStatus.RUNNING
    assert job.started_at is not None
    assert job.is_finished() is False

    # RUNNING -> COMPLETED
    job.transition_to(JobStatus.COMPLETED, exit_code=0)
    assert job.status == JobStatus.COMPLETED
    assert job.is_finished() is True
    assert job.finished_at is not None
    assert job.exit_code == 0


def test_job_lifecycle_to_failed() -> None:
    job = Job(session_id="sess-1", command="bad_command")
    job.transition_to(JobStatus.RUNNING)
    job.transition_to(
        JobStatus.FAILED, exit_code=127, failure_reason="Command not found"
    )

    assert job.status == JobStatus.FAILED
    assert job.exit_code == 127
    assert job.failure_reason == "Command not found"
    assert job.is_finished() is True


def test_job_lifecycle_to_cancelled() -> None:
    job = Job(session_id="sess-1", command="sleep 100")
    job.transition_to(JobStatus.CANCELLED)
    assert job.status == JobStatus.CANCELLED
    assert job.is_finished() is True


def test_job_lifecycle_to_timeout() -> None:
    job = Job(session_id="sess-1", command="long_running")
    job.transition_to(JobStatus.RUNNING)
    job.transition_to(JobStatus.TIMEOUT, failure_reason="Execution timeout exceeded")
    assert job.status == JobStatus.TIMEOUT
    assert job.is_finished() is True


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (JobStatus.COMPLETED, JobStatus.RUNNING),
        (JobStatus.FAILED, JobStatus.RUNNING),
        (JobStatus.CANCELLED, JobStatus.RUNNING),
        (JobStatus.TIMEOUT, JobStatus.RUNNING),
        (JobStatus.CREATED, JobStatus.TIMEOUT),
        (JobStatus.COMPLETED, JobStatus.FAILED),
    ],
)
def test_job_invalid_transitions_rejected(
    from_status: JobStatus, to_status: JobStatus
) -> None:
    job = Job(session_id="sess-1", command="test", status=from_status)
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        job.transition_to(to_status)

    assert exc_info.value.current_state == from_status.value
    assert exc_info.value.target_state == to_status.value
    assert exc_info.value.entity_type == "Job"
