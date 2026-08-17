// Minimal "turn bro on" flow for the standby (off) server - kept separate from
// screen-share.js so this lightweight page never loads the RTC-heavy module.

const POWER_STATUS_POLL_MS = 1500;

function initStandbyApp(ui = {}) {
  const powerOnBtn = ui.powerOnBtn ?? document.getElementById('powerOnBtn');
  const statusDiv = ui.statusDiv ?? document.getElementById('status');

  if (!powerOnBtn || !statusDiv) {
    return null;
  }

  let polling = false;

  async function pollUntilOn() {
    if (polling) {
      return;
    }
    polling = true;

    while (true) {
      try {
        const res = await fetch('/power-status');
        if (res.ok) {
          const data = await res.json();
          if (data.on) {
            statusDiv.textContent = 'bro is on, taking you there...';
            window.location.reload();
            return;
          }
        }
      } catch (err) {
        // Expected during the brief standby->full server swap; keep retrying.
        console.warn('Power status check failed, retrying:', err);
      }

      await new Promise((resolve) => setTimeout(resolve, POWER_STATUS_POLL_MS));
    }
  }

  powerOnBtn.onclick = async () => {
    powerOnBtn.disabled = true;
    statusDiv.textContent = 'turning bro on...';

    try {
      await fetch('/power-on', { method: 'POST' });
    } catch (err) {
      console.error('Power-on request failed:', err);
    }

    pollUntilOn();
  };

  return { powerOnBtn, statusDiv };
}

initStandbyApp();
