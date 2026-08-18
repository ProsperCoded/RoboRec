class RecoveryError(Exception):
    """Base class for recovery-engine errors."""


class BtcrecoverNotFoundError(RecoveryError):
    """The vendored btcrecover checkout is missing or incomplete."""


class InvalidSpecError(RecoveryError):
    """A RecoverySpec is malformed or exceeds the PRD's supported scope
    (e.g. 3+ missing words with unknown positions — see robo-rec-prd.md Section 4.2)."""


class LaunchError(RecoveryError):
    """The btcrecover subprocess failed to start."""
