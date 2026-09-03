from app_logging import get_adapter

logger = get_adapter("web", "web")
consoleLogger = get_adapter("console", "web")
logger.info("Importing web interface...")

import asyncio
import json

from globals import DISPLAY, INPUT, WEB
from ui.gui import CustomQWidget

from PyQt5 import sip
from PyQt5.QtCore import QEvent, Qt, QTimer, QUrl
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QApplication, QVBoxLayout
from PyQt5.QtWebEngineWidgets import (
    QWebEngineView,
    QWebEngineProfile,
    QWebEnginePage,
    QWebEngineScript,
    QWebEngineSettings,
)

# Custom directional-navigation heuristic (rather than the WICG spatial-navigation
# polyfill) so we avoid a runtime network fetch and third-party licensing to vendor.
# Injected once per profile as a QWebEngineScript (DocumentReady, ApplicationWorld) so it
# survives redirects/SPA soft-navigations and stays isolated from - and invisible to -
# page scripts. Every command returns a `state()` snapshot ({focus, player}) so Python
# always has a fresh view of the page after each remote press.
# __PLAYER_COVERAGE__ is substituted from globals.WEB.PLAYER_MIN_VIDEO_COVERAGE at install.
_NAV_HELPERS_JS = """
(function() {
    if (window.__broNav) { return; }

    var PLAYER_COVERAGE = __PLAYER_COVERAGE__;

    // Role selectors cover the div-based controls streaming SPAs (Netflix, Disney+, Prime)
    // use instead of real <button>/<a> tags.
    var FOCUS_SELECTOR = [
        'a[href]', 'button', 'input', 'select', 'textarea',
        '[tabindex]:not([tabindex="-1"])', '[contenteditable="true"]',
        '[role="button"]', '[role="link"]', '[role="menuitem"]', '[role="menuitemradio"]',
        '[role="option"]', '[role="tab"]', '[role="checkbox"]', '[role="radio"]', '[role="switch"]'
    ].join(', ');

    function collectFocusable(root, out) {
        var found = root.querySelectorAll(FOCUS_SELECTOR);
        for (var i = 0; i < found.length; i++) { out.push(found[i]); }
        // YouTube (Polymer) and other SPAs keep controls inside open shadow roots, which
        // querySelectorAll never crosses on its own.
        var hosts = root.querySelectorAll('*');
        for (var j = 0; j < hosts.length; j++) {
            if (hosts[j].shadowRoot) { collectFocusable(hosts[j].shadowRoot, out); }
        }
    }

    function isVisible(el, rect) {
        if (rect.width <= 0 || rect.height <= 0) { return false; }
        var style = window.getComputedStyle(el);
        if (style.visibility === 'hidden' || style.display === 'none' || parseFloat(style.opacity) === 0) { return false; }
        if (el.getAttribute('aria-hidden') === 'true' || el.disabled === true) { return false; }
        return true;
    }

    // document.activeElement stops at shadow hosts; descend to the really-focused element.
    function deepActiveElement() {
        var el = document.activeElement;
        while (el && el.shadowRoot && el.shadowRoot.activeElement) { el = el.shadowRoot.activeElement; }
        return (el && el !== document.body && el !== document.documentElement) ? el : null;
    }

    function centerX(rect) { return rect.left + rect.width / 2; }
    function centerY(rect) { return rect.top + rect.height / 2; }

    var nav = {
        _focusable: function() {
            var all = [];
            collectFocusable(document, all);
            // Restrict to roughly one screen above/below the viewport so one NAV press moves
            // one row instead of teleporting to a footer many screens away.
            var minY = -window.innerHeight;
            var maxY = window.innerHeight * 2;
            var seen = new Set();
            var out = [];
            for (var i = 0; i < all.length; i++) {
                var el = all[i];
                if (seen.has(el)) { continue; }
                seen.add(el);
                var rect = el.getBoundingClientRect();
                if (rect.bottom < minY || rect.top > maxY) { continue; }
                if (!isVisible(el, rect)) { continue; }
                out.push({ el: el, rect: rect });
            }
            return out;
        },

        move: function(direction) {
            var current = deepActiveElement();
            var currentRect = current ? current.getBoundingClientRect()
                : { left: 0, top: 0, right: 0, bottom: 0, width: 0, height: 0 };
            var cx = centerX(currentRect), cy = centerY(currentRect);
            var best = null;
            var bestScore = Infinity;
            var candidates = nav._focusable();
            for (var i = 0; i < candidates.length; i++) {
                var el = candidates[i].el;
                var rect = candidates[i].rect;
                if (current && (el === current || current.contains(el) || el.contains(current))) { continue; }
                var dx = centerX(rect) - cx;
                var dy = centerY(rect) - cy;
                // Edge-overlap slack: virtualized carousels misalign rows/tiles by a few px,
                // which the old strict edge comparison rejected outright.
                var slackY = Math.min(rect.height, currentRect.height || rect.height) * 0.4;
                var slackX = Math.min(rect.width, currentRect.width || rect.width) * 0.4;
                var primary, secondary, aligned;
                if (direction === 'up') {
                    if (rect.bottom > currentRect.top + slackY) { continue; }
                    primary = -dy; secondary = Math.abs(dx);
                    aligned = rect.right > currentRect.left && rect.left < currentRect.right;
                } else if (direction === 'down') {
                    if (rect.top < currentRect.bottom - slackY) { continue; }
                    primary = dy; secondary = Math.abs(dx);
                    aligned = rect.right > currentRect.left && rect.left < currentRect.right;
                } else if (direction === 'left') {
                    if (rect.right > currentRect.left + slackX) { continue; }
                    primary = -dx; secondary = Math.abs(dy);
                    aligned = rect.bottom > currentRect.top && rect.top < currentRect.bottom;
                } else {
                    if (rect.left < currentRect.right - slackX) { continue; }
                    primary = dx; secondary = Math.abs(dy);
                    aligned = rect.bottom > currentRect.top && rect.top < currentRect.bottom;
                }
                if (primary <= 0) { continue; }
                var score = primary + secondary * 2;
                // Prefer candidates in the same row/column over diagonal jumps.
                if (!aligned) { score *= 2; }
                if (score < bestScore) { bestScore = score; best = el; }
            }
            if (best) {
                try { best.focus({ preventScroll: true }); } catch (err) { best.focus(); }
                best.scrollIntoView({ block: 'center', inline: 'nearest' });
            }
            return nav.state();
        },

        focusFirst: function() {
            // Player-style pages (full-viewport video) shouldn't have focus forced onto
            // some off-screen control at load - key forwarding handles them instead.
            if (nav.player().active) { return nav.state(); }
            var candidates = nav._focusable();
            var target = null;
            for (var i = 0; i < candidates.length; i++) {
                var rect = candidates[i].rect;
                if (rect.top >= 0 && rect.bottom <= window.innerHeight) { target = candidates[i].el; break; }
            }
            if (!target && candidates.length > 0) { target = candidates[0].el; }
            if (target) { target.focus(); }
            return nav.state();
        },

        focusInfo: function() {
            var el = deepActiveElement();
            if (!el) { return null; }
            var rect = el.getBoundingClientRect();
            var editableTag = el.tagName === 'INPUT' || el.tagName === 'TEXTAREA';
            var editableType = !el.type || ['button', 'submit', 'checkbox', 'radio', 'range', 'color', 'file'].indexOf(el.type) === -1;
            return {
                x: rect.left, y: rect.top, width: rect.width, height: rect.height,
                editable: (editableTag && editableType) || el.isContentEditable === true,
                value: el.isContentEditable ? el.textContent : (el.value || "")
            };
        },

        player: function() {
            var fullscreen = !!(document.fullscreenElement || document.webkitFullscreenElement);
            var viewArea = window.innerWidth * window.innerHeight;
            var coverage = 0;
            var playing = false;
            var videos = document.querySelectorAll('video');
            for (var i = 0; i < videos.length; i++) {
                var v = videos[i];
                if (v.readyState < 2) { continue; }
                var rect = v.getBoundingClientRect();
                var c = viewArea > 0 ? (rect.width * rect.height) / viewArea : 0;
                if (c > coverage) { coverage = c; playing = !v.paused; }
            }
            return {
                fullscreen: fullscreen,
                coverage: coverage,
                playing: playing,
                active: fullscreen || coverage >= PLAYER_COVERAGE
            };
        },

        state: function() {
            return { focus: nav.focusInfo(), player: nav.player() };
        },

        revealControlsAndMove: function(direction) {
            // Players hide their overlay chrome after a few idle seconds; a synthetic
            // mousemove is what every mainstream player listens for to bring it back.
            var cx = window.innerWidth / 2, cy = window.innerHeight / 2;
            var target = document.elementFromPoint(cx, cy) || document.body;
            var evt = new MouseEvent('mousemove', { bubbles: true, cancelable: true, view: window, clientX: cx, clientY: cy });
            target.dispatchEvent(evt);
            document.dispatchEvent(evt);
            // Controls typically fade in via a CSS transition kicked off by that event; a
            // synchronous move() right away can still see opacity:0 mid-transition, so wait
            // a couple of frames (Chromium waits out returned Promises before resolving
            // runJavaScript) before actually moving focus into the now-visible controls.
            return new Promise(function(resolve) {
                requestAnimationFrame(function() {
                    requestAnimationFrame(function() { resolve(nav.move(direction)); });
                });
            });
        },

        activate: function() {
            var el = deepActiveElement();
            if (el) {
                // Plain el.click() is ignored by many custom tiles/players; emulate a real
                // pointer press at the element's centre (still untrusted, but far more
                // handlers listen to pointer/mouse events than to bare click()).
                var rect = el.getBoundingClientRect();
                var opts = {
                    bubbles: true, cancelable: true, composed: true, view: window,
                    clientX: centerX(rect), clientY: centerY(rect), button: 0
                };
                try {
                    el.dispatchEvent(new PointerEvent('pointerdown', opts));
                    el.dispatchEvent(new MouseEvent('mousedown', opts));
                    el.dispatchEvent(new PointerEvent('pointerup', opts));
                    el.dispatchEvent(new MouseEvent('mouseup', opts));
                } catch (err) { /* no PointerEvent support: click() below still fires */ }
                if (typeof el.click === 'function') { el.click(); }
            }
            return nav.state();
        },

        setValue: function(text) {
            var el = deepActiveElement();
            if (!el) { return null; }
            if (el.isContentEditable) { el.textContent = text; } else { el.value = text; }
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            return nav.state();
        }
    };
    window.__broNav = nav;
})();
"""

_NAV_DIRECTION_JS = {
    INPUT.NAV_UP: "up",
    INPUT.NAV_RIGHT: "right",
    INPUT.NAV_DOWN: "down",
    INPUT.NAV_LEFT: "left",
}

# Seek-mode key forwarding: left/right map to every mainstream web player's seek shortcut.
# Up/down are deliberately not forwarded - they instead toggle into player-controls
# navigation (see navigate()), since this remote has no separate volume control to give up.
_PLAYER_NAV_KEYS = {
    INPUT.NAV_RIGHT: Qt.Key_Right,
    INPUT.NAV_LEFT: Qt.Key_Left,
}


class FocusedElement:
    """Mirrors the `.rect` dict contract InputInterface already expects from non-Button selections."""
    def __init__(self, rect):
        self.rect = rect


_JS_CONSOLE_LOG_METHODS = {
    QWebEnginePage.InfoMessageLevel: consoleLogger.info,
    QWebEnginePage.WarningMessageLevel: consoleLogger.warning,
    QWebEnginePage.ErrorMessageLevel: consoleLogger.error,
}


def _installNavScript(profile):
    # Guard against duplicate inserts: the default profile is re-configured every time we
    # bounce between incognito and normal browsing.
    if not profile.scripts().findScript("broNav").isNull():
        return
    script = QWebEngineScript()
    script.setName("broNav")
    script.setSourceCode(_NAV_HELPERS_JS.replace("__PLAYER_COVERAGE__", str(WEB.PLAYER_MIN_VIDEO_COVERAGE)))
    script.setInjectionPoint(QWebEngineScript.DocumentReady)
    script.setWorldId(QWebEngineScript.ApplicationWorld)
    script.setRunsOnSubFrames(False)
    profile.scripts().insert(script)


def _configureWebProfile(profile):
    profile.setHttpUserAgent(WEB.USER_AGENT)
    profile.setHttpAcceptLanguage(WEB.ACCEPT_LANGUAGE)
    if not profile.isOffTheRecord():
        # Keep streaming-service logins across restarts (many sites use session cookies by
        # default); bound the disk cache for SD-card wear.
        profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        profile.setHttpCacheMaximumSize(WEB.HTTP_CACHE_MAX_BYTES)

    settings = profile.settings()
    # PluginsEnabled is what lets Chromium load the Widevine CDM (see WEB_INTEGRATION.md);
    # without it DRM playback fails even with a valid --widevine-path.
    settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
    # Player fullscreen buttons silently no-op unless fullscreen support is enabled AND the
    # resulting fullScreenRequested signal is accepted (see _onFullScreenRequested).
    settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
    # There is no mouse/touch to provide the "user gesture" autoplay normally requires.
    settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
    # Popups (OAuth logins, target=_blank) must be allowed so createWindow() gets a chance
    # to route them back into the main view.
    settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
    # TV UX: no scrollbars, smooth-scroll rows into view.
    settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
    settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
    if hasattr(QWebEngineSettings, "DnsPrefetchEnabled"):  # Qt >= 5.12
        settings.setAttribute(QWebEngineSettings.DnsPrefetchEnabled, True)

    _installNavScript(profile)


class _LoggingWebEnginePage(QWebEnginePage):
    """Forwards the page's JS console output (errors, warnings, console.log) into the app logger
    instead of letting Qt print it straight to the process console."""
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        logMethod = _JS_CONSOLE_LOG_METHODS.get(level, consoleLogger.info)
        logMethod(message, js_source=sourceID, js_line=lineNumber)

    def certificateError(self, error):
        # Never override TLS validation - just make the failure visible in app logs, since
        # Qt's own stderr output doesn't reach the /logs page.
        logger.error(f'TLS certificate error "{error.errorDescription()}"', url=error.url().toString())
        return False

    def createWindow(self, _windowType):
        # eglfs has no window manager, so popups (OAuth login windows, target=_blank links)
        # can't become real windows - the default createWindow returns None and they silently
        # fail. Instead hand the popup a throwaway page and adopt its first navigation into
        # this page, which is the standard kiosk-browser pattern.
        bridge = QWebEnginePage(self.profile(), self)

        def adoptPopupUrl(url):
            if url.isEmpty() or url.toString() == "about:blank":
                return
            logger.info(f'Popup routed into main view "{url.toString()}"', url=url.toString())
            self.setUrl(url)
            bridge.deleteLater()

        bridge.urlChanged.connect(adoptPopupUrl)
        return bridge


class WebInterface(CustomQWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__inputInterface = None
        self.__incognitoProfile = None
        self.__retiredProfiles = []
        self.__lastFocusRect = None
        self.__isEditableFocus = False
        self.__lastFocusValue = ""
        self.__playerActive = False
        # True while the remote is browsing the player's own overlay buttons (see navigate());
        # false is the default "seeking" sub-mode where left/right forward as real arrow keys.
        self.__playerControlsMode = False
        # Tracked directly from fullScreenRequested rather than re-derived from JS each RETURN -
        # synthetic key events can't reliably reach Chromium's native fullscreen-escape handling.
        self.__pageFullscreen = False

        self.__view = QWebEngineView(self)
        self.__view.setFixedSize(DISPLAY.WIDTH, DISPLAY.HEIGHT)
        # Replace the view's lazily-created default page up front so console logging is
        # active even before the first openURL()/incognito switch installs one explicitly.
        defaultProfile = QWebEngineProfile.defaultProfile()
        _configureWebProfile(defaultProfile)
        self.__view.setPage(self._makePage(defaultProfile))
        self.__view.loadFinished.connect(self._onLoadFinished)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__view)
        self.hide()

    def getInputInterface(self):
        return self.__inputInterface

    def setInputInterface(self, inputInterface):
        self.__inputInterface = inputInterface

    def _setWindowTab(self, tab=None):
        parent = self.parent()
        setTab = getattr(parent, "setTab", None)
        if callable(setTab):
            setTab(tab)

    def getPrimaryButton(self):
        # None until the first loadFinished callback resolves a focus rect; InputInterface
        # already tolerates a None selection (see setSelectedButton's early-return branch).
        return FocusedElement(self.__lastFocusRect) if self.__lastFocusRect is not None else None

    def _replacePage(self, page):
        oldPage = self.__view.page()
        self.__view.setPage(page)
        # The very first swap replaces the page QWebEngineView lazily created for itself, which the
        # view owns and destroys inside setPage(). Touching that stale wrapper (deleteLater/destroyed)
        # raises "wrapped C/C++ object ... has been deleted", which used to abort the first openURL().
        # Pages we construct here stay Python-owned and must still be deleted explicitly.
        if oldPage is None or sip.isdeleted(oldPage):
            return None
        oldPage.deleteLater()
        return oldPage

    def _retireProfileAfterPageDelete(self, profile, page):
        if profile is None:
            return

        self.__retiredProfiles.append(profile)

        def releaseProfile():
            if profile in self.__retiredProfiles:
                self.__retiredProfiles.remove(profile)
            profile.deleteLater()

        if page is None:
            releaseProfile()
        else:
            page.destroyed.connect(releaseProfile)

    def _makePage(self, profile):
        """Every page we install must come through here so browser-parity signal handling
        (fullscreen, permissions, crash recovery) survives incognito page swaps."""
        page = _LoggingWebEnginePage(profile, self.__view)
        page.fullScreenRequested.connect(self._onFullScreenRequested)
        page.featurePermissionRequested.connect(
            lambda origin, feature, page=page: self._onFeaturePermissionRequested(page, origin, feature)
        )
        page.renderProcessTerminated.connect(self._onRenderProcessTerminated)
        return page

    def _onFullScreenRequested(self, request):
        # The view is already fullscreen-sized, so accepting is all the HTML5 fullscreen API
        # needs to report success; rejecting (the default) makes player fullscreen buttons no-op.
        request.accept()
        self.__pageFullscreen = request.toggleOn()
        logger.info("Page fullscreen toggled", fullscreen=self.__pageFullscreen)

    def _onFeaturePermissionRequested(self, page, origin, feature):
        # The TV has no camera/mic/location; deny immediately so sites don't wait forever on
        # a permission prompt that nothing can answer.
        page.setFeaturePermission(origin, feature, QWebEnginePage.PermissionDeniedByUser)
        logger.info("Denied page feature permission request", origin=origin.toString(), feature=int(feature))

    def _onRenderProcessTerminated(self, status, exitCode):
        if status == QWebEnginePage.NormalTerminationStatus:
            return
        # Renderer OOM-kills are a real possibility on the Pi; auto-reload instead of leaving
        # a dead white page that the remote can't interact with.
        url = self.__view.url().toString()
        logger.error(f'Web renderer died for "{url}"', url=url, status=int(status), exit_code=exitCode)
        # Small delay avoids the reload racing the dying render process's teardown.
        QTimer.singleShot(1000, self.__view.reload)

    def _forwardKey(self, key, text=""):
        # Streaming players ignore untrusted synthetic JS KeyboardEvents, so playback keys are
        # posted as real Qt key events to Chromium's input widget (the view's focusProxy).
        # postEvent (not sendEvent): Qt takes ownership and delivers on the event loop.
        target = self.__view.focusProxy() or self.__view
        QApplication.postEvent(target, QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier, text))
        QApplication.postEvent(target, QKeyEvent(QEvent.KeyRelease, key, Qt.NoModifier, text))

    def openURL(self, url, incognito=False):
        if incognito:
            oldProfile = self.__incognitoProfile
            # A profile constructed without a storage name is off-the-record (mirrors old --incognito flag).
            self.__incognitoProfile = QWebEngineProfile()
            _configureWebProfile(self.__incognitoProfile)
            oldPage = self._replacePage(self._makePage(self.__incognitoProfile))
            self._retireProfileAfterPageDelete(oldProfile, oldPage)
        elif self.__incognitoProfile is not None:
            oldProfile = self.__incognitoProfile
            defaultProfile = QWebEngineProfile.defaultProfile()
            _configureWebProfile(defaultProfile)
            oldPage = self._replacePage(self._makePage(defaultProfile))
            self.__incognitoProfile = None
            self._retireProfileAfterPageDelete(oldProfile, oldPage)

        self.__lastFocusRect = None
        self.__isEditableFocus = False
        self.__playerActive = False
        self.__playerControlsMode = False
        self.__pageFullscreen = False
        # Fresh history per tile so RETURN's history-back never walks into a previously
        # opened site (clear() keeps only the current entry).
        self.__view.history().clear()
        logger.info(f'Loading webpage "{url}"', url=url, incognito=incognito)
        self.__view.load(QUrl(url))
        self.show()

        inputInterface = self.getInputInterface()
        if inputInterface is not None:
            inputInterface.setWebMode(self)
        self._setWindowTab(self)

    def _onLoadFinished(self, ok):
        url = self.__view.url().toString()
        if not ok:
            # QWebEnginePage doesn't hand us an error message/code here, so we can only
            # log that navigation failed, not why (Qt logs the underlying network error itself).
            logger.error(f'Webpage failed to load "{url}"', url=url)
            return
        logger.info(f'Webpage loaded "{url}"', url=url)
        # Nav helpers are injected by the profile-level QWebEngineScript at DocumentReady;
        # here we only seed the initial focus (focusFirst() skips player-style pages itself).
        self._runJs("window.__broNav && window.__broNav.focusFirst();", self._applyState)

    def _runJs(self, script, callback=None):
        # Must target ApplicationWorld - that's the isolated world __broNav is injected into.
        page = self.__view.page()
        if callback is None:
            page.runJavaScript(script, QWebEngineScript.ApplicationWorld)
        else:
            page.runJavaScript(script, QWebEngineScript.ApplicationWorld, callback)

    async def _queryState(self, script):
        """Run nav-helper JS and await its returned state dict (None on timeout/non-dict)."""
        future = asyncio.get_running_loop().create_future()

        def onResult(result):
            if not future.done():
                future.set_result(result)

        self._runJs(script, onResult)
        try:
            # Timeout guard: a page navigating/crashing mid-call can drop the callback, and
            # an unresolved await here would wedge InputInterface's backlog queue forever.
            state = await asyncio.wait_for(future, WEB.JS_QUERY_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            logger.warning("Timed out waiting for page JS result", url=self.__view.url().toString())
            return None
        self._applyState(state)
        return state if isinstance(state, dict) else None

    def _applyState(self, state):
        if not isinstance(state, dict):
            return
        player = state.get("player") or {}
        self.__playerActive = bool(player.get("active"))
        if not self.__playerActive:
            # Controls navigation only makes sense while a player is actually active.
            self.__playerControlsMode = False
        inputInterface = self.getInputInterface()
        if self.__playerActive and not self.__playerControlsMode:
            # A selection outline floating over a full-viewport video is just visual noise;
            # setSelectedButton() re-shows the overlay once controls-mode focus tracking resumes.
            if inputInterface is not None:
                inputInterface.hide()
            return
        focus = state.get("focus")
        if not focus:
            return
        # getBoundingClientRect() returns floats; Qt's setGeometry() only accepts ints.
        self.__lastFocusRect = {
            "x": int(focus["x"]),
            "y": int(focus["y"]),
            "width": int(focus["width"]),
            "height": int(focus["height"]),
        }
        self.__isEditableFocus = bool(focus.get("editable"))
        self.__lastFocusValue = focus.get("value") or ""
        if inputInterface is not None:
            inputInterface.setSelectedButton(FocusedElement(self.__lastFocusRect))

    async def navigate(self, direction):
        jsDirection = _NAV_DIRECTION_JS.get(direction)
        if jsDirection is None:
            return

        if self.__playerActive and not self.__playerControlsMode:
            if direction in _PLAYER_NAV_KEYS:
                self._forwardKey(_PLAYER_NAV_KEYS[direction])
                return
            # First up/down press while seeking switches into player-controls navigation.
            # Revealing the overlay and moving focus happen in one JS round trip so the
            # move can't race the controls' fade-in transition.
            self.__playerControlsMode = True
            await self._queryState(f"window.__broNav && window.__broNav.revealControlsAndMove('{jsDirection}');")
            return

        await self._queryState(f"window.__broNav && window.__broNav.move('{jsDirection}');")

    async def select(self):
        if self.__playerActive and not self.__playerControlsMode:
            # Space toggles play/pause in every mainstream web player.
            self._forwardKey(Qt.Key_Space, " ")
        elif self.__isEditableFocus:
            self._openKeyboardForFocusedField()
        else:
            await self._queryState("window.__broNav && window.__broNav.activate();")

    def _openKeyboardForFocusedField(self):
        window = self.window()
        if window is None or not hasattr(window, "openTextInput"):
            return

        inputInterface = self.getInputInterface()

        def restoreWebMode():
            if inputInterface is not None:
                inputInterface.setWebMode(self)

        def onSubmit(text):
            restoreWebMode()
            self._runJs(f"window.__broNav.setValue({json.dumps(text)});", self._applyState)

        # The keyboard is an ordinary GUI overlay, so input must leave WEB mode while it is
        # open or NAV would keep moving focus around the webpage instead of between keys.
        if inputInterface is not None:
            inputInterface.setMode(INPUT.MODES.GUI)

        window.openTextInput(
            prompt="Enter text",
            initialText=self.__lastFocusValue,
            onSubmit=onSubmit,
            onCancel=restoreWebMode,
        )

    async def back(self):
        """Browser-like RETURN: leave player-controls navigation, then exit fullscreen, then
        history-back, then close the page. Returns True while handled in-page so
        InputInterface keeps WEB mode active."""
        if self.__playerControlsMode:
            # Back out of controls navigation into seek mode first, mirroring a real player's
            # controls fading back out; only a second RETURN goes further than this.
            self.__playerControlsMode = False
            inputInterface = self.getInputInterface()
            if inputInterface is not None:
                inputInterface.hide()
            return True

        if self.__pageFullscreen:
            # The dedicated web action - not a synthetic Escape key event - is what actually
            # reaches Chromium's fullscreen-exit handling; escape alone was a silent no-op.
            self.__view.page().triggerAction(QWebEnginePage.ExitFullScreen)
            # Also forward Escape in case the site layers its own non-Fullscreen-API overlay
            # (theatre mode, a settings menu) on top that only listens for a real keydown.
            self._forwardKey(Qt.Key_Escape)
            return True

        history = self.__view.history()
        # Never history-back into the about:blank the view idles on between tiles.
        if history.canGoBack() and history.backItem().url().toString() not in ("", "about:blank"):
            self.__view.back()
            return True
        await self.closeAndReturnHome()
        return False

    def debugPage(self, reason=None):
        """Log a diagnostic snapshot of the page (MENU-button hook; /webdebug has full CDP)."""
        url = self.__view.url().toString()

        def logSnapshot(state):
            player = (state or {}).get("player") or {}
            focus = (state or {}).get("focus") or {}
            logger.info(
                f'Page debug snapshot "{url}"',
                url=url,
                reason=reason,
                nav_helpers_present=state is not None,
                player_active=bool(player.get("active")),
                player_controls_mode=self.__playerControlsMode,
                page_fullscreen=self.__pageFullscreen,
                video_coverage=round(player.get("coverage", 0) or 0, 3),
                focus_editable=bool(focus.get("editable")),
                history_can_go_back=self.__view.history().canGoBack(),
            )

        self._runJs("window.__broNav && window.__broNav.state();", logSnapshot)

    async def closeAndReturnHome(self):
        url = self.__view.url().toString()
        logger.info(f'Shutting down webpage "{url}"', url=url)
        self.__view.stop()
        if self.__incognitoProfile is not None:
            oldProfile = self.__incognitoProfile
            defaultProfile = QWebEngineProfile.defaultProfile()
            _configureWebProfile(defaultProfile)
            oldPage = self._replacePage(self._makePage(defaultProfile))
            self.__incognitoProfile = None
            self._retireProfileAfterPageDelete(oldProfile, oldPage)
        self.__lastFocusRect = None
        self.__isEditableFocus = False
        self.__playerActive = False
        self.__playerControlsMode = False
        self.__pageFullscreen = False
        self.__view.setUrl(QUrl("about:blank"))
        self.hide()
        self._setWindowTab()

webInterface = WebInterface()