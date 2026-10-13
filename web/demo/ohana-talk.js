/* 🫶 Talk to MayI — LIVE agent chat, bottom-right (2026-09-27)
   Not a contact card anymore: a real bell-waked agent (MAYI DESK 🫶) answers on the
   mayi-chat hub, same lane as Terri/Spector/Globy doors. Self-contained: injects its
   own styles + DOM, zero console output.
   Cursor law (shaka-home scar 2026-09-27): NEVER advance `after` on send — the hub seq
   is global and an interleaved reply can carry a lower seq; the poll loop consumes
   everything and a seen-set dedupes our own echo. Catch-up renders full history on open. */
(function () {
  'use strict';
  if (document.getElementById('mayiTalkRoot')) return;
  var HUB = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
    ? window.location.origin
    : 'https://mayi-chat.shakaverse.workers.dev';

  var css = `
  #mayiTalkRoot{position:fixed;right:24px;bottom:calc(24px + env(safe-area-inset-bottom,0px));z-index:9000;font-family:'Plus Jakarta Sans',-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
  #mayiTalkRoot .ot-fab{display:flex;align-items:center;gap:11px;border:1px solid rgba(255,255,255,.3);border-radius:999px;padding:13px 22px;cursor:pointer;color:#ffffff;font-size:14.5px;font-weight:800;letter-spacing:.02em;background:linear-gradient(180deg,#38bdf8 0%,#0284c7 100%);box-shadow:0 6px 0 #0369a1,0 14px 30px rgba(14,165,233,.5),inset 0 1px 0 rgba(255,255,255,.5);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);transition:all .18s cubic-bezier(0.16,1,0.3,1)}
  #mayiTalkRoot .ot-fab:hover{transform:translateY(-3px);box-shadow:0 9px 0 #0369a1,0 20px 40px rgba(14,165,233,.7),inset 0 1px 0 rgba(255,255,255,.6)}
  #mayiTalkRoot .ot-fab:active{transform:translateY(3px);box-shadow:0 2px 0 #0369a1,0 6px 15px rgba(14,165,233,.3)}
  #mayiTalkRoot .ot-fab .ot-dot{width:9px;height:9px;border-radius:50%;background:#10b981;box-shadow:0 0 12px #10b981;flex:none;animation:otPulse 2s infinite}
  @keyframes otPulse{0%{box-shadow:0 0 0 0 rgba(16,185,129,.7)}70%{box-shadow:0 0 0 8px rgba(16,185,129,0)}100%{box-shadow:0 0 0 0 rgba(16,185,129,0)}}
  #mayiTalkRoot .ot-back{position:fixed;inset:0;background:rgba(2,5,18,.65);backdrop-filter:blur(6px);border:0;padding:0;cursor:default}
  #mayiTalkRoot .ot-panel[hidden]{display:none}
  #mayiTalkRoot .ot-panel{position:absolute;right:0;bottom:calc(100% + 16px);width:min(390px,calc(100vw - 36px));height:min(560px,calc(100vh - 120px));display:flex;flex-direction:column;border-radius:26px;border:1px solid rgba(255,255,255,.18);background:linear-gradient(180deg,rgba(16,28,68,.98),rgba(6,13,36,.99));box-shadow:0 30px 80px rgba(0,5,20,.8),0 0 40px rgba(56,189,248,.25),inset 0 1px 0 rgba(255,255,255,.3);overflow:hidden;backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);animation:slideUp .35s cubic-bezier(0.16,1,0.3,1)}
  #mayiTalkRoot .ot-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;padding:20px 22px 16px;border-bottom:1px solid rgba(255,255,255,.12);flex:none;background:rgba(255,255,255,.02)}
  #mayiTalkRoot .ot-title{font-size:18px;font-weight:800;color:#ffffff;letter-spacing:-0.02em}
  #mayiTalkRoot .ot-sub{font-size:12.5px;line-height:1.45;color:#cbd5e1;margin-top:2px}
  #mayiTalkRoot .ot-sub .ot-live{color:#10b981;font-weight:700}
  #mayiTalkRoot .ot-x{border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.08);color:#cbd5e1;border-radius:12px;width:32px;height:32px;cursor:pointer;font-size:14px;line-height:1;flex:none;transition:all .2s}
  #mayiTalkRoot .ot-x:hover{color:#ffffff;background:rgba(255,255,255,.2);border-color:#fff}
  #mayiTalkRoot .ot-log{flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:12px;-webkit-overflow-scrolling:touch}
  #mayiTalkRoot .ot-m{max-width:85%;padding:11px 16px;border-radius:18px;font-size:14px;line-height:1.55;white-space:pre-wrap;word-wrap:break-word;color:#ffffff}
  #mayiTalkRoot .ot-m.ot-v{align-self:flex-end;background:linear-gradient(135deg,#38bdf8,#0284c7);color:#ffffff;border-bottom-right-radius:4px;box-shadow:0 6px 18px rgba(2,132,199,.45),inset 0 1px 0 rgba(255,255,255,.4)}
  #mayiTalkRoot .ot-m.ot-a{align-self:flex-start;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);border-bottom-left-radius:4px;color:#f8fafc;box-shadow:0 4px 15px rgba(0,0,0,.2),inset 0 1px 0 rgba(255,255,255,.1)}
  #mayiTalkRoot .ot-m.ot-a .ot-who{font-size:11.5px;color:#38bdf8;font-weight:800;margin-bottom:4px;letter-spacing:.4px}
  #mayiTalkRoot .ot-note{align-self:center;font-size:12px;color:#94a3b8;text-align:center;max-width:92%;line-height:1.5;background:rgba(255,255,255,.04);padding:8px 14px;border-radius:14px;border:1px solid rgba(255,255,255,.08)}
  #mayiTalkRoot .ot-m a,#mayiTalkRoot .ot-note a{color:#38bdf8;text-decoration:underline;word-break:break-all}
  #mayiTalkRoot .ot-typing{display:none;padding:4px 22px 8px;color:#cbd5e1;font-size:13px;flex:none}
  #mayiTalkRoot .ot-typing.on{display:block}
  #mayiTalkRoot .ot-typing span{display:inline-block;animation:otB 1.2s infinite;color:#38bdf8}
  #mayiTalkRoot .ot-typing span:nth-child(2){animation-delay:.2s}
  #mayiTalkRoot .ot-typing span:nth-child(3){animation-delay:.4s}
  @keyframes otB{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-4px)}}
  #mayiTalkRoot .ot-form{display:flex;gap:10px;padding:14px 18px;border-top:1px solid rgba(255,255,255,.1);flex:none;background:rgba(0,0,0,.35)}
  #mayiTalkRoot .ot-in{flex:1;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.18);border-radius:14px;color:#ffffff;padding:11px 16px;font-size:14.5px;font-family:inherit;resize:none;height:46px;outline:none;transition:border-color .2s}
  #mayiTalkRoot .ot-in:focus{border-color:#38bdf8;box-shadow:0 0 15px rgba(56,189,248,.35)}
  #mayiTalkRoot .ot-send{background:linear-gradient(180deg,#38bdf8 0%,#0284c7 100%);color:#ffffff;border:1px solid rgba(255,255,255,.3);border-radius:14px;padding:0 20px;font-weight:800;font-size:14px;cursor:pointer;box-shadow:0 4px 0 #0369a1,0 8px 20px rgba(14,165,233,.45),inset 0 1px 0 rgba(255,255,255,.4);transition:all .15s}
  #mayiTalkRoot .ot-send:hover{transform:translateY(-1px);filter:brightness(1.1)}
  #mayiTalkRoot .ot-send:active{transform:translateY(2px);box-shadow:0 1px 0 #0369a1}
  #mayiTalkRoot .ot-foot{flex:none;text-align:center;font-size:11px;color:#94a3b8;padding:0 18px 14px;background:rgba(0,0,0,.35)}
  #mayiTalkRoot .ot-foot a{color:#cbd5e1;text-decoration:none}
  #mayiTalkRoot .ot-foot a:hover{color:#fff;text-decoration:underline}
  @media(max-width:560px){
    #mayiTalkRoot .ot-panel{position:fixed;right:0;left:0;bottom:0;width:100vw;height:100dvh;max-height:100dvh;border-radius:0;border:none;border-top:1px solid var(--line,rgba(255,255,255,.18))}
    #mayiTalkRoot .ot-in{font-size:16px}
    #mayiTalkRoot .ot-form{padding-bottom:calc(11px + env(safe-area-inset-bottom))}
  }`;

  var st = document.createElement('style');
  st.textContent = css;
  document.head.appendChild(st);

  var root = document.createElement('div');
  root.id = 'mayiTalkRoot';
  root.innerHTML =
    '<button type="button" class="ot-fab" aria-label="Talk to MayI — live agent chat">' +
      '<span class="ot-dot"></span><span>💬 Talk to MayI</span></button>' +
    '<div class="ot-panel" role="dialog" aria-label="MayI live chat" hidden>' +
      '<div class="ot-head"><div><div class="ot-title">🛡️ Talk to MayI</div>' +
        '<div class="ot-sub"><span class="ot-live">● live</span> — Qwen2.5 3B answers offline & locally.</div></div>' +
        '<button type="button" class="ot-x" aria-label="Close chat">✕</button></div>' +
      '<div class="ot-log" aria-live="polite"></div>' +
      '<div class="ot-typing"><span>●</span><span>●</span><span>●</span></div>' +
      '<form class="ot-form"><textarea class="ot-in" rows="1" placeholder="Ask MayI anything — permissions, consent, local AI…"></textarea>' +
        '<button type="submit" class="ot-send">Send</button></form>' +
      '<div class="ot-foot">prefer another door? <a href="https://t.me/AgentMayIBot" target="_blank" rel="noopener">Telegram</a> · <a href="mailto:aloha@mayi.com">aloha@mayi.com</a></div>' +
    '</div>';
  document.body.appendChild(root);

  var $ = function (s) { return root.querySelector(s); };
  var fab = $('.ot-fab'), panel = $('.ot-panel'), log = $('.ot-log'),
      typing = $('.ot-typing'), form = $('.ot-form'), input = $('.ot-in');

  var sess = null;
  try { sess = localStorage.getItem('oh_talk_sess'); } catch (e) {}
  if (!sess) {
    sess = (window.crypto && crypto.randomUUID ? crypto.randomUUID()
           : Date.now() + '-' + Math.random().toString(36).slice(2)).slice(0, 36);
    try { localStorage.setItem('oh_talk_sess', sess); } catch (e) {}
  }

  var after = 0, seen = {}, open = false, polling = false, caughtUp = false;

  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
  function anchor(url, txt) {
    url = url.replace(/"/g, '%22');
    var label = txt || (url.length > 42 ? url.slice(0, 40) + '…' : url).replace(/^https?:\/\//, '');
    return '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + label + '</a>';
  }
  function rich(s) {
    var h = esc(s);
    h = h.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, function (m, t, u) { return anchor(u, t); });
    h = h.replace(/(^|[^"'>])(https?:\/\/[^\s<]+)/g, function (m, pre, u) {
      var trail = ''; var mm = u.match(/[.,!?;:)\]]+$/);
      if (mm) { trail = mm[0]; u = u.slice(0, u.length - trail.length); }
      return pre + anchor(u) + trail;
    });
    h = h.replace(/\*\*([^*\n]+)\*\*/g, '<b>$1</b>');
    return h;
  }
  function scroll() { log.scrollTop = log.scrollHeight; }
  function add(role, text, name) {
    var m = document.createElement('div');
    m.className = 'ot-m ' + (role === 'visitor' ? 'ot-v' : 'ot-a');
    m.innerHTML = (role === 'visitor' ? '' : '<div class="ot-who">' + esc(name || 'MayI') + '</div>') + rich(text);
    log.appendChild(m); scroll();
  }
  function note(t) {
    var n = document.createElement('div'); n.className = 'ot-note'; n.innerHTML = rich(t);
    log.appendChild(n); scroll();
  }
  function render(m) {
    // advance the cursor for EVERY delivered message (incl. our own echo) so the
    // long-poll never spins; interleaved replies arrive in the same batch, in order.
    if (m.seq > after) after = m.seq;
    if (seen[m.seq]) return;
    seen[m.seq] = 1;
    if (m.role === 'visitor') add('visitor', m.text);
    else if (m.role === 'system') note(m.text);
    else add('agent', m.text, m.name);
  }
  function greet() {
    if (log.children.length) return;
    note('Live line to MayI — local Qwen2.5 3B answers offline with verified consent.');
    add('agent', '🛡️ Hello! You’ve reached MayI — your local AI agent consent system. Ask about permissions, time limits, actions, or anything about how I run offline on Qwen2.5 3B!');
  }
  function catchUp() {
    // full-history render once per page load — any stuck client self-heals on open
    return fetch(HUB + '/poll?session=' + encodeURIComponent(sess) + '&after=0')
      .then(function (r) { return r.json(); })
      .then(function (d) { (d.messages || []).forEach(render); caughtUp = true; greet(); })
      .catch(function () { caughtUp = true; greet(); });
  }
  function poll() {
    if (polling) return; polling = true;
    (function loop() {
      if (!open) { polling = false; return; }
      fetch(HUB + '/poll?session=' + encodeURIComponent(sess) + '&after=' + after + '&wait=25')
        .then(function (r) { return r.json(); })
        .then(function (d) {
          (d.messages || []).forEach(render);
          typing.className = 'ot-typing' + (d.typing ? ' on' : '');
          if (d.typing) scroll();
          setTimeout(loop, 2500);
        })
        .catch(function () { setTimeout(loop, 4000); });
    })();
  }

  function openPanel() {
    open = true; panel.hidden = false; fab.style.display = 'none';
    (caughtUp ? Promise.resolve(greet()) : catchUp()).then(function () { poll(); });
    setTimeout(function () { try { input.focus(); } catch (e) {} }, 50);
  }
  function closePanel() { open = false; panel.hidden = true; fab.style.display = ''; }

  fab.addEventListener('click', openPanel);
  $('.ot-x').addEventListener('click', closePanel);

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var t = input.value.trim();
    if (!t) return;
    input.value = '';
    add('visitor', t);
    fetch(HUB + '/send', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ session: sess, text: t, name: 'guest' })
    }).then(function (r) { return r.json(); })
      .then(function (d) {
        // cursor law: mark our echo seen, but NEVER advance `after` here —
        // the poll loop owns the cursor (interleaved replies stay visible).
        if (d && d.seq) seen[d.seq] = 1;
        if (d && d.error) note(d.error);
      })
      .catch(function () { note('connection hiccup — that message may not have sent; try again 🫶'); });
  });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.dispatchEvent(new Event('submit', { cancelable: true })); }
  });
})();
