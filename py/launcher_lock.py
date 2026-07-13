"""Single-instance lock helpers for Pi launcher startup."""

import fcntl
import os

LOCK_PATH = "/tmp/brosmarttv-launch.lock"


class LaunchAlreadyRunningError(RuntimeError):
    """Raised when another launcher instance already holds the lock."""


def acquire_launch_lock(lock_path=LOCK_PATH):
    """Acquire non-blocking exclusive lock and return the opened file handle."""
    lock_handle = open(lock_path, "a+")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        lock_handle.close()
        raise LaunchAlreadyRunningError("Another launcher instance is already running.") from exc

    lock_handle.seek(0)
    lock_handle.truncate()
    lock_handle.write(str(os.getpid()))
    lock_handle.flush()

    return lock_handle


def release_launch_lock(lock_handle):
    """Release launcher lock and close the associated handle."""
    if lock_handle is None:
        return

    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
    finally:
        lock_handle.close()
