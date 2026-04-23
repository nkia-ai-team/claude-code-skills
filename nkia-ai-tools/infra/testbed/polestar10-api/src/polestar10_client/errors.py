"""Exception hierarchy for the polestar10 HTTP client.

`FallThroughRequired` is the hook point Issue 6 (NKIAAI-542) orchestrator
listens for to switch from API path to UI-guide path.
"""


class PolestarApiError(Exception):
    """Base class for all polestar10 API errors."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: object = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class FallThroughRequired(PolestarApiError):
    """Raised when the caller should fall back to the UI-guided flow.

    Orchestrator catches this, renders `ui_hint` to the user, and resumes
    the higher-level step after manual confirmation.
    """

    def __init__(self, operation: str, ui_hint: str, *, cause: Exception | None = None):
        super().__init__(f"fall through to UI for {operation!r}: {ui_hint}")
        self.operation = operation
        self.ui_hint = ui_hint
        self.cause = cause
