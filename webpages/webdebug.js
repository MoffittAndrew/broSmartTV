// Lists debuggable CDP targets (proxied/rewritten by webserver/webdebug_routes.py) as links into
// the devtools frontend, which the same proxy also fronts so no direct access to the internal
// CDP port is ever needed from the browser.

async function loadTargets() {
  const list = document.getElementById('targets');
  list.replaceChildren();

  let targets;
  try {
    const response = await fetch('/webdebug/json/list');
    if (!response.ok) {
      throw new Error(`status ${response.status}`);
    }
    targets = await response.json();
  } catch (err) {
    const item = document.createElement('li');
    item.textContent = `Failed to load debug targets: ${err}`;
    list.appendChild(item);
    return;
  }

  if (targets.length === 0) {
    const item = document.createElement('li');
    item.textContent = 'No debuggable pages right now.';
    list.appendChild(item);
    return;
  }

  targets.forEach((target) => {
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.href = target.devtoolsFrontendUrl;
    link.textContent = target.title || target.url || target.id;
    item.appendChild(link);
    list.appendChild(item);
  });
}

loadTargets();
