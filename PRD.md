# Journal App - Product Requirements Document (PRD)

## 1. Overview
A personal journal web application with AI-powered summarization, sentiment analysis, and insights. Users can quickly log entries, filter by date range, bulk-select entries, and generate AI-driven summaries using Azure OpenAI.

**Status:** Implementation Phase  
**Last Updated:** January 10, 2026

---

## 2. Core Features

### 2.1 Authentication
- **Email/Password Registration:** Users can sign up with email + password (hashed with `werkzeug.security`).
- **Google OAuth Sign-In:** Users can sign in via Google (no password stored for Google auth).
- **Password Reset:** Email-based password reset flow with time-limited tokens.
- **Session Management:** Flask sessions with secure cookies.

### 2.2 Journal Entries
- **Create:** Quick entry with title and content.
- **Read:** View all entries or filter by date range (past entries page).
- **Update:** Edit existing entries.
- **Delete:** Single delete or bulk delete multiple selected entries.

### 2.3 Summarization & Insights
- **Bulk Select:** Users select multiple entries via checkboxes.
- **Azure OpenAI Integration:** Call Azure OpenAI (gpt-4o-mini) to:
  - Generate a concise summary of selected entries.
  - Extract sentiment (positive/neutral/negative).
  - Provide key insights (bullet points).
- **Display:** Show summary, sentiment, and insights on a results page.
- **No Persistence:** Summaries are generated on-the-fly, not stored in DB.

### 2.4 UI/UX
- **Purple/Lilac Theme:** Cohesive color palette (primary: #9B7CF5, lilac: #EEDFFB).
- **Responsive Design:** Mobile and desktop friendly.
- **Quick Entry CTA:** Prominent "New Entry" call-to-action on homepage.
- **Filter & Search:** Date range filtering on past entries page.
- **Bulk Operations:** Select, summarize, and delete multiple entries at once.

---

## 3. Tech Stack

### Backend
- **Framework:** Flask (Python 3.x)
- **Database:** Azure PostgreSQL (managed, cloud-hosted)
- **ORM:** SQLAlchemy (Flask-SQLAlchemy)
- **Authentication:** 
  - Local: `werkzeug.security.generate_password_hash()` + `check_password_hash()`
  - OAuth: `google-auth-oauthlib`
- **AI/ML:** Azure OpenAI (`openai` SDK)
- **Environment:** Python 3.9+, gunicorn (WSGI server)

### Frontend
- **Templating:** Jinja2 (server-side rendering)
- **Styling:** CSS (custom, purple/lilac theme)
- **Interactivity:** Vanilla JavaScript (no framework)

### Deployment
- **API/App Server:** Fly.io (Docker container, free tier)
- **Database:** Azure PostgreSQL (managed, free tier available)
- **AI API:** Azure OpenAI (pay-per-token, gpt-4o-mini)
- **Optional CDN:** Cloudflare (optional, for caching/DDoS protection)

---

## 4. Database Schema (Entity-Relationship Model)

### Entities & Relationships

```
┌─────────────────────────────────────────────────────┐
│                     USERS                           │
├─────────────────────────────────────────────────────┤
│ id (UUID, PK)                                       │
│ email (VARCHAR, UNIQUE)                             │
│ name (VARCHAR)                                      │
│ password_hash (VARCHAR, NULLABLE)                   │
│ google_id (VARCHAR, UNIQUE, NULLABLE)               │
│ created_at (TIMESTAMP)                              │
│ updated_at (TIMESTAMP)                              │
└─────────────────────────────────────────────────────┘
         │
         │ 1:N
         │
         ├──────────────────────────────────────────┐
         │                                          │
         ▼                                          ▼
┌──────────────────────┐           ┌────────────────────────┐
│      ENTRIES         │           │   RESET_TOKENS         │
├──────────────────────┤           ├────────────────────────┤
│ id (UUID, PK)        │           │ id (UUID, PK)          │
│ user_id (FK)         │           │ user_id (FK)           │
│ title (VARCHAR)      │           │ token (VARCHAR)        │
│ content (TEXT)       │           │ created_at (TIMESTAMP) │
│ created_at (TIMESTAMP)           │ expires_at (TIMESTAMP) │
│ updated_at (TIMESTAMP)           │                        │
└──────────────────────┘           └────────────────────────┘
```

### Table Definitions

| Table | Columns | Purpose |
|-------|---------|---------|
| **USERS** | id, email, name, password_hash, google_id, created_at, updated_at | User accounts; supports email/password or Google OAuth |
| **ENTRIES** | id, user_id (FK), title, content, created_at, updated_at | Journal entries authored by users |
| **RESET_TOKENS** | id, user_id (FK), token, created_at, expires_at | Password reset tokens with expiry |

### Relationships
- **USERS → ENTRIES:** 1:N (One user has many entries)
- **USERS → RESET_TOKENS:** 1:N (One user has many reset tokens)
- **Cascade Delete:** Deleting a user deletes all their entries and tokens.

---

## 5. Authentication Flow

### 5.1 Email/Password Sign-Up
```
User → Sign-Up Form → Hash Password → Store in DB → Auto-Login
```

### 5.2 Email/Password Sign-In
```
User → Login Form → Verify Email Exists → Compare Password Hash → Session Cookie
```

### 5.3 Google OAuth Sign-In
```
User → "Sign in with Google" → Google Auth → Store/Link Google ID → Session Cookie
```

### 5.4 Password Reset
```
User → Forgot Password → Submit Email → Generate Token (expiry: 24h) → Email Link → Reset Form → Update Hash → Clear Token
```

---

## 6. API Endpoints (Summary)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/` | Homepage (quick entry) | Optional |
| GET | `/past` | View/filter past entries | Required |
| POST | `/new` | Create new entry | Required |
| POST | `/edit/<id>` | Update entry | Required |
| POST | `/delete/<id>` | Delete single entry | Required |
| POST | `/delete_bulk` | Delete multiple entries | Required |
| POST | `/summarize` | Generate AI summary of selected entries | Required |
| GET/POST | `/login` | Sign in (email/password or Google) | Public |
| GET/POST | `/register` | Sign up | Public |
| GET/POST | `/forgot` | Request password reset | Public |
| GET/POST | `/reset/<token>` | Reset password | Public |
| POST | `/logout` | Sign out | Required |

---

## 7. Deployment Architecture

### Development
```
Local Machine
├── Flask App (app.py)
├── Local DB (optional SQLite for testing)
└── .env (TEST credentials)
```

### Production
```
┌──────────────────┐
│   Fly.io         │
│   ┌────────────┐ │
│   │ Flask App  │ │
│   │ + Gunicorn │ │
│   └────────────┘ │
│   (Always-on)    │
└────────┬─────────┘
         │ TCP
         │
    ┌────▼──────────────────────┐
    │  Azure PostgreSQL          │
    │  ┌──────────────────────┐  │
    │  │ users                │  │
    │  │ entries              │  │
    │  │ reset_tokens         │  │
    │  └──────────────────────┘  │
    └────────────────────────────┘
         │ HTTPS
         │
    ┌────▼──────────────────────┐
    │  Azure OpenAI              │
    │  (gpt-4o-mini)             │
    └────────────────────────────┘

Optional:
┌────────────────────────────────┐
│  Cloudflare (CDN/Cache/DDoS)   │
│  ↓                             │
│  Fly.io                        │
└────────────────────────────────┘
```

### Deployment Flow
1. **Create Azure PostgreSQL** → Get connection string.
2. **Create Azure OpenAI resource** → Deploy gpt-4o-mini → Get endpoint + key.
3. **Push code to Fly.io** → fly launch + fly deploy.
4. **Set secrets in Fly.io** → DATABASE_URL, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, SECRET_KEY.
5. **Verify endpoints** → Test login, create entry, summarize.
6. **(Optional) Configure Cloudflare** → Point domain to Fly.io, enable caching.

---

## 8. Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Flask session secret | `your-random-secret-key` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI service endpoint | `https://resource.openai.azure.com/` |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key | `your-api-key` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | `xxxxx.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | `xxxxx-xxxxx` |
| `FLASK_ENV` | Environment mode | `production` (Fly.io) or `development` (local) |

---

## 9. Cost Estimate (Monthly)

| Service | Tier | Cost |
|---------|------|------|
| Fly.io | Free (1 small VM) | $0 |
| Azure PostgreSQL | Free tier (if available) or B1 | $0–$15 |
| Azure OpenAI (gpt-4o-mini) | Pay-per-token | $5–$20 (depending on usage) |
| Cloudflare | Free (optional) | $0 |
| **Total** | | **$5–$35/month** |

---

## 10. Success Metrics

- ✅ Users can sign up and log in securely (email/password or Google).
- ✅ Users can create, edit, delete entries with full CRUD.
- ✅ Entries are persisted in Azure PostgreSQL.
- ✅ Users can select multiple entries and generate AI summaries.
- ✅ Azure OpenAI returns summaries, sentiment, and insights within 5 seconds.
- ✅ App is live and accessible on Fly.io.
- ✅ Zero password data breaches (passwords hashed, Google OAuth used where possible).

---

## 11. Timeline

| Phase | Task | Estimated Duration |
|-------|------|-------------------|
| 1 | Design & approve PRD | ✅ Complete |
| 2 | Create DB schema + models.py | 1 hour |
| 3 | Migrate app.py to SQLAlchemy | 2 hours |
| 4 | Add password hashing + Google OAuth | 1.5 hours |
| 5 | Add Azure OpenAI integration | 1 hour |
| 6 | Create Dockerfile + fly.toml | 30 minutes |
| 7 | Test locally | 30 minutes |
| 8 | Deploy to Fly.io | 30 minutes |
| 9 | Configure Azure resources | 1 hour |
| **Total** | | **~8 hours** |

---

## 12. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Azure DB connection limits on Fly.io | Set SQLAlchemy pool_size=5, max_overflow=10. Monitor connections. |
| Cold starts (Fly.io wake-up) | None needed; Fly.io is always-on (unlike Render). |
| Azure OpenAI rate limits | Implement retry logic + exponential backoff. Set user-level limits. |
| Data loss during migration | Backup JSON files before importing. Test migration script locally first. |
| Security (password breaches) | Use bcrypt hashing, enforce strong passwords, rate-limit login attempts. |
| Google OAuth key leaks | Store keys in Fly.io secrets, never commit to repo. Rotate keys quarterly. |

---

## 13. Next Steps

1. **Approval:** Confirm PRD with stakeholders.
2. **Database Setup:** Create Azure PostgreSQL instance.
3. **Implementation:** Build models.py, update app.py, add OAuth.
4. **Testing:** Test auth flows, CRUD, AI summarization locally.
5. **Deployment:** Deploy to Fly.io, configure secrets.
6. **Monitoring:** Set up error logging, monitor Azure DB connections and OpenAI costs.

---

**Document Owner:** Development Team  
**Last Reviewed:** January 10, 2026  
**Next Review:** After initial deployment
