# Web Integration (streaming tiles / in-app browsing)

This documents how "launch a website and interact with it from the remote" works:
`WebTile` clicks -> `interface/web_interface.py` -> an embedded `QWebEngineView` ->
`interface/input_interface.py` routing NAV/SELECT/RETURN/keyboard input into it.

This feature is unrelated to the screencast webserver (`py/web_server/` /
`py/webserver/`, `webpages/`) - that exists for mirroring a phone/laptop screen to the
TV over WebRTC. Don't conflate the two.

## Why QWebEngineView (and not the original Selenium + win32gui approach)

The original implementation launched a real Chromium process via Selenium and embedded
its native window into the Qt UI using `win32gui.EnumWindows` + `QWindow.fromWinId`
(`webdriver.py`, since deleted). That only ever worked on a Windows dev machine.

The Raspberry Pi runs Qt with `QT_QPA_PLATFORM=eglfs` (see `launcher/launch`) - a
fullscreen framebuffer backend with **no window manager**. There is no window handle to
embed a separate process's window into, so that approach can never work on the actual
Pi target.

`QWebEngineView` is a real Qt widget (Chromium embedded *in-process*, not a separate
window), so it composites correctly with other Qt widgets under `eglfs` - including
stacking underneath/above the `InputInterface` selection overlay - and needs no
platform-specific window-embedding code at all.

This also fixed two latent bugs in the old design:
- The selection outline (`InputInterface`) used to carry `Qt.WindowStaysOnTopHint`,
  which is unreliable on a widget that's a child of another widget (window flags are
  meant for top-level windows). It now relies on plain `show()` + `raise_()`, the same
  pattern every other overlay in this app already uses.
- Chromium spin-up (fresh process + `webdriver_manager` install checks + a
  `sleep(0.5)`-polling `EnumWindows` loop) made pages slow to appear. `QWebEngineView`
  removes all of that - `view.load(url)` is enough.

## Architecture

- `interface/web_interface.py` - `WebInterface(CustomQWidget)`, owns one
  `QWebEngineView`, added to `MAIN_WINDOW` like any other tab (`ui/gui.py`'s
  `CustomQWindow.addWidget`/`setTab`).
- `interface/input_interface.py` - `InputInterface.setWebMode(webInterface)` switches
  `INPUT.MODES.WEB` on and stores the `WebInterface` reference; while in that mode,
  `navigate()`/`select()`/`back()` delegate to `WebInterface.navigate()`/`select()`/
  `closeAndReturnHome()` instead of walking a GUI button nav mesh.
- `ui/tools/tile.py` - `WebTile` (loaded from `tiles/web/*` files by
  `ui/tools/tiles.py`) calls `webInterface.openURL(url, incognito)` on click.

### Directional navigation (NAV_UP/RIGHT/DOWN/LEFT)

Arbitrary websites don't expose a "next button in this direction" API, and the old
Selenium relative-locator approach (`getElementAbove`/`Right`/`Below`/`Left`) was
fragile and Selenium-specific. Instead, `web_interface.py` injects a small custom JS
helper object (`window.__broNav`, defined by the `_NAV_HELPERS_JS` string constant) on
every page load:

- `_focusable()` - finds visible focusable elements (links, buttons, inputs, etc.).
- `move(direction)` - scores focusable elements by distance/overlap relative to
  `document.activeElement` and focuses the best match in that direction.
- `focusFirst()` - focuses the first focusable element (used right after page load).
- `focusInfo()` - returns the focused element's bounding rect, whether it's editable,
  and its current value.
- `activate()` - clicks the focused element (used for SELECT).
- `setValue(text)` - writes text into the focused field and dispatches `input`/`change`
  events (used after the on-screen keyboard submits).

This is a small **custom heuristic written for this app**, not the WICG
spatial-navigation polyfill - that avoids a runtime network fetch on every page load
and any third-party licensing to vendor. It hasn't been validated against real
streaming-site DOM structures yet (Netflix/Disney+/Prime) and may need per-site tuning.

`InputInterface.setSelectedButton()` already accepted a non-`Button` selection with a
`.rect` dict (previously fed by Selenium's `WebElement.rect`). `web_interface.py`'s
`FocusedElement` class just wraps the JS-returned rect in that same shape, so
`setSelectedButton()` needed no changes.

### Keyboard integration (typing into search boxes etc.)

When `focusInfo()` reports the focused element is editable, pressing SELECT opens the
existing on-screen keyboard via `MAIN_WINDOW.openTextInput(...)`
(`ui/gui.py`/`ui/tools/onscreen_keyboard.py`) instead of clicking. On submit, the typed
text is written back into the page via `window.__broNav.setValue(...)`.

## DRM / Widevine

Most streaming services require Widevine DRM to actually play video. Qt WebEngine
officially supports HTML5 DRM (this is a documented open feature, not commercial-only -
see Qt's "HTML5 DRM" docs), gated on two things:

1. **Proprietary codecs** (H.264) enabled in the installed QtWebEngine build.
   `launcher/update`'s `ensure_system_qtwebengine` installs the Pi's
   `python3-pyqt5.qtwebengine` apt package, but whether *that specific package* was
   built with proprietary codecs enabled needs to be confirmed on-device (some distro
   packages disable this for patent-licensing reasons, same issue as distro ffmpeg
   builds).
2. **A Widevine CDM binary** (`libwidevinecdm.so`) matching the Pi's CPU architecture.
  Google doesn't publish official Chrome builds for Linux ARM. The installer now
  provisions this per-device by installing `libwidevinecdm0` and copying
  `/opt/WidevineCdm/gmp-widevinecdm/latest/libwidevinecdm.so` to
  `/bro/widevine/libwidevinecdm.so`.

Once a CDM binary exists at `/bro/widevine/libwidevinecdm.so`, `launcher/launch`
automatically exports `QTWEBENGINE_CHROMIUM_FLAGS=--widevine-path=...` pointing at it -
no script changes needed when a device gets its CDM sourced.

### Why the CDM binary isn't checked into this repo

- **Licensing**: Widevine CDM binaries are proprietary and Google restricts
  redistribution. This repo is public, so committing the binary would mean publicly
  redistributing a proprietary Google binary, which is a materially bigger legal
  exposure than a single private device having an unofficially-sourced copy for
  personal use.
- **Version coupling**: the CDM must match the exact Chromium version the installed
  QtWebEngine build uses. A binary frozen in git would silently drift out of sync as
  the Pi's OS/apt packages update, with no way to detect it went stale.
- **Architecture-specific**: it's armhf/aarch64-specific depending on the OS image, so
  it's inherently a per-device provisioning concern, not a single repo asset.
- **Supply-chain hygiene**: an unofficially-extracted binary blob with no verifiable
  origin/signature is exactly the kind of untrusted-binary risk worth keeping out of
  source control, which also never cleanly forgets binaries once committed.
- **Consistent with existing conventions**: other sensitive/per-device artifacts
  (TLS certs, sudoers rules, the reboot-pending flag) already live outside git under
  `/bro/` on the device itself, provisioned by the launcher scripts rather than tracked
  in the repo.

### Sourcing the CDM binary

`install-bro` now attempts to provision the CDM by installing
`libwidevinecdm0` and copying the resulting binary into `/bro/widevine/`.
If that package is unavailable on a given image/repo configuration, provisioning
still remains a per-device concern.
