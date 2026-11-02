import re

EMAIL_RE = re.compile(
    r"(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])"
)
INDIAN_MOBILE_RE = re.compile(r"(?<!\d)(?:\+91[-\s]?)?[6-9]\d{9}(?!\d)")
INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions", re.I),
    re.compile(r"(?:reveal|print|show)\s+(?:the\s+)?system\s+prompt", re.I),
    re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.I),
)


def redact_simple_pii(text: str) -> str:
    """Redact complete email and Indian mobile matches; this is not full DLP."""
    text = EMAIL_RE.sub("[EMAIL_REDACTED]", text)
    return INDIAN_MOBILE_RE.sub("[PHONE_REDACTED]", text)


def has_injection_signal(text: str) -> bool:
    """Return a teaching signal, not a reliable security decision."""
    return any(pattern.search(text) is not None for pattern in INJECTION_PATTERNS)
