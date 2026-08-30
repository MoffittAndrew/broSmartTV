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
fragile and Selenium-specific. Instead, `web_interface.py` installs a small custom JS
helper object (`window.__broNav`, defined by the `_NAV_HELPERS_JS` string constant) as
a profile-level `QWebEngineScript` (injection point `DocumentReady`, world
`ApplicationWorld`, main frame only). Script-collection injection - rather than a
`loadFinished`-time `runJavaScript()` - survives redirects and SPA soft-navigations,
and the isolated world keeps `__broNav` invisible to (and untouchable by) page scripts.
All `runJavaScript` calls therefore pass `QWebEngineScript.ApplicationWorld`.

- `_focusable()` - finds visible focusable elements: links, buttons, inputs,
  `tabindex`, plus ARIA roles (`role="button"` etc., which streaming SPAs use on plain
  divs), traversing open shadow roots (YouTube/Polymer). Candidates are restricted to
  roughly one screen above/below the viewport so a NAV press moves one row instead of
  teleporting to a distant footer.
- `move(direction)` - scores candidates by centre-to-centre distance with a
  perpendicular penalty, prefers row/column-aligned candidates over diagonal jumps,
  tolerates the few-px edge misalignment of virtualized carousels, then focuses the
  best match and `scrollIntoView`s it.
- `focusFirst()` - focuses the first fully-visible focusable element after page load
  (skipped on player-style pages, see player mode below).
- `focusInfo()` - returns the focused element's bounding rect, whether it's editable,
  and its current value.
- `player()` - reports HTML5-fullscreen state and the viewport coverage of the largest
  ready `<video>`; drives player-mode detection.
- `state()` - `{focus, player}` snapshot; every command returns it so Python always has
  a fresh view of the page after each remote press.
- `handleNav(direction)` / `handleSelect()` - mode-aware wrappers: in player mode they
  return state untouched so Python forwards a real key event instead (see below).
- `activate()` - emulates a full pointer press (pointerdown/mousedown/pointerup/
  mouseup/click at the element's centre), since many custom tiles/players ignore a bare
  `.click()` (used for SELECT).
- `setValue(text)` - writes text into the focused field and dispatches `input`/`change`
  events (used after the on-screen keyboard submits).

Python awaits each command's returned state via `_queryState()` (an asyncio future
resolved by the `runJavaScript` callback, with a `WEB.JS_QUERY_TIMEOUT_SECONDS` guard so
a hung/navigating page can never wedge `InputInterface`'s backlog queue).

`InputInterface.setSelectedButton()` already accepted a non-`Button` selection with a
`.rect` dict (previously fed by Selenium's `WebElement.rect`). `web_interface.py`'s
`FocusedElement` class just wraps the JS-returned rect in that same shape, so
`setSelectedButton()` needed no changes.

### Player mode (watching video)

Streaming players (Netflix `/watch`, fullscreen YouTube, etc.) don't use focusable DOM
navigation - they bind document-level keyboard shortcuts, and they ignore untrusted
synthetic JS `KeyboardEvent`s. So when a page is "player-like" - HTML5 fullscreen is
active, or a ready `<video>` covers at least `WEB.PLAYER_MIN_VIDEO_COVERAGE` of the
viewport (0.85: above Netflix's browse-page billboard, below its full-viewport player) -
input switches to forwarding **real Qt key events** into Chromium's input widget (the
view's `focusProxy()`):

- NAV arrows -> real arrow keys (seek/volume, per the site's own shortcuts).
- SELECT -> Space (play/pause everywhere).
- RETURN -> Escape while fullscreen (Chromium exits HTML5 fullscreen natively).

The selection outline is hidden while player mode is active. Because these are trusted
native key events, they work on players that ignore everything scriptable.

### RETURN behaves like a browser back button

`WebInterface.back()` (RETURN in WEB mode) tries, in order: exit HTML5 fullscreen ->
`history.back()` (never back into the idle `about:blank`; `openURL()` clears history per
tile so back never crosses into a previously-opened site) -> close the page and return
home. It returns whether it was handled in-page so `InputInterface` only leaves WEB mode
on a real close. HOME still always closes the page outright, and MENU logs a
`debugPage()` diagnostic snapshot (nav-helper presence, player state, focus, history).

### Browser parity (profile/page configuration)

`_configureWebProfile()` makes the embedded view behave like a normal desktop Chromium
toward the sites (applied to both the default and incognito profiles):

- `WEB.USER_AGENT` plus `WEB.ACCEPT_LANGUAGE` (a missing Accept-Language is another
  embedded-browser tell some CDNs check).
- **`PluginsEnabled`** - required for Chromium to load the Widevine CDM at all; DRM
  playback fails without it even with a valid `--widevine-path`.
- `FullScreenSupportEnabled` + accepting `fullScreenRequested` on every page - player
  fullscreen buttons silently no-op without both halves.
- `PlaybackRequiresUserGesture=False` - there is no mouse/touch to provide the "user
  gesture" autoplay normally requires.
- `JavascriptCanOpenWindows` + a `createWindow()` override that adopts a popup's first
  navigation back into the main view (standard kiosk pattern) - OAuth login windows and
  `target=_blank` links would otherwise silently fail under eglfs (no window manager).
- `featurePermissionRequested` is denied immediately (no camera/mic/location on a TV) so
  sites don't hang waiting on an unanswerable prompt.
- Persistent cookies are forced on the default profile so streaming logins survive
  restarts; the HTTP cache is bounded (`WEB.HTTP_CACHE_MAX_BYTES`) for SD-card wear.
- `renderProcessTerminated` triggers a delayed auto-reload - renderer OOM-kills are a
  real possibility on the Pi and used to leave a dead white page.
- TLS certificate errors are logged (never overridden) and scrollbars are hidden.

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
