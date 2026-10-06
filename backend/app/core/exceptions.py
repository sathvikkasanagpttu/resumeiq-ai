from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class ResumeIQException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "INTERNAL_ERROR",
        extra: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.extra = extra or {}

class DocumentParsingError(ResumeIQException):
    def __init__(self, detail: str, extra: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=422,
            detail=detail,
            error_code="DOCUMENT_PARSING_FAILED",
            extra=extra,
        )

class EvidenceNotFoundError(ResumeIQException):
    def __init__(self, detail: str, extra: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="EVIDENCE_NOT_FOUND",
            extra=extra,
        )

class HallucinationDetectedError(ResumeIQException):
    def __init__(self, detail: str, extra: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="HALLUCINATION_DETECTED",
            extra=extra,
        )

class PromptInjectionDetectedError(ResumeIQException):
    def __init__(self, detail: str, extra: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="PROMPT_INJECTION_DETECTED",
            extra=extra,
        )

class AuthenticationError(ResumeIQException):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTHENTICATION_FAILED",
        )

class AuthorizationError(ResumeIQException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="PERMISSION_DENIED",
        )
