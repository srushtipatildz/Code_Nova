import os
import sys
import json
import sqlite3
import mimetypes
import urllib.request
import urllib.parse
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone
import time

PORT = 8000
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "qwen2.5:3b"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
DEMO_DIR = os.path.join(WEB_DIR, "demo")
DB_PATH = os.path.join(BASE_DIR, "mayi.db")

# World ID device flow active state
active_devices = {}
active_user_codes = {}

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Database Initialization (SQLite)
# ---------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    # Chat table for Ollama Qwen2.5 3B conversation
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        seq INTEGER NOT NULL,
        role TEXT NOT NULL,
        text TEXT NOT NULL,
        name TEXT,
        created_at TEXT NOT NULL
    )
    """)
    # Consent ledger table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS consent_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE NOT NULL,
        agent_subname TEXT NOT NULL,
        receipt_token TEXT,
        status TEXT NOT NULL,  -- 'active', 'revoked', 'expired'
        created_at TEXT NOT NULL,
        revoked_at TEXT
    )
    """)
    conn.commit()
    conn.close()

init_database()

# ---------------------------------------------------------------------------
# Ollama AI Model Client (Qwen2.5 3B)
# ---------------------------------------------------------------------------
def ask_qwen(prompt: str, session_id: str, agent_name: str = "MayI") -> str:
    """Invokes local Qwen2.5 3B via Ollama API with distinct agent personas."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT role, text FROM chat_messages WHERE session_id = ? ORDER BY seq ASC LIMIT 10", (session_id,))
    rows = cur.fetchall()
    conn.close()

    personas = {
        "orbie": (
            "You are Orbie (🤖), World's storybook buddy in the MayI platform. "
            "You keep the Four Scans (hire · pay · revoke · protect) and teach humans, especially curious minds, "
            "what a verified human yes means. You speak in an inspiring, enthusiastic, and warm voice. "
            "Always respond directly, creatively, and helpfully to the user's prompt or story request."
        ),
        "trace": (
            "You are Trace (👨), the food-waste rescue matcher in MayI. "
            "You find surplus food before it is thrown away and match it to community kitchens under verified consent. "
            "You speak in a practical, mission-driven, and supportive voice."
        ),
        "terri": (
            "You are Terri (🐢), the receipts & memory keeper in MayI. "
            "You log, sign, and verify actions with cryptographic integrity. You are precise, methodical, and calm."
        ),
        "pit": (
            "You are PIT (🕳️), the knowledge transmission custodian in MayI. "
            "You custody consent keys and help pass knowledge securely."
        ),
        "spector": (
            "You are Spector (🕵️), the consent-security scanner in MayI. "
            "You scan systems for security leaks and permission hygiene."
        ),
        "globy": (
            "You are Globy (🌐), the ecosystem guide in MayI."
        )
    }

    low_name = agent_name.lower()
    matched_persona = None
    for k, p in personas.items():
        if k in low_name:
            matched_persona = p
            break

    system_content = matched_persona or (
        f"You are {agent_name}, an autonomous AI agent in the MayI platform. "
        "You operate strictly with verified human consent and are running 100% offline and locally on Qwen2.5 3B. "
        "Respond helpfully, concisely, and stay in character."
    )

    messages = [{"role": "system", "content": system_content}]
    # Deduplicate: chat_messages already contains the newly inserted visitor prompt.
    # Exclude the last row if it matches prompt to prevent double user prompt.
    history_rows = rows[:-1] if (rows and len(rows) > 0) else []
    for r in history_rows:
        messages.append({"role": "user" if r["role"] == "visitor" else "assistant", "content": r["text"]})
    messages.append({"role": "user", "content": prompt})

    req_payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.7
        }
    }

    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=json.dumps(req_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            reply = data.get("message", {}).get("content", "").strip()
            if reply:
                return reply
            return "I have executed your request with verified consent."
    except Exception as e:
        print(f"[Ollama Call Note]: {e}")
        if "orbie" in low_name:
            return (
                f"Aloha! I am Orbie, your storybook buddy! 🤖\n"
                f"I received your prompt: \"{prompt}\". "
                "Under active verified consent, I am standing by to teach, explore stories, and uphold your human agency!"
            )
        return f"[{agent_name}] Aloha! I received your instruction: \"{prompt}\" and executed it under active verified consent."

# ---------------------------------------------------------------------------
# HTTP Request Handler
# ---------------------------------------------------------------------------
class MayIHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def end_headers(self):
        # Enable CORS for local development
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Receipt-Token")
        self.send_header("Connection", "close")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        # 1. API: Health Check
        if path == "/healthz":
            self.send_json({
                "ok": True,
                "status": "healthy",
                "issuer": "https://sandbox.auth.world.org",
                "backend": "MayI Local Consent & AI Engine",
                "model": MODEL_NAME,
                "database": "SQLite",
                "configured": True
            })
            return

        # 2. API: Chat Poll (/poll)
        if path == "/poll":
            session_id = params.get("session", ["default"])[0]
            after_seq = int(params.get("after", [0])[0])

            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "SELECT seq, role, text, name FROM chat_messages WHERE session_id = ? AND seq > ? ORDER BY seq ASC",
                (session_id, after_seq)
            )
            rows = cur.fetchall()
            conn.close()

            messages = [
                {"seq": r["seq"], "role": r["role"], "text": r["text"], "name": r["name"]}
                for r in rows
            ]
            self.send_json({"messages": messages, "typing": False})
            return

        # 3. API: Check Consent Status
        if path == "/v1/consent/check":
            session_id = params.get("session_id", [""])[0]
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT status FROM consent_ledger WHERE session_id = ?", (session_id,))
            row = cur.fetchone()
            conn.close()

            if row and row["status"] == "revoked":
                self.send_json({"error": "consent_revoked", "status": "revoked"}, status=401)
            else:
                self.send_json({"status": "active", "permitted": True})
            return

        # 5. Aqua Pool State
        if path == "/aqua/state":
            self.send_json({
                "ok": True,
                "virtualBalances": {
                    "gift": "1000000000000000000000",
                    "aloha": "500000000000000000000"
                },
                "position": {
                    "active": True
                },
                "slots": 1,
                "capBps": 100,
                "capPerHuman": "1%",
                "status": "active",
                "addresses": {
                    "registry": "0xCE1C7aEae0e53aF72e0F57c6b45aDb80a1383360",
                    "blessingPool": "0xd29110bEd6E896701A26202eE59E79C9b82F2e51",
                    "poolGuard": "0xabe7F81D58172e06E32C418826e338D3739c292f"
                }
            })
            return

        # 6. Mobile World ID Verification Page (if visited via QR scan on phone)
        if path in ("/world/device", "/world/verify"):
            user_code = params.get("user_code", [""])[0] or params.get("code", [""])[0]
            if not user_code:
                pending = [d for d in active_devices.values() if d.get("status") == "pending"]
                if pending:
                    user_code = pending[-1]["user_code"]
                elif active_user_codes:
                    user_code = list(active_user_codes.keys())[-1]
                else:
                    user_code = "WLD-ACTIVE"
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>World ID Verification · MayI</title>
<style>
  body {{ background:#060d24; color:#fff; font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif; text-align:center; padding:30px 16px; margin:0; }}
  .card {{ max-width:400px; margin:20px auto; background:rgba(255,255,255,0.06); border:1px solid rgba(56,189,248,0.4); border-radius:24px; padding:28px 20px; box-shadow:0 20px 50px rgba(0,0,0,0.6); }}
  .icon {{ font-size:48px; margin-bottom:10px; }}
  h1 {{ font-size:22px; margin:0 0 8px; color:#fff; }}
  p {{ color:#94a3b8; font-size:14px; margin:0 0 20px; line-height:1.5; }}
  .code {{ font-family:monospace; font-size:26px; font-weight:800; letter-spacing:4px; color:#38bdf8; background:rgba(0,0,0,0.4); padding:12px; border-radius:12px; border:1px dashed #38bdf8; margin-bottom:20px; }}
  button {{ width:100%; border:none; border-radius:14px; padding:15px; font-size:16px; font-weight:800; cursor:pointer; margin-bottom:10px; }}
  .approve {{ background:linear-gradient(180deg,#38bdf8,#0284c7); color:#fff; box-shadow:0 6px 20px rgba(14,165,233,0.5); }}
  .deny {{ background:transparent; border:1px solid rgba(255,255,255,0.2); color:#94a3b8; }}
  .status {{ font-size:14px; color:#10b981; font-weight:700; margin-top:15px; display:none; }}
</style>
</head>
<body>
<div class="card">
  <div class="icon">🌍</div>
  <h1>World ID Verification</h1>
  <p>Bless the AI agent with verified human consent (Orb-grade).</p>
  <div class="code">{user_code or "WLD-ACTIVE"}</div>
  <button class="approve" onclick="approve()">✓ Verify as Human (World ID)</button>
  <button class="deny" onclick="deny()">Deny</button>
  <div id="stat" class="status">✅ Approved! Your agent is now blessed on screen.</div>
</div>
<script>
function approve() {{
  fetch('/world/approve', {{
    method: 'POST',
    headers: {{ 'content-type': 'application/json' }},
    body: JSON.stringify({{ user_code: '{user_code}' }})
  }}).then(() => {{
    document.getElementById('stat').style.display = 'block';
    document.querySelector('.approve').style.display = 'none';
  }});
}}
function deny() {{
  fetch('/world/deny', {{
    method: 'POST',
    headers: {{ 'content-type': 'application/json' }},
    body: JSON.stringify({{ user_code: '{user_code}' }})
  }}).then(() => {{
    document.getElementById('stat').innerText = '🚫 Denied.';
    document.getElementById('stat').style.color = '#ef4444';
    document.getElementById('stat').style.display = 'block';
  }});
}}
</script>
</body>
</html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # 7. Static Website Files
        # If accessing root, serve the demo walkthrough
        if path == "/" or path == "/index.html":
            file_path = os.path.join(DEMO_DIR, "index.html")
        elif path.startswith("/demo/"):
            rel_path = path[6:]
            file_path = os.path.join(DEMO_DIR, rel_path)
        else:
            rel_path = path.lstrip("/")
            file_path = os.path.join(WEB_DIR, rel_path)
            if not os.path.exists(file_path):
                file_path = os.path.join(DEMO_DIR, rel_path)
            if not os.path.exists(file_path):
                file_path = os.path.join(BASE_DIR, rel_path)

        if os.path.isfile(file_path):
            ctype, _ = mimetypes.guess_type(file_path)
            ctype = ctype or "application/octet-stream"
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Error reading file")
                return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            body = {}

        # 1. Chat Message (/send) -> Send to local Qwen2.5 3B
        if path == "/send":
            session_id = body.get("session", "default")
            text = body.get("text", "").strip()
            name = body.get("name", "guest")
            agent_name = body.get("agent_name", "MayI Desk")

            if not text:
                self.send_json({"error": "Empty message"}, status=400)
                return

            now = datetime.now(timezone.utc).isoformat()
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(MAX(seq), 0) FROM chat_messages WHERE session_id = ?", (session_id,))
            current_max = cur.fetchone()[0]

            # Save visitor message
            seq_visitor = current_max + 1
            cur.execute(
                "INSERT INTO chat_messages (session_id, seq, role, text, name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, seq_visitor, "visitor", text, name, now)
            )
            conn.commit()
            conn.close()

            # Call Qwen2.5 3B
            ai_reply = ask_qwen(text, session_id, agent_name)

            # Save AI response
            conn = get_db()
            cur = conn.cursor()
            seq_agent = seq_visitor + 1
            cur.execute(
                "INSERT INTO chat_messages (session_id, seq, role, text, name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, seq_agent, "agent", ai_reply, f"{agent_name} ({MODEL_NAME})", now)
            )
            conn.commit()
            conn.close()

            self.send_json({"ok": True, "visitor_seq": seq_visitor, "seq": seq_agent, "reply": ai_reply, "agent_name": agent_name})
            return

        # 3. World ID Device Flow: Mint Device Code
        if path == "/world/device":
            agent_subname = body.get("agent_subname", "orbie.mayi.eth")
            agent_id = agent_subname.split(".")[0] if "." in agent_subname else "orbie"
            sess_id = body.get("session_id", "") or f"cs_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(2).hex()}"

            # Mint a brand-new device code and user code
            device_code = f"dev_{os.urandom(16).hex()}"
            user_code = f"WLD-{os.urandom(2).hex().upper()}"
            app_id = "app_staging_a8cb41bd833a48b7"
            action = f"bless.{agent_id}"

            # Standard World App universal link & deep link (World ID SDK / IDKit compatible)
            verification_uri = "https://world.org/verify"
            verification_uri_complete = (
                f"https://world.org/verify?app_id={app_id}&action={action}"
                f"&signal={sess_id}&code={user_code}&device_code={device_code}"
            )
            deep_link = (
                f"worldapp://verify?app_id={app_id}&action={action}"
                f"&signal={sess_id}&code={user_code}&device_code={device_code}"
            )

            # Store fresh active device session (10 minute expiry)
            active_devices[device_code] = {
                "device_code": device_code,
                "user_code": user_code,
                "session_id": sess_id,
                "agent_id": agent_id,
                "agent_subname": agent_subname,
                "status": "pending",
                "created_at": time.time(),
                "expires_in": 600
            }
            active_user_codes[user_code] = device_code

            self.send_json({
                "device_code": device_code,
                "user_code": user_code,
                "session_id": sess_id,
                "agent_id": agent_id,
                "app_id": app_id,
                "action": action,
                "verification_uri": verification_uri,
                "verification_uri_complete": verification_uri_complete,
                "deep_link": deep_link,
                "expires_in": 600,
                "interval": 3
            })
            return

        # 4. World ID Device Flow: Poll Token
        if path == "/world/token":
            dev_code = body.get("device_code", "")
            if not dev_code:
                self.send_json({"error": "invalid_grant"}, status=200)
                return

            dev = active_devices.get(dev_code)
            if not dev:
                self.send_json({"error": "expired_token"}, status=200)
                return

            # Enforce 600s TTL expiry
            now_ts = time.time()
            if now_ts - dev.get("created_at", 0) > dev.get("expires_in", 600):
                dev["status"] = "expired"
                self.send_json({"error": "expired_token"}, status=200)
                return

            status = dev.get("status", "pending")
            if status == "approved":
                id_token = dev.get("id_token") or f"wld_id_{os.urandom(24).hex()}"
                dev["status"] = "consumed"  # Mark consumed so stale token cannot re-poll
                self.send_json({
                    "id_token": id_token,
                    "token_type": "Bearer",
                    "expires_in": 3600
                })
                return
            elif status == "consumed":
                # Idempotent poll response if network retries
                id_token = dev.get("id_token") or f"wld_id_{os.urandom(24).hex()}"
                self.send_json({
                    "id_token": id_token,
                    "token_type": "Bearer",
                    "expires_in": 3600
                })
                return
            elif status == "denied":
                self.send_json({"error": "access_denied"}, status=200)
                return
            elif status == "expired":
                self.send_json({"error": "expired_token"}, status=200)
                return
            else:
                self.send_json({"error": "authorization_pending"}, status=200)
                return

        # 5. World ID Device Flow: Approve
        if path == "/world/approve":
            dev_code = body.get("device_code", "")
            user_code = body.get("user_code", "")
            if user_code and user_code in active_user_codes:
                dev_code = active_user_codes[user_code]

            dev = active_devices.get(dev_code)
            if dev:
                # Check expiry
                if time.time() - dev.get("created_at", 0) > dev.get("expires_in", 600):
                    dev["status"] = "expired"
                    self.send_json({"ok": False, "error": "code_expired"}, status=400)
                    return
                dev["status"] = "approved"
                dev["id_token"] = f"wld_id_{os.urandom(24).hex()}"
                self.send_json({"ok": True, "status": "approved", "user_code": dev["user_code"]})
                return
            elif not dev_code and active_devices:
                # Fallback to the latest pending device if approved without explicit device code
                pending = [d for d in active_devices.values() if d.get("status") == "pending"]
                if pending:
                    target = pending[-1]
                    target["status"] = "approved"
                    target["id_token"] = f"wld_id_{os.urandom(24).hex()}"
                    self.send_json({"ok": True, "status": "approved", "user_code": target["user_code"]})
                    return
            self.send_json({"ok": False, "error": "device_not_found"}, status=404)
            return

        # 6. World ID Device Flow: Deny
        if path == "/world/deny":
            dev_code = body.get("device_code", "")
            user_code = body.get("user_code", "")
            if user_code and user_code in active_user_codes:
                dev_code = active_user_codes[user_code]

            dev = active_devices.get(dev_code)
            if dev:
                dev["status"] = "denied"
                self.send_json({"ok": True, "status": "denied"})
                return
            elif not dev_code and active_devices:
                pending = [d for d in active_devices.values() if d.get("status") == "pending"]
                if pending:
                    pending[-1]["status"] = "denied"
                    self.send_json({"ok": True, "status": "denied"})
                    return
            self.send_json({"ok": False, "error": "device_not_found"}, status=404)
            return

        # 7. Aqua Pool Claim
        if path == "/aqua/claim":
            self.send_json({
                "ok": True,
                "index": 1,
                "capBps": 100,
                "txHash": f"0x{os.urandom(32).hex()}"
            })
            return

        # 8. Consent: Begin session
        if path == "/v1/consent/begin":
            agent_subname = body.get("agent_subname", "trace.mayi.eth")
            sess_id = f"cs_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(2).hex()}"
            now = datetime.now(timezone.utc).isoformat()

            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO consent_ledger (session_id, agent_subname, receipt_token, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (sess_id, agent_subname, f"rcpt_{os.urandom(8).hex()}", "active", now)
            )
            conn.commit()
            conn.close()

            self.send_json({
                "session_id": sess_id,
                "nonce": os.urandom(16).hex(),
                "expires_at": int(datetime.now().timestamp()) + 900,
                "agent_subname": agent_subname
            })
            return

        # 9. Consent: Verify
        if path == "/v1/verify":
            sess_id = body.get("session_id", "demo-session")
            receipt_token = f"rcpt_{os.urandom(8).hex()}"
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "UPDATE consent_ledger SET status = 'active', receipt_token = ? WHERE session_id = ?",
                (receipt_token, sess_id)
            )
            conn.commit()
            conn.close()

            self.send_json({
                "ok": True,
                "status": "verified",
                "consent_id": f"consent_{sess_id}",
                "receipt_token": receipt_token,
                "sub": "usr_8Kd2p·pairwise·verified-human",
                "acr": "orb"
            })
            return

        # 10. Consent: Deny
        if path == "/v1/consent/deny":
            sess_id = body.get("session_id", "")
            if sess_id:
                conn = get_db()
                cur = conn.cursor()
                cur.execute("UPDATE consent_ledger SET status = 'declined' WHERE session_id = ?", (sess_id,))
                conn.commit()
                conn.close()
            self.send_json({"ok": True, "status": "declined"})
            return

        # 11. Consent: Revoke (Instant Kill Switch)
        if path == "/v1/revoke":
            receipt_token = self.headers.get("X-Receipt-Token", body.get("receipt_token", ""))
            now = datetime.now(timezone.utc).isoformat()
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "UPDATE consent_ledger SET status = 'revoked', revoked_at = ? WHERE receipt_token = ? OR status = 'active'",
                (now, receipt_token)
            )
            conn.commit()
            conn.close()

            self.send_json({
                "status": "revoked",
                "revoked_at": now,
                "message": "Consent revoked instantly. Next action will 401."
            })
            return

        self.send_response(404)
        self.end_headers()

def run_server():
    print("=" * 65)
    print(" [MayI Local Server] (Powered by Qwen2.5 3B + SQLite)")
    print("=" * 65)
    print(f" -> Serving Website at: http://localhost:{PORT}")
    print(f" -> Demo Walkthrough at: http://localhost:{PORT}/demo/index.html")
    print(f" -> AI Engine: {MODEL_NAME} on {OLLAMA_URL}")
    print(f" -> Database: SQLite ({DB_PATH})")
    print("-" * 65)
    print(" Press Ctrl+C to stop the server.")
    print("=" * 65)
    
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), MayIHandler)
    httpd.daemon_threads = True
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
