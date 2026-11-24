
import re

from nemoguardrails.actions import action


# Detect common prompt-injection and jailbreak attempts.
JAILBREAK_PATTERNS = [
    re.compile(
        r"\bignore\s+(all\s+)?(previous|prior|above)\s+instructions\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(bypass|disable|override)\s+(the\s+)?"
        r"(guardrails|safety rules|security checks)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(reveal|print|expose|show)\s+(the\s+)?"
        r"(system prompt|hidden instructions)\b",
        re.IGNORECASE,
    ),
]

# Detect credential-like values and sensitive identifiers.
SENSITIVE_PATTERNS = [
    re.compile(
        r"\b(?:api[_ -]?key|access[_ -]?token|password|secret)"
        r"\s*[:=]\s*\S+",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:gsk_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,})\b"),
    re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),  # PAN-like identifier
    re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),  # Aadhaar-like number
]


SUPPORT_TERMS = (
    "support",
    "help",
    "customer service",
    "technical issue",
    "technical support",
    "troubleshoot",
    "error",
    "bug",
    "not working",
    "problem",
    "product",
    "service",
    "feature",
    "account",
    "login",
    "sign in",
    "password",
    "subscription",
    "billing",
    "invoice",
    "payment",
    "refund",
    "refund policy",
    "refund status",
    "return",
    "return policy",
    "cancellation",
    "cancel",
    "order",
    "shipping",
    "delivery",
    "tracking",
    "warranty",
    "installation",
    "install",
    "setup",
    "update",
    "crash",
    "website",
    "mobile app",
    "application",
    "contact support",
    "working hours",
    "charged",
    "charged twice",
    "double charge",
    "failed payment",
    "payment failed",
    "damaged item",
    "late delivery",
    "missing order",
    "forgot password",
    "reset password",
    "human agent",
    "live agent",
)


from typing import Optional


def _get_message(
    context: Optional[dict],
    *keys: str,
) -> str:
    if not isinstance(context, dict):
        return ""

    for key in keys:
        value = context.get(key)

        if isinstance(value, str) and value.strip():
            return value

    return ""


def _contains_pattern(text: str, patterns: list) -> bool:
    return any(pattern.search(text) for pattern in patterns)


@action()
async def check_input_safety(context: dict) -> bool:
    """Return False for suspicious input or detected sensitive values."""
    message = _get_message(context, "last_user_message","user_message")

    if not message.strip():
        return False

    # Prevent unusually large inputs.
    if len(message) > 5000:
        return False

    if _contains_pattern(message, JAILBREAK_PATTERNS):
        return False

    if _contains_pattern(message, SENSITIVE_PATTERNS):
        return False
    print(
    "[Guardrails Debug]",
    "action=check_input_safety",
    "message_found=", bool(message),
    "context_keys=",
    list(context.keys()) if isinstance(context, dict) else [],
)
    return True



@action()
async def check_topic_allowed(context: dict) -> bool:
    """Basic keyword-based customer-support topic check."""

    message = _get_message(
        context,
        "last_user_message",
        "user_message",
    ).strip().lower()

    if not message:
        print("[Guardrails Debug] topic_check=False reason=empty_message")
        return False

    # Allow common greetings.
    if re.match(
        r"^(hi|hello|hey|good morning|good afternoon|good evening)\b",
        message,
    ):
        print("[Guardrails Debug] topic_check=True reason=greeting")
        return True

    allowed = any(term in message for term in SUPPORT_TERMS)

    print(
        "[Guardrails Debug]",
        "action=check_topic_allowed",
        f"allowed={allowed}",
        f"message_found={bool(message)}",
    )

    return allowed


@action()
async def check_output_safety(context: dict) -> bool:
    """Reject responses containing detectable secrets or identifiers."""
    response = _get_message(context, "last_bot_message","bot_message")

    # Fail closed if there is no response available to inspect.
    if not response.strip():
        return False

    if _contains_pattern(response, SENSITIVE_PATTERNS):
        return False

    print(
    "[Guardrails Debug]",
    "action=check_output_safety",
    "message_found=", bool(response),
    "context_keys=",
    list(context.keys()) if isinstance(context, dict) else [],
    )
    return True
