"""Project-level exception hierarchy."""

from __future__ import annotations


class OpenResearchAgentError(Exception):
    """Base exception for all domain-specific errors."""


class ConfigurationError(OpenResearchAgentError):
    """Raised when runtime configuration is invalid."""


class ValidationError(OpenResearchAgentError):
    """Raised when domain validation fails."""


class StorageError(OpenResearchAgentError):
    """Raised when artifact persistence operations fail."""


class WorkflowError(OpenResearchAgentError):
    """Raised when a workflow stage fails unexpectedly."""


class NotImplementedWorkflowError(WorkflowError):
    """Raised for intentionally deferred workflow functionality."""
