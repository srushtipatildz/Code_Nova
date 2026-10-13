/**
 * MayI — Live AI Agent Chat Assistant (Powered by Qwen2.5 3B Offline)
 * Seamlessly available across the entire website as a floating assistant or docked sidebar.
 */
(function (window) {
  'use strict';
  if (document.getElementById('mayiTalkRoot')) return;

  var HUB = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
    ? window.location.origin
    : '';

  var css = `
  #mayiTalkRoot {
    position: fixed;
    right: 28px;
    bottom: calc(28px + env(safe-area-inset-bottom, 0px));
    z-index: 99999;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    pointer-events: none;
  }
  #mayiTalkRoot > * {
    pointer-events: auto;
  }
  #mayiTalkRoot .ot-fab {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: 999px;
    padding: 13px 22px;
    cursor: pointer;
    color: #ffffff;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: .02em;
    background: linear-gradient(180deg, #38bdf8 0%, #0284c7 100%);
    box-shadow: 0 6px 0 #0369a1, 0 14px 30px rgba(14, 165, 233, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    transition: all .2s cubic-bezier(0.16, 1, 0.3, 1);
  }
  #mayiTalkRoot .ot-fab:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow: 0 9px 0 #0369a1, 0 20px 40px rgba(14, 165, 233, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.6);
  }
  #mayiTalkRoot .ot-fab:active {
    transform: translateY(3px);
    box-shadow: 0 2px 0 #0369a1, 0 6px 15px rgba(14, 165, 233, 0.3);
  }
  #mayiTalkRoot .ot-fab .ot-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 12px #10b981;
    flex: none;
    animation: otPulse 2s infinite;
  }
  @keyframes otPulse {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
  }
  #mayiTalkRoot .ot-panel[hidden] { display: none !important; }
  #mayiTalkRoot .ot-panel {
    position: fixed;
    right: 28px;
    bottom: calc(28px + env(safe-area-inset-bottom, 0px));
    width: min(440px, calc(100vw - 36px));
    height: min(620px, calc(100vh - 80px));
    display: flex;
    flex-direction: column;
    border-radius: 26px;
    border: 1px solid rgba(56, 189, 248, 0.35);
    background: linear-gradient(180deg, rgba(11, 21, 54, 0.98), rgba(6, 13, 36, 0.99));
    box-shadow: 0 30px 80px rgba(0, 5, 20, 0.95), 0 0 45px rgba(56, 189, 248, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3);
    overflow: hidden;
    backdrop-filter: blur(28px);
    -webkit-backdrop-filter: blur(28px);
    animation: slideUp .3s cubic-bezier(0.16, 1, 0.3, 1);
    transition: width 0.25s cubic-bezier(0.16, 1, 0.3, 1), height 0.25s cubic-bezier(0.16, 1, 0.3, 1), top 0.25s cubic-bezier(0.16, 1, 0.3, 1), right 0.25s cubic-bezier(0.16, 1, 0.3, 1), border-radius 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    z-index: 100000;
  }
  #mayiTalkRoot .ot-panel.ot-expanded:not(.ot-docked) {
    width: min(720px, calc(100vw - 36px));
    height: min(820px, calc(100vh - 60px));
  }
  #mayiTalkRoot .ot-panel.ot-docked {
    top: 0;
    right: 0;
    bottom: 0;
    width: min(480px, 100vw);
    height: 100vh;
    max-height: 100vh;
    border-radius: 0;
    border-left: 1px solid rgba(56, 189, 248, 0.45);
    border-top: none;
    border-right: none;
    border-bottom: none;
    box-shadow: -15px 0 60px rgba(0, 5, 20, 0.95), 0 0 40px rgba(56, 189, 248, 0.25);
  }
  @keyframes slideUp {
    from { opacity: 0; transform: translateY(20px) scale(0.97); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }
  #mayiTalkRoot .ot-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 16px 20px 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    flex: none;
    background: rgba(255, 255, 255, 0.03);
  }
  #mayiTalkRoot .ot-title {
    font-size: 16px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.02em;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  #mayiTalkRoot .ot-sub {
    font-size: 11.5px;
    line-height: 1.4;
    color: #cbd5e1;
    margin-top: 2px;
  }
  #mayiTalkRoot .ot-sub .ot-live {
    color: #10b981;
    font-weight: 700;
  }
  #mayiTalkRoot .ot-head-actions {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    flex: none;
  }
  #mayiTalkRoot .ot-btn-tool {
    border: 1px solid rgba(255, 255, 255, 0.18);
    background: rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
    border-radius: 10px;
    width: 32px;
    height: 32px;
    cursor: pointer;
    font-size: 13px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all .15s;
  }
  #mayiTalkRoot .ot-btn-tool:hover {
    color: #ffffff;
    background: rgba(56, 189, 248, 0.25);
    border-color: #38bdf8;
    transform: translateY(-1px);
  }
  #mayiTalkRoot .ot-btn-tool.active {
    background: #0284c7;
    color: #ffffff;
    border-color: #38bdf8;
  }
  #mayiTalkRoot .ot-x {
    border: 1px solid rgba(255, 255, 255, 0.18);
    background: rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
    border-radius: 10px;
    width: 32px;
    height: 32px;
    cursor: pointer;
    font-size: 14px;
    line-height: 1;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex: none;
    transition: all .2s;
  }
  #mayiTalkRoot .ot-x:hover {
    color: #ffffff;
    background: rgba(239, 68, 68, 0.35);
    border-color: #ef4444;
  }
  #mayiTalkRoot .ot-pills {
    display: flex;
    gap: 6px;
    padding: 10px 18px;
    overflow-x: auto;
    background: rgba(0, 0, 0, 0.25);
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    flex: none;
    scrollbar-width: none;
  }
  #mayiTalkRoot .ot-pills::-webkit-scrollbar { display: none; }
  #mayiTalkRoot .ot-pill-btn {
    border: 1px solid rgba(56, 189, 248, 0.3);
    background: rgba(56, 189, 248, 0.1);
    color: #bae6fd;
    font-size: 11.5px;
    font-weight: 700;
    padding: 5px 11px;
    border-radius: 999px;
    cursor: pointer;
    white-space: nowrap;
    transition: all .15s;
    flex: none;
  }
  #mayiTalkRoot .ot-pill-btn:hover {
    background: #38bdf8;
    color: #030712;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(56, 189, 248, 0.4);
  }
  #mayiTalkRoot .ot-log {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    -webkit-overflow-scrolling: touch;
  }
  #mayiTalkRoot .ot-m {
    max-width: 85%;
    padding: 11px 16px;
    border-radius: 18px;
    font-size: 14px;
    line-height: 1.55;
    white-space: pre-wrap;
    word-wrap: break-word;
    color: #ffffff;
    transition: opacity .2s;
  }
  #mayiTalkRoot .ot-m[data-pending="true"] {
    opacity: 0.82;
  }
  #mayiTalkRoot .ot-m.ot-v {
    align-self: flex-end;
    background: linear-gradient(135deg, #38bdf8, #0284c7);
    color: #ffffff;
    border-bottom-right-radius: 4px;
    box-shadow: 0 6px 18px rgba(2, 132, 199, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.4);
  }
  #mayiTalkRoot .ot-m.ot-a {
    align-self: flex-start;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-bottom-left-radius: 4px;
    color: #f8fafc;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }
  #mayiTalkRoot .ot-m.ot-a .ot-who {
    font-size: 11.5px;
    color: #38bdf8;
    font-weight: 800;
    margin-bottom: 4px;
    letter-spacing: .4px;
  }
  #mayiTalkRoot .ot-note {
    align-self: center;
    font-size: 12px;
    color: #94a3b8;
    text-align: center;
    max-width: 92%;
    line-height: 1.5;
    background: rgba(255, 255, 255, 0.04);
    padding: 8px 14px;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.08);
  }
  #mayiTalkRoot .ot-m a, #mayiTalkRoot .ot-note a {
    color: #38bdf8;
    text-decoration: underline;
    word-break: break-all;
  }
  #mayiTalkRoot .ot-typing {
    display: none;
    padding: 6px 20px;
    color: #cbd5e1;
    font-size: 13px;
    flex: none;
  }
  #mayiTalkRoot .ot-typing.on { display: block; }
  #mayiTalkRoot .ot-typing span {
    display: inline-block;
    animation: otB 1.2s infinite;
    color: #38bdf8;
    margin-right: 3px;
  }
  #mayiTalkRoot .ot-typing span:nth-child(2) { animation-delay: .2s; }
  #mayiTalkRoot .ot-typing span:nth-child(3) { animation-delay: .4s; }
  @keyframes otB {
    0%, 80%, 100% { transform: scale(0); opacity: .4; }
    40% { transform: scale(1); opacity: 1; }
  }
  #mayiTalkRoot .ot-form {
    display: flex;
    gap: 8px;
    padding: 12px 16px;
    border-top: 1px solid rgba(255, 255, 255, 0.12);
    background: rgba(3, 7, 18, 0.75);
    flex: none;
  }
  #mayiTalkRoot .ot-in {
    flex: 1;
    border: 1px solid rgba(255, 255, 255, 0.16);
    background: rgba(255, 255, 255, 0.06);
    color: #ffffff;
    border-radius: 14px;
    padding: 10px 14px;
    font-size: 13.5px;
    line-height: 1.4;
    font-family: inherit;
    resize: none;
    height: 44px;
    outline: none;
    transition: border-color .2s;
  }
  #mayiTalkRoot .ot-in:focus {
    border-color: #38bdf8;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.35);
  }
  #mayiTalkRoot .ot-send {
    background: linear-gradient(180deg, #38bdf8 0%, #0284c7 100%);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 14px;
    padding: 0 20px;
    font-weight: 800;
    font-size: 13.5px;
    cursor: pointer;
    box-shadow: 0 4px 0 #0369a1, 0 8px 20px rgba(14, 165, 233, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.4);
    transition: all .15s;
    flex: none;
  }
  #mayiTalkRoot .ot-send:hover {
    transform: translateY(-1px);
    filter: brightness(1.1);
  }
  #mayiTalkRoot .ot-send:active {
    transform: translateY(2px);
    box-shadow: 0 1px 0 #0369a1;
  }
  #mayiTalkRoot .ot-foot {
    flex: none;
    text-align: center;
    font-size: 11px;
    color: #94a3b8;
    padding: 0 18px 10px;
    background: rgba(3, 7, 18, 0.75);
  }
  #mayiTalkRoot .ot-foot a {
    color: #cbd5e1;
    text-decoration: none;
  }
  #mayiTalkRoot .ot-foot a:hover {
    color: #fff;
    text-decoration: underline;
  }
  @media(max-width: 560px) {
    #mayiTalkRoot .ot-panel {
      position: fixed;
      right: 0;
      left: 0;
      bottom: 0;
      top: 0;
      width: 100vw;
      height: 100dvh;
      max-height: 100dvh;
      border-radius: 0;
      border: none;
    }
    #mayiTalkRoot .ot-in { font-size: 16px; }
    #mayiTalkRoot .ot-form { padding-bottom: calc(11px + env(safe-area-inset-bottom)); }
  }
  `;

  var st = document.createElement('style');
  st.textContent = css;
  document.head.appendChild(st);

  var root = document.createElement('div');
  root.id = 'mayiTalkRoot';
  root.innerHTML =
    '<button type="button" class="ot-fab" aria-label="Talk to MayI — live AI agent">' +
      '<span class="ot-dot"></span><span>💬 AI Assistant (Qwen2.5 3B)</span></button>' +
    '<div class="ot-panel" role="dialog" aria-label="MayI live chat" hidden>' +
      '<div class="ot-head">' +
        '<div>' +
          '<div class="ot-title">🛡️ MayI AI Assistant</div>' +
          '<div class="ot-sub"><span class="ot-live">● active</span> — Powered by Qwen2.5 3B local offline AI.</div>' +
        '</div>' +
        '<div class="ot-head-actions">' +
          '<button type="button" class="ot-btn-tool ot-dock-toggle" title="Dock as sidebar / Float as window">◫</button>' +
          '<button type="button" class="ot-btn-tool ot-expand-toggle" title="Expand width / Normal size">⛶</button>' +
          '<button type="button" class="ot-x" title="Minimize / Close chat">✕</button>' +
        '</div>' +
      '</div>' +
      '<div class="ot-pills">' +
        '<button type="button" class="ot-pill-btn" data-prompt="How does MayI verified consent and instant revocation work?">🛡️ How Consent Works</button>' +
        '<button type="button" class="ot-pill-btn" data-prompt="What AI agents are available to hire right now on MayI?">🤖 Available Agents</button>' +
        '<button type="button" class="ot-pill-btn" data-prompt="Explain how the local Qwen2.5 3B model and SQLite ledger work offline.">⚡ Local Architecture</button>' +
        '<button type="button" class="ot-pill-btn" data-prompt="How do I bless an agent with a consent time window?">⏱️ Time Windows</button>' +
      '</div>' +
      '<div class="ot-log"></div>' +
      '<div class="ot-typing"><span>●</span><span>●</span><span>●</span> <b style="color:#38bdf8">MayI AI</b> is thinking via local Qwen2.5 3B…</div>' +
      '<form class="ot-form">' +
        '<textarea class="ot-in" placeholder="Ask about agents, consent, time windows, or give a task…" rows="1"></textarea>' +
        '<button type="submit" class="ot-send">Send</button>' +
      '</form>' +
      '<div class="ot-foot">Private &amp; Offline · Verified by SQLite · Press <kbd style="background:rgba(255,255,255,0.15);padding:1px 5px;border-radius:4px;color:#fff">Alt + C</kbd> anywhere</div>' +
    '</div>';
  document.body.appendChild(root);

  function $(s) { return root.querySelector(s); }
  var fab = $('.ot-fab');
  var panel = $('.ot-panel');
  var log = $('.ot-log');
  var typing = $('.ot-typing');
  var form = $('.ot-form');
  var input = $('.ot-in');
  var dockBtn = $('.ot-dock-toggle');
  var expandBtn = $('.ot-expand-toggle');

  var sess = localStorage.getItem('mayi_chat_session');
  if (!sess) {
    sess = ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, function (c) {
      return (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16);
    });
    localStorage.setItem('mayi_chat_session', sess);
  }

  var open = false;
  var isDocked = localStorage.getItem('mayi_chat_docked') === 'true';
  var isExpanded = localStorage.getItem('mayi_chat_expanded') === 'true';
  if (isDocked) { panel.classList.add('ot-docked'); dockBtn.classList.add('active'); }
  if (isExpanded) { panel.classList.add('ot-expanded'); expandBtn.classList.add('active'); }

  var after = 0;
  var seen = {};
  var polling = false;
  var caughtUp = false;
  var isSubmitting = false;

  function esc(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function rich(s) {
    var h = esc(s);
    h = h.replace(/`([^`\n]+)`/g, '<code style="background:rgba(255,255,255,0.12);padding:2px 6px;border-radius:6px;font-size:12px;color:#38bdf8">$1</code>');
    h = h.replace(/\*\*([^*\n]+)\*\*/g, '<b>$1</b>');
    return h;
  }

  function scroll() { log.scrollTop = log.scrollHeight; }

  function add(role, text, name, optSeq) {
    if (optSeq) seen[optSeq] = 1;
    var m = document.createElement('div');
    m.className = 'ot-m ' + (role === 'visitor' ? 'ot-v' : 'ot-a');
    if (optSeq) m.setAttribute('data-seq', optSeq);
    m.innerHTML = (role === 'visitor' ? '' : '<div class="ot-who">' + esc(name || 'MayI AI') + '</div>') + rich(text);
    log.appendChild(m);
    scroll();
    return m;
  }

  function note(t) {
    var n = document.createElement('div');
    n.className = 'ot-note';
    n.innerHTML = rich(t);
    log.appendChild(n);
    scroll();
  }

  function render(m) {
    if (m.seq > after) after = m.seq;
    if (seen[m.seq]) return;

    // Check if an existing element in log already has this seq
    if (log.querySelector('[data-seq="' + m.seq + '"]')) {
      seen[m.seq] = 1;
      return;
    }

    if (m.role === 'visitor') {
      // Check if visitor message is already present in recent visitor elements
      var vNodes = log.querySelectorAll('.ot-v');
      for (var i = vNodes.length - 1; i >= 0 && i >= vNodes.length - 4; i--) {
        var node = vNodes[i];
        if (node && node.textContent.trim() === m.text.trim()) {
          node.setAttribute('data-seq', m.seq);
          node.removeAttribute('data-pending');
          seen[m.seq] = 1;
          return; // Suppress duplicate!
        }
      }
      add('visitor', m.text, null, m.seq);
    } else if (m.role === 'system') {
      seen[m.seq] = 1;
      note(m.text);
    } else {
      // Avoid duplicate if agent response is already in DOM
      var aNodes = log.querySelectorAll('.ot-a');
      for (var j = aNodes.length - 1; j >= 0 && j >= aNodes.length - 3; j--) {
        var aNode = aNodes[j];
        if (aNode && aNode.textContent.trim().replace(/^.*?\n/, '').trim() === m.text.trim()) {
          aNode.setAttribute('data-seq', m.seq);
          seen[m.seq] = 1;
          return;
        }
      }
      add('agent', m.text, m.name, m.seq);
    }
  }

  function greet() {
    if (log.children.length) return;
    note('⚡ Live AI Connection Active — Running on local Qwen2.5 3B with SQLite consent verification.');
    add('agent', '🛡️ Hello! I am your MayI AI Assistant. I operate under verified human consent and run 100% offline via local Qwen2.5 3B. Ask me about agent hiring, permissions, time windows, or give me a task to execute!');
  }

  function catchUp() {
    return fetch(HUB + '/poll?session=' + encodeURIComponent(sess) + '&after=0')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        (d.messages || []).forEach(render);
        caughtUp = true;
        greet();
      })
      .catch(function () {
        caughtUp = true;
        greet();
      });
  }

  function poll() {
    if (polling) return;
    polling = true;
    (function loop() {
      if (!open) { polling = false; return; }
      fetch(HUB + '/poll?session=' + encodeURIComponent(sess) + '&after=' + after + '&wait=25')
        .then(function (r) { return r.json(); })
        .then(function (d) {
          (d.messages || []).forEach(render);
          typing.className = 'ot-typing' + (d.typing ? ' on' : '');
          if (d.typing) scroll();
          setTimeout(loop, 2500); // 2.5s poll delay
        })
        .catch(function () {
          setTimeout(loop, 4000);
        });
    })();
  }

  var currentAgentTarget = 'MayI AI';

  function openPanel(customPrompt, targetAgent) {
    open = true;
    panel.hidden = false;
    fab.style.display = 'none';
    if (targetAgent) currentAgentTarget = targetAgent;
    else if (customPrompt && /Orbie/i.test(customPrompt)) currentAgentTarget = 'Orbie';
    else if (customPrompt && /Trace/i.test(customPrompt)) currentAgentTarget = 'Trace';
    else if (customPrompt && /Terri/i.test(customPrompt)) currentAgentTarget = 'Terri';
    else if (customPrompt && /Globy/i.test(customPrompt)) currentAgentTarget = 'Globy';
    (caughtUp ? Promise.resolve(greet()) : catchUp()).then(function () { poll(); });
    setTimeout(function () {
      if (customPrompt && input) {
        input.value = customPrompt;
      }
      try { input.focus(); } catch (e) {}
    }, 60);
  }

  function closePanel() {
    open = false;
    panel.hidden = true;
    fab.style.display = '';
  }

  function togglePanel() {
    if (open) closePanel();
    else openPanel();
  }

  fab.addEventListener('click', function () { openPanel(); });
  $('.ot-x').addEventListener('click', closePanel);

  if (dockBtn) {
    dockBtn.addEventListener('click', function () {
      isDocked = !isDocked;
      localStorage.setItem('mayi_chat_docked', String(isDocked));
      if (isDocked) {
        panel.classList.add('ot-docked');
        dockBtn.classList.add('active');
      } else {
        panel.classList.remove('ot-docked');
        dockBtn.classList.remove('active');
      }
    });
  }

  if (expandBtn) {
    expandBtn.addEventListener('click', function () {
      isExpanded = !isExpanded;
      localStorage.setItem('mayi_chat_expanded', String(isExpanded));
      if (isExpanded) {
        panel.classList.add('ot-expanded');
        expandBtn.classList.add('active');
      } else {
        panel.classList.remove('ot-expanded');
        expandBtn.classList.remove('active');
      }
    });
  }

  // Quick suggestion pills click
  var pillButtons = root.querySelectorAll('.ot-pill-btn');
  pillButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var prompt = btn.getAttribute('data-prompt');
      if (prompt) {
        input.value = prompt;
        form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
      }
    });
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (isSubmitting) return;

    var t = input.value.trim();
    if (!t) return;
    isSubmitting = true;
    input.value = '';

    // Check if user is addressing an agent specifically
    var sendTarget = currentAgentTarget;
    if (/\borbie\b/i.test(t)) sendTarget = 'Orbie';
    else if (/\btrace\b/i.test(t)) sendTarget = 'Trace';
    else if (/\bterri\b/i.test(t)) sendTarget = 'Terri';
    else if (/\bgloby\b/i.test(t)) sendTarget = 'Globy';

    // Add optimistic visitor message
    var optEl = add('visitor', t);
    optEl.setAttribute('data-pending', 'true');
    typing.className = 'ot-typing on';
    scroll();

    fetch(HUB + '/send', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ session: sess, text: t, name: 'guest', agent_name: sendTarget })
    })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      isSubmitting = false;
      typing.className = 'ot-typing';
      if (d) {
        if (d.visitor_seq) {
          seen[d.visitor_seq] = 1;
          if (optEl) {
            optEl.setAttribute('data-seq', d.visitor_seq);
            optEl.removeAttribute('data-pending');
          }
        }
        var agentAlreadyRendered = d.seq && (seen[d.seq] || log.querySelector('[data-seq="' + d.seq + '"]'));
        if (d.seq) seen[d.seq] = 1;
        if (d.reply && !agentAlreadyRendered) {
          add('agent', d.reply, d.agent_name || 'MayI (Qwen2.5 3B)', d.seq);
        }
        if (d.error) note(d.error);
      }
    })
    .catch(function () {
      isSubmitting = false;
      typing.className = 'ot-typing';
      note('connection hiccup — message may not have sent; try again 🫶');
    });
  });

  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    }
  });

  // Global window helpers so chatbot can be opened from anywhere on any page
  window.openMayIChat = openPanel;
  window.closeMayIChat = closePanel;
  window.toggleMayIChat = togglePanel;

  // Global keyboard shortcuts: Alt+C or Ctrl+/
  window.addEventListener('keydown', function (e) {
    if ((e.altKey && (e.key === 'c' || e.key === 'C')) || (e.ctrlKey && e.key === '/')) {
      e.preventDefault();
      togglePanel();
    }
  });

})(window);
