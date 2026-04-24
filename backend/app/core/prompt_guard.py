"""Prompt injection guard for custom_prompt field.

Validates and sanitizes user-provided prompt additions before they are
appended to AI Gateway requests. Prevents common injection attacks that
attempt to override system instructions.
"""
import re
from fastapi import HTTPException, status

_MAX_LEN = 2000

_INJECTION_PATTERNS = [
    # Classic override attempts
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|context)",
    r"forget\s+(everything|all|the\s+above|previous)",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    # Role/persona hijacking
    r"you\s+are\s+now\s+",
    r"act\s+as\s+(if|though|a|an)\s+",
    r"pretend\s+(to\s+be|you\s+are)",
    r"roleplay\s+as",
    # Jailbreak markers
    r"\bjailbreak\b",
    r"\bDAN\b",
    r"do\s+anything\s+now",
    # System prompt injection via markup
    r"<\s*/?system\s*>",
    r"\[INST\]",
    r"###\s*system\s*:",
    r"<<SYS>>",
    # Prompt boundary injection
    r"[-–—]{5,}",                          # long dashes used to break context
    r"={5,}",                              # long equals used as section dividers
    r"SYSTEM\s*PROMPT\s*:",
    r"NEW\s+INSTRUCTIONS?\s*:",
]

_COMPILED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _INJECTION_PATTERNS]


def sanitize_custom_prompt(text: str | None) -> str | None:
    """Validate and sanitize a user-supplied prompt extension.

    Raises HTTP 422 if the text is too long or contains injection patterns.
    Strips control characters and returns the cleaned text.
    """
    if not text:
        return text

    text = text.strip()

    if len(text) > _MAX_LEN:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "PROMPT_TOO_LONG",
                    "message": f"custom_prompt must not exceed {_MAX_LEN} characters (got {len(text)}).",
                    "details": [],
                }
            },
        )

    for pattern in _COMPILED:
        if pattern.search(text):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "PROMPT_INJECTION_DETECTED",
                        "message": (
                            "Suspicious content detected in custom_prompt. "
                            "Describe the clinical requirements directly without "
                            "override instructions."
                        ),
                        "details": [],
                    }
                },
            )

    # Strip null bytes and non-printable control chars (keep newlines/tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    return text or None
