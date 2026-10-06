const API = {
  student: '/api/student',
  parcel: '/api/parcel',
  pickup: '/api/pickup',
  storage: '/api/storage'
};

const state = { students: [], parcels: [], pickups: [], storage: [] };

async function apiFetch(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options
  });
  let data = null;
  try { data = await response.json(); } catch (_) {}
  if (!response.ok) {
    const message = data?.detail || data?.error || `Request failed (${response.status})`;
    throw new Error(message);
  }
  return data;
}

function showToast(message, error = false) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `toast show${error ? ' error' : ''}`;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.className = 'toast', 3000);
}

function esc(value) {
  return String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

function studentName(id) {
  const student = state.students.find(s => Number(s.id) === Number(id));
  return student ? `${student.name} (#${student.id})` : `Student #${id}`;
}

function renderStudentSelects() {
  const options = state.students.length
    ? state.students.map(s => `<option value="${s.id}">${esc(s.name)} (#${s.id})</option>`).join('')
    : '<option value="">No students available</option>';
  document.getElementById('parcelStudent').innerHTML = options;
  document.getElementById('pickupStudent').innerHTML = options;

  const parcelOptions = state.parcels.length
    ? state.parcels.map(p => `<option value="${p.parcel_id}">Parcel #${p.parcel_id} — ${esc(p.tracking_id)}</option>`).join('')
    : '<option value="">No parcels available</option>';
  document.getElementById('pickupParcel').innerHTML = parcelOptions;
}

function renderStudents() {
  const body = document.getElementById('studentsTable');
  body.innerHTML = state.students.length ? state.students.map(s => `
    <tr>
      <td>${s.id}</td><td>${esc(s.name)}</td><td>${esc(s.department)}</td><td>${s.year}</td>
      <td><div class="row-actions"><button class="mini-btn" onclick="editStudent(${s.id})">Edit</button><button class="mini-btn" onclick="deleteStudent(${s.id})">Delete</button></div></td>
    </tr>`).join('') : '<tr><td colspan="5">No students yet.</td></tr>';
}

function renderParcels() {
  const body = document.getElementById('parcelsTable');
  body.innerHTML = state.parcels.length ? state.parcels.map(p => `
    <tr>
      <td>${p.parcel_id}</td><td>${esc(studentName(p.student_id))}</td><td>${esc(p.courier)}</td><td>${esc(p.tracking_id)}</td>
      <td><span class="status-chip">${esc(p.status)}</span></td>
      <td><div class="row-actions"><button class="mini-btn" onclick="editParcel(${p.parcel_id})">Edit</button><button class="mini-btn" onclick="deleteParcel(${p.parcel_id})">Delete</button></div></td>
    </tr>`).join('') : '<tr><td colspan="6">No parcels yet.</td></tr>';
}

function renderPickups() {
  const body = document.getElementById('pickupsTable');
  body.innerHTML = state.pickups.length ? state.pickups.map(p => `
    <tr>
      <td>${p.pickup_id}</td><td>${esc(studentName(p.student_id))}</td><td>#${p.parcel_id}</td>
      <td><span class="status-chip ${p.status === 'PENDING' ? 'pending' : 'completed'}">${esc(p.status)}</span></td>
      <td>${p.status === 'PENDING' ? `<button class="mini-btn" onclick="completePickup(${p.pickup_id})">Complete</button>` : '—'}</td>
    </tr>`).join('') : '<tr><td colspan="5">No pickup requests yet.</td></tr>';
}

function renderStorage() {
  const body = document.getElementById('storageTable');
  body.innerHTML = state.storage.length ? state.storage.map(s => `
    <tr>
      <td>${s.storage_id}</td><td>${esc(s.location)}</td>
      <td><span class="status-chip ${s.status === 'AVAILABLE' ? 'available' : 'assigned'}">${esc(s.status)}</span></td>
      <td>${s.status === 'AVAILABLE'
        ? `<button class="mini-btn" onclick="assignStorage(${s.storage_id})">Assign</button>`
        : `<button class="mini-btn" onclick="releaseStorage(${s.storage_id})">Release</button>`}</td>
    </tr>`).join('') : '<tr><td colspan="4">No storage locations.</td></tr>';
}

function renderDashboard() {
  document.getElementById('studentCount').textContent = state.students.length;
  document.getElementById('parcelCount').textContent = state.parcels.length;
  document.getElementById('pendingPickupCount').textContent = state.pickups.filter(p => p.status === 'PENDING').length;
  document.getElementById('availableStorageCount').textContent = state.storage.filter(s => s.status === 'AVAILABLE').length;
}

async function checkService(name, url) {
  const item = document.createElement('div');
  item.className = 'service-row';
  item.innerHTML = `<div><div class="name">${name}</div><div class="url">${url}</div></div><span class="service-dot"></span>`;
  document.getElementById('serviceStatus').appendChild(item);
  const dot = item.querySelector('.service-dot');
  try {
    await apiFetch(url);
    dot.classList.add('ok');
  } catch (_) {
    dot.classList.add('bad');
  }
}

async function checkServices() {
  const list = document.getElementById('serviceStatus');
  list.innerHTML = '';
  const services = [
    ['Student Service', API.student + '/'],
    ['Parcel Service', API.parcel + '/'],
    ['Pickup Service', API.pickup + '/'],
    ['Storage Service', API.storage + '/']
  ];
  await Promise.all(services.map(([name, url]) => checkService(name, url)));
  const dots = [...list.querySelectorAll('.service-dot')];
  const healthy = dots.length === 4 && dots.every(d => d.classList.contains('ok'));
  const badge = document.getElementById('systemBadge');
  badge.textContent = healthy ? 'All services online' : 'Check service status';
  badge.className = `badge ${healthy ? 'ok' : 'bad'}`;
}

async function loadAll() {
  try {
    const [students, parcels, pickups, storage] = await Promise.all([
      apiFetch(API.student + '/students'),
      apiFetch(API.parcel + '/parcels'),
      apiFetch(API.pickup + '/pickup'),
      apiFetch(API.storage + '/storage')
    ]);
    state.students = students || [];
    state.parcels = parcels || [];
    state.pickups = pickups || [];
    state.storage = storage || [];
    renderStudents(); renderParcels(); renderPickups(); renderStorage(); renderStudentSelects(); renderDashboard();
    await checkServices();
  } catch (error) {
    showToast(error.message, true);
    await checkServices();
  }
}

function switchSection(section) {
  document.querySelectorAll('.page-section').forEach(el => el.classList.remove('active-section'));
  document.getElementById(section).classList.add('active-section');
  document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.toggle('active', btn.dataset.section === section));
  const titles = { dashboard: 'Dashboard', students: 'Students', parcels: 'Parcels', pickups: 'Pickups', storage: 'Storage' };
  document.getElementById('pageTitle').textContent = titles[section];
}

document.querySelectorAll('.nav-btn').forEach(btn => btn.addEventListener('click', () => switchSection(btn.dataset.section)));

document.getElementById('studentForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const id = document.getElementById('studentId').value;
  const payload = {
    name: document.getElementById('studentName').value.trim(),
    email: document.getElementById('studentEmail').value.trim(),
    department: document.getElementById('studentDepartment').value.trim(),
    year: Number(document.getElementById('studentYear').value)
  };
  try {
    await apiFetch(id ? `${API.student}/students/${id}` : `${API.student}/students`, { method: id ? 'PUT' : 'POST', body: JSON.stringify(payload) });
    showToast(id ? 'Student updated.' : 'Student created.');
    resetStudentForm();
    await loadAll();
  } catch (error) { showToast(error.message, true); }
});

function resetStudentForm() {
  document.getElementById('studentForm').reset();
  document.getElementById('studentId').value = '';
  document.getElementById('studentYear').value = 2;
  document.getElementById('studentFormTitle').textContent = 'Add Student';
}

function editStudent(id) {
  const s = state.students.find(x => Number(x.id) === Number(id));
  if (!s) return;
  switchSection('students');
  document.getElementById('studentId').value = s.id;
  document.getElementById('studentName').value = s.name;
  document.getElementById('studentEmail').value = s.email;
  document.getElementById('studentDepartment').value = s.department;
  document.getElementById('studentYear').value = s.year;
  document.getElementById('studentFormTitle').textContent = `Edit Student #${s.id}`;
}

async function deleteStudent(id) {
  if (!confirm(`Delete student #${id}?`)) return;
  try { await apiFetch(`${API.student}/students/${id}`, { method: 'DELETE' }); showToast('Student deleted.'); await loadAll(); }
  catch (error) { showToast(error.message, true); }
}

document.getElementById('parcelForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const id = document.getElementById('parcelId').value;
  const payload = {
    student_id: Number(document.getElementById('parcelStudent').value),
    courier: document.getElementById('parcelCourier').value.trim(),
    tracking_id: document.getElementById('parcelTracking').value.trim(),
    status: document.getElementById('parcelStatus').value
  };
  try {
    await apiFetch(id ? `${API.parcel}/parcels/${id}` : `${API.parcel}/parcels`, { method: id ? 'PUT' : 'POST', body: JSON.stringify(payload) });
    showToast(id ? 'Parcel updated.' : 'Parcel created.');
    resetParcelForm();
    await loadAll();
  } catch (error) { showToast(error.message, true); }
});

function resetParcelForm() {
  document.getElementById('parcelForm').reset();
  document.getElementById('parcelId').value = '';
  document.getElementById('parcelFormTitle').textContent = 'Add Parcel';
  renderStudentSelects();
}

function editParcel(id) {
  const p = state.parcels.find(x => Number(x.parcel_id) === Number(id));
  if (!p) return;
  switchSection('parcels');
  document.getElementById('parcelId').value = p.parcel_id;
  document.getElementById('parcelStudent').value = p.student_id;
  document.getElementById('parcelCourier').value = p.courier;
  document.getElementById('parcelTracking').value = p.tracking_id;
  document.getElementById('parcelStatus').value = p.status;
  document.getElementById('parcelFormTitle').textContent = `Edit Parcel #${p.parcel_id}`;
}

async function deleteParcel(id) {
  if (!confirm(`Delete parcel #${id}?`)) return;
  try { await apiFetch(`${API.parcel}/parcels/${id}`, { method: 'DELETE' }); showToast('Parcel deleted.'); await loadAll(); }
  catch (error) { showToast(error.message, true); }
}

document.getElementById('pickupForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    parcel_id: Number(document.getElementById('pickupParcel').value),
    student_id: Number(document.getElementById('pickupStudent').value)
  };
  try {
    await apiFetch(`${API.pickup}/pickup`, { method: 'POST', body: JSON.stringify(payload) });
    showToast('Pickup created and validated across services.');
    await loadAll();
    switchSection('pickups');
  } catch (error) { showToast(error.message, true); }
});

async function completePickup(id) {
  try { await apiFetch(`${API.pickup}/pickup/${id}/complete`, { method: 'PUT' }); showToast(`Pickup #${id} completed.`); await loadAll(); }
  catch (error) { showToast(error.message, true); }
}

document.getElementById('storageForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    storage_id: Number(document.getElementById('storageId').value),
    location: document.getElementById('storageLocation').value.trim(),
    status: document.getElementById('storageStatus').value
  };
  try {
    await apiFetch(`${API.storage}/storage`, { method: 'POST', body: JSON.stringify(payload) });
    showToast('Storage location added.');
    document.getElementById('storageForm').reset();
    await loadAll();
  } catch (error) { showToast(error.message, true); }
});

async function assignStorage(id) {
  try { await apiFetch(`${API.storage}/storage/assign`, { method: 'POST', body: JSON.stringify({ storage_id: id }) }); showToast(`Storage #${id} assigned.`); await loadAll(); }
  catch (error) { showToast(error.message, true); }
}

async function releaseStorage(id) {
  try { await apiFetch(`${API.storage}/storage/release`, { method: 'POST', body: JSON.stringify({ storage_id: id }) }); showToast(`Storage #${id} released.`); await loadAll(); }
  catch (error) { showToast(error.message, true); }
}

loadAll();
