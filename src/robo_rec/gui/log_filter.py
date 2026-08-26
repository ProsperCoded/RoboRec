"""Filter recovery events and extract essential log lines for display."""

from __future__ import annotations

from robo_rec.recovery.models import RecoveryEvent


def extract_log_from_event(event: RecoveryEvent) -> tuple[str | None, str]:
    """Extract a log line and level from a RecoveryEvent.

    Returns (line, level) where line is None if the event shouldn't be logged.
    Essential events: progress, found, error, status updates.
    """
    kind = event.kind

    if kind == "progress":
        # Format: "Attempt X of Y | Rate: Z attempts/sec"
        progress = event.progress
        if progress:
            attempts = progress.get("attempts", 0)
            total = progress.get("total", "?")
            rate = progress.get("rate", 0)
            rate_str = f"{rate:.0f}/sec" if rate else "?"
            line = f"Attempt {attempts}/{total} | {rate_str}"
            return (line, "progress")

    elif kind == "found":
        # Seed phrase found!
        if event.result:
            seed = event.result.seed_phrase[:20] + "..." if event.result.seed_phrase else "???"
            line = f"✓ FOUND: {seed}"
            return (line, "found")

    elif kind == "error":
        # Error occurred
        error = event.error or "Unknown error"
        # Truncate at 80 chars
        error = error[:80]
        return (f"✗ ERROR: {error}", "error")

    elif kind == "status":
        # Status updates (GPU info, etc)
        status = event.status or ""
        if status and any(
            x in status.lower()
            for x in ["gpu", "cuda", "opencl", "cpu", "started", "finished", "cancel"]
        ):
            status = status[:85]
            return (f"• {status}", "info")

    elif kind == "warning":
        # Warnings
        warning = event.warning or ""
        if warning:
            warning = warning[:85]
            return (f"⚠ {warning}", "warn")

    # Skip other events (they're internal state changes)
    return (None, "debug")


__all__ = ["extract_log_from_event"]
