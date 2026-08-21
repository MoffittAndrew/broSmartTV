# bro Smart TV Launcher

This directory owns the Raspberry Pi deployment and process lifecycle. It is
not used for normal local development: run `py/main.py` directly on a
development machine. On the deployed Pi, the application is rooted at
`/bro/app`, so files in this local directory map to `/bro/app/launcher` on the
device. Do not add an extra `broSmartTV` path component when referring to the
Pi checkout.

## Startup Flow

The boot and application flow is:

```text
systemd bro-smart-tv.service
  -> /bro/app/launcher/launch
    -> /bro/.venv/bin/python /bro/app/py/launch.py
      -> standby phase (web wake button or Bluetooth remote discovery)
      -> launch screen and projector power-on
      -> /bro/app/launcher/update
      -> import main.py, show the full UI, and start screen cast
```

`bro-smart-tv.service` is enabled by `install-bro` and starts after the network
is online. It runs as the `bro` user with `/bro` as its working directory.
The unit starts the shell launcher, not Python directly, because the shell
script owns restart policy and runtime environment setup.

## Launcher Responsibilities

`launch` runs only on the Pi and does the following before starting Python:

- Sets `QT_QPA_PLATFORM=eglfs` and points `QT_QPA_EGLFS_KMS_CONFIG` at
  `eglfs_kms_conf.json`.
- Uses the shared `/bro/.venv` virtual environment, disables user-site Python
  packages, and clears `PYTHONPATH`.
- Optionally enables Widevine if a manually provisioned CDM exists at
  `/bro/widevine/libwidevinecdm.so`.
- Repairs the executable bit on `launcher/update`, which can be lost when code
  is checked out from a non-Linux host.
- Runs `py/launch.py` in a loop, waiting five seconds before retrying crashes.

The shell launcher deliberately stops instead of restarting when `launch.py`
exits with either of these codes:

| Exit code | Meaning |
| --- | --- |
| `130` | Manual cancellation or service stop via `SIGINT`. |
| `200` | A second launcher instance was rejected by `py/launcher_lock.py`. |

It also stops when `/bro/brosmarttv-reboot-pending.flag` exists. That flag is
written before an application-triggered reboot, allowing the outer process to
exit cleanly while preserving state for the next boot. Other exit codes are
treated as failures and restart `launch.py`.

`systemd` uses `Restart=on-failure` as a secondary safety net only if the shell
launcher itself dies. `SuccessExitStatus=1` prevents systemd from overriding
the launcher's intentional no-restart exits. `KillSignal=SIGINT` ensures a
service stop follows `launch.py`'s existing `KeyboardInterrupt` shutdown path.

## Python Startup Phases

`py/launch.py` is the Python orchestration entrypoint. Keep its responsibilities
separate from the application UI in `py/main.py`.

1. It acquires `/tmp/brosmarttv-launch.lock`; another live instance exits with
   code `200`.
2. Unless a restart/reboot flag says otherwise, it starts the lightweight
   standby web server and waits for either the web page's wake action or
   Bluetooth remote discovery. Qt is intentionally not initialized during this
   phase to keep the idle device lightweight.
3. It stops the standby server, creates the launch-screen `QApplication`, starts
   projector power-on, and runs `launcher/update` on Pi hardware only.
4. It reloads selected modules after the updater changes the checkout, connects
   the remote, imports `main.py`, displays `MAIN_WINDOW`, and starts the full
   screen-cast server. The full server replaces the standby server at the same
   URL.
5. Fatal startup or server failures force exit code `1`, so the outer launcher
   can retry.

An in-app restart writes `/tmp/brosmarttv-skip-standby.flag`; a reboot writes
`/bro/brosmarttv-reboot-pending.flag`, which persists across reboot. The next
`launch.py` run consumes either flag and bypasses standby so the application
returns directly to the main startup path.

## Install and Update

Run `install-bro` for initial Pi provisioning. It creates `/bro`, clones the
repository into `/bro/app`, creates `/bro/.venv` with `--system-site-packages`,
adds `/bro/app/launcher` to the `bro` user's `PATH`, installs/enables the
systemd unit, and provisions one-time device integration such as LIRC,
NetworkManager permissions, reboot sudo permissions, TLS bootstrap, and the
QtWebEngine-compatible 4K-page kernel setting. Enabling the systemd service
does not start it; reboot or run `sudo systemctl start bro-smart-tv` afterward.

Use `update` for regular code/dependency updates. It reads the selected branch
from `/bro/app/launcher/branch` (default `live`), stashes local changes, fetches
and switches the checkout, ensures system PyQt5/QtWebEngine dependencies and
the shared venv, and installs Python requirements. It also refreshes the screen
cast certificate for the current `wlan0` IP, ensures the Python runtime can bind
the configured screen-cast port, and adds the non-persistent `iptables` rule
for that port. `launch.py` runs this automatically before each Pi application
startup; it is reasonable to run manually when maintaining the device.

`install-bro` is intentionally responsible for one-time system configuration.
Do not expect `update` to re-copy the systemd unit, LIRC configuration, static
IP settings, or polkit rules.

## Operating the Pi

From the deployed checkout or any shell where `launcher` is on `PATH`:

```bash
sudo systemctl start bro-smart-tv
stop
attach
update
```

- `stop` invokes `sudo systemctl stop bro-smart-tv`.
- `attach` follows the service journal with `journalctl -u bro-smart-tv -f`.
- Use `systemctl status bro-smart-tv` and the journal when diagnosing boot or
  restart loops.

Avoid killing Python or the shell launcher directly: it bypasses the intended
`SIGINT` shutdown path and obscures the service's restart behavior. Application
shutdown should remain centralized in `py/teardown.py`.

## Pi-Specific Notes

- The Pi 5 default 16K-page kernel is incompatible with Qt5 WebEngine's bundled
  Chromium. `install-bro` adds `kernel=kernel8.img` to the boot configuration;
  reboot and verify `getconf PAGESIZE` reports `4096` before investigating a
  blank QWebEngine view further.
- The screen-cast server normally reads `certs/screen-cast.crt` and
  `certs/screen-cast.key`; `SCREEN_CAST_SSL_CERT` and `SCREEN_CAST_SSL_KEY`
  override those defaults.
- The runtime checkout should keep `git config core.filemode false`, because
  launcher-side executable-bit repairs must not create mode-only changes that
  block updates or branch switches.
- The application needs a live network connection for its update check. A
  failed update is surfaced on the launch screen; startup continues with the
  currently checked-out code where possible.