"""Filter recovery events and extract essential log lines for display."""

from __future__ import annotations

from robo_rec.recovery.models import RecoveryEvent


def extract_log_from_event(event: RecoveryEvent) -> tuple[str | None, str]:
    """Extract a log line and level from a RecoveryEvent.

    Returns (line, level) where line is None if the event shouldn't be logged.
    RecoveryEvent.kind is one of:
    "started", "phase", "eta", "found", "not_found", "error", "log", "finished".
    """
    kind = event.kind

    if kind == "started":
        return (f"• {event.message}", "info")

    elif kind == "phase":
        # event.message already includes "Phase N/M: ..." (see parser.py _PHASE_RE).
        return (event.message, "progress")

    elif kind == "eta":
        return (event.message, "progress")

    elif kind == "found":
        mnemonic = event.result.mnemonic if event.result else None
        seed = (mnemonic[:20] + "...") if mnemonic else "???"
        return (f"✓ FOUND: {seed}", "found")

    elif kind == "not_found":
        return (f"• {event.message}", "info")

    elif kind == "error":
        message = (event.message or "Unknown error")[:80]
        return (f"✗ ERROR: {message}", "error")

    elif kind == "log":
        # Raw passthrough lines from the underlying btcrecover process that didn't
        # match a more specific pattern (parser.py: parse_line's catch-all).
        line = event.message
        if not line:
            return (None, "debug")
        return (line, "info")

    elif kind == "finished":
        return (f"• {event.message}", "info")

    return (None, "debug")


__all__ = ["extract_log_from_event"]
