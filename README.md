# Corpus — Backend

FastAPI backend for Corpus, the tattoo art decision layer. Powered by **Google Gemini AI**, SQLAlchemy (async), and FastAPI.

## Features

- **Phrase & Symbol Verification (`/verify`)**: Universal language & script accuracy checks (Latin, Japanese, Arabic, Greek, Sanskrit, French, Spanish, English, etc.) with automatic language detection, grounded linguistic audits, and confidence scores.
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

### Authentication (`/auth`)
- `POST /auth/register` — create account with `email`, `password`, and optional `full_name` (returns JWT + profile)
- `POST /auth/login` — authenticate with `email` and `password` (returns JWT + profile)
- `POST /auth/google` — authenticate or auto-register using a Google ID token (`credential`)
- `POST /auth/forgot-password` — request a password reset email via Brevo
- `POST /auth/reset-password` — reset password using a single-use reset token
- `GET /auth/me` — retrieve authenticated user profile (`Authorization: Bearer <token>`)

### Phrase & Symbol Verification (`/verify`)
- `POST /verify` — verify a phrase across languages (auto-associated with user if authenticated)
- `GET /verify/history` — fetch user's private verification history (requires auth)
- `GET /verify/{record_id}` — retrieve a single verification record (owner or public if guest)
- `DELETE /verify/{record_id}` — delete a verification record (owner or admin only)

### AI Tattoo Concierge (`/concierge`)
- `POST /concierge/sessions` — start a new concierge conversation (associated with user if logged in)
- `GET /concierge/sessions` — list all concierge conversations belonging to current user
- `GET /concierge/sessions/{session_id}` — fetch conversation history & `ready_for_brief` status
- `POST /concierge/sessions/{session_id}/messages` — send a message to the concierge
- `POST /concierge/sessions/{session_id}/brief` — generate structured brief

### Taste Profile (`/taste-profile`)
- `POST /taste-profile` — submit style quiz (associates with user if logged in)
- `GET /taste-profile/me` — fetch current user's latest taste profile (requires auth)
- `GET /taste-profile/deck` — fetch curated swipe deck of real tattoo photos with style tags
- `GET /taste-profile/{profile_id}` — retrieve taste profile by ID

### Artists (`/artists`)
- `POST /artists` — register an artist (**Admin only**: requires `is_admin` token or `X-Admin-Key` header)
- `GET /artists` — list all artists
- `GET /artists/{artist_id}` — get single artist
- `PUT /artists/{artist_id}` — update artist profile & style tags (**Admin only**)
- `DELETE /artists/{artist_id}` — delete an artist (**Admin only**)
- `GET /artists/match/{profile_id}` — rank artists against a taste profile

### Admin Control Suite (`/admin`)
All `/admin/*` endpoints require `is_admin=True` or `X-Admin-Key: <ADMIN_API_KEY>`.
- `GET /admin/metrics` — global analytics dashboard (total users, active users, verifications, language breakdown, chat stats, artists)
- `GET /admin/users` — paginated user list with search (`q`), role filter, and activity counts
- `GET /admin/users/{user_id}` — full user activity inspector (verifications, chats, taste profiles)
- `PATCH /admin/users/{user_id}` — manage user status (ban/activate, toggle admin rights)
- `GET /admin/verifications` — global feed of all phrase verifications across the platform
- `DELETE /admin/verifications/{record_id}` — remove any verification record
- `GET /admin/concierge/sessions` — global feed of all AI concierge chat sessions
- `GET /admin/concierge/sessions/{session_id}` — inspect full transcript and generated brief
- `DELETE /admin/concierge/sessions/{session_id}` — remove any chat session
- `GET /admin/taste-profiles` — view all submitted taste discovery profiles

### Health
- `GET /health` — basic health check

