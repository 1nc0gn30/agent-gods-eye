/**
 * AGENT GOD'S EYE v2.6.0 — Dual-Theme 3D Kinetic Planetary Radar & OSINT Cockpit
 * Zero DOM XSS sinks · Live named SSE telemetry · Honest live/offline status · RFC 5737 demo fallback
 * Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform
 */

(function () {
  'use strict';

  const OFFLINE_ACCOUNT_INFO = {
    api_configured: false,
    mode: 'offline_demo',
    plan: 'offline',
    query_credits: 0,
    scan_credits: 0,
    status: 'offline_demo',
  };

  // Strictly RFC 5737 documentation IPs ONLY for static hosting fallback
  const RFC5737_STATIC_TARGETS = [
    {
      ip: '198.51.100.42',
      hostname: 'cam-gate01.test.invalid',
      country: 'US',
      country_name: 'United States',
      city: 'Ashburn',
      org: 'Perimeter Vision Lab (RFC 5737 Demo)',
      latitude: 39.0438,
      longitude: -77.4874,
      threat_score: 85,
      threat_level: 'CRITICAL',
      port: 554,
      ports: [554, 80, 8000],
      tags: ['camera', 'rtsp', 'surveillance', 'screenshot'],
      vulns: ['CVE-2021-36260'],
      product: 'RTSP Stream Server',
      banner: 'RTSP/1.0 200 OK\r\nServer: H.264 IPCam Streamer\r\nPublic: DESCRIBE, SETUP, TEARDOWN, PLAY',
      is_simulated: true,
    },
    {
      ip: '198.51.100.77',
      hostname: 'dvr-harbor02.test.invalid',
      country: 'SG',
      country_name: 'Singapore',
      city: 'Singapore',
      org: 'Harbor Optics Testbed (RFC 5737 Demo)',
      latitude: 1.3521,
      longitude: 103.8198,
      threat_score: 85,
      threat_level: 'CRITICAL',
      port: 554,
      ports: [554, 37777],
      tags: ['camera', 'rtsp', 'dahua', 'screenshot'],
      vulns: ['CVE-2021-33044'],
      product: 'Dahua RTSP Gateway',
      banner: 'RTSP/1.0 200 OK\r\nServer: Dahua-RTSP-Gateway\r\nChannels: 1-8',
      is_simulated: true,
    },
    {
      ip: '203.0.113.19',
      hostname: 'scada-substation04.test.invalid',
      country: 'DE',
      country_name: 'Germany',
      city: 'Nuremberg',
      org: 'GridSim Substation Lab (RFC 5737 Demo)',
      latitude: 49.4521,
      longitude: 11.0767,
      threat_score: 75,
      threat_level: 'CRITICAL',
      port: 502,
      ports: [502, 102],
      tags: ['scada', 'modbus', 'ics', 'industrial'],
      vulns: ['CVE-2022-45788'],
      product: 'Modbus TCP Gateway',
      banner: 'Modbus Unit ID: 1, Function Code: 0x03 (Read Holding Registers), PLC Modicon M340',
      is_simulated: true,
    },
    {
      ip: '203.0.113.55',
      hostname: 'plc-s7-plant02.test.invalid',
      country: 'GB',
      country_name: 'United Kingdom',
      city: 'London',
      org: 'Nordic Turbine Control Sim (RFC 5737 Demo)',
      latitude: 51.5074,
      longitude: -0.1278,
      threat_score: 75,
      threat_level: 'CRITICAL',
      port: 502,
      ports: [102, 502, 44818],
      tags: ['scada', 'modbus', 'siemens', 'ics'],
      vulns: ['CVE-2019-13945'],
      product: 'Siemens S7 / Modbus PLC',
      banner: 'Siemens S7-1200 CPU 1214C Modbus TCP Slave Active',
      is_simulated: true,
    },
    {
      ip: '192.0.2.78',
      hostname: 'mongo-replica01.test.invalid',
      country: 'JP',
      country_name: 'Japan',
      city: 'Tokyo',
      org: 'Kanto Document Store Lab (RFC 5737 Demo)',
      latitude: 35.6895,
      longitude: 139.6917,
      threat_score: 85,
      threat_level: 'CRITICAL',
      port: 27017,
      ports: [27017],
      tags: ['database', 'mongodb', 'unauthenticated'],
      vulns: ['CVE-2019-2386'],
      product: 'MongoDB Server',
      banner: 'MongoDB Server Information: version 6.0.4 authMechanism: NONE',
      is_simulated: true,
    },
    {
      ip: '198.51.100.101',
      hostname: 'vnc-desktop-paris.test.invalid',
      country: 'FR',
      country_name: 'France',
      city: 'Paris',
      org: 'Seine Remote Lab (RFC 5737 Demo)',
      latitude: 48.8566,
      longitude: 2.3522,
      threat_score: 90,
      threat_level: 'CRITICAL',
      port: 5900,
      ports: [5900],
      tags: ['vnc', 'remote-desktop', 'screenshot', 'unauthenticated'],
      vulns: ['CVE-2023-38606'],
      product: 'RFB / VNC Remote Display',
      banner: 'RFB 003.008\nSecurity types: None (1) authentication disabled',
      is_simulated: true,
    },
  ];

  // Runtime state
  let targets = [];
  let selectedTarget = null;
  let rotationX = 0.2;
  let rotationY = 0;
  let isDragging = false;
  let lastMouseX = 0;
  let lastMouseY = 0;
  const reducedMotion = Boolean(
    window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );
  let autoRotate = !reducedMotion;
  let eventSource = null;
  let isLiveBackend = false;
  let ambientStars = null;
  let lastCanvasWidth = 0;
  let lastCanvasHeight = 0;

  const canvas = document.getElementById('globeCanvas');
  const ctx = canvas ? canvas.getContext('2d') : null;

  function isLightTheme() {
    return document.documentElement.getAttribute('data-theme') === 'light';
  }

  function applyTheme(theme) {
    const t = theme === 'light' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', t);
    try {
      window.localStorage.setItem('age-theme', t);
    } catch (_) {}
    const label = document.getElementById('themeToggleLabel');
    if (label) {
      label.textContent = t === 'light' ? '☾ Dark' : '☀ Light';
    }
  }

  // Probe live backend dynamically via /api/health on window.location.origin
  async function detectLiveBackend() {
    try {
      const res = await fetch('/api/health', { headers: { Accept: 'application/json' } });
      if (!res.ok) return false;
      const ct = res.headers.get('content-type') || '';
      if (!ct.includes('application/json')) return false;
      const data = await res.json();
      return Boolean(data && data.status === 'ok' && data.service === 'agent-gods-eye');
    } catch (_) {
      return false;
    }
  }

  document.addEventListener('DOMContentLoaded', async () => {
    applyTheme(document.documentElement.getAttribute('data-theme') || 'dark');
    setupCanvas();
    setupEventListeners();
    isLiveBackend = await detectLiveBackend();
    await loadInitialData();
    if (isLiveBackend) {
      startSSE();
    } else {
      const sseTag = document.getElementById('sseStatusTag');
      if (sseTag) sseTag.textContent = '● STATIC DEMO';
    }
    requestAnimationFrame(renderLoop);
  });

  // Canvas Setup & Resize (regenerates stars on resize!)
  function setupCanvas() {
    if (!canvas) return;
    const resize = () => {
      if (!canvas.parentElement) return;
      const rect = canvas.parentElement.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.floor(rect.width * dpr));
      canvas.height = Math.max(1, Math.floor(rect.height * dpr));
      if (ctx) {
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      }
      if (Math.abs(rect.width - lastCanvasWidth) > 8 || Math.abs(rect.height - lastCanvasHeight) > 8) {
        lastCanvasWidth = rect.width;
        lastCanvasHeight = rect.height;
        ambientStars = null; // regenerate cleanly for new dimensions
      }
    };
    window.addEventListener('resize', resize);
    resize();

    canvas.addEventListener('mousedown', (e) => {
      isDragging = true;
      autoRotate = false;
      lastMouseX = e.clientX;
      lastMouseY = e.clientY;
    });

    window.addEventListener('mouseup', () => {
      if (!isDragging) return;
      isDragging = false;
      if (!reducedMotion) {
        setTimeout(() => { autoRotate = true; }, 4000);
      }
    });

    canvas.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const dx = e.clientX - lastMouseX;
      const dy = e.clientY - lastMouseY;
      rotationY += dx * 0.006;
      rotationX = Math.max(-Math.PI / 2.2, Math.min(Math.PI / 2.2, rotationX + dy * 0.006));
      lastMouseX = e.clientX;
      lastMouseY = e.clientY;
    });

    canvas.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        isDragging = true;
        autoRotate = false;
        lastMouseX = e.touches[0].clientX;
        lastMouseY = e.touches[0].clientY;
      }
    }, { passive: true });

    window.addEventListener('touchend', () => {
      if (!isDragging) return;
      isDragging = false;
      if (!reducedMotion) {
        setTimeout(() => { autoRotate = true; }, 4000);
      }
    });

    canvas.addEventListener('touchmove', (e) => {
      if (!isDragging || e.touches.length !== 1) return;
      const dx = e.touches[0].clientX - lastMouseX;
      const dy = e.touches[0].clientY - lastMouseY;
      rotationY += dx * 0.008;
      rotationX = Math.max(-Math.PI / 2.2, Math.min(Math.PI / 2.2, rotationX + dy * 0.008));
      lastMouseX = e.touches[0].clientX;
      lastMouseY = e.touches[0].clientY;
    }, { passive: true });

    canvas.addEventListener('click', (e) => {
      const rect = canvas.getBoundingClientRect();
      checkTargetClick(e.clientX - rect.left, e.clientY - rect.top);
    });
  }

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
    return {
      screenX: cx + x1 * radius * scale,
      screenY: cy - y2 * radius * scale,
      zIndex: z2,
      visible: z2 > -0.1,
    };
  }

  function latLonToVector(lat, lon) {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    return {
      x: -(Math.sin(phi) * Math.cos(theta)),
      y: Math.cos(phi),
      z: Math.sin(phi) * Math.sin(theta),
    };
  }

  function renderLoop(timestamp) {
    if (ctx && canvas && canvas.parentElement) {
      const w = canvas.parentElement.clientWidth;
      const h = canvas.parentElement.clientHeight;
      ctx.clearRect(0, 0, w, h);

      if (autoRotate && !isDragging && !reducedMotion) {
        rotationY += 0.0022;
      }

      const cx = w / 2;
      const cy = h / 2;
      const radius = Math.min(w, h) * 0.38;
      const light = isLightTheme();

      drawAmbientParticles(w, h, light);

      // Globe atmosphere halo
      const grad = ctx.createRadialGradient(cx, cy, radius * 0.78, cx, cy, radius * 1.22);
      if (light) {
        grad.addColorStop(0, 'rgba(3, 105, 161, 0.12)');
        grad.addColorStop(0.55, 'rgba(154, 114, 9, 0.08)');
        grad.addColorStop(1, 'rgba(247, 243, 233, 0)');
      } else {
        grad.addColorStop(0, 'rgba(6, 182, 212, 0.16)');
        grad.addColorStop(0.5, 'rgba(212, 175, 55, 0.06)');
        grad.addColorStop(1, 'rgba(8, 8, 11, 0)');
      }
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(cx, cy, radius * 1.22, 0, Math.PI * 2);
      ctx.fill();

      drawGlobeWireframe(cx, cy, radius, light);
      drawTargetNodes(cx, cy, radius, timestamp, light);

      if (selectedTarget) {
        drawTargetReticle(light);
      }
    }
    requestAnimationFrame(renderLoop);
  }

  function drawAmbientParticles(w, h, light) {
    if (!ambientStars) {
      ambientStars = [];
      for (let i = 0; i < 42; i++) {
        ambientStars.push({
          x: Math.random() * w,
          y: Math.random() * h,
          size: Math.random() * 1.4 + 0.5,
          alpha: Math.random() * 0.45 + 0.15,
        });
      }
    }
    ctx.save();
    for (const s of ambientStars) {
      ctx.fillStyle = light
        ? `rgba(154, 114, 9, ${s.alpha * 0.45})`
        : `rgba(255, 255, 255, ${s.alpha})`;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  function drawGlobeWireframe(cx, cy, radius, light) {
    ctx.save();
    ctx.strokeStyle = light ? 'rgba(3, 105, 161, 0.28)' : 'rgba(6, 182, 212, 0.22)';
    ctx.lineWidth = 1;

    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.stroke();

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

  function drawTargetNodes(cx, cy, radius, timestamp, light) {
    ctx.save();
    for (const t of targets) {
      const lat = Number(t.latitude || 0);
      const lon = Number(t.longitude || 0);
      const v = latLonToVector(lat, lon);
      const p = project3D(v.x, v.y, v.z, cx, cy, radius);
      if (!p.visible) continue;

      t._screenX = p.screenX;
      t._screenY = p.screenY;

      let nodeColor = light ? '#0369A1' : '#22D3EE';
      if (t.threat_score >= 75) nodeColor = light ? '#BE123C' : '#EF4444';
      else if (t.threat_score >= 40) nodeColor = light ? '#B45309' : '#F59E0B';

      if (t.threat_score >= 75 && !reducedMotion) {
        const wave = (Math.sin(timestamp * 0.005 + lat) + 1) / 2;
        ctx.beginPath();
        ctx.arc(p.screenX, p.screenY, 7 + wave * 9, 0, Math.PI * 2);
        ctx.strokeStyle = light
          ? `rgba(190, 18, 60, ${0.42 - wave * 0.3})`
          : `rgba(239, 68, 68, ${0.42 - wave * 0.3})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      ctx.beginPath();
      ctx.arc(p.screenX, p.screenY, selectedTarget && selectedTarget.ip === t.ip ? 5.5 : 3.8, 0, Math.PI * 2);
      ctx.fillStyle = nodeColor;
      ctx.shadowColor = nodeColor;
      ctx.shadowBlur = light ? 4 : 8;
      ctx.fill();

      if (selectedTarget && selectedTarget.ip === t.ip) {
        ctx.shadowBlur = 0;
        ctx.font = '700 11px ui-monospace, monospace';
        ctx.fillStyle = light ? '#1C1917' : '#D4AF37';
        ctx.fillText(`[${t.ip}]`, p.screenX + 10, p.screenY - 8);
      }
    }
    ctx.restore();
  }

  function drawTargetReticle(light) {
    if (!selectedTarget || selectedTarget._screenX === undefined) return;
    const x = selectedTarget._screenX;
    const y = selectedTarget._screenY;
    ctx.save();
    ctx.strokeStyle = light ? '#9A7209' : '#D4AF37';
    ctx.lineWidth = 1.6;
    const sz = 12;
    ctx.beginPath();
    ctx.moveTo(x - sz, y - sz + 4); ctx.lineTo(x - sz, y - sz); ctx.lineTo(x - sz + 4, y - sz);
    ctx.moveTo(x + sz - 4, y - sz); ctx.lineTo(x + sz, y - sz); ctx.lineTo(x + sz, y - sz + 4);
    ctx.moveTo(x - sz, y + sz - 4); ctx.lineTo(x - sz, y + sz); ctx.lineTo(x - sz + 4, y + sz);
    ctx.moveTo(x + sz - 4, y + sz); ctx.lineTo(x + sz, y + sz); ctx.lineTo(x + sz, y + sz - 4);
    ctx.stroke();
    ctx.restore();
  }

  function checkTargetClick(clickX, clickY) {
    for (const t of targets) {
      if (t._screenX === undefined) continue;
      const dist = Math.hypot(clickX - t._screenX, clickY - t._screenY);
      if (dist < 14) {
        selectTarget(t);
        highlightTableRow(t.ip);
        break;
      }
    }
  }

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
      const simNote = target.is_simulated ? ' [DEMO]' : '';
      hudTarget.textContent = `TARGET: ${target.ip} (${target.country_name || 'Global'}) · THREAT ${target.threat_score}/100${simNote}`;
    }
  }

  function setupEventListeners() {
    const themeBtn = document.getElementById('btnThemeToggle');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => {
        applyTheme(isLightTheme() ? 'dark' : 'light');
      });
    }

    // Solana copy buttons (no inline onclick)
    document.querySelectorAll('[data-solana]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const addr = btn.getAttribute('data-solana') || '';
        copyToClipboard(addr);
      });
    });

    // Export buttons (JSON & CSV)
    document.querySelectorAll('[data-export-format]').forEach((btn) => {
      btn.addEventListener('click', () => {
        exportTargets(btn.getAttribute('data-export-format') || 'json');
      });
    });

    // Modal close button & backdrop click & Escape key
    const closeBtn = document.getElementById('btnCloseHostModal');
    if (closeBtn) closeBtn.addEventListener('click', closeHostModal);
    const modalBackdrop = document.getElementById('hostModal');
    if (modalBackdrop) {
      modalBackdrop.addEventListener('click', (e) => {
        if (e.target === modalBackdrop) closeHostModal();
      });
    }
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeHostModal();
    });

    // Preset Chips
    document.querySelectorAll('.preset-chip').forEach((btn) => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.preset-chip').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        const query = btn.getAttribute('data-query') || '';
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
        const q = (document.getElementById('searchInput')?.value || '').trim();
        executeSearch(q || 'port:554 has_screenshot:true');
      });
    }

    // Globe controls
    const btn3D = document.getElementById('btnView3D');
    const btnReset = document.getElementById('btnResetGlobe');
    if (btn3D) {
      btn3D.textContent = autoRotate ? '⏸ Pause Orbit' : '▶ Resume Orbit';
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

    // Delegated table click + keyboard activation (zero inline onclick)
    const tableBody = document.getElementById('targetsTableBody');
    if (tableBody) {
      tableBody.addEventListener('click', (e) => {
        const inspectBtn = e.target.closest('button[data-ip]');
        if (inspectBtn) {
          e.stopPropagation();
          inspectHost(inspectBtn.getAttribute('data-ip') || '');
          return;
        }
        const row = e.target.closest('tr[data-ip]');
        if (row) {
          inspectHost(row.getAttribute('data-ip') || '');
        }
      });
      tableBody.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          const row = e.target.closest('tr[data-ip]');
          if (row && e.target === row) {
            e.preventDefault();
            inspectHost(row.getAttribute('data-ip') || '');
          }
        }
      });
    }
  }

  async function loadInitialData() {
    if (!isLiveBackend) {
      renderAccountInfo(OFFLINE_ACCOUNT_INFO);
      targets = RFC5737_STATIC_TARGETS.slice();
      renderStats({
        total_nodes: targets.length,
        high_threat_nodes: targets.filter((t) => t.threat_score >= 75).length,
        unique_countries: new Set(targets.map((t) => t.country)).size,
      });
      renderTargetsTable(targets);
      if (targets.length > 0) selectTarget(targets[0]);
      appendStreamEntry('[DEMO]', 'STATIC', 'Static preview mode — RFC 5737 documentation catalog loaded (run local daemon :8112 for live SQLite & Shodan).', 'stream-tag-gold');
      return;
    }

    await Promise.all([
      fetchAccountInfo(),
      fetchStats(),
      executeSearch('port:554 has_screenshot:true'),
    ]);
  }

  async function fetchAccountInfo() {
    try {
      const res = await fetch('/api/info');
      if (!res.ok) {
        renderAccountInfo(OFFLINE_ACCOUNT_INFO);
        return;
      }
      renderAccountInfo(await res.json());
    } catch (_) {
      renderAccountInfo(OFFLINE_ACCOUNT_INFO);
    }
  }

  function formatPlanLabel(data) {
    if (data && data.api_configured && data.mode === 'live_shodan') {
      const raw = String(data.plan || 'LIVE').trim().toUpperCase();
      return raw.length > 10 ? raw.slice(0, 10) : raw;
    }
    return 'OFFLINE';
  }

  function renderAccountInfo(data) {
    const planEl = document.getElementById('metricPlan');
    const creditsEl = document.getElementById('metricCredits');
    const statusBadge = document.getElementById('shodanStatus');
    const statusText = document.getElementById('shodanStatusText');
    const embedMode = document.getElementById('embedModeText');

    const isLiveKey = Boolean(data && data.api_configured === true && data.mode === 'live_shodan');

    if (planEl) {
      planEl.textContent = formatPlanLabel(data);
    }
    if (creditsEl) {
      const qc = Number((data && data.query_credits) || 0);
      const sc = Number((data && data.scan_credits) || 0);
      creditsEl.textContent = isLiveKey
        ? `${qc.toLocaleString()} Query / ${sc.toLocaleString()} Scan`
        : 'RFC 5737 Demo · Set SHODAN_API_KEY';
    }
    if (statusBadge && statusText) {
      statusBadge.classList.toggle('status-live', isLiveKey);
      statusBadge.classList.toggle('status-offline', !isLiveKey);
      statusText.textContent = isLiveKey ? 'SHODAN LIVE' : 'OFFLINE DEMO';
    }
    if (embedMode) {
      embedMode.textContent = isLiveKey ? '● SHODAN LIVE (:8112)' : '● OFFLINE DEMO (:8112)';
    }
  }

  async function fetchStats() {
    try {
      const res = await fetch('/api/stats');
      if (!res.ok) return;
      renderStats(await res.json());
    } catch (_) {}
  }

  function renderStats(data) {
    const countEl = document.getElementById('metricTotal');
    const threatEl = document.getElementById('metricThreats');
    const geoEl = document.getElementById('metricCountries');

    if (countEl) countEl.textContent = Number(data.total_nodes || data.total_targets || 0).toLocaleString();
    if (threatEl) threatEl.textContent = Number(data.high_threat_nodes || 0).toLocaleString();
    if (geoEl) geoEl.textContent = Number(data.unique_countries || 0).toLocaleString();
  }

  function filterStaticTargets(query) {
    const qLower = String(query || '').toLowerCase();
    return RFC5737_STATIC_TARGETS.filter((t) => {
      if (qLower.includes('554') || qLower.includes('camera') || qLower.includes('rtsp')) {
        return t.ports.includes(554) || t.tags.includes('camera');
      }
      if (qLower.includes('502') || qLower.includes('modbus') || qLower.includes('scada')) {
        return t.ports.includes(502) || t.tags.includes('scada');
      }
      if (qLower.includes('27017') || qLower.includes('mongo')) {
        return t.ports.includes(27017) || t.tags.includes('mongodb');
      }
      if (qLower.includes('5900') || qLower.includes('vnc')) {
        return t.ports.includes(5900) || t.tags.includes('vnc');
      }
      if (qLower.includes('vuln') || qLower.includes('cve')) {
        return Array.isArray(t.vulns) && t.vulns.length > 0;
      }
      return true;
    });
  }

  async function executeSearch(query) {
    const tableBody = document.getElementById('targetsTableBody');
    if (tableBody) {
      tableBody.textContent = '';
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 6;
      td.className = 'table-placeholder';
      td.textContent = `Scanning attack surface for "${query}"...`;
      tr.appendChild(td);
      tableBody.appendChild(tr);
    }

    if (!isLiveBackend) {
      targets = filterStaticTargets(query);
      renderTargetsTable(targets);
      if (targets.length > 0) selectTarget(targets[0]);
      appendStreamEntry('[SWEEP]', 'DEMO', `Vector query "${query}" matched ${targets.length} RFC 5737 hosts.`, 'stream-tag-cyan');
      return;
    }

    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=40`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      targets = Array.isArray(data.targets) ? data.targets : [];

      renderTargetsTable(targets);
      fetchStats();

      if (targets.length > 0) {
        selectTarget(targets[0]);
      } else {
        const hudTarget = document.getElementById('hudTarget');
        if (hudTarget) hudTarget.textContent = `TARGET: 0 MATCHES FOR "${query}"`;
      }
    } catch (err) {
      appendStreamEntry('[ERROR]', 'SEARCH', `Query failed: ${err.message}`, 'stream-tag-ruby');
      renderTargetsTable([]);
    }
  }

  // Safe DOM table builder — ZERO innerHTML interpolation!
  function renderTargetsTable(items) {
    const tableBody = document.getElementById('targetsTableBody');
    if (!tableBody) return;
    tableBody.textContent = '';

    if (!items || items.length === 0) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 6;
      td.className = 'table-placeholder';
      td.textContent = 'No targets cataloged for this vector query.';
      tr.appendChild(td);
      tableBody.appendChild(tr);
      return;
    }

    for (const t of items) {
      const tr = document.createElement('tr');
      const ipStr = String(t.ip || '');
      tr.setAttribute('data-ip', ipStr);
      tr.setAttribute('tabindex', '0');
      tr.setAttribute('role', 'button');
      tr.setAttribute('aria-label', `Inspect host ${ipStr}`);

      // Col 1: Threat Score
      const tdThreat = document.createElement('td');
      const score = Number(t.threat_score || 0);
      const pill = document.createElement('span');
      pill.className = `threat-score-pill ${score >= 75 ? 'threat-high' : score >= 40 ? 'threat-med' : 'threat-low'}`;
      pill.textContent = `${score}/100`;
      tdThreat.appendChild(pill);
      tr.appendChild(tdThreat);

      // Col 2: IP & Hostname
      const tdIp = document.createElement('td');
      const ipWrap = document.createElement('div');
      const ipStrong = document.createElement('strong');
      ipStrong.className = 'ip-primary';
      ipStrong.textContent = ipStr;
      ipWrap.appendChild(ipStrong);
      if (t.is_simulated) {
        const simBadge = document.createElement('span');
        simBadge.className = 'sim-pill';
        simBadge.textContent = 'DEMO';
        ipWrap.appendChild(simBadge);
      }
      tdIp.appendChild(ipWrap);
      const hostSub = document.createElement('div');
      hostSub.className = 'cell-sub';
      hostSub.textContent = Array.isArray(t.hostnames) ? t.hostnames.join(', ') : String(t.hostname || '');
      tdIp.appendChild(hostSub);
      tr.appendChild(tdIp);

      // Col 3: Location
      const tdLoc = document.createElement('td');
      const countryDiv = document.createElement('div');
      countryDiv.textContent = String(t.country_name || 'Unknown');
      const cityDiv = document.createElement('div');
      cityDiv.className = 'cell-sub';
      cityDiv.textContent = String(t.city || '');
      tdLoc.appendChild(countryDiv);
      tdLoc.appendChild(cityDiv);
      tr.appendChild(tdLoc);

      // Col 4: Org
      const tdOrg = document.createElement('td');
      tdOrg.className = 'cell-org';
      tdOrg.textContent = String(t.org || t.isp || 'Unknown');
      tdOrg.title = tdOrg.textContent;
      tr.appendChild(tdOrg);

      // Col 5: Ports
      const tdPorts = document.createElement('td');
      const portsList = Array.isArray(t.ports) && t.ports.length ? t.ports : (t.port ? [t.port] : []);
      for (const p of portsList.slice(0, 4)) {
        const badge = document.createElement('span');
        badge.className = 'port-badge';
        badge.textContent = String(p);
        tdPorts.appendChild(badge);
      }
      tr.appendChild(tdPorts);

      // Col 6: Inspect Action (strict >= 44px touch target)
      const tdAct = document.createElement('td');
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn btn-outline btn-compact';
      btn.setAttribute('data-ip', ipStr);
      btn.textContent = 'Inspect';
      tdAct.appendChild(btn);
      tr.appendChild(tdAct);

      tableBody.appendChild(tr);
    }
  }

  function highlightTableRow(ip) {
    document.querySelectorAll('#targetsTableBody tr').forEach((r) => {
      r.classList.toggle('row-selected', r.getAttribute('data-ip') === ip);
    });
  }

  // Safe DOM host inspection modal — ZERO innerHTML interpolation!
  async function inspectHost(ip) {
    const modal = document.getElementById('hostModal');
    const modalContent = document.getElementById('hostModalContent');
    if (!modal || !modalContent) return;

    modal.classList.add('open');
    modalContent.textContent = '';
    const loading = document.createElement('div');
    loading.className = 'table-placeholder';
    loading.textContent = `Interrogating host intelligence for ${ip}...`;
    modalContent.appendChild(loading);

    let data = targets.find((t) => t.ip === ip) || RFC5737_STATIC_TARGETS.find((t) => t.ip === ip);

    if (isLiveBackend) {
      try {
        const res = await fetch(`/api/host/${encodeURIComponent(ip)}`);
        const payload = await res.json();
        if (!res.ok) {
          modalContent.textContent = '';
          const errBox = document.createElement('div');
          errBox.className = 'table-placeholder';
          errBox.textContent = `Blocked (${res.status}): ${payload.error || 'Invalid target IP'}`;
          modalContent.appendChild(errBox);
          return;
        }
        data = payload;
      } catch (_) {}
    }

    if (!data) {
      modalContent.textContent = '';
      const empty = document.createElement('div');
      empty.className = 'table-placeholder';
      empty.textContent = `No cached intelligence found for ${ip}.`;
      modalContent.appendChild(empty);
      return;
    }

    modalContent.textContent = '';

    // Top row
    const top = document.createElement('div');
    top.className = 'modal-host-header';
    const left = document.createElement('div');
    const h2 = document.createElement('h2');
    h2.className = 'modal-host-ip';
    h2.textContent = String(data.ip || data.ip_str || ip);
    const sub = document.createElement('div');
    sub.className = 'card-hint';
    sub.textContent = `${data.org || data.isp || 'Unknown Org'} · ${data.country_name || 'Global'} (${data.city || 'N/A'})`;
    left.appendChild(h2);
    left.appendChild(sub);

    const score = Number(data.threat_score || 0);
    const pill = document.createElement('span');
    pill.className = `threat-score-pill ${score >= 75 ? 'threat-high' : score >= 40 ? 'threat-med' : 'threat-low'}`;
    pill.textContent = `THREAT: ${score} / 100`;
    top.appendChild(left);
    top.appendChild(pill);
    modalContent.appendChild(top);

    // Grid
    const grid = document.createElement('div');
    grid.className = 'modal-grid';

    const boxPorts = document.createElement('div');
    boxPorts.className = 'modal-stat-box';
    const lblPorts = document.createElement('div');
    lblPorts.className = 'modal-stat-label';
    lblPorts.textContent = 'Open Ports';
    const valPorts = document.createElement('div');
    valPorts.className = 'ip-primary';
    const portsArr = Array.isArray(data.ports) && data.ports.length ? data.ports : (data.port ? [data.port] : []);
    valPorts.textContent = portsArr.length ? portsArr.join(', ') : 'None';
    boxPorts.appendChild(lblPorts);
    boxPorts.appendChild(valPorts);

    const boxGeo = document.createElement('div');
    boxGeo.className = 'modal-stat-box';
    const lblGeo = document.createElement('div');
    lblGeo.className = 'modal-stat-label';
    lblGeo.textContent = 'Geolocation Vector';
    const valGeo = document.createElement('div');
    valGeo.className = 'text-mono';
    valGeo.textContent = `${Number(data.latitude || 0).toFixed(4)}° N, ${Number(data.longitude || 0).toFixed(4)}° E`;
    boxGeo.appendChild(lblGeo);
    boxGeo.appendChild(valGeo);

    grid.appendChild(boxPorts);
    grid.appendChild(boxGeo);
    modalContent.appendChild(grid);

    // CVEs
    const cveWrap = document.createElement('div');
    cveWrap.style.marginBottom = '1rem';
    const cveLbl = document.createElement('div');
    cveLbl.className = 'modal-stat-label';
    cveLbl.style.marginBottom = '0.35rem';
    cveLbl.textContent = 'Correlated CVEs';
    cveWrap.appendChild(cveLbl);
    const cveList = Array.isArray(data.vulns) ? data.vulns : [];
    if (cveList.length > 0) {
      for (const v of cveList) {
        const badge = document.createElement('span');
        badge.className = 'threat-score-pill threat-high';
        badge.style.marginRight = '0.35rem';
        badge.textContent = String(v);
        cveWrap.appendChild(badge);
      }
    } else {
      const none = document.createElement('span');
      none.className = 'stream-tag-emerald';
      none.textContent = 'No CVEs flagged';
      cveWrap.appendChild(none);
    }
    modalContent.appendChild(cveWrap);

    // Tags
    const tagWrap = document.createElement('div');
    tagWrap.style.marginBottom = '1rem';
    const tagLbl = document.createElement('div');
    tagLbl.className = 'modal-stat-label';
    tagLbl.style.marginBottom = '0.35rem';
    tagLbl.textContent = 'Classification Tags';
    tagWrap.appendChild(tagLbl);
    const tags = Array.isArray(data.tags) ? data.tags : [];
    if (tags.length > 0) {
      for (const tg of tags) {
        const b = document.createElement('span');
        b.className = 'port-badge';
        b.textContent = String(tg);
        tagWrap.appendChild(b);
      }
    } else {
      const none = document.createElement('span');
      none.className = 'cell-sub';
      none.textContent = 'None';
      tagWrap.appendChild(none);
    }
    modalContent.appendChild(tagWrap);

    // Banner
    const banWrap = document.createElement('div');
    const banLbl = document.createElement('div');
    banLbl.className = 'modal-stat-label';
    banLbl.style.marginBottom = '0.35rem';
    banLbl.textContent = 'Raw Service Banner Preview';
    const pre = document.createElement('pre');
    pre.className = 'modal-banner-pre';
    pre.textContent = String(data.banner || data.banner_snippet || 'No raw banner returned.');
    banWrap.appendChild(banLbl);
    banWrap.appendChild(pre);
    modalContent.appendChild(banWrap);

    // Modal action buttons (delegated, zero inline onclick)
    const actions = document.createElement('div');
    actions.className = 'modal-actions-row';
    const btnCopy = document.createElement('button');
    btnCopy.type = 'button';
    btnCopy.className = 'btn btn-outline';
    btnCopy.textContent = 'Copy IP';
    btnCopy.addEventListener('click', () => copyToClipboard(String(data.ip || ip)));

    const btnCidr = document.createElement('button');
    btnCidr.type = 'button';
    btnCidr.className = 'btn btn-primary';
    btnCidr.textContent = '⚡ Trace Subnet CIDR';
    btnCidr.addEventListener('click', () => triggerCIDRLookup(String(data.ip || ip)));

    actions.appendChild(btnCopy);
    actions.appendChild(btnCidr);
    modalContent.appendChild(actions);
  }

  function closeHostModal() {
    const modal = document.getElementById('hostModal');
    if (modal) modal.classList.remove('open');
  }

  // Subscribe to NAMED SSE events (init, search, targets_updated) + message fallback!
  function startSSE() {
    const streamBox = document.getElementById('streamConsole');
    const sseTag = document.getElementById('sseStatusTag');
    if (!streamBox || !isLiveBackend) return;

    try {
      eventSource = new EventSource('/api/stream');

      eventSource.addEventListener('open', () => {
        if (sseTag) sseTag.textContent = '● SSE LIVE';
      });

      eventSource.addEventListener('init', (e) => {
        try {
          const payload = JSON.parse(e.data);
          const timeStr = new Date().toLocaleTimeString();
          const modeLabel = payload.mode === 'live_shodan' ? 'SHODAN LIVE' : 'OFFLINE DEMO';
          appendStreamEntry(
            `[${timeStr}]`,
            'SYNC',
            `Stream connected (${modeLabel}) · ${payload.total_targets || 0} targets, ${payload.unique_countries || 0} countries.`,
            'stream-tag-emerald'
          );
          if (sseTag) sseTag.textContent = '● SSE LIVE';
        } catch (_) {}
      });

      eventSource.addEventListener('search', (e) => {
        try {
          const payload = JSON.parse(e.data);
          const timeStr = new Date().toLocaleTimeString();
          const tag = payload.is_simulated ? 'DEMO SWEEP' : 'LIVE SWEEP';
          appendStreamEntry(
            `[${timeStr}]`,
            tag,
            `Query "${payload.query || ''}" matched ${payload.returned_count || 0}/${payload.total_hits || 0} targets.`,
            'stream-tag-cyan'
          );
        } catch (_) {}
      });

      eventSource.addEventListener('targets_updated', (e) => {
        try {
          const payload = JSON.parse(e.data);
          const timeStr = new Date().toLocaleTimeString();
          appendStreamEntry(
            `[${timeStr}]`,
            'DB SYNC',
            `Cataloged ${payload.count || 0} target nodes (${payload.simulated_count || 0} simulated).`,
            'stream-tag-gold'
          );
        } catch (_) {}
      });

      eventSource.onmessage = (e) => {
        try {
          const payload = JSON.parse(e.data);
          const timeStr = new Date().toLocaleTimeString();
          appendStreamEntry(`[${timeStr}]`, 'EVENT', String(payload.message || e.data), 'stream-tag-gold');
        } catch (_) {}
      };
    } catch (_) {}
  }

  // Safe DOM stream entry builder — ZERO innerHTML!
  function appendStreamEntry(prefix, tagLabel, message, tagClass) {
    const streamBox = document.getElementById('streamConsole');
    if (!streamBox) return;
    const entry = document.createElement('div');
    entry.className = 'stream-entry';

    const timeSpan = document.createElement('span');
    timeSpan.className = 'stream-time';
    timeSpan.textContent = String(prefix);

    const tagSpan = document.createElement('span');
    tagSpan.className = tagClass || 'stream-tag-gold';
    tagSpan.textContent = `[${tagLabel}] `;

    const msgNode = document.createTextNode(String(message));

    entry.appendChild(timeSpan);
    entry.appendChild(tagSpan);
    entry.appendChild(msgNode);
    streamBox.appendChild(entry);
    streamBox.scrollTop = streamBox.scrollHeight;

    while (streamBox.children.length > 60) {
      streamBox.removeChild(streamBox.firstChild);
    }
  }

  function showToast(msg) {
    let toast = document.getElementById('godseyeToast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'godseyeToast';
      toast.style.cssText =
        'position:fixed;bottom:24px;right:24px;z-index:100000;background:var(--bg-card);border:1px solid var(--gold);color:var(--text-main);padding:0.65rem 1.25rem;border-radius:8px;font-family:var(--font-mono);font-size:0.82rem;box-shadow:var(--card-shadow);transition:opacity 0.25s ease,transform 0.25s ease;opacity:0;transform:translateY(10px);pointer-events:none;';
      document.body.appendChild(toast);
    }
    toast.textContent = String(msg);
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
    }, 2600);
  }

  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        showToast(`Copied ${text}`);
      }).catch(() => {
        showToast(`Value: ${text}`);
      });
    } else {
      showToast(`Value: ${text}`);
    }
  }

  function triggerCIDRLookup(ip) {
    const parts = String(ip || '198.51.100.42').split('.');
    const cidr = parts.length === 4 ? `${parts[0]}.${parts[1]}.${parts[2]}.0/24` : ip;
    closeHostModal();
    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.value = `net:${cidr}`;
    showToast(`Sweeping Subnet CIDR net:${cidr}`);
    executeSearch(`net:${cidr}`);
  }

  function csvSafeCell(v) {
    const s = v === null || v === undefined ? '' : String(v);
    const safe = /^[=+\-@\t\r]/.test(s) ? `'${s}` : s;
    return `"${safe.replace(/"/g, '""')}"`;
  }

  async function exportTargets(format) {
    const fmt = format === 'csv' ? 'csv' : 'json';
    if (isLiveBackend) {
      try {
        const res = await fetch(`/api/export?format=${fmt}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `godseye_targets_${Date.now()}.${fmt}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        showToast(`Exported targets (${fmt.toUpperCase()})`);
        return;
      } catch (err) {
        showToast(`Export failed: ${err.message}`);
        return;
      }
    }

    // Static fallback download
    let content = '';
    let mime = 'application/json;charset=utf-8';
    if (fmt === 'csv') {
      mime = 'text/csv;charset=utf-8';
      const rows = ['ip,latitude,longitude,country_name,city,org,threat_score,ports,is_simulated'];
      for (const t of targets) {
        const portsStr = (Array.isArray(t.ports) ? t.ports : [t.port]).filter(Boolean).join(';');
        rows.push([
          t.ip, t.latitude, t.longitude, t.country_name, t.city,
          t.org, t.threat_score, portsStr, Boolean(t.is_simulated),
        ].map(csvSafeCell).join(','));
      }
      content = rows.join('\n');
    } else {
      content = JSON.stringify({ version: '2.6.0', count: targets.length, targets }, null, 2);
    }

    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `godseye_targets_${Date.now()}.${fmt}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast(`Exported ${fmt.toUpperCase()} bundle`);
  }
})();
