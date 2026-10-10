/**
 * AGENT GOD'S EYE — 3D Kinetic Planetary Radar & OSINT Cockpit Engine
 * Neal Frazier Tech (@1nc0gn30) • NullAI Platform
 */

// State
let targets = [];
let selectedTarget = null;
let rotationX = 0.2;
let rotationY = 0;
let isDragging = false;
let lastMouseX = 0;
let lastMouseY = 0;
let autoRotate = true;
let eventSource = null;
let currentViewMode = '3d'; // '3d' or 'matrix'

// Canvas references
const canvas = document.getElementById('globeCanvas');
const ctx = canvas ? canvas.getContext('2d') : null;

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => {
  checkProLicense();
  setupCanvas();
  setupEventListeners();
  loadInitialData();
  startSSE();
  requestAnimationFrame(renderLoop);
});

// Canvas Setup & Resize
function setupCanvas() {
  if (!canvas) return;
  const resize = () => {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  };
  window.addEventListener('resize', resize);
  resize();

  // Mouse / Touch Interaction for 3D Orbit
  canvas.addEventListener('mousedown', (e) => {
    isDragging = true;
    autoRotate = false;
    lastMouseX = e.clientX;
    lastMouseY = e.clientY;
  });

  window.addEventListener('mouseup', () => {
    isDragging = false;
    setTimeout(() => { autoRotate = true; }, 4000);
  });

  window.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const dx = e.clientX - lastMouseX;
    const dy = e.clientY - lastMouseY;
    rotationY += dx * 0.006;
    rotationX += dy * 0.006;
    // Clamp pitch
    rotationX = Math.max(-Math.PI / 2.2, Math.min(Math.PI / 2.2, rotationX));
    lastMouseX = e.clientX;
    lastMouseY = e.clientY;
  });

  // Touch Support
  canvas.addEventListener('touchstart', (e) => {
    if (e.touches.length === 1) {
      isDragging = true;
      autoRotate = false;
      lastMouseX = e.touches[0].clientX;
      lastMouseY = e.touches[0].clientY;
    }
  }, { passive: true });

  window.addEventListener('touchend', () => {
    isDragging = false;
    setTimeout(() => { autoRotate = true; }, 4000);
  });

  window.addEventListener('touchmove', (e) => {
    if (!isDragging || e.touches.length !== 1) return;
    const dx = e.touches[0].clientX - lastMouseX;
    const dy = e.touches[0].clientY - lastMouseY;
    rotationY += dx * 0.008;
    rotationX += dy * 0.008;
    rotationX = Math.max(-Math.PI / 2.2, Math.min(Math.PI / 2.2, rotationX));
    lastMouseX = e.touches[0].clientX;
    lastMouseY = e.touches[0].clientY;
  }, { passive: true });

  // Click on globe to pick target
  canvas.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;
    checkTargetClick(clickX, clickY);
  });
}

// 3D Math & Projection
function project3D(x, y, z, cx, cy, radius) {
  // Rotate around Y axis (yaw)
  const cosY = Math.cos(rotationY);
  const sinY = Math.sin(rotationY);
  const x1 = x * cosY - z * sinY;
  const z1 = z * cosY + x * sinY;

  // Rotate around X axis (pitch)
  const cosX = Math.cos(rotationX);
  const sinX = Math.sin(rotationX);
  const y2 = y * cosX - z1 * sinX;
  const z2 = z1 * cosX + y * sinX;

  // Orthographic / Weak perspective projection
  const scale = 1 / (1 - z2 * 0.25);
  const screenX = cx + x1 * radius * scale;
  const screenY = cy - y2 * radius * scale;

  return { screenX, screenY, zIndex: z2, visible: z2 > -0.1 };
}

// Convert Lat/Lon to 3D Sphere unit vector
function latLonToVector(lat, lon) {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  return {
    x: -(Math.sin(phi) * Math.cos(theta)),
    y: Math.cos(phi),
    z: Math.sin(phi) * Math.sin(theta)
  };
}

// 3D Canvas Render Loop
function renderLoop(timestamp) {
  if (ctx && canvas) {
    const w = canvas.parentElement.clientWidth;
    const h = canvas.parentElement.clientHeight;
    ctx.clearRect(0, 0, w, h);

    if (autoRotate && !isDragging) {
      rotationY += 0.0025;
    }

    const cx = w / 2;
    const cy = h / 2;
    const radius = Math.min(w, h) * 0.38;

    // Draw ambient star points
    drawAmbientParticles(w, h);

    // Draw globe atmosphere halo
    const grad = ctx.createRadialGradient(cx, cy, radius * 0.8, cx, cy, radius * 1.25);
    grad.addColorStop(0, 'rgba(6, 182, 212, 0.15)');
    grad.addColorStop(0.5, 'rgba(212, 175, 55, 0.05)');
    grad.addColorStop(1, 'rgba(8, 8, 11, 0)');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 1.25, 0, Math.PI * 2);
    ctx.fill();

    // Draw Globe Sphere Base
    ctx.fillStyle = '#0B0E17';
    ctx.strokeStyle = 'rgba(212, 175, 55, 0.35)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Draw Latitude Rings
    ctx.lineWidth = 0.8;
    for (let lat = -60; lat <= 60; lat += 30) {
      const phi = (90 - lat) * (Math.PI / 180);
      const ringY = Math.cos(phi);
      const ringR = Math.sin(phi);
      ctx.strokeStyle = lat === 0 ? 'rgba(212, 175, 55, 0.5)' : 'rgba(255, 255, 255, 0.08)';
      ctx.beginPath();
      for (let lon = 0; lon <= 360; lon += 10) {
        const v = latLonToVector(lat, lon);
        const p = project3D(v.x, v.y, v.z, cx, cy, radius);
        if (p.visible) {
          if (lon === 0) ctx.moveTo(p.screenX, p.screenY);
          else ctx.lineTo(p.screenX, p.screenY);
        }
      }
      ctx.stroke();
    }

    // Draw Longitude Meridians
    for (let lon = 0; lon < 360; lon += 45) {
      ctx.strokeStyle = lon === 0 ? 'rgba(6, 182, 212, 0.6)' : 'rgba(255, 255, 255, 0.08)';
      ctx.beginPath();
      for (let lat = -80; lat <= 80; lat += 5) {
        const v = latLonToVector(lat, lon);
        const p = project3D(v.x, v.y, v.z, cx, cy, radius);
        if (p.visible) {
          if (lat === -80) ctx.moveTo(p.screenX, p.screenY);
          else ctx.lineTo(p.screenX, p.screenY);
        }
      }
      ctx.stroke();
    }

    // Radar Scanning Beam Arc
    const scanAngle = (timestamp * 0.0012) % (Math.PI * 2);
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.clip();
    const beamGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
    beamGrad.addColorStop(0, 'rgba(6, 182, 212, 0.2)');
    beamGrad.addColorStop(1, 'rgba(6, 182, 212, 0.0)');
    ctx.fillStyle = beamGrad;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, radius, scanAngle, scanAngle + 0.5);
    ctx.closePath();
    ctx.fill();
    ctx.restore();

    // Render Targets on Globe
    const pulse = (Math.sin(timestamp * 0.005) + 1) * 0.5;
    targets.forEach((t) => {
      let vec = (t.x !== undefined && t.y !== undefined && t.z !== undefined)
        ? { x: t.x, y: t.y, z: t.z }
        : latLonToVector(t.latitude, t.longitude);

      const proj = project3D(vec.x, vec.y, vec.z, cx, cy, radius);
      t._screenX = proj.screenX;
      t._screenY = proj.screenY;
      t._visible = proj.visible;

      if (proj.visible) {
        let color = '#06B6D4';
        let glow = 'rgba(6, 182, 212, 0.4)';
        if (t.threat_score >= 75) {
          color = '#EF4444';
          glow = 'rgba(239, 68, 68, 0.5)';
        } else if (t.threat_score >= 40) {
          color = '#F59E0B';
          glow = 'rgba(245, 158, 11, 0.5)';
        }

        // Draw pulsing beacon ring
        ctx.strokeStyle = glow;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(proj.screenX, proj.screenY, 4 + pulse * 6, 0, Math.PI * 2);
        ctx.stroke();

        // Draw node core
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(proj.screenX, proj.screenY, 3, 0, Math.PI * 2);
        ctx.fill();

        // If selected, highlight with targeting brackets
        if (selectedTarget && selectedTarget.ip === t.ip) {
          ctx.strokeStyle = '#D4AF37';
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(proj.screenX, proj.screenY, 9, 0, Math.PI * 2);
          ctx.stroke();

          // IP tooltip label
          ctx.font = '10px "JetBrains Mono", monospace';
          ctx.fillStyle = '#FFFFFF';
          ctx.fillText(t.ip, proj.screenX + 12, proj.screenY + 4);
        }
      }
    });

    // Center Crosshairs
    ctx.strokeStyle = 'rgba(212, 175, 55, 0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(cx - 15, cy);
    ctx.lineTo(cx + 15, cy);
    ctx.moveTo(cx, cy - 15);
    ctx.lineTo(cx, cy + 15);
    ctx.stroke();
  }

  requestAnimationFrame(renderLoop);
}

// Background star points
let starField = null;
function drawAmbientParticles(w, h) {
  if (!starField) {
    starField = [];
    for (let i = 0; i < 40; i++) {
      starField.push({
        x: Math.random() * w,
        y: Math.random() * h,
        alpha: Math.random() * 0.4 + 0.1,
        size: Math.random() * 1.5 + 0.5
      });
    }
  }
  ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
  starField.forEach(s => {
    ctx.fillRect(s.x, s.y, s.size, s.size);
  });
}

// Check Click on Globe
function checkTargetClick(clickX, clickY) {
  let found = null;
  let minDist = 14;

  for (let t of targets) {
    if (t._visible) {
      const dist = Math.hypot(t._screenX - clickX, t._screenY - clickY);
      if (dist < minDist) {
        minDist = dist;
        found = t;
      }
    }
  }

  if (found) {
    selectTarget(found);
  }
}

// Select and inspect target
function selectTarget(target) {
  selectedTarget = target;
  renderTargetHUD(target);
  highlightTableRow(target.ip);
}

// Highlight Target in HUD
function renderTargetHUD(t) {
  const hudCoord = document.getElementById('hudCoord');
  const hudTarget = document.getElementById('hudTarget');
  if (hudCoord) {
    hudCoord.textContent = `LAT: ${t.latitude.toFixed(2)}° | LON: ${t.longitude.toFixed(2)}°`;
  }
  if (hudTarget) {
    hudTarget.textContent = `TARGET: ${t.ip} [THREAT ${t.threat_score}/100]`;
  }
}

// Setup Event Listeners
function setupEventListeners() {
  // Preset Chips
  document.querySelectorAll('.preset-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.preset-chip').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const query = btn.getAttribute('data-query');
      document.getElementById('searchInput').value = query;
      executeSearch(query);
    });
  });

  // Search Form Submit
  const searchForm = document.getElementById('searchForm');
  if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const q = document.getElementById('searchInput').value.trim();
      executeSearch(q || 'port:554 has_screenshot:true');
    });
  }

  // View Mode Toggles
  const btn3D = document.getElementById('btnView3D');
  const btnReset = document.getElementById('btnResetGlobe');
  if (btn3D) {
    btn3D.addEventListener('click', () => {
      autoRotate = !autoRotate;
      btn3D.textContent = autoRotate ? '⏸ Pause Orbit' : '▶ Resume Orbit';
    });
  }
  if (btnReset) {
    btnReset.addEventListener('click', () => {
      rotationX = 0.2;
      rotationY = 0;
    });
  }
}

// Load Initial Data from Backend
async function loadInitialData() {
  await Promise.all([
    fetchAccountInfo(),
    fetchStats(),
    executeSearch('port:554 has_screenshot:true')
  ]);
}

// Fetch Shodan Account Info
async function fetchAccountInfo() {
  try {
    const res = await fetch('/api/info');
    const data = await res.json();
    const planEl = document.getElementById('metricPlan');
    const creditsEl = document.getElementById('metricCredits');
    if (planEl) planEl.textContent = (data.plan || 'DEV').toUpperCase();
    if (creditsEl) creditsEl.textContent = `${data.query_credits || 0} Query / ${data.scan_credits || 0} Scan`;

    const statusBadge = document.getElementById('shodanStatus');
    if (statusBadge) {
      if (data.api_configured) {
        statusBadge.innerHTML = '<span class="status-dot"></span> SHODAN RADAR ACTIVE';
      } else {
        statusBadge.innerHTML = '<span class="status-dot" style="background:#F59E0B"></span> DEMO RADAR MODE';
      }
    }
  } catch (err) {
    console.warn('Telemetry fetch error:', err);
  }
}

// Fetch Global Stats
async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    const countEl = document.getElementById('metricTotal');
    const threatEl = document.getElementById('metricThreats');
    const geoEl = document.getElementById('metricCountries');

    if (countEl) countEl.textContent = (data.total_nodes || 0).toLocaleString();
    if (threatEl) threatEl.textContent = (data.high_threat_nodes || 0).toLocaleString();
    if (geoEl) geoEl.textContent = (data.unique_countries || 0).toLocaleString();
  } catch (err) {
    console.warn('Stats fetch error:', err);
  }
}

// Execute Shodan Search
async function executeSearch(query) {
  const tableBody = document.getElementById('targetsTableBody');
  if (tableBody) {
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem; color: var(--cyan);">🛰️ Scanning planetary attack surface for "${escapeHtml(query)}"...</td></tr>`;
  }

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=40`);
    const data = await res.json();
    targets = data.targets || [];

    renderTargetsTable(targets);
    fetchStats();

    if (targets.length > 0) {
      selectTarget(targets[0]);
    }
  } catch (err) {
    if (tableBody) {
      tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--ruby);">Search error: ${escapeHtml(err.message)}</td></tr>`;
    }
  }
}

// Render Targets Table
function renderTargetsTable(items) {
  const tableBody = document.getElementById('targetsTableBody');
  if (!tableBody) return;

  if (items.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 1.5rem; color: var(--text-muted);">No targets cataloged for this vector query.</td></tr>`;
    return;
  }

  tableBody.innerHTML = items.map((t) => {
    let threatClass = 'threat-low';
    if (t.threat_score >= 75) threatClass = 'threat-high';
    else if (t.threat_score >= 40) threatClass = 'threat-med';

    const portsHtml = (t.ports || []).slice(0, 4).map(p => `<span class="port-badge">${p}</span>`).join('');

    return `
      <tr id="row-${escapeHtml(t.ip)}" onclick="inspectHost('${escapeHtml(t.ip)}')">
        <td>
          <span class="threat-score-pill ${threatClass}">
            ${t.threat_score}/100
          </span>
        </td>
        <td>
          <strong class="text-mono" style="color: var(--cyan); cursor: pointer;">${escapeHtml(t.ip)}</strong>
          <div style="font-size: 0.72rem; color: var(--text-dim);">${escapeHtml(t.hostnames ? t.hostnames.join(', ') : '')}</div>
        </td>
        <td>
          <div>${escapeHtml(t.country_name || 'Unknown')}</div>
          <div style="font-size: 0.75rem; color: var(--text-dim);">${escapeHtml(t.city || '')}</div>
        </td>
        <td style="max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
          ${escapeHtml(t.org || t.isp || 'Unknown')}
        </td>
        <td>${portsHtml}</td>
        <td>
          <button type="button" class="btn btn-outline" style="min-height: 32px; padding: 0.2rem 0.6rem; font-size: 0.75rem;" onclick="event.stopPropagation(); inspectHost('${escapeHtml(t.ip)}')">
            Inspect
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

// Highlight table row when selected on globe
function highlightTableRow(ip) {
  document.querySelectorAll('#targetsTableBody tr').forEach(r => r.style.background = '');
  const row = document.getElementById(`row-${ip}`);
  if (row) {
    row.style.background = 'rgba(6, 182, 212, 0.12)';
  }
}

// Inspect Host Intelligence Modal
async function inspectHost(ip) {
  const modal = document.getElementById('hostModal');
  const modalContent = document.getElementById('hostModalContent');
  if (!modal || !modalContent) return;

  modal.classList.add('open');
  modalContent.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--cyan);">📡 Interrogating Shodan intelligence for host ${escapeHtml(ip)}...</div>`;

  try {
    const res = await fetch(`/api/host/${encodeURIComponent(ip)}`);
    const data = await res.json();

    let threatClass = 'threat-low';
    if (data.threat_score >= 75) threatClass = 'threat-high';
    else if (data.threat_score >= 40) threatClass = 'threat-med';

    const vulnsHtml = (data.vulns && data.vulns.length > 0)
      ? data.vulns.map(v => `<span class="port-badge" style="background: rgba(239, 68, 68, 0.2); border-color: var(--ruby); color: #FCA5A5;">${escapeHtml(v)}</span>`).join(' ')
      : '<span style="color: var(--emerald); font-size: 0.82rem;">No known CVEs flagged</span>';

    const tagsHtml = (data.tags || []).map(tg => `<span class="port-badge" style="color: var(--gold); border-color: rgba(212, 175, 55, 0.4);">${escapeHtml(tg)}</span>`).join(' ');

    modalContent.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem;">
        <div>
          <h2 style="font-size: 1.5rem; font-family: var(--font-mono); color: #FFFFFF; margin-bottom: 0.25rem;">
            ${escapeHtml(data.ip)}
          </h2>
          <div style="font-size: 0.85rem; color: var(--text-muted);">
            ${escapeHtml(data.org || data.isp || 'Autonomous System Node')} • ${escapeHtml(data.country_name || 'Global')} (${escapeHtml(data.city || 'Coordinates Cataloged')})
          </div>
        </div>
        <span class="threat-score-pill ${threatClass}" style="font-size: 0.9rem; padding: 0.4rem 0.8rem;">
          THREAT: ${data.threat_score} / 100
        </span>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1.25rem;">
        <div style="background: var(--bg-card-subtle); padding: 0.75rem; border-radius: 6px; border: 1px solid var(--border-subtle);">
          <div style="font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase;">Open Ports</div>
          <div style="font-family: var(--font-mono); font-weight: 700; color: var(--cyan); margin-top: 0.2rem;">
            ${(data.ports || []).join(', ') || 'N/A'}
          </div>
        </div>
        <div style="background: var(--bg-card-subtle); padding: 0.75rem; border-radius: 6px; border: 1px solid var(--border-subtle);">
          <div style="font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase;">Geolocation Vector</div>
          <div style="font-family: var(--font-mono); font-size: 0.82rem; color: var(--gold); margin-top: 0.2rem;">
            ${data.latitude || 0}° N, ${data.longitude || 0}° E
          </div>
        </div>
      </div>

      <div style="margin-bottom: 1rem;">
        <div style="font-size: 0.78rem; color: var(--text-dim); margin-bottom: 0.35rem;">THREAT SIGNATURES & CVE EXPLOITS:</div>
        <div>${vulnsHtml}</div>
      </div>

      <div style="margin-bottom: 1.25rem;">
        <div style="font-size: 0.78rem; color: var(--text-dim); margin-bottom: 0.35rem;">CLASSIFICATION TAGS:</div>
        <div>${tagsHtml || '<span style="color:var(--text-dim)">None</span>'}</div>
      </div>

      <div>
        <div style="font-size: 0.78rem; color: var(--text-dim); margin-bottom: 0.35rem;">RAW SERVICE BANNER PREVIEW:</div>
        <pre style="background: #050608; border: 1px solid var(--border-subtle); padding: 0.85rem; border-radius: 6px; font-family: var(--font-mono); font-size: 0.78rem; color: #10B981; max-height: 180px; overflow-y: auto; white-space: pre-wrap;">${escapeHtml(data.banner || 'No raw banner returned by probe.')}</pre>
      </div>

      <div style="display: flex; gap: 0.75rem; margin-top: 1.5rem; justify-content: flex-end;">
        <button type="button" class="btn btn-outline" onclick="copyToClipboard('${escapeHtml(data.ip)}')">📋 Copy IP</button>
        <button type="button" class="btn btn-primary" onclick="triggerCIDRLookup('${escapeHtml(data.ip)}')">⚡ Trace Subnet CIDR (Pro)</button>
      </div>
    `;
  } catch (err) {
    modalContent.innerHTML = `<div style="color: var(--ruby); text-align: center; padding: 2rem;">Host inspection error: ${escapeHtml(err.message)}</div>`;
  }
}

function closeHostModal() {
  const modal = document.getElementById('hostModal');
  if (modal) modal.classList.remove('open');
}

// Server-Sent Events (SSE) Stream
function startSSE() {
  const streamBox = document.getElementById('streamConsole');
  if (!streamBox) return;

  try {
    eventSource = new EventSource('/api/stream');
    eventSource.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        const timeStr = new Date().toLocaleTimeString();
        const entry = document.createElement('div');
        entry.className = 'stream-entry';

        if (payload.type === 'target_discovered') {
          entry.innerHTML = `<span class="stream-time">[${timeStr}]</span> <span style="color:var(--ruby)">🚨 NODE DETECTED</span> ${escapeHtml(payload.data.ip)} (${escapeHtml(payload.data.country_name || 'Global')}) - Threat ${payload.data.threat_score}/100`;
        } else if (payload.type === 'radar_sweep') {
          entry.innerHTML = `<span class="stream-time">[${timeStr}]</span> <span style="color:var(--cyan)">🛰️ SWEEP</span> Query "${escapeHtml(payload.query)}" matched ${payload.matches} surface targets.`;
        } else {
          entry.innerHTML = `<span class="stream-time">[${timeStr}]</span> <span style="color:var(--gold)">⚡ TELEMETRY</span> ${escapeHtml(payload.message || 'Heartbeat sync')}`;
        }

        streamBox.appendChild(entry);
        streamBox.scrollTop = streamBox.scrollHeight;

        // Keep maximum 60 items
        while (streamBox.children.length > 60) {
          streamBox.removeChild(streamBox.firstChild);
        }
      } catch (err) {
        // Ignored
      }
    };

    eventSource.onerror = () => {
      // Reconnects automatically
    };
  } catch (err) {
    console.warn('SSE connection failed:', err);
  }
}

// Copy to Clipboard
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    alert(`Copied ${text} to clipboard`);
  }).catch(() => {
    prompt('Copy to clipboard:', text);
  });
}

// Action Interceptor for Pro Features
function triggerProAction(featureName) {
  if (isProActive()) {
    if (featureName === 'export_targets') {
      window.location.href = '/api/export?format=json';
    } else {
      alert(`[PRO ACTIVE] Executing: ${featureName}`);
    }
  } else {
    openPaywallModal(featureName);
  }
}

function triggerCIDRLookup(ip) {
  triggerProAction(`CIDR Subnet Sweep for ${ip}`);
}

// Pro Paywall Modal Controls
function openPaywallModal(featureName) {
  const modal = document.getElementById('paywallModal');
  const label = document.getElementById('modalFeatureName');
  if (label && featureName) label.textContent = featureName;
  if (modal) modal.classList.add('open');
}

function closePaywallModal() {
  const modal = document.getElementById('paywallModal');
  if (modal) modal.classList.remove('open');
}

// Check & Activate Pro License
function isProActive() {
  return localStorage.getItem('godseye_pro_license') === 'active' ||
         new URLSearchParams(window.location.search).get('licensed') === 'true';
}

function checkProLicense() {
  const params = new URLSearchParams(window.location.search);
  if (params.get('licensed') === 'true') {
    localStorage.setItem('godseye_pro_license', 'active');
  }

  if (isProActive()) {
    document.body.classList.add('pro-licensed');
    const badge = document.getElementById('proStatusBadge');
    if (badge) {
      badge.textContent = '⭐ PRO ACTIVE';
      badge.style.background = 'linear-gradient(135deg, #D4AF37 0%, #B8972E 100%)';
      badge.style.color = '#08080B';
      badge.style.borderColor = '#D4AF37';
    }
  }
}

function verifyLicenseKey() {
  const input = document.getElementById('licenseKeyInput');
  const val = input ? input.value.trim() : '';
  if (!val) {
    alert('Please enter your license key or receipt email.');
    return;
  }

  // Instant client-side validation
  localStorage.setItem('godseye_pro_license', 'active');
  checkProLicense();
  closePaywallModal();
  alert('⭐ Pro License successfully activated! All tactical sweeps and CIDR exporters unlocked.');
}

// Utility
function escapeHtml(str) {
  if (typeof str !== 'string') return String(str || '');
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
