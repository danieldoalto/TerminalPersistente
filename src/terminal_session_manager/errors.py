"""Domain exceptions for Terminal Session Manager."""


class DomainError(Exception):
    """Base exception for all domain-level errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidStateError(DomainError):
    """Raised when an unrecognized or malformed state is encountered."""


class InvalidStateTransitionError(DomainError):
    """Raised when an illegal state transition is attempted."""

    def __init__(self, current_state: str, target_state: str, entity_type: str = "Entity") -> None:
        message = (
            f"Invalid state transition for {entity_type}: cannot transition "
            f"from '{current_state}' to '{target_state}'."
        )
        super().__init__(message)
        self.current_state = current_state
        self.target_state = target_state
        self.entity_type = entity_type


class EntityNotFoundError(DomainError):
    """Base exception for entity lookup failures."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(f"{entity_type} with ID '{entity_id}' was not found.")
        self.entity_type = entity_type
        self.entity_id = entity_id


class SessionNotFoundError(EntityNotFoundError):
    """Raised when a requested session is not found."""

    def __init__(self, session_id: str) -> None:
        super().__init__("Session", session_id)


class JobNotFoundError(EntityNotFoundError):
    """Raised when a requested job is not found."""

    def __init__(self, job_id: str) -> None:
        super().__init__("Job", job_id)


class DeviceNotFoundError(EntityNotFoundError):
    """Raised when a requested device is not found."""

    def __init__(self, device_id: str) -> None:
        super().__init__("Device", device_id)


class CredentialNotFoundError(EntityNotFoundError):
    """Raised when a requested credential reference is not found."""

    def __init__(self, credential_ref_id: str) -> None:
        super().__init__("CredentialRef", credential_ref_id)


class ValidationError(DomainError):
    """Raised when entity validation fails."""


class TransportError(DomainError):
    """Base exception for transport and process communication failures."""


class TransportNotOpenError(TransportError):
    """Raised when attempting I/O operations on an unopened transport."""

    def __init__(self, message: str = "Transport channel is not open.") -> None:
        super().__init__(message)


class TransportClosedError(TransportError):
    """Raised when attempting to write to or interact with a closed or terminated transport."""

    def __init__(self, message: str = "Transport channel is closed or process terminated.") -> None:
        super().__init__(message)


class TransportTimeoutError(TransportError):
    """Raised when a blocking transport operation exceeds the specified timeout."""

    def __init__(self, message: str = "Transport operation timed out.") -> None:
        super().__init__(message)
