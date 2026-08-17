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

// Crop padding in SVG user-units (not screen pixels), added around the button group's bbox.
const CROP_PADDING = 12;

async function loadRemoteSvg() {
  const container = document.getElementById("remote-buttons-container");
  if (!container) return;

  const response = await fetch("./remote-buttons.svg");
  const markup = await response.text();
  const doc = new DOMParser().parseFromString(markup, "image/svg+xml");
  const svg = doc.documentElement;

  // Responsive sizing so the container/CSS controls on-page placement, not the SVG's own pixel dims.
  svg.removeAttribute("height");
  svg.setAttribute("width", "100%");
  svg.setAttribute("preserveAspectRatio", "xMidYMid meet");

  container.replaceChildren(svg);

  // Crop empty margins by fitting the viewBox to the actual button artwork, not hardcoded coordinates,
  // so this keeps working if the SVG art is ever moved/resized.
  const group = svg.querySelector("#remote-buttons-group");
  if (group) {
    const box = group.getBBox();
    svg.setAttribute(
      "viewBox",
      `${box.x - CROP_PADDING} ${box.y - CROP_PADDING} ${box.width + CROP_PADDING * 2} ${box.height + CROP_PADDING * 2}`
    );
  }

  wireButtonShapes(svg);
}

function wireButtonShapes(svg) {
  svg.querySelectorAll("[data-button]").forEach((el) => {
    const button = el.dataset.button;

    el.addEventListener("pointerdown", () => {
      el.classList.add("pressed");
      press(button);
    });
    const releaseShape = () => {
      el.classList.remove("pressed");
      release(button);
    };
    el.addEventListener("pointerup", releaseShape);
    el.addEventListener("pointerleave", releaseShape);
    el.addEventListener("pointercancel", releaseShape);

    el.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault(); // stop space from scrolling the page
      if (event.repeat) return;
      el.classList.add("pressed");
      press(button);
    });
    el.addEventListener("keyup", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      releaseShape();
    });
  });
}

loadRemoteSvg();

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
