"""Job domain model and lifecycle states."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

from terminal_session_manager.errors import InvalidStateTransitionError, ValidationError


class JobStatus(str, Enum):
    """Conceptual states of an asynchronous or synchronous job."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


JOB_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.CREATED: {
        JobStatus.RUNNING,
        JobStatus.CANCELLED,
        JobStatus.FAILED,
    },
    JobStatus.RUNNING: {
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
        JobStatus.TIMEOUT,
    },
    JobStatus.COMPLETED: set(),
    JobStatus.FAILED: set(),
    JobStatus.CANCELLED: set(),
    JobStatus.TIMEOUT: set(),
}


@dataclass
class Job:
    """Represents an execution unit within a persistent session."""

    session_id: str
    command: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.CREATED
    device_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    exit_code: int | None = None
    inputs: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    failure_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("Job ID cannot be empty.")
        if not self.session_id:
            raise ValidationError("Job must be linked to a valid session_id.")
        if not self.command:
            raise ValidationError("Job command cannot be empty.")
        if not isinstance(self.status, JobStatus):
            try:
                self.status = JobStatus(self.status)
            except ValueError as err:
                raise ValidationError(f"Invalid job status: {self.status}") from err

    def is_finished(self) -> bool:
        """Indicates whether the job has reached a terminal state."""
        return self.status in {
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.TIMEOUT,
        }

    def transition_to(
        self,
        new_status: JobStatus,
        *,
        exit_code: int | None = None,
        failure_reason: str | None = None,
    ) -> None:
        """Transitions job to a new state and updates timestamps."""
        if not isinstance(new_status, JobStatus):
            try:
                new_status = JobStatus(new_status)
            except ValueError as err:
                raise ValidationError(f"Invalid target job status: {new_status}") from err

        if new_status == self.status:
            return

        allowed = JOB_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                current_state=self.status.value,
                target_state=new_status.value,
                entity_type="Job",
            )

        now = datetime.now(timezone.utc)
        self.status = new_status

        if new_status == JobStatus.RUNNING and self.started_at is None:
            self.started_at = now

        if self.is_finished():
            if self.finished_at is None:
                self.finished_at = now
            if exit_code is not None:
                self.exit_code = exit_code
            if failure_reason is not None:
                self.failure_reason = failure_reason
