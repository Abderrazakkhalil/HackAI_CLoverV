"""Domain errors mapped to safe, user-facing messages.

Stack traces never reach the frontend; these carry a clean ``message``.
"""

from __future__ import annotations


class HackAIError(Exception):
    """Base class. ``message`` is safe to show end users."""

    status_code = 502
    message = "Something went wrong. Please try again."

    def __init__(self, message: str | None = None, detail: str | None = None):
        self.message = message or self.message
        self.detail = detail
        super().__init__(self.message)


class ValidationError(HackAIError):
    status_code = 400
    message = "The uploaded file is not valid."


class TranscriptionError(HackAIError):
    status_code = 502
    message = "Could not transcribe the audio. Please try recording again."


class EmptyTranscriptionError(HackAIError):
    status_code = 422
    message = "We couldn't hear any speech. Please record a clearer voice note."


class LLMError(HackAIError):
    status_code = 502
    message = "The AI could not generate a listing. Please try again."
