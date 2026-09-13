# Corpus — Backend

FastAPI backend for Corpus, the tattoo art decision layer. Powered by **Google Gemini AI**, SQLAlchemy (async), and FastAPI.

## Features

- **Phrase & Symbol Verification (`/verify`)**: Classical language accuracy checks (Latin, Classical Greek, Sanskrit) with grounded prompts and confidence scores.
- **AI Tattoo Concierge (`/concierge/*`)**: Interactive conversational discovery steering intent, placement, and style to produce a structured Tattoo Brief.
- **Taste Profile Quiz (`/taste-profile`)**: Deterministic aesthetic classification and plain-language summary.
- **Artist Directory & Matching (`/artists`)**: Overlap scoring algorithm matching client taste profiles with artists.
- **CORS Enabled**: Configured out of the box for web and mobile frontends.

---

## Local Setup

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and add your **Google Gemini API Key**:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   PORT=8003
   ```

4. **Run locally:**
   ```bash
   uvicorn app.main:app --reload --port 8003
   ```
   Visit `http://localhost:8003/docs` for the interactive Swagger UI.

---

## Deploying to Contabo VPS (Alongside Existing Backends)

Assuming you already have 2 backends running on your Contabo VPS, here is how to host this as your 3rd backend on a dedicated port (e.g. `8003`):

### 1. Copy Project to VPS
Clone or upload the repository to your VPS (e.g., `/var/www/corpus-backend`):
```bash
sudo mkdir -p /var/www/corpus-backend
sudo chown -R $USER:$USER /var/www/corpus-backend
# Upload your files or git clone here
```

### 2. Setup Virtualenv and `.env`
```bash
cd /var/www/corpus-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env # Paste your GEMINI_API_KEY and set PORT=8003
```

### 3. Setup Systemd Service
Copy the provided unit file to `/etc/systemd/system/`:
```bash
sudo cp deploy/corpus.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable corpus.service
sudo systemctl start corpus.service
sudo systemctl status corpus.service
```

### 4. Configure Nginx Reverse Proxy
Add a new site configuration for your subdomain:
```bash
sudo cp deploy/nginx-corpus.conf /etc/nginx/sites-available/corpus
sudo ln -s /etc/nginx/sites-available/corpus /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Enable SSL with Certbot
```bash
sudo certbot --nginx -d corpus-api.bankole.xyz
```

---

## Endpoints Summary

- `GET /health` — basic health check
- `POST /verify` — verify a phrase in Latin / Classical Greek / Sanskrit
- `POST /concierge/sessions` — start a new concierge conversation
- `GET /concierge/sessions/{session_id}` — fetch conversation history & `ready_for_brief` status
- `POST /concierge/sessions/{session_id}/messages` — send a message to the concierge
- `POST /concierge/sessions/{session_id}/brief` — generate structured brief
- `POST /taste-profile` — submit style quiz
- `GET /taste-profile/{profile_id}` — retrieve taste profile
- `POST /artists` — register an artist
- `GET /artists` — list all artists
- `GET /artists/{artist_id}` — get single artist
- `GET /artists/match/{profile_id}` — rank artists against a taste profile

