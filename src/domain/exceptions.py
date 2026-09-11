"""Domain exceptions for ATS Core MVP."""


class DomainException(Exception):
    """Base exception for all domain errors."""
    pass


class EntityNotFoundError(DomainException):
    """Raised when an entity is not found."""
    pass


class DuplicateEntityError(DomainException):
    """Raised when an entity violates uniqueness constraints (e.g. DNI, email, phone)."""
    pass


class OptimisticLockError(DomainException):
    """Raised when concurrent modification detects a record version mismatch."""
    pass


class AuthenticationError(DomainException):
    """Raised on invalid credentials or authentication failure."""
    pass


class AccountLockedError(DomainException):
    """Raised when an account is temporarily locked due to excessive failed attempts."""
    pass


class InsufficientPermissionsError(DomainException):
    """Raised when a user attempts an unauthorized operation under RBAC policy."""
    pass


class AuditIntegrityError(DomainException):
    """Raised when an attempt is made to mutate or delete audit log entries."""
    pass


class FinancialValidationError(DomainException):
    """Raised when financial inputs are mathematically invalid or out of bounds."""
    pass
