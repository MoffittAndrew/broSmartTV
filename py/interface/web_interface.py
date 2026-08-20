print("Importing web interface...")

import json

from globals import DISPLAY, INPUT
from ui.gui import CustomQWidget

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage

# Custom directional-navigation heuristic (rather than the WICG spatial-navigation
# polyfill) so we avoid a runtime network fetch and third-party licensing to vendor.
# Finds focusable elements and scores them by direction/overlap relative to the
# currently focused element, so NAV works generically across sites without
# per-site element locators (unlike the old Selenium relative-locator approach).
_NAV_HELPERS_JS = """
(function() {
    if (window.__broNav) { return; }
    window.__broNav = {
        _focusable: function() {
            return Array.prototype.slice.call(document.querySelectorAll(
                'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"]), [contenteditable="true"]'
            )).filter(function(el) {
                var rect = el.getBoundingClientRect();
                var style = window.getComputedStyle(el);
                return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
            });
        },
        move: function(direction) {
            var current = (document.activeElement && document.activeElement !== document.body) ? document.activeElement : null;
            var currentRect = current ? current.getBoundingClientRect() : { left: 0, top: 0, right: 0, bottom: 0 };
            var best = null;
            var bestScore = Infinity;
            window.__broNav._focusable().forEach(function(el) {
                if (el === current) { return; }
                var rect = el.getBoundingClientRect();
                var dx = rect.left - currentRect.left;
                var dy = rect.top - currentRect.top;
                var primary, inDirection;
                if (direction === 'up') { primary = -dy; inDirection = rect.bottom <= currentRect.top + 1; }
                else if (direction === 'down') { primary = dy; inDirection = rect.top >= currentRect.bottom - 1; }
                else if (direction === 'left') { primary = -dx; inDirection = rect.right <= currentRect.left + 1; }
                else { primary = dx; inDirection = rect.left >= currentRect.right - 1; }
                if (!inDirection || primary < 0) { return; }
                var perpendicular = (direction === 'up' || direction === 'down') ? Math.abs(dx) : Math.abs(dy);
                var score = primary + perpendicular * 2;
                if (score < bestScore) { bestScore = score; best = el; }
            });
            if (best) { best.focus(); }
            return window.__broNav.focusInfo();
        },
        focusFirst: function() {
            var candidates = window.__broNav._focusable();
            if (candidates.length > 0) { candidates[0].focus(); }
            return window.__broNav.focusInfo();
        },
        focusInfo: function() {
            var el = document.activeElement;
            if (!el || el === document.body) { return null; }
            var rect = el.getBoundingClientRect();
            var editableTag = el.tagName === 'INPUT' || el.tagName === 'TEXTAREA';
            var editableType = !el.type || ['button', 'submit', 'checkbox', 'radio', 'range', 'color', 'file'].indexOf(el.type) === -1;
            return {
                x: rect.left, y: rect.top, width: rect.width, height: rect.height,
                editable: (editableTag && editableType) || el.isContentEditable === true,
                value: el.isContentEditable ? el.textContent : (el.value || "")
            };
        },
        activate: function() {
            if (document.activeElement) { document.activeElement.click(); }
            return window.__broNav.focusInfo();
        },
        setValue: function(text) {
            var el = document.activeElement;
            if (!el) { return; }
            if (el.isContentEditable) { el.textContent = text; } else { el.value = text; }
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            return window.__broNav.focusInfo();
        }
    };
})();
"""

_NAV_DIRECTION_JS = {
    INPUT.NAV_UP: "up",
    INPUT.NAV_RIGHT: "right",
    INPUT.NAV_DOWN: "down",
    INPUT.NAV_LEFT: "left",
}


class FocusedElement:
    """Mirrors the `.rect` dict contract InputInterface already expects from non-Button selections."""
    def __init__(self, rect):
        self.rect = rect


class WebInterface(CustomQWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__inputInterface = None
        self.__incognitoProfile = None
        self.__retiredProfiles = []
        self.__lastFocusRect = None
        self.__isEditableFocus = False
        self.__lastFocusValue = ""

        self.__view = QWebEngineView(self)
        self.__view.setFixedSize(DISPLAY.WIDTH, DISPLAY.HEIGHT)
        self.__view.loadFinished.connect(self._onLoadFinished)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__view)

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
        if oldPage is not None:
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

    def openURL(self, url, incognito=False):
        if incognito:
            oldProfile = self.__incognitoProfile
            # A profile constructed without a storage name is off-the-record (mirrors old --incognito flag).
            self.__incognitoProfile = QWebEngineProfile()
            oldPage = self._replacePage(QWebEnginePage(self.__incognitoProfile, self.__view))
            self._retireProfileAfterPageDelete(oldProfile, oldPage)
        elif self.__incognitoProfile is not None:
            oldProfile = self.__incognitoProfile
            oldPage = self._replacePage(QWebEnginePage(QWebEngineProfile.defaultProfile(), self.__view))
            self.__incognitoProfile = None
            self._retireProfileAfterPageDelete(oldProfile, oldPage)

        self.__lastFocusRect = None
        self.__view.load(QUrl(url))

        inputInterface = self.getInputInterface()
        if inputInterface is not None:
            inputInterface.setWebMode(self)
        self._setWindowTab(self)

    def _onLoadFinished(self, ok):
        if not ok:
            return
        self.__view.page().runJavaScript(_NAV_HELPERS_JS)
        self._runJs("window.__broNav.focusFirst();")

    def _runJs(self, script):
        self.__view.page().runJavaScript(script, self._applyFocusInfo)

    def _applyFocusInfo(self, result):
        if not result:
            return
        # getBoundingClientRect() returns floats; Qt's setGeometry() only accepts ints.
        self.__lastFocusRect = {
            "x": int(result["x"]),
            "y": int(result["y"]),
            "width": int(result["width"]),
            "height": int(result["height"]),
        }
        self.__isEditableFocus = bool(result.get("editable"))
        self.__lastFocusValue = result.get("value") or ""
        inputInterface = self.getInputInterface()
        if inputInterface is not None:
            inputInterface.setSelectedButton(FocusedElement(self.__lastFocusRect))

    async def navigate(self, direction):
        jsDirection = _NAV_DIRECTION_JS.get(direction)
        if jsDirection is not None:
            self._runJs(f"window.__broNav.move('{jsDirection}');")

    async def select(self):
        if self.__isEditableFocus:
            self._openKeyboardForFocusedField()
        else:
            self._runJs("window.__broNav.activate();")

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
            self._runJs(f"window.__broNav.setValue({json.dumps(text)});")

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

    async def closeAndReturnHome(self):
        self.__view.stop()
        if self.__incognitoProfile is not None:
            oldProfile = self.__incognitoProfile
            oldPage = self._replacePage(QWebEnginePage(QWebEngineProfile.defaultProfile(), self.__view))
            self.__incognitoProfile = None
            self._retireProfileAfterPageDelete(oldProfile, oldPage)
        self.__view.setUrl(QUrl("about:blank"))
        self._setWindowTab()

webInterface = WebInterface()