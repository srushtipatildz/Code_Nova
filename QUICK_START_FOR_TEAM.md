# 🛡️ MayI — Quick Start Guide for Team Members

Welcome to **MayI** (Local Consent Layer for Open-Source AI Agents)!

---

## 🚀 How to Run the Project on Your Computer (In 2 Easy Steps)

### Step 1: Start the Local Server
Double-click `START_SERVER.bat` (or open your terminal and run):
```bash
python server.py
```
This starts the multi-threaded web server on `http://localhost:8000`.

### Step 2: Open in Your Browser
Open any web browser and visit:
* **Interactive 3D Walkthrough:** [http://localhost:8000/demo/index.html](http://localhost:8000/demo/index.html)
* **Main Launchpad & Listings:** [http://localhost:8000/](http://localhost:8000/)
* **Hackathon Presentation PDF Guide:** [http://localhost:8000/MayI_Hackathon_Guide.pdf](http://localhost:8000/MayI_Hackathon_Guide.pdf)

---

## 🤖 Optional: Running the Local AI Engine (Qwen2.5 3B)
The website works seamlessly offline with simulated fallbacks. If you want **live offline AI chat** with the Qwen2.5 3B model:
1. Download & install **Ollama** from [https://ollama.com](https://ollama.com).
2. Open terminal and run:
   ```bash
   ollama run qwen2.5:3b
   ```
3. Once running, MayI's floating chat assistant and agent execution will automatically route prompts through your local GPU/CPU with 100% privacy!

---

## 📂 Project Structure Overview
* **`START_SERVER.bat`** — 1-click launcher for Windows.
* **`server.py`** — Multi-threaded Python server, REST API (`/send`, `/poll`, `/v1/consent/*`) & Ollama bridge.
* **`mayi.db`** — Local SQLite database storing consent ledger and deduplicated chat messages.
* **`MayI_Hackathon_Guide.pdf`** — 5-page dossier for mentors & judges covering workflow, stack, and pitch Q&A.
* **`web/`** — All frontend pages, interactive 3D Cyber Shield WebGL (`mayi-3d.js`), glassmorphic UI, and chat assistant (`mayi-talk.js`).
* **`contracts/`** — Smart contracts for ERC-8004 machine pennies, ENS subnames, and 1inch Aqua pool guard.
* **`docs/`** — Specifications, ceremony protocols, and hackathon presentation guides.

---

## 💬 Tips for Pitching to Judges
* Read `MayI_Hackathon_Guide.pdf` for complete answers to judge questions!
* Remember the 5-step flow: **Browse → Hire → Bless → Utility (AI execution) → Revoke (one-word halt)**.
* Key selling point: **100% offline, zero cloud API fees, and instant 0ms revocation**.
