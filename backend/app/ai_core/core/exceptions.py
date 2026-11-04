"""AI Core exceptions."""
from typing import Any, Optional


class AICoreError(Exception):
    """Base AI Core exception."""

    def __init__(self, message: str, code: str = "ai_core_error", details: Optional[Any] = None, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details
        self.status_code = status_code


class AIAuthenticationError(AICoreError):
    def __init__(self, message: str = "Authentication required", details: Optional[Any] = None):
        super().__init__(message, code="ai_auth_required", details=details, status_code=401)


class AIAuthorizationError(AICoreError):
    def __init__(self, message: str = "Insufficient AI permissions", details: Optional[Any] = None):
        super().__init__(message, code="ai_forbidden", details=details, status_code=403)


class AIValidationError(AICoreError):
    def __init__(self, message: str = "Validation error", details: Optional[Any] = None):
        super().__init__(message, code="ai_validation_error", details=details, status_code=400)


class AINotFoundError(AICoreError):
    def __init__(self, message: str = "AI resource not found", details: Optional[Any] = None):
        super().__init__(message, code="ai_not_found", details=details, status_code=404)


class AIConflictError(AICoreError):
    def __init__(self, message: str = "AI resource conflict", details: Optional[Any] = None):
        super().__init__(message, code="ai_conflict", details=details, status_code=409)


class AIProviderError(AICoreError):
    def __init__(self, message: str = "Model provider error", details: Optional[Any] = None):
        super().__init__(message, code="ai_provider_error", details=details, status_code=502)


class AIRateLimitError(AICoreError):
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Any] = None):
        super().__init__(message, code="ai_rate_limited", details=details, status_code=429)


class AISecurityError(AICoreError):
    def __init__(self, message: str = "Security policy violation", details: Optional[Any] = None):
        super().__init__(message, code="ai_security_violation", details=details, status_code=403)
