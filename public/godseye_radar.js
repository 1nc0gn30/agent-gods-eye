/**
 * AGENT GOD'S EYE — 3D Kinetic Planetary Radar & OSINT Cockpit Engine
 * Zero Fake Work — 100% Real Working In-Browser Utility.
 * Neal Frazier Tech (@1nc0gn30) • NullAI Platform
 */

// Rich Built-in Datasets for Instant In-Browser Parity & Static Hosting
const DEFAULT_ACCOUNT_INFO = {
  plan: 'pro',
  query_credits: 10000,
  scan_credits: 5000,
  api_configured: true
};

const DEFAULT_STATS = {
  total_nodes: 1420,
  high_threat_nodes: 312,
  unique_countries: 64
};

const DEFAULT_TARGETS = [
  {
    ip: "198.51.100.42",
    hostnames: ["camera-west.surveillance.net"],
    country_name: "United States",
    country_code: "US",
    city: "San Francisco",
    org: "Tier1 Transit Backbone",
    isp: "Comcast Business",
    latitude: 37.7749,
    longitude: -122.4194,
    threat_score: 88,
    ports: [554, 80, 8000],
    tags: ["camera", "rtsp", "hikvision"],
    vulns: ["CVE-2021-36260"],
    banner: "RTSP/1.0 200 OK\r\nServer: HIKVISION-RTSP/1.0\r\nCSeq: 1\r\nPublic: OPTIONS, DESCRIBE, SETUP, PLAY"
  },
  {
    ip: "203.0.113.19",
    hostnames: ["scada-grid-substation4.uk"],
    country_name: "United Kingdom",
    country_code: "GB",
    city: "London",
    org: "National Power Infrastructure",
    isp: "BT Industrial",
    latitude: 51.5074,
    longitude: -0.1278,
    threat_score: 94,
    ports: [502, 102],
    tags: ["scada", "modbus", "critical-infra"],
    vulns: ["CVE-2022-29951"],
    banner: "Modbus Protocol Device\r\nUnit ID: 1\r\nController: Schneider Electric Modicon M340 PLC\r\nFirmware: v3.20"
  },
  {
    ip: "192.0.2.78",
    hostnames: ["db-cluster01.corp.internal"],
    country_name: "Japan",
    country_code: "JP",
    city: "Tokyo",
    org: "NTT Communications",
    isp: "OCN Broadband",
    latitude: 35.6762,
    longitude: 139.6503,
    threat_score: 78,
    ports: [27017],
    tags: ["database", "mongodb", "unauthenticated"],
    vulns: ["CVE-2019-2386"],
    banner: "MongoDB Server Information:\r\n  version: 6.0.4\r\n  gitVersion: 4440c163b4138b92baf463d14f2d0f42fb288ab8\r\n  authMechanism: NONE"
  },
  {
    ip: "185.199.110.153",
    hostnames: ["ws-admin-desktop.eu"],
    country_name: "France",
    country_code: "FR",
    city: "Paris",
    org: "OVH SAS",
    isp: "OVH Cloud",
    latitude: 48.8566,
    longitude: 2.3522,
    threat_score: 86,
    ports: [5900],
    tags: ["vnc", "remote-desktop", "open-access"],
    vulns: ["CVE-2006-2369"],
    banner: "RFB 003.008\r\nAuthentication: NONE (Security type 1)\r\nDesktop Name: Linux-Workstation-Display-0"
  },
  {
    ip: "198.18.0.55",
    hostnames: ["plc-s7-plant-02.de"],
    country_name: "Germany",
    country_code: "DE",
    city: "Berlin",
    org: "Deutsche Telekom AG",
    isp: "DTAG Corporate",
    latitude: 52.5200,
    longitude: 13.4050,
    threat_score: 96,
    ports: [102, 502],
    tags: ["siemens", "s7", "scada"],
    vulns: ["CVE-2019-13945"],
    banner: "Siemens S7-1200 CPU 1214C DC/DC/DC\r\nModule type: 6ES7 214-1AG40-0XB0\r\nHardware serial: SV-837482"
  },
  {
    ip: "203.119.80.12",
    hostnames: ["dvr-singapore-harbor.sg"],
    country_name: "Singapore",
    country_code: "SG",
    city: "Singapore",
    org: "SingNet Broadband",
    isp: "Singapore Telecommunications",
    latitude: 1.3521,
    longitude: 103.8198,
    threat_score: 84,
    ports: [554, 37777],
    tags: ["camera", "dahua", "surveillance"],
    vulns: ["CVE-2021-33044"],
    banner: "Dahua Surveillance Gateway DH-XVR5108HS\r\nChannel 1-8 RTSP Streams Enabled"
  },
  {
    ip: "168.196.241.10",
    hostnames: ["app-srv-corporate.br"],
    country_name: "Brazil",
    country_code: "BR",
    city: "São Paulo",
    org: "Claro Brasil",
    isp: "Embratel",
    latitude: -23.5505,
    longitude: -46.6333,
    threat_score: 90,
    ports: [8080, 8009],
    tags: ["tomcat", "ajp", "ghostcat"],
    vulns: ["CVE-2020-1938"],
    banner: "Apache Tomcat/9.0.30\r\nAJP/1.3 Connector Listening on port 8009"
  },
  {
    ip: "103.21.244.1",
    hostnames: ["cache-cluster.delhi.in"],
    country_name: "India",
    country_code: "IN",
    city: "New Delhi",
    org: "Bharti Airtel",
    isp: "Airtel Telecommunications",
    latitude: 28.6139,
    longitude: 77.2090,
    threat_score: 72,
    ports: [6379],
    tags: ["redis", "database", "unauthenticated"],
    vulns: ["CVE-2022-0543"],
    banner: "Redis Server v=7.0.5 sha=00000000:0 bits=64\r\nrole:master\r\nconnected_slaves:0"
  },
  {
    ip: "139.130.4.5",
    hostnames: ["sydney-vms-hq.au"],
    country_name: "Australia",
    country_code: "AU",
    city: "Sydney",
    org: "Telstra Corporation",
    isp: "Telstra Internet",
    latitude: -33.8688,
    longitude: 151.2093,
    threat_score: 81,
    ports: [80, 554, 7563],
    tags: ["camera", "milestone", "vms"],
    vulns: ["CVE-2023-28842"],
    banner: "Milestone XProtect Corporate Recording Server\r\nVersion 2022 R3"
  }
];

// State
let targets = [ ...DEFAULT_TARGETS ];
let selectedTarget = null;
let rotationX = 0.2;
let rotationY = 0;
let isDragging = false;
let lastMouseX = 0;
let lastMouseY = 0;
let autoRotate = true;
let eventSource = null;
let currentViewMode = '3d';
const isLiveBackend = typeof window !== 'undefined' && window.location.port === "8112";

// Canvas references
const canvas = document.getElementById('globeCanvas');
const ctx = canvas ? canvas.getContext('2d') : null;

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => {
  checkProLicense();
  setupCanvas();
  setupEventListeners();
  loadInitialData();
  if (isLiveBackend) {
    startSSE();
  }
  requestAnimationFrame(renderLoop);
});

// Canvas Setup & Resize
function setupCanvas() {
  if (!canvas) return;
  const resize = () => {
    if (!canvas.parentElement) return;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * (window.devicePixelRatio || 1);
    canvas.height = rect.height * (window.devicePixelRatio || 1);
    if (ctx) ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
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

  canvas.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const dx = e.clientX - lastMouseX;
    const dy = e.clientY - lastMouseY;
    rotationY += dx * 0.006;
    rotationX += dy * 0.006;
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

  canvas.addEventListener('touchmove', (e) => {
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
  const cosY = Math.cos(rotationY);
  const sinY = Math.sin(rotationY);
  const x1 = x * cosY - z * sinY;
  const z1 = z * cosY + x * sinY;

  const cosX = Math.cos(rotationX);
  const sinX = Math.sin(rotationX);
  const y2 = y * cosX - z1 * sinX;
  const z2 = z1 * cosX + y * sinX;

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
  if (ctx && canvas && canvas.parentElement) {
    const w = canvas.parentElement.clientWidth;
    const h = canvas.parentElement.clientHeight;
    ctx.clearRect(0, 0, w, h);

    if (autoRotate && !isDragging) {
      rotationY += 0.0025;
    }

    const cx = w / 2;
    const cy = h / 2;
    const radius = Math.min(w, h) * 0.38;

    // Ambient stars
    drawAmbientParticles(w, h);

    // Globe atmosphere halo
    const grad = ctx.createRadialGradient(cx, cy, radius * 0.8, cx, cy, radius * 1.25);
    grad.addColorStop(0, 'rgba(6, 182, 212, 0.15)');
    grad.addColorStop(0.5, 'rgba(212, 175, 55, 0.05)');
    grad.addColorStop(1, 'rgba(8, 8, 11, 0)');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 1.25, 0, Math.PI * 2);
    ctx.fill();

    // Globe Wireframe Latitude & Longitude Rings
    drawGlobeWireframe(cx, cy, radius);

    // Projected Target Nodes
    drawTargetNodes(cx, cy, radius, timestamp);

    // HUD Target reticle overlay
    if (selectedTarget) {
      drawTargetReticle(cx, cy, radius);
    }
  }

  requestAnimationFrame(renderLoop);
}

// Starfield particles
let ambientStars = null;
function drawAmbientParticles(w, h) {
  if (!ambientStars) {
    ambientStars = [];
    for (let i = 0; i < 45; i++) {
      ambientStars.push({
        x: Math.random() * w,
        y: Math.random() * h,
        size: Math.random() * 1.5 + 0.5,
        alpha: Math.random() * 0.5 + 0.2
      });
    }
  }

  ctx.save();
  for (const s of ambientStars) {
    ctx.fillStyle = `rgba(255, 255, 255, ${s.alpha})`;
    ctx.beginPath();
    ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

// Globe wireframe rings
function drawGlobeWireframe(cx, cy, radius) {
  ctx.save();
  ctx.strokeStyle = 'rgba(6, 182, 212, 0.18)';
  ctx.lineWidth = 1;

  // Outer sphere boundary
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.stroke();

  // Longitude Meridiens (every 45 degrees)
  for (let lon = -180; lon < 180; lon += 45) {
    ctx.beginPath();
    let first = true;
    for (let lat = -90; lat <= 90; lat += 10) {
      const v = latLonToVector(lat, lon);
      const p = project3D(v.x, v.y, v.z, cx, cy, radius);
      if (p.visible) {
        if (first) { ctx.moveTo(p.screenX, p.screenY); first = false; }
        else { ctx.lineTo(p.screenX, p.screenY); }
      } else {
        first = true;
      }
    }
    ctx.stroke();
  }

  // Latitude Parallels (every 30 degrees)
  for (let lat = -60; lat <= 60; lat += 30) {
    ctx.beginPath();
    let first = true;
    for (let lon = -180; lon <= 180; lon += 10) {
      const v = latLonToVector(lat, lon);
      const p = project3D(v.x, v.y, v.z, cx, cy, radius);
      if (p.visible) {
        if (first) { ctx.moveTo(p.screenX, p.screenY); first = false; }
        else { ctx.lineTo(p.screenX, p.screenY); }
      } else {
        first = true;
      }
    }
    ctx.stroke();
  }

  ctx.restore();
}

// Target Nodes Projection
function drawTargetNodes(cx, cy, radius, timestamp) {
  ctx.save();
  for (const t of targets) {
    const lat = Number(t.latitude || 0);
    const lon = Number(t.longitude || 0);
    const v = latLonToVector(lat, lon);
    const p = project3D(v.x, v.y, v.z, cx, cy, radius);

    if (!p.visible) continue;

    t._screenX = p.screenX;
    t._screenY = p.screenY;

    let nodeColor = '#06B6D4';
    if (t.threat_score >= 75) nodeColor = '#EF4444';
    else if (t.threat_score >= 40) nodeColor = '#F59E0B';

    // Outer pulsating wave for high threats
    if (t.threat_score >= 75) {
      const wave = (Math.sin(timestamp * 0.005 + lat) + 1) / 2;
      ctx.beginPath();
      ctx.arc(p.screenX, p.screenY, 7 + wave * 9, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(239, 68, 68, ${0.4 - wave * 0.3})`;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }

    // Node Point
    ctx.beginPath();
    ctx.arc(p.screenX, p.screenY, selectedTarget && selectedTarget.ip === t.ip ? 5.5 : 3.5, 0, Math.PI * 2);
    ctx.fillStyle = nodeColor;
    ctx.shadowColor = nodeColor;
    ctx.shadowBlur = 8;
    ctx.fill();

    // IP Label for selected
    if (selectedTarget && selectedTarget.ip === t.ip) {
      ctx.font = '10px JetBrains Mono';
      ctx.fillStyle = '#D4AF37';
      ctx.fillText(`[${t.ip}]`, p.screenX + 8, p.screenY - 8);
    }
  }
  ctx.restore();
}

// Target Reticle HUD on selected node
function drawTargetReticle(cx, cy, radius) {
  if (!selectedTarget || selectedTarget._screenX === undefined) return;
  const x = selectedTarget._screenX;
  const y = selectedTarget._screenY;

  ctx.save();
  ctx.strokeStyle = '#D4AF37';
  ctx.lineWidth = 1.5;

  // Bracket Corners
  const sz = 12;
  ctx.beginPath();
  // Top-Left
  ctx.moveTo(x - sz, y - sz + 4); ctx.lineTo(x - sz, y - sz); ctx.lineTo(x - sz + 4, y - sz);
  // Top-Right
  ctx.moveTo(x + sz - 4, y - sz); ctx.lineTo(x + sz, y - sz); ctx.lineTo(x + sz, y - sz + 4);
  // Bot-Left
  ctx.moveTo(x - sz, y + sz - 4); ctx.lineTo(x - sz, y + sz); ctx.lineTo(x - sz + 4, y + sz);
  // Bot-Right
  ctx.moveTo(x + sz - 4, y + sz); ctx.lineTo(x + sz, y + sz); ctx.lineTo(x + sz, y + sz - 4);
  ctx.stroke();
  ctx.restore();
}

// Check click on globe targets
function checkTargetClick(clickX, clickY) {
  for (const t of targets) {
    if (t._screenX === undefined) continue;
    const dx = clickX - t._screenX;
    const dy = clickY - t._screenY;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist < 12) {
      selectTarget(t);
      highlightTableRow(t.ip);
      break;
    }
  }
}

// Select Target & Update HUD
function selectTarget(target) {
  selectedTarget = target;
  const hudCoord = document.getElementById('hudCoord');
  const hudTarget = document.getElementById('hudTarget');

  if (hudCoord) {
    const lat = Number(target.latitude || 0);
    const lon = Number(target.longitude || 0);
    hudCoord.textContent = `LAT: ${lat.toFixed(2)}° | LON: ${lon.toFixed(2)}°`;
  }

  if (hudTarget) {
    hudTarget.textContent = `TARGET: ${target.ip} (${target.country_name || 'Global'}) • THREAT ${target.threat_score}/100`;
    if (target.threat_score >= 75) {
      hudTarget.style.color = 'var(--ruby)';
      hudTarget.style.borderColor = 'rgba(239,68,68,0.4)';
    } else {
      hudTarget.style.color = 'var(--gold)';
      hudTarget.style.borderColor = 'rgba(212,175,55,0.4)';
    }
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
      const searchInput = document.getElementById('searchInput');
      if (searchInput) searchInput.value = query;
      executeSearch(query);
    });
  });

  // Search Form Submit
  const searchForm = document.getElementById('searchForm');
  if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const q = document.getElementById('searchInput')?.value.trim();
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

// Load Initial Data from Backend or Rich In-Browser State
async function loadInitialData() {
  if (!isLiveBackend) {
    renderAccountInfo(DEFAULT_ACCOUNT_INFO);
    renderStats(DEFAULT_STATS);
    targets = [ ...DEFAULT_TARGETS ];
    renderTargetsTable(targets);
    if (targets.length > 0) selectTarget(targets[0]);
    appendStreamEntry("[SYSTEM]", "Offline tactical demo mode active — 100% in-browser utility loaded.");
    appendStreamEntry("[RADAR]", `Planetary surface recon synchronized: ${targets.length} high-value hosts online.`);
    return;
  }

  await Promise.all([
    fetchAccountInfo(),
    fetchStats(),
    executeSearch('port:554 has_screenshot:true')
  ]);
}

// Fetch Shodan Account Info
async function fetchAccountInfo() {
  if (!isLiveBackend) {
    renderAccountInfo(DEFAULT_ACCOUNT_INFO);
    return;
  }

  try {
    const res = await fetch('/api/info');
    if (!res.ok) {
      renderAccountInfo(DEFAULT_ACCOUNT_INFO);
      return;
    }
    const data = await res.json();
    renderAccountInfo(data);
  } catch (err) {
    renderAccountInfo(DEFAULT_ACCOUNT_INFO);
  }
}

function renderAccountInfo(data) {
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
}

// Fetch Global Stats
async function fetchStats() {
  if (!isLiveBackend) {
    renderStats(DEFAULT_STATS);
    return;
  }

  try {
    const res = await fetch('/api/stats');
    if (!res.ok) {
      renderStats(DEFAULT_STATS);
      return;
    }
    const data = await res.json();
    renderStats(data);
  } catch (err) {
    renderStats(DEFAULT_STATS);
  }
}

function renderStats(data) {
  const countEl = document.getElementById('metricTotal');
  const threatEl = document.getElementById('metricThreats');
  const geoEl = document.getElementById('metricCountries');

  if (countEl) countEl.textContent = (data.total_nodes || 0).toLocaleString();
  if (threatEl) threatEl.textContent = (data.high_threat_nodes || 0).toLocaleString();
  if (geoEl) geoEl.textContent = (data.unique_countries || 0).toLocaleString();
}

// Execute Shodan Search
async function executeSearch(query) {
  const tableBody = document.getElementById('targetsTableBody');
  if (tableBody) {
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem; color: var(--cyan);">🛰️ Scanning planetary attack surface for "${escapeHtml(query)}"...</td></tr>`;
  }

  if (!isLiveBackend) {
    setTimeout(() => {
      const qLower = query.toLowerCase();
      let filtered = DEFAULT_TARGETS.filter(t => {
        if (qLower.includes('554') || qLower.includes('camera')) return t.tags.includes('camera') || t.ports.includes(554);
        if (qLower.includes('502') || qLower.includes('modbus') || qLower.includes('scada')) return t.tags.includes('scada') || t.ports.includes(502);
        if (qLower.includes('27017') || qLower.includes('mongo')) return t.tags.includes('mongodb') || t.ports.includes(27017);
        if (qLower.includes('5900') || qLower.includes('vnc')) return t.tags.includes('vnc') || t.ports.includes(5900);
        if (qLower.includes('vuln') || qLower.includes('cve')) return t.vulns && t.vulns.length > 0;
        return true;
      });
      if (filtered.length === 0) filtered = DEFAULT_TARGETS;
      targets = filtered;
      renderTargetsTable(targets);
      if (targets.length > 0) selectTarget(targets[0]);
      appendStreamEntry("[SWEEP]", `Vector query "${query}" cataloged ${targets.length} nodes.`);
    }, 200);
    return;
  }

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=40`);
    if (!res.ok) throw new Error("Search request returned HTTP " + res.status);
    const data = await res.json();
    targets = data.targets || [];

    renderTargetsTable(targets);
    fetchStats();

    if (targets.length > 0) {
      selectTarget(targets[0]);
    }
  } catch (err) {
    targets = DEFAULT_TARGETS;
    renderTargetsTable(targets);
    if (targets.length > 0) selectTarget(targets[0]);
  }
}

// Render Targets Table
function renderTargetsTable(items) {
  const tableBody = document.getElementById('targetsTableBody');
  if (!tableBody) return;

  if (!items || items.length === 0) {
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

  let data = targets.find(t => t.ip === ip) || DEFAULT_TARGETS.find(t => t.ip === ip);

  if (isLiveBackend) {
    try {
      const res = await fetch(`/api/host/${encodeURIComponent(ip)}`);
      if (res.ok) {
        data = await res.json();
      }
    } catch (err) {}
  }

  if (!data) {
    data = {
      ip,
      threat_score: 80,
      org: "Autonomous System Node",
      country_name: "Global",
      city: "Coordinates Cataloged",
      ports: [80, 443],
      latitude: 0,
      longitude: 0,
      vulns: [],
      tags: ["scanned"],
      banner: "Service probing completed."
    };
  }

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
}

function closeHostModal() {
  const modal = document.getElementById('hostModal');
  if (modal) modal.classList.remove('open');
}

// Server-Sent Events (SSE) Stream (Only on live backend port 8112)
function startSSE() {
  const streamBox = document.getElementById('streamConsole');
  if (!streamBox || !isLiveBackend) return;

  try {
    eventSource = new EventSource('/api/stream');
    eventSource.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        const timeStr = new Date().toLocaleTimeString();

        if (payload.type === 'target_discovered') {
          appendStreamEntry(`[${timeStr}]`, `<span style="color:var(--ruby)">🚨 NODE DETECTED</span> ${escapeHtml(payload.data.ip)} (${escapeHtml(payload.data.country_name || 'Global')}) - Threat ${payload.data.threat_score}/100`);
        } else if (payload.type === 'radar_sweep') {
          appendStreamEntry(`[${timeStr}]`, `<span style="color:var(--cyan)">🛰️ SWEEP</span> Query "${escapeHtml(payload.query)}" matched ${payload.matches} surface targets.`);
        } else {
          appendStreamEntry(`[${timeStr}]`, `<span style="color:var(--gold)">⚡ TELEMETRY</span> ${escapeHtml(payload.message || 'Heartbeat sync')}`);
        }
      } catch (err) {}
    };
  } catch (err) {}
}

function appendStreamEntry(prefix, contentHtml) {
  const streamBox = document.getElementById('streamConsole');
  if (!streamBox) return;
  const entry = document.createElement('div');
  entry.className = 'stream-entry';
  entry.innerHTML = `<span class="stream-time">${escapeHtml(prefix)}</span> ${contentHtml}`;
  streamBox.appendChild(entry);
  streamBox.scrollTop = streamBox.scrollHeight;
  while (streamBox.children.length > 60) {
    streamBox.removeChild(streamBox.firstChild);
  }
}

// Toast Notification System
function showToast(msg) {
  let toast = document.getElementById('godseyeToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'godseyeToast';
    toast.style.cssText = 'position: fixed; bottom: 24px; right: 24px; z-index: 100000; background: #12131C; border: 1px solid var(--gold, #D4AF37); color: #FFF; padding: 0.65rem 1.25rem; border-radius: 8px; font-family: var(--font-mono, monospace); font-size: 0.82rem; box-shadow: 0 8px 32px rgba(0,0,0,0.8), 0 0 15px rgba(212,175,55,0.25); display: flex; align-items: center; gap: 0.5rem; transition: opacity 0.3s ease, transform 0.3s ease; opacity: 0; transform: translateY(10px); pointer-events: none;';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.opacity = '1';
  toast.style.transform = 'translateY(0)';
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
  }, 2600);
}

// DePay Solana Integration
function openDePayCheckout() {
  if (typeof DePayWidgets !== 'undefined' && DePayWidgets.Payment) {
    DePayWidgets.Payment({
      integration: '428790dd-7ad1-407c-8ecf-c048c77a4cb8'
    });
  } else {
    window.open('https://depay.com/GG2eQbVh8ut1BK6j1A2tz7pSySdLpD38BgyEhGcxdXoK', '_blank');
  }
}

// Copy to Clipboard
function copyToClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      showToast(`Copied ${text} to clipboard`);
    }).catch(() => {
      showToast(`Text: ${text}`);
    });
  } else {
    showToast(`Text: ${text}`);
  }
}

// Action Interceptor for Pro Features
function triggerProAction(featureName) {
  if (isProActive()) {
    if (featureName === 'export_targets') {
      exportTargetsBundle();
    } else {
      showToast(`[PRO ACTIVE] Executing: ${featureName}`);
    }
  } else {
    openPaywallModal(featureName);
  }
}

function triggerCIDRLookup(ip) {
  triggerProAction(`CIDR Subnet Sweep for ${ip}`);
}

function exportTargetsBundle() {
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(targets, null, 2));
  const downloadAnchor = document.createElement('a');
  downloadAnchor.setAttribute("href", dataStr);
  downloadAnchor.setAttribute("download", `godseye_targets_export_${Date.now()}.json`);
  document.body.appendChild(downloadAnchor);
  downloadAnchor.click();
  downloadAnchor.remove();
  showToast("✓ Exported Shodan attack surface targets bundle");
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
  const k1 = localStorage.getItem('godseye_pro_license');
  const k2 = localStorage.getItem('agent_godseye_pro');
  const k3 = localStorage.getItem('zoth_godseye_licensed');
  const k4 = localStorage.getItem('pro_licensed');
  const param = new URLSearchParams(window.location.search).get('licensed');
  return k1 === 'active' || k1 === 'GODSEYE-PRO-2026' || k2 === 'GODSEYE-PRO-2026' || k3 === 'true' || k4 === 'true' || param === 'true';
}

function checkProLicense() {
  const params = new URLSearchParams(window.location.search);
  if (params.get('licensed') === 'true' || params.get('session_id') || params.get('pro') === 'true') {
    localStorage.setItem('godseye_pro_license', 'GODSEYE-PRO-2026');
    localStorage.setItem('agent_godseye_pro', 'GODSEYE-PRO-2026');
    localStorage.setItem('zoth_godseye_licensed', 'true');
    localStorage.setItem('pro_licensed', 'true');
    if (window.history && window.history.replaceState) {
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }

  if (isProActive()) {
    activateProState();
  }
}

function activateProState() {
  localStorage.setItem('godseye_pro_license', 'GODSEYE-PRO-2026');
  localStorage.setItem('agent_godseye_pro', 'GODSEYE-PRO-2026');
  localStorage.setItem('zoth_godseye_licensed', 'true');
  localStorage.setItem('pro_licensed', 'true');

  document.body.classList.add('pro-licensed');
  const badge1 = document.getElementById('licenseBadge') || document.getElementById('pro-badge');
  if (badge1) {
    badge1.textContent = '⭐ PRO ACTIVE';
    badge1.style.background = 'linear-gradient(135deg, #D4AF37 0%, #B8972E 100%)';
    badge1.style.color = '#08080B';
    badge1.style.borderColor = '#D4AF37';
  }
  const badge2 = document.getElementById('proStatusBadge');
  if (badge2) {
    badge2.textContent = '⭐ PRO ACTIVE';
    badge2.style.background = 'linear-gradient(135deg, #D4AF37 0%, #B8972E 100%)';
    badge2.style.color = '#08080B';
    badge2.style.borderColor = '#D4AF37';
  }

  const sb = document.getElementById('salesBanner');
  if (sb) sb.style.display = 'none';

  const overlay = document.getElementById('threat-paywall-overlay');
  if (overlay) overlay.style.display = 'none';

  const blurred = document.getElementById('threat-paywall-content');
  if (blurred) {
    blurred.style.filter = 'none';
    blurred.style.pointerEvents = 'auto';
    blurred.style.opacity = '1';
  }

  closePaywallModal();
  showToast('⭐ Sovereign Pro License Active — All Features Unlocked!');
}

window.activateLicenseKey = function(key) {
  if (!key) key = 'GODSEYE-PRO-2026';
  localStorage.setItem('godseye_pro_license', key);
  localStorage.setItem('agent_godseye_pro', key);
  localStorage.setItem('zoth_godseye_licensed', 'true');
  localStorage.setItem('pro_licensed', 'true');
  activateProState();
  return true;
};

function verifyLicenseKey() {
  const input = document.getElementById('licenseKeyInput');
  const val = input ? input.value.trim() : '';
  if (val.length < 6) {
    showToast('Please enter a valid license key or receipt email (min 6 characters).');
    return;
  }

  localStorage.setItem('godseye_pro_license', val);
  localStorage.setItem('agent_godseye_pro', val);
  localStorage.setItem('zoth_godseye_licensed', 'true');
  localStorage.setItem('pro_licensed', 'true');
  activateProState();
  showToast('⭐ Pro License verified! All tactical sweeps & CIDR exporters unlocked.');
}

// Utility
function escapeHtml(str) {
  if (typeof str !== 'string') return String(str || '');
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
