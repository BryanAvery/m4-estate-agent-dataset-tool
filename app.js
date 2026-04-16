const STORAGE_KEY = 'm4_estate_records_v1';
const TOWNS_KEY = 'm4_towns_v1';

const DEFAULT_TOWNS = [
  'Reading', 'Slough', 'Maidenhead', 'Newbury', 'Swindon', 'Chippenham', 'Bath', 'Bristol'
];

const STATUSES = ['New', 'Reviewed', 'Contacted', 'Follow-up', 'Not suitable'];

const state = {
  records: load(STORAGE_KEY, []),
  towns: load(TOWNS_KEY, DEFAULT_TOWNS),
  sortKey: 'dateCaptured',
  sortAsc: false
};

const el = {
  form: byId('recordForm'),
  formTitle: byId('formTitle'),
  recordId: byId('recordId'),
  businessName: byId('businessName'),
  location: byId('location'),
  postcode: byId('postcode'),
  phone: byId('phone'),
  email: byId('email'),
  website: byId('website'),
  services: byId('services'),
  status: byId('status'),
  sourceUrl: byId('sourceUrl'),
  dateCaptured: byId('dateCaptured'),
  notes: byId('notes'),
  cancelEdit: byId('cancelEdit'),
  formMessage: byId('formMessage'),
  recordsTbody: byId('recordsTbody'),
  rowTemplate: byId('rowTemplate'),
  searchInput: byId('searchInput'),
  filterTown: byId('filterTown'),
  filterService: byId('filterService'),
  filterStatus: byId('filterStatus'),
  exportCsvBtn: byId('exportCsvBtn'),
  importCsvInput: byId('importCsvInput'),
  qualitySummary: byId('qualitySummary'),
  newTown: byId('newTown'),
  addTownBtn: byId('addTownBtn'),
  townList: byId('townList')
};

init();

function init() {
  el.dateCaptured.value = today();
  hydrateTownSelectors();
  hydrateStatusFilter();
  renderTownPills();
  wireEvents();
  render();
}

function wireEvents() {
  el.form.addEventListener('submit', onSubmitRecord);
  el.cancelEdit.addEventListener('click', resetForm);
  el.searchInput.addEventListener('input', render);
  el.filterTown.addEventListener('change', render);
  el.filterService.addEventListener('change', render);
  el.filterStatus.addEventListener('change', render);
  el.exportCsvBtn.addEventListener('click', exportCsv);
  el.importCsvInput.addEventListener('change', importCsv);
  el.addTownBtn.addEventListener('click', addTown);
  document.querySelectorAll('th[data-sort]').forEach((th) => {
    th.addEventListener('click', () => {
      const key = th.dataset.sort;
      state.sortAsc = state.sortKey === key ? !state.sortAsc : true;
      state.sortKey = key;
      render();
    });
  });
}

function onSubmitRecord(e) {
  e.preventDefault();
  const record = readForm();
  const err = validateRecord(record);
  if (err) return setFormMessage(err);

  if (el.recordId.value) {
    state.records = state.records.map((r) => (r.id === el.recordId.value ? { ...record, id: r.id } : r));
    setFormMessage('Record updated.', false);
  } else {
    state.records.push({ ...record, id: crypto.randomUUID() });
    setFormMessage('Record added.', false);
  }

  persist();
  resetForm();
  render();
}

function readForm() {
  return {
    businessName: el.businessName.value.trim(),
    location: el.location.value,
    postcode: el.postcode.value.trim(),
    phone: el.phone.value.trim(),
    email: el.email.value.trim(),
    website: normalizeUrl(el.website.value.trim()),
    services: selectedMulti(el.services),
    status: el.status.value,
    sourceUrl: normalizeUrl(el.sourceUrl.value.trim()),
    dateCaptured: el.dateCaptured.value || today(),
    notes: el.notes.value.trim()
  };
}

function validateRecord(record) {
  if (!record.businessName) return 'Business name is required.';
  if (!record.location) return 'Location is required.';
  if (record.email && !/^\S+@\S+\.\S+$/.test(record.email)) return 'Email format looks invalid.';
  if (record.website && !isUrl(record.website)) return 'Website URL is invalid.';
  if (record.sourceUrl && !isUrl(record.sourceUrl)) return 'Source URL is invalid.';
  return null;
}

function render() {
  const filtered = getFilteredRecords();
  renderRows(filtered);
  renderQualitySummary();
  hydrateServiceFilter();
  hydrateTownSelectors();
}

function getFilteredRecords() {
  const q = el.searchInput.value.trim().toLowerCase();
  return [...state.records]
    .filter((r) => !el.filterTown.value || r.location === el.filterTown.value)
    .filter((r) => !el.filterStatus.value || r.status === el.filterStatus.value)
    .filter((r) => !el.filterService.value || r.services.includes(el.filterService.value))
    .filter((r) => {
      if (!q) return true;
      return [r.businessName, r.location, r.postcode, r.website, r.email, r.phone, r.notes]
        .join(' ')
        .toLowerCase()
        .includes(q);
    })
    .sort((a, b) => {
      const av = String(a[state.sortKey] || '').toLowerCase();
      const bv = String(b[state.sortKey] || '').toLowerCase();
      return state.sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
    });
}

function renderRows(records) {
  const duplicateIds = findDuplicateIds();
  el.recordsTbody.innerHTML = '';

  records.forEach((r) => {
    const row = el.rowTemplate.content.firstElementChild.cloneNode(true);
    for (const td of row.querySelectorAll('td[data-k]')) {
      const key = td.dataset.k;
      let value = r[key] ?? '';
      if (key === 'services') value = r.services.join(', ');
      if ((key === 'website' || key === 'sourceUrl') && value) {
        td.innerHTML = `<a href="${escapeHtml(value)}" target="_blank" rel="noopener">${escapeHtml(value)}</a>`;
      } else {
        td.textContent = value;
      }
    }

    if (duplicateIds.has(r.id)) {
      row.firstElementChild.innerHTML += ' <span class="tag-duplicate">(Possible duplicate)</span>';
    }

    const actions = row.querySelector('.row-actions');
    const editBtn = actionBtn('Edit', () => startEdit(r));
    const deleteBtn = actionBtn('Delete', () => deleteRecord(r.id));
    actions.append(editBtn, deleteBtn);

    el.recordsTbody.appendChild(row);
  });
}

function renderQualitySummary() {
  const duplicateCount = findDuplicateIds().size;
  const missingEmail = state.records.filter((r) => !r.email).length;
  const missingPhone = state.records.filter((r) => !r.phone).length;
  el.qualitySummary.textContent = `Total records: ${state.records.length} | Possible duplicates: ${duplicateCount} | Missing email: ${missingEmail} | Missing phone: ${missingPhone}`;
}

function findDuplicateIds() {
  const map = new Map();
  const dupes = new Set();
  state.records.forEach((r) => {
    const key = [
      normalize(r.businessName),
      normalize(r.location),
      normalize(r.postcode),
      normalize(r.website)
    ].join('|');
    if (!key.replace(/\|/g, '')) return;
    if (map.has(key)) {
      dupes.add(r.id);
      dupes.add(map.get(key));
    } else {
      map.set(key, r.id);
    }
  });
  return dupes;
}

function startEdit(record) {
  el.formTitle.textContent = 'Edit Estate Agent';
  el.recordId.value = record.id;
  el.businessName.value = record.businessName;
  el.location.value = record.location;
  el.postcode.value = record.postcode;
  el.phone.value = record.phone;
  el.email.value = record.email;
  el.website.value = record.website;
  Array.from(el.services.options).forEach((o) => (o.selected = record.services.includes(o.value)));
  el.status.value = record.status;
  el.sourceUrl.value = record.sourceUrl;
  el.dateCaptured.value = record.dateCaptured;
  el.notes.value = record.notes;
  el.cancelEdit.hidden = false;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function resetForm() {
  el.form.reset();
  el.dateCaptured.value = today();
  el.recordId.value = '';
  el.formTitle.textContent = 'Add Estate Agent';
  el.cancelEdit.hidden = true;
}

function deleteRecord(id) {
  if (!confirm('Delete this record?')) return;
  state.records = state.records.filter((r) => r.id !== id);
  persist();
  render();
}

function addTown() {
  const town = el.newTown.value.trim();
  if (!town) return;
  if (state.towns.some((t) => normalize(t) === normalize(town))) {
    el.newTown.value = '';
    return;
  }
  state.towns.push(town);
  state.towns.sort((a, b) => a.localeCompare(b));
  persist();
  renderTownPills();
  hydrateTownSelectors();
  el.newTown.value = '';
}

function removeTown(town) {
  const isUsed = state.records.some((r) => r.location === town);
  if (isUsed) return alert('Cannot remove a town that is used by existing records.');
  state.towns = state.towns.filter((t) => t !== town);
  persist();
  renderTownPills();
  hydrateTownSelectors();
}

function renderTownPills() {
  el.townList.innerHTML = '';
  state.towns.forEach((town) => {
    const li = document.createElement('li');
    li.className = 'pill';
    li.innerHTML = `<span>${escapeHtml(town)}</span>`;
    const btn = actionBtn('×', () => removeTown(town));
    li.appendChild(btn);
    el.townList.appendChild(li);
  });
}

function hydrateTownSelectors() {
  refillSelect(el.location, state.towns, { required: true });
  refillSelect(el.filterTown, state.towns, { keepFirst: true });
}

function hydrateServiceFilter() {
  const services = [...new Set(state.records.flatMap((r) => r.services))].sort();
  refillSelect(el.filterService, services, { keepFirst: true });
}

function hydrateStatusFilter() {
  refillSelect(el.filterStatus, STATUSES, { keepFirst: true });
}

function refillSelect(select, options, config = {}) {
  const prev = select.value;
  const first = config.keepFirst ? select.options[0]?.outerHTML : '';
  select.innerHTML = first;
  options.forEach((opt) => {
    const option = document.createElement('option');
    option.value = opt;
    option.textContent = opt;
    select.appendChild(option);
  });
  if (options.includes(prev)) select.value = prev;
  else if (config.required && options[0]) select.value = options[0];
}

function exportCsv() {
  const header = ['businessName', 'location', 'postcode', 'phone', 'email', 'website', 'services', 'notes', 'sourceUrl', 'dateCaptured', 'status'];
  const rows = state.records.map((r) => header.map((k) => (k === 'services' ? r.services.join('|') : r[k] || '')));
  const csv = [header, ...rows]
    .map((row) => row.map(csvCell).join(','))
    .join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `m4-estate-agents-${today()}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function importCsv(e) {
  const [file] = e.target.files;
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const rows = parseCsv(String(reader.result));
    const [header, ...data] = rows;
    const idx = Object.fromEntries(header.map((h, i) => [h, i]));
    const imported = data
      .filter((r) => r.length)
      .map((r) => ({
        id: crypto.randomUUID(),
        businessName: (r[idx.businessName] || '').trim(),
        location: (r[idx.location] || '').trim(),
        postcode: (r[idx.postcode] || '').trim(),
        phone: (r[idx.phone] || '').trim(),
        email: (r[idx.email] || '').trim(),
        website: normalizeUrl((r[idx.website] || '').trim()),
        services: (r[idx.services] || '').split('|').map((x) => x.trim()).filter(Boolean),
        notes: (r[idx.notes] || '').trim(),
        sourceUrl: normalizeUrl((r[idx.sourceUrl] || '').trim()),
        dateCaptured: (r[idx.dateCaptured] || today()).trim(),
        status: (r[idx.status] || 'New').trim()
      }))
      .filter((r) => r.businessName && r.location);

    state.records.push(...imported);
    persist();
    render();
    setFormMessage(`Imported ${imported.length} records.`, false);
    e.target.value = '';
  };
  reader.readAsText(file);
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = '';
  let q = false;

  for (let i = 0; i < text.length; i += 1) {
    const c = text[i];
    const n = text[i + 1];
    if (c === '"') {
      if (q && n === '"') {
        cell += '"';
        i += 1;
      } else {
        q = !q;
      }
    } else if (c === ',' && !q) {
      row.push(cell);
      cell = '';
    } else if ((c === '\n' || c === '\r') && !q) {
      if (c === '\r' && n === '\n') i += 1;
      row.push(cell);
      rows.push(row);
      row = [];
      cell = '';
    } else {
      cell += c;
    }
  }

  if (cell || row.length) {
    row.push(cell);
    rows.push(row);
  }

  return rows;
}

function selectedMulti(select) {
  return Array.from(select.selectedOptions).map((o) => o.value);
}

function actionBtn(label, onClick) {
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = label;
  button.addEventListener('click', onClick);
  return button;
}

function setFormMessage(text, isError = true) {
  el.formMessage.textContent = text;
  el.formMessage.style.color = isError ? 'var(--danger)' : 'var(--muted)';
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state.records));
  localStorage.setItem(TOWNS_KEY, JSON.stringify(state.towns));
}

function load(key, fallback) {
  try {
    const value = JSON.parse(localStorage.getItem(key));
    return value ?? fallback;
  } catch {
    return fallback;
  }
}

function normalize(value) {
  return String(value || '').trim().toLowerCase();
}

function normalizeUrl(value) {
  if (!value) return '';
  if (/^https?:\/\//i.test(value)) return value;
  return `https://${value}`;
}

function isUrl(value) {
  try {
    new URL(value);
    return true;
  } catch {
    return false;
  }
}

function csvCell(value) {
  const text = String(value ?? '');
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

function byId(id) {
  return document.getElementById(id);
}

function today() {
  return new Date().toISOString().slice(0, 10);
}
