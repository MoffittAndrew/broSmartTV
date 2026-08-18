const MAX_VISIBLE_RECORDS = 1000;
const filterNames = ['category', 'level', 'source'];

const state = {
  filters: {
    category: new Set(),
    level: new Set(),
    source: new Set(),
  },
  eventSource: null,
  historicalFile: '',
};

const elements = {
  form: document.querySelector('#log-filters'),
  category: document.querySelector('#category-filter'),
  level: document.querySelector('#level-filter'),
  source: document.querySelector('#source-filter'),
  clear: document.querySelector('#clear-filters'),
  status: document.querySelector('#connection-status'),
  live: document.querySelector('#live-records'),
  files: document.querySelector('#session-files'),
  refreshFiles: document.querySelector('#refresh-files'),
  historical: document.querySelector('#historical-records'),
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
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    option.selected = selectedValues.has(value);
    select.appendChild(option);
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
  setOptions(elements.category, values.category, state.filters.category);
  setOptions(elements.level, values.level, state.filters.level);
  setOptions(elements.source, values.source, state.filters.source);
}

function readFilters() {
  state.filters.category = new Set([...elements.category.selectedOptions].map((option) => option.value));
  state.filters.level = new Set([...elements.level.selectedOptions].map((option) => option.value.toUpperCase()));
  state.filters.source = new Set([...elements.source.selectedOptions].map((option) => option.value));
}

function appendRecord(list, record) {
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

  list.appendChild(item);
  while (list.children.length > MAX_VISIBLE_RECORDS) list.removeChild(list.firstChild);
}

function replaceRecords(list, records) {
  list.replaceChildren();
  records.forEach((record) => appendRecord(list, record));
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
  updateFilterOptions(payload.records || []);
  replaceRecords(elements.live, payload.records || []);
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
      appendRecord(elements.live, record);
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
  closeLiveStream();
  try {
    await loadLiveHistory();
    connectLiveStream();
    if (state.historicalFile) await loadHistoricalFile(state.historicalFile);
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
    elements.historical.replaceChildren();
    return;
  }
  const payload = await fetchJson(`/logs/api/files/${encodeURIComponent(filename)}?${queryForFilters()}`);
  replaceRecords(elements.historical, payload.records || []);
}

elements.form.addEventListener('submit', (event) => {
  event.preventDefault();
  applyFilters();
});
elements.clear.addEventListener('click', () => {
  filterNames.forEach((name) => {
    state.filters[name].clear();
  });
  filterNames.forEach((name) => {
    const select = elements[name];
    [...select.options].forEach((option) => {
      option.selected = false;
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

Promise.all([loadLiveHistory(), loadFiles()])
  .then(connectLiveStream)
  .catch((error) => {
    elements.status.textContent = error.message;
  });
