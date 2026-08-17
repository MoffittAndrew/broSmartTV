// Buttons mirror globals.py INPUT constants; keys mirror INPUT.LOOKUP (Qt app) plus
// remote_emulator.py's VOL_UP/VOL_DOWN/MIC bindings (not present in INPUT.LOOKUP).
const BUTTONS = [
  { name: "POWER", key: "KeyQ" },
  { name: "HOME", key: "Space" },
  { name: "SELECT", key: "Enter" },
  { name: "NAV_UP", key: "ArrowUp" },
  { name: "NAV_RIGHT", key: "ArrowRight" },
  { name: "NAV_DOWN", key: "ArrowDown" },
  { name: "NAV_LEFT", key: "ArrowLeft" },
  { name: "MENU", key: "Tab" },
  { name: "RETURN", key: "Escape" },
  { name: "VOL_UP", key: "PageUp" },
  { name: "VOL_DOWN", key: "PageDown" },
  { name: "MIC", key: "F1" },
];

const keyToButton = new Map(BUTTONS.map((b) => [b.key, b.name]));
// Tracks currently-pressed buttons so a stray keyup/pointerup can't send a duplicate release.
const pressedButtons = new Set();

async function sendInput(button, state) {
  try {
    await fetch("/input", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ button, state }),
    });
  } catch (err) {
    console.error(`Failed to send ${state} for ${button}`, err);
  }
}

function press(button) {
  if (pressedButtons.has(button)) return;
  pressedButtons.add(button);
  sendInput(button, "press");
}

function release(button) {
  if (!pressedButtons.has(button)) return;
  pressedButtons.delete(button);
  sendInput(button, "release");
}

document.querySelectorAll("[data-button]").forEach((el) => {
  const button = el.dataset.button;
  el.addEventListener("pointerdown", () => press(button));
  el.addEventListener("pointerup", () => release(button));
  el.addEventListener("pointerleave", () => release(button));
  el.addEventListener("pointercancel", () => release(button));
});

window.addEventListener("keydown", (event) => {
  const button = keyToButton.get(event.code);
  if (!button) return;
  event.preventDefault(); // stop space/tab/arrows from scrolling or shifting focus
  if (event.repeat) return;
  press(button);
});

window.addEventListener("keyup", (event) => {
  const button = keyToButton.get(event.code);
  if (!button) return;
  event.preventDefault();
  release(button);
});
