"""Safe shell command execution utilities."""

from subprocess import run, CalledProcessError, TimeoutExpired
from typing import Sequence, Optional


def sh(args: Sequence[str], cwd: Optional[str] = None, timeout: Optional[int] = None) -> str:
    """Execute shell command safely without shell=True.

    Args:
        args: Command and arguments as list
        cwd: Working directory
        timeout: Timeout in seconds

    Returns:
        stdout as string

    Raises:
        CalledProcessError: If command fails
        TimeoutExpired: If command times out
    """
    result = run(args, check=True, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    return result.stdout
