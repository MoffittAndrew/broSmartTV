"""Signals for coordinating restart/reboot behavior across launch.py runs."""

import os

SKIP_STANDBY_FLAG_PATH = "/tmp/brosmarttv-skip-standby.flag"

# This marker must survive the reboot that it requests; /tmp is cleared during boot.
REBOOT_PENDING_FLAG_PATH = "/bro/brosmarttv-reboot-pending.flag"


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


def request_reboot_pending(flag_path=REBOOT_PENDING_FLAG_PATH):
    """Mark that the current launch process is preparing to reboot the device."""
    with open(flag_path, "a"):
        os.utime(flag_path, None)


def consume_reboot_pending(flag_path=REBOOT_PENDING_FLAG_PATH):
    """Check-and-clear the reboot marker left for the next launch after boot."""
    if not os.path.exists(flag_path):
        return False

    os.remove(flag_path)
    return True
