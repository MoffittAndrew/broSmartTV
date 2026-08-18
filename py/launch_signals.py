"""Signals for coordinating restart/reboot behavior across launch.py runs.

Two distinct mechanisms, because they need to survive different lifetimes:
- Skip-standby is file-based: Restart/Reboot end the current process, so a
  brand-new launch.py process (respawned by the bash loop or a real reboot)
  has to read it back from disk.
- Exit-code request is an in-memory module global: it only needs to survive
  from the button click to right after APP.exec_() returns in the same
  process/run, so a file would be unnecessary persistence.
"""

import os

SKIP_STANDBY_FLAG_PATH = "/tmp/brosmarttv-skip-standby.flag"

# Sentinel exit code launch.py can return to tell launcher/launch's bash loop
# "don't restart me" (mirrors the existing 130/200 cases) because a real OS
# reboot is already underway and racing a restart against it would hang the
# service stop.
EXIT_CODE_REBOOTING = 201

_requested_exit_code = None


def request_skip_standby(flag_path=SKIP_STANDBY_FLAG_PATH):
    """Mark that the next launch.py run should skip off_phase()."""
    with open(flag_path, "a"):
        os.utime(flag_path, None)


def consume_skip_standby(flag_path=SKIP_STANDBY_FLAG_PATH):
    """Check-and-clear the skip-standby flag; True only once per request."""
    if not os.path.exists(flag_path):
        return False

    os.remove(flag_path)
    return True


def request_exit_code(code):
    """Ask the current launch.py run to exit with `code` once APP.exec_() returns."""
    global _requested_exit_code
    _requested_exit_code = code


def consume_exit_code(default=0):
    """Check-and-clear the requested exit code, falling back to `default`."""
    global _requested_exit_code
    code = _requested_exit_code if _requested_exit_code is not None else default
    _requested_exit_code = None
    return code
