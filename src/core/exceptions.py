"""Project-level exception hierarchy."""

from __future__ import annotations


class OpenResearchAgentError(Exception):
    """Base exception for all domain-specific errors."""


class ConfigurationError(OpenResearchAgentError):
    """Raised when runtime configuration is invalid."""


class WorkflowError(OpenResearchAgentError):
    """Raised when a workflow stage fails unexpectedly."""


class StorageError(OpenResearchAgentError):
    """Raised when artifact persistence operations fail."""
