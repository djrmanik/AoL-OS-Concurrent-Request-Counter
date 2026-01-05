const API_A = 'http://localhost:8001'; // Mapped in docker-compose
const API_B = 'http://localhost:8002'; // Mapped in docker-compose

let currentVersion = 'A';
let useLock = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateUIState();
    startPolling();
});

function setVersion(version) {
    currentVersion = version;
    document.getElementById('btn-version-a').classList.toggle('active', version === 'A');
    document.getElementById('btn-version-b').classList.toggle('active', version === 'B');

    // Toggle Lock Control visibility
    const lockControl = document.getElementById('lock-control');
    if (version === 'B') {
        lockControl.style.display = 'flex';
        document.getElementById('concurrency-status').textContent = 'Multi-Threaded (8 Workers)';
    } else {
        lockControl.style.display = 'none';
        document.getElementById('concurrency-status').textContent = 'Single Thread';
    }

    document.getElementById('active-version').textContent =
        version === 'A' ? 'Version A (Serial)' : 'Version B (Concurrent)';

    updateCashierVisuals();
}

function setSafety(safe) {
    useLock = safe;
    document.getElementById('btn-safe').classList.toggle('active', safe);
    document.getElementById('btn-unsafe').classList.toggle('active', !safe);
}

function getBaseUrl() {
    // In local dev without docker, this might need fallback, but we assume docker env structure
    // Since browser runs on host, we use localhost ports mapped in docker-compose
    return currentVersion === 'A' ? 'http://localhost:8001' : 'http://localhost:8002';
}

async function sendRequests(count) {
    const baseUrl = getBaseUrl();
    const endpoint = `${baseUrl}/process`;

    // For Version B, we construct the query param
    const params = new URLSearchParams();
    if (currentVersion === 'B') {
        params.append('use_lock', useLock);
    }
    // Artificial duration for visibility
    params.append('duration_ms', 100);

    const url = `${endpoint}?${params.toString()}`;

    // Visual feedback that requests are queued
    logRequestBatch(count, "Pending");

    // Launch requests
    const promises = [];
    for (let i = 0; i < count; i++) {
        promises.push(
            fetch(url, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    handleResponse(data);
                })
                .catch(err => console.error(err))
        );
    }

    // We don't await all here to allow UI to update as they come in
}


function handleResponse(data) {
    // Update Counter
    document.getElementById('counter-display').textContent = data.total_processed_requests;

    // Update Latency Display
    document.getElementById('last-latency').textContent = `${data.processing_time_ms} ms`;

    // Visual: Activate Cashier
    activateCashier(data.worker_id);

    // Log
    addLogEntry(data);
}

async function resetCounter() {
    const baseUrl = getBaseUrl();
    await fetch(`${baseUrl}/reset`);
    document.getElementById('counter-display').textContent = '0';
}


// Visualization Logic
const cashierElements = {};

function updateCashierVisuals() {
    const container = document.getElementById('cashier-container');
    container.innerHTML = '';

    let cashierCount = currentVersion === 'A' ? 1 : 8; // 8 threads for Version B

    for (let i = 0; i < cashierCount; i++) {
        const id = currentVersion === 'A' ? `worker_A` : `thread` // Simplified matching

        const el = document.createElement('div');
        el.className = 'cashier';
        // We need a stable ID for the DOM element to animate it
        // Since worker IDs come from backend (pid or thread id), we'll do a loose mapping or dynamic creation
        // For visualization simplicity: Version A has 1 box. Version B has 8 boxes.
        // We will map dynamic worker_id strings to these boxes.
        el.innerHTML = `
            <div class="cashier-icon">👤</div>
            <div class="cashier-id">Worker ${i + 1}</div>
        `;

        // We add a data attribute to map backend IDs to this slot? 
        // Actually, let's just create slots and map dynamically on response
        el.dataset.slot = i;
        container.appendChild(el);
    }
}

function activateCashier(workerId) {
    // Determine which slot to light up
    const container = document.getElementById('cashier-container');
    const cashiers = container.children;

    let slotIndex = 0;
    if (currentVersion === 'B') {
        // Extract thread id or hash it to one of the 8 slots
        // worker_id format: thread_<id>
        const parts = workerId.split('_');
        const num = parseInt(parts[parts.length - 1]) || 0;
        slotIndex = num % 8;
    }

    if (cashiers[slotIndex]) {
        const el = cashiers[slotIndex];
        el.classList.add('active');
        setTimeout(() => el.classList.remove('active'), 200);
    }
}

function addLogEntry(data) {
    const tbody = document.getElementById('request-log');
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${data.request_id.substring(0, 8)}...</td>
        <td class="status-completed">Completed</td>
        <td>${data.processing_time_ms}</td>
        <td>${data.worker_id}</td>
    `;
    tbody.insertBefore(row, tbody.firstChild);

    // Limit log size
    if (tbody.children.length > 50) {
        tbody.removeChild(tbody.lastChild);
    }
}

function logRequestBatch(count, status) {
    // Optional: Add pending rows? Maybe too much noise.
}

function updateUIState() {
    updateCashierVisuals();
}

// Polling for metrics (optional, to keep counter in sync if multiple tabs open)
function startPolling() {
    setInterval(async () => {
        try {
            const baseUrl = getBaseUrl();
            const res = await fetch(`${baseUrl}/metrics`);
            const data = await res.json();
            // Only update if value is higher (to avoid jitter if we reset elsewhere)
            // Actually just update it
            if (data.total_processed !== undefined) {
                document.getElementById('counter-display').textContent = data.total_processed;
            }
        } catch (e) {
            // ignore poll errors
        }
    }, 2000);
}
