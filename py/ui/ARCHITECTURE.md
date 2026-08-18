# GUI Architecture

## Goal
The GUI is designed to be built from reusable custom sections and tools, so new screens can be assembled by declaring what appears and where it goes with minimal bespoke layout code.

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

## Section Primitives
`ui/tools/section.py` provides generic containers that accept any widget.

- `VSection`: vertical stacking and automatic up/down nav links for navigable children.
- `HSection`: horizontal stacking and automatic left/right nav links.
- `GridSection`: row-major placement with automatic horizontal and vertical nav links.

`GridSection` edge behavior defaults to `edgePolicy="last"`, preserving tile-grid behavior for ragged rows.

## Navigation Rules
- Navigation relies on directional links set on interactive widgets.
- Section primitives auto-wire links where possible.
- Screen code should only add explicit overrides for special transitions (for example, navbar <-> body, overlay back/close).

## Button Callbacks
`ui/tools/button.py` supports three independent, optional callbacks per `Button`:
- `clickCallback` - fires on `Button.click()` when SELECT (Enter) is pressed on a focused button. This is the primary action.
- `menuCallback` - fires on `Button.menu()` when MENU (Tab) is pressed on a focused button. Used for secondary/contextual actions (for example, CAPS toggle in the on-screen keyboard). Omit entirely when a button has no secondary action.
- `returnCallback` - fires on `Button.back()` when RETURN (Esc) is pressed on a focused button. Used to back out of a screen/overlay without performing the primary action.

A button can freely mix and match these; a menu/list option button, for example, may only need `clickCallback` and `returnCallback`.

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

## Current First-Wave Migrations
- Home/navbar/tile-grid now rely on section primitives.
- On-screen keyboard uses `GridSection` for key matrix and `HSection` for control row.
- Settings and wifi overlay are aligned to global spacing tokens and section composition.

## Future Work
- Add a shared screen-factory helper for dict specs.
- Migrate search/edit/filter screens fully onto section primitives.
- Add unit tests for section sizing and navigation mesh generation.
