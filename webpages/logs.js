const MAX_VISIBLE_RECORDS = 1000;
const filterNames = ['category', 'level', 'source'];

const state = {
  filters: {
    category: new Set(),
    level: new Set(),
    source: new Set(),
  },
  available: {
    category: new Set(),
    level: new Set(),
    source: new Set(),
  },
  eventSource: null,
  historicalFile: '',
  view: 'live',
  followLatest: true,
};

const elements = {
  form: document.querySelector('#log-filters'),
  category: document.querySelector('#category-filter'),
  level: document.querySelector('#level-filter'),
  source: document.querySelector('#source-filter'),
  clear: document.querySelector('#clear-filters'),
  status: document.querySelector('#connection-status'),
  view: document.querySelector('#log-view'),
  historyControls: document.querySelector('#history-controls'),
  viewport: document.querySelector('#log-viewport'),
  records: document.querySelector('#records'),
  files: document.querySelector('#session-files'),
  refreshFiles: document.querySelector('#refresh-files'),
};

function queryForFilters() {
  const query = new URLSearchParams();
  filterNames.forEach((name) => {
    state.filters[name].forEach((value) => query.append(name, value));
  });
  return query;
}

function recordMatches(record) {
  return filterNames.every((name) => {
    const selected = state.filters[name];
    return selected.size === 0 || selected.has(name === 'level' ? record[name].toUpperCase() : record[name]);
  });
}

function setOptions(select, values, selectedValues) {
  const sorted = [...values].sort();
  select.replaceChildren();
  sorted.forEach((value) => {
    const label = document.createElement('label');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = value;
    checkbox.dataset.filterValue = value;
    checkbox.checked = selectedValues.has(value);
    label.appendChild(checkbox);
    label.append(` ${value}`);
    select.appendChild(label);
  });
}

function updateFilterOptions(records) {
  const values = {
    category: new Set(),
    level: new Set(),
    source: new Set(),
  };
  records.forEach((record) => {
    if (record.category) values.category.add(record.category);
    if (record.level) values.level.add(record.level.toUpperCase());
    if (record.source) values.source.add(record.source);
  });
  values.category.forEach((value) => state.available.category.add(value));
  values.level.forEach((value) => state.available.level.add(value));
  values.source.forEach((value) => state.available.source.add(value));
  setOptions(elements.category, state.available.category, state.filters.category);
  setOptions(elements.level, state.available.level, state.filters.level);
  setOptions(elements.source, state.available.source, state.filters.source);
}

function readFilters() {
  state.filters.category = readFilterGroup(elements.category);
  state.filters.level = readFilterGroup(elements.level, true);
  state.filters.source = readFilterGroup(elements.source);
}

function readFilterGroup(group, uppercase = false) {
  return new Set(
    [...group.querySelectorAll('input[type="checkbox"]:checked')]
      .map((checkbox) => uppercase ? checkbox.value.toUpperCase() : checkbox.value),
  );
}

function isAtLatest() {
  const distanceFromBottom = elements.viewport.scrollHeight
    - elements.viewport.scrollTop
    - elements.viewport.clientHeight;
  return distanceFromBottom <= 8;
}

function scrollToLatest() {
  elements.viewport.scrollTop = elements.viewport.scrollHeight;
}

function appendRecord(record) {
  if (!recordMatches(record)) return;

  const item = document.createElement('li');
  const summary = document.createElement('span');
  summary.textContent = `${record.timestamp || ''} [${record.level || ''}] [${record.source || ''}:${record.category || ''}] ${record.message || ''}`;
  item.appendChild(summary);

  if (record.fields && Object.keys(record.fields).length > 0) {
    const fields = document.createElement('pre');
    fields.textContent = JSON.stringify(record.fields, null, 2);
    item.appendChild(fields);
  }

  elements.records.appendChild(item);
  while (elements.records.children.length > MAX_VISIBLE_RECORDS) {
    elements.records.removeChild(elements.records.firstChild);
  }
  if (state.view === 'live' && state.followLatest) scrollToLatest();
}

function replaceRecords(records, shouldFollow = false) {
  elements.records.replaceChildren();
  records.forEach((record) => appendRecord(record));
  if (shouldFollow) scrollToLatest();
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`request failed (${response.status})`);
  return response.json();
}

function closeLiveStream() {
  if (state.eventSource) {
    state.eventSource.close();
    state.eventSource = null;
  }
}

async function loadLiveHistory() {
  const payload = await fetchJson(`/logs/api/history?${queryForFilters()}`);
  replaceRecords(payload.records || [], true);
}

async function loadFilterOptions() {
  const payload = await fetchJson('/logs/api/options');
  state.available.category = new Set(payload.categories || []);
  state.available.level = new Set((payload.levels || []).map((level) => level.toUpperCase()));
  state.available.source = new Set(payload.sources || []);
  setOptions(elements.category, state.available.category, state.filters.category);
  setOptions(elements.level, state.available.level, state.filters.level);
  setOptions(elements.source, state.available.source, state.filters.source);
}

function connectLiveStream() {
  closeLiveStream();
  state.eventSource = new EventSource(`/logs/api/stream?${queryForFilters()}`);
  state.eventSource.onopen = () => {
    elements.status.textContent = 'live';
  };
  state.eventSource.onmessage = (event) => {
    try {
      const record = JSON.parse(event.data);
      updateFilterOptions([record]);
      appendRecord(record);
    } catch (error) {
      elements.status.textContent = 'received an invalid log record';
    }
  };
  state.eventSource.onerror = () => {
    elements.status.textContent = 'connection lost; retrying...';
  };
}

async function applyFilters() {
  readFilters();
  try {
    if (state.view === 'live') {
      closeLiveStream();
      await loadLiveHistory();
      connectLiveStream();
    } else if (state.historicalFile) {
      await loadHistoricalFile(state.historicalFile);
    }
  } catch (error) {
    elements.status.textContent = error.message;
  }
}

async function loadFiles() {
  const payload = await fetchJson('/logs/api/files');
  const previous = state.historicalFile;
  elements.files.replaceChildren();
  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = 'select a session';
  elements.files.appendChild(placeholder);
  (payload.files || []).forEach((file) => {
    const option = document.createElement('option');
    option.value = file.filename;
    option.textContent = `${file.filename} (${file.size} bytes)`;
    elements.files.appendChild(option);
  });
  state.historicalFile = previous;
  elements.files.value = previous;
}

async function loadHistoricalFile(filename) {
  state.historicalFile = filename;
  if (!filename) {
    elements.records.replaceChildren();
    return;
  }
  const payload = await fetchJson(`/logs/api/files/${encodeURIComponent(filename)}?${queryForFilters()}`);
  replaceRecords(payload.records || [], false);
}

async function switchView(view) {
  state.view = view;
  elements.historyControls.hidden = view !== 'history';
  if (view === 'history') {
    closeLiveStream();
    elements.status.textContent = 'historical session';
    if (!state.historicalFile) {
      elements.records.replaceChildren();
      return;
    }
    await loadHistoricalFile(state.historicalFile);
    return;
  }

  state.followLatest = true;
  await loadLiveHistory();
  connectLiveStream();
}

elements.form.addEventListener('submit', (event) => {
  event.preventDefault();
  applyFilters();
});
elements.view.addEventListener('change', () => switchView(elements.view.value).catch((error) => {
  elements.status.textContent = error.message;
}));
filterNames.forEach((name) => {
  elements[name].addEventListener('change', () => {
    state.filters[name] = readFilterGroup(elements[name], name === 'level');
  });
});
elements.viewport.addEventListener('scroll', () => {
  state.followLatest = isAtLatest();
});
elements.clear.addEventListener('click', () => {
  filterNames.forEach((name) => {
    state.filters[name].clear();
  });
  filterNames.forEach((name) => {
    state.filters[name].clear();
    elements[name].querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
      checkbox.checked = false;
    });
  });
  applyFilters();
});
elements.refreshFiles.addEventListener('click', () => loadFiles().catch((error) => {
  elements.status.textContent = error.message;
}));
elements.files.addEventListener('change', () => loadHistoricalFile(elements.files.value).catch((error) => {
  elements.status.textContent = error.message;
}));

Promise.all([loadFilterOptions(), loadLiveHistory(), loadFiles()])
  .then(connectLiveStream)
  .catch((error) => {
    elements.status.textContent = error.message;
  });
