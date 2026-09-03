# GUI Architecture

## Goal
The GUI is designed to be built from reusable custom sections and tools, so new screens can be assembled by declaring what appears and where it goes with minimal bespoke layout code.
- Treat the GUI as a hierarchy of custom sections and tools, not direct Qt primitives at screen level.
- Build screen layouts using `VSection`, `HSection`, and `GridSection` from `py/ui/tools/section.py`.
- Keep screen modules (`py/ui/*.py`) focused on composition of reusable tools and sections.
- Keep `CustomQWidget` and `CustomQLabel` in `py/ui/gui.py` as the only base widget types for new UI components.

## Layered Structure
1. Base widgets in `ui/gui.py`:
- `CustomQWidget`
- `CustomQLabel`

2. Primitive UI tools in `ui/tools/`:
- `Button` and tile/button subclasses
- `VSection`, `HSection`, `GridSection`
- Overlay helpers like `OnScreenKeyboard`, `WifiOverlay`, `MenuOverlay`

3. Screens in `ui/*.py`:
- Compose sections and tool widgets
- Avoid manual Qt layout wiring unless needed for unusual behavior

## Layout Tokens
All spacing and margins should come from `globals.py`:
- `GUI.SPACING.TIGHT`
- `GUI.SPACING.NORMAL`
- `GUI.SPACING.WIDE`
- `GUI.MARGINS.COMPACT`
- `GUI.MARGINS.STANDARD`
- `GUI.MARGINS.OVERLAY`

Do not hardcode new spacing constants in screens/components.
Use these tokens instead of hardcoded layout spacing/margin values in new or refactored UI code.
When adding a new spacing tier, add it to globals first, then consume it from sections/screens.

## Section Primitives
`ui/tools/section.py` provides generic containers that accept any widget.

- `VSection`: vertical stacking and automatic up/down nav links for navigable children.
- `HSection`: horizontal stacking and automatic left/right nav links.
- `GridSection`: row-major placement with automatic horizontal and vertical nav links.

`GridSection` edge behavior defaults to `edgePolicy="last"`, preserving tile-grid behavior for ragged rows.

## Navigation Rules
- Directional navigation must be wired through the button nav links (`setNavUp/Right/Down/Left`).
- Section primitives auto-wire links where possible.
- Screen code should only add explicit overrides for special transitions (for example, navbar <-> body, overlay back/close).
- Preserve tile-grid edge behavior where downward navigation in short rows falls back to the last item of the next row.

## Button Callbacks
`ui/tools/button.py` supports three independent, optional callbacks per `Button`:
- `clickCallback` - fires on `Button.click()` when SELECT (Enter) is pressed on a focused button. This is the primary action.
- `menuCallback` - fires on `Button.menu()` when MENU (Tab) is pressed on a focused button. Used for secondary/contextual actions (for example, CAPS toggle in the on-screen keyboard). Omit entirely when a button has no secondary action.
- `returnCallback` - fires on `Button.back()` when RETURN (Esc) is pressed on a focused button. Used to back out of a screen/overlay without performing the primary action.

A button can freely mix and match these; a menu/list option button, for example, may only need `clickCallback` and `returnCallback`.

`ToggleButton` is a `Button` front end for a boolean owned by its parent screen, overlay, or model. It does not store the boolean itself: keep the source of truth in the owning component and let the button fetch it whenever it draws.

Every `ToggleButton` must define:
- `trueText`: text rendered when the fetched value is truthy.
- `falseText`: text rendered when the fetched value is falsy.
- `fetchValueCallback`: a synchronous callback that returns the current owner-held boolean.

Use the inherited `clickCallback` and, where needed, `menuCallback` to change the owner-held value. These callbacks must be async because `Button.click()` and `Button.menu()` await them. After either callback completes, `ToggleButton` redraws and fetches the value again, keeping its label in sync with the owner.

```python
def _getCapsEnabled(self):
    return self.__capsEnabled

async def _toggleCaps(self):
    self.__capsEnabled = not self.__capsEnabled
    self._applyCapsState()

self.__capsButton = ToggleButton(
    trueText="CAPS ON",
    falseText="CAPS OFF",
    fetchValueCallback=self._getCapsEnabled,
    clickCallback=self._toggleCaps,
    menuCallback=self._toggleCaps,
    returnCallback=self._cancel,
)
```

Do not mirror state in a `ToggleButton` or use the button as the authority for the value. When the owner changes a value outside a button interaction, redraw the affected button so it fetches and displays the updated value.

## MAIN_WINDOW Tab Stacking (StackAll Gotcha)
`CustomQWindow` (`MAIN_WINDOW` in `ui/gui.py`) holds its top-level screens (`homeScreen`, `webInterface`, `bibleVerseScreen`, the on-screen keyboard, the shutdown screen, ...) in a `QStackedLayout` constructed with `setStackingMode(QStackedLayout.StackAll)`.

**This is not the default `QStackedLayout` behavior.** The default mode (`StackOne`) automatically hides every widget except the current one. `StackAll` does not - every widget added via `MAIN_WINDOW.addWidget(...)` stays visible (and keeps receiving paint/layout updates) unless something explicitly hides it. `setTab()`/`setCurrentWidget()` only change *z-order* (which widget is on top) and which widget's `getPrimaryButton()` feeds the input-focus outline - they do **not** hide the widgets being switched away from.

Consequences for any new top-level screen added to `MAIN_WINDOW`:
- **You own your own visibility.** Call `self.show()` when your screen becomes the active tab and `self.hide()` when leaving it. Do this from the screen itself (see `web_interface.py`'s `openURL()` calling `self.show()` and `closeAndReturnHome()` calling `self.hide()`, or `bible_verse_screen.py`'s `showVerse()`/`_onOk()`), not from the caller - keep the show/hide pairing next to the state change that causes it.
- **`homeScreen` is the one exception** - it is never explicitly hidden, since it is the always-present background tab. Every other full-screen tab must be opaque (see below) and explicitly hidden when done, so it stops covering `homeScreen` (or whatever was behind it).
- **Give full-screen tabs an opaque background you can rely on.** A bare `setStyleSheet("background-color: ...")` on a plain `CustomQWidget` subclass does not reliably paint (Qt requires `Qt.WA_StyledBackground` or a custom `paintEvent` for stylesheet backgrounds to actually render on non-standard widget classes). Use `setAutoFillBackground(True)` plus a palette color instead (see `LaunchScreen`, `MAIN_WINDOW` itself, and `bible_verse_screen.py`). Otherwise the "hidden" screen underneath can visibly bleed through even while your screen is topmost.
- **Symptom to recognize:** if two full-screen tabs appear simultaneously overlaid (or a screen you thought you left is still faintly visible), first check that the screen you're leaving/entering actually calls `.hide()`/`.show()` on itself, then check that it has a real opaque background via `setAutoFillBackground` + palette.

## Overlay Recipes
- Full-bleed panel (`WifiOverlay`, `OnScreenKeyboard`): covers the whole screen and replaces its content in place. Use for content-heavy overlays (scrollable lists, keyboards).
- Centered dimmed popup (`MenuOverlay`): dims the whole screen and shows a smaller centered box of options. Use for lightweight choice menus. `MenuOverlay` is intentionally generic - it takes a list of `{"text", "clickCallback"}` option dicts and auto-wires each option's `returnCallback` to close the menu, so it can be reused for any picker, not just git branches.

## Absolute Position Contract
Use `getAbsolutePos()` from custom base widgets. It maps each widget into window coordinates via `mapTo(window, QPoint(0, 0))`.

This should be the standard way to anchor overlays, selection outlines, and diagnostics.

## How To Build A New Screen
1. Create screen class inheriting `CustomQWidget`.
2. Define screen items (buttons, labels, section containers).
3. Compose items using `VSection`, `HSection`, `GridSection`.
4. Use `GUI.SPACING` and `GUI.MARGINS` tokens.
5. Add only required custom nav overrides.
6. Expose `getPrimaryButton()` for input focus handoff.

## Declarative Composition Pattern
Use a Python dict-like structure in the screen module to describe what sections contain, then instantiate widgets from that spec.

Example shape:

```python
spec = {
    "type": "vertical",
    "spacing": GUI.SPACING.NORMAL,
    "children": [
        heading_label,
        status_label,
        action_button,
    ],
}
```

A screen can progressively move from handwritten composition to spec-driven factories while keeping callback logic in Python functions.

## GUI Extension Workflow
- For a new screen, compose sections first (header/content/actions), then attach callbacks.
- For a new grid-like UI (keyboards, lists, tiles), prefer `GridSection` and only add bespoke wiring for special edge cases.
- Keep overlay widgets self-contained and compute absolute placement using the `mapTo(window, QPoint(0, 0))` pattern via custom base widgets.