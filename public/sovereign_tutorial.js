/**
 * Sovereign Quickstart Tutorial Modal (Accessible & XSS-Safe)
 * Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform
 */
(function () {
  if (window.__SOVEREIGN_TUTORIAL_ATTACHED__) return;
  window.__SOVEREIGN_TUTORIAL_ATTACHED__ = true;

  window.createSovereignTutorial = function (config) {
    const {
      toolId,
      toolName,
      tagline,
      steps,
      accentColor = '#D4AF37',
    } = config;

    if (document.getElementById(`sovTutorial-${toolId}`)) return;

    const modal = document.createElement('div');
    modal.id = `sovTutorial-${toolId}`;
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-label', `${toolName} quickstart`);
    modal.style.cssText =
      'display:none;position:fixed;inset:0;z-index:999999;background:rgba(4,6,12,0.82);backdrop-filter:blur(12px);align-items:center;justify-content:center;padding:18px;box-sizing:border-box;';

    const card = document.createElement('div');
    card.style.cssText =
      `background:var(--bg-card,#0D111E);border:2px solid ${accentColor};border-radius:16px;max-width:620px;width:100%;max-height:90vh;overflow-y:auto;padding:24px;color:var(--text-main,#F8FAFC);position:relative;font-family:var(--font-sans,sans-serif);box-sizing:border-box;`;

    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.id = `sovCloseBtn-${toolId}`;
    closeBtn.setAttribute('aria-label', 'Close tutorial');
    closeBtn.textContent = '✕';
    closeBtn.style.cssText =
      'position:absolute;top:14px;right:14px;background:transparent;border:1px solid var(--border-subtle);color:var(--text-main);width:44px;height:44px;border-radius:50%;font-size:16px;cursor:pointer;font-weight:bold;';

    const title = document.createElement('h2');
    title.textContent = toolName;
    title.style.cssText = `margin:0 48px 4px 0;font-size:18px;font-weight:800;color:${accentColor};`;

    const tagEl = document.createElement('p');
    tagEl.textContent = tagline;
    tagEl.style.cssText = 'margin:0 0 16px 0;color:var(--text-muted);font-size:13px;';

    const list = document.createElement('div');
    list.style.cssText = 'display:flex;flex-direction:column;gap:10px;';
    (steps || []).forEach((s, idx) => {
      const item = document.createElement('div');
      item.style.cssText =
        'display:flex;gap:12px;background:var(--bg-card-subtle);border:1px solid var(--border-subtle);border-radius:10px;padding:12px;align-items:flex-start;';
      const ic = document.createElement('span');
      ic.textContent = s.icon || '✦';
      ic.style.cssText = 'font-size:20px;line-height:1.2;';
      const body = document.createElement('div');
      const h4 = document.createElement('h4');
      h4.textContent = `Step ${idx + 1}: ${s.title}`;
      h4.style.cssText = 'margin:0 0 3px 0;font-size:14px;font-weight:700;color:var(--text-heading);';
      const p = document.createElement('p');
      p.textContent = s.desc;
      p.style.cssText = 'margin:0;color:var(--text-muted);font-size:12.5px;line-height:1.45;';
      body.appendChild(h4);
      body.appendChild(p);
      item.appendChild(ic);
      item.appendChild(body);
      list.appendChild(item);
    });

    const footer = document.createElement('div');
    footer.style.cssText =
      'margin-top:18px;display:flex;justify-content:space-between;align-items:center;padding-top:14px;border-top:1px solid var(--border-subtle);flex-wrap:wrap;gap:12px;';

    const chkId = `sovDontShow-${toolId}`;
    const chkLabel = document.createElement('label');
    chkLabel.setAttribute('for', chkId);
    chkLabel.style.cssText = 'display:flex;align-items:center;gap:8px;font-size:12px;color:var(--text-muted);cursor:pointer;min-height:44px;';
    const chk = document.createElement('input');
    chk.type = 'checkbox';
    chk.id = chkId;
    chk.setAttribute('aria-label', "Don't show automatically on first visit");
    chkLabel.appendChild(chk);
    chkLabel.appendChild(document.createTextNode("Don't show automatically on first visit"));

    const actionBtn = document.createElement('button');
    actionBtn.type = 'button';
    actionBtn.id = `sovActionBtn-${toolId}`;
    actionBtn.textContent = 'Start Recon';
    actionBtn.style.cssText =
      `background:${accentColor};color:#08080B;border:none;padding:10px 22px;min-height:44px;border-radius:8px;font-weight:800;font-size:13px;cursor:pointer;`;

    footer.appendChild(chkLabel);
    footer.appendChild(actionBtn);

    card.appendChild(closeBtn);
    card.appendChild(title);
    card.appendChild(tagEl);
    card.appendChild(list);
    card.appendChild(footer);
    modal.appendChild(card);
    document.body.appendChild(modal);

    function openModal() {
      modal.style.display = 'flex';
    }
    function closeModal() {
      modal.style.display = 'none';
      if (chk.checked) {
        try { localStorage.setItem(`sov_tutorial_seen_${toolId}`, 'true'); } catch (_) {}
      }
    }

    closeBtn.addEventListener('click', closeModal);
    actionBtn.addEventListener('click', closeModal);

    return { open: openModal, close: closeModal };
  };
})();
