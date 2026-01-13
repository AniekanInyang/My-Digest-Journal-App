# Fly.io Deployment Guide

## Overview

This app is deployed to **Fly.io** using **SQLite** (local database stored in `/data/app.db`).

- **Local mode:** Uses JSON files for storage (development)
- **Deployed mode:** Uses SQLite database (production on Fly.io)
- **Cost:** Completely free on Fly.io's free tier

---

## Prerequisites

Before deploying, ensure you have:

1. **Fly.io CLI installed:**
   ```bash
   brew install flyctl
   ```

2. **Fly.io account** (free tier available):
   - Sign up at https://fly.io

3. **Azure OpenAI** (for summarization feature):
   - Azure OpenAI resource (endpoint + API key)
   - Model: `gpt-4o-mini` (cheap and performant)

4. **Git repository initialized:**
   ```bash
   cd /path/to/My-Digest-Journal-App
   git init
   git add .
   git commit -m "Initial commit"
   ```

---

## Step 1: Authenticate with Fly.io

```bash
flyctl auth login
```

This opens a browser window. Log in with your Fly.io account.

---

## Step 2: Create Fly.io App (First Time Only)

```bash
flyctl launch
```

When prompted:
- **App name:** `my-journal-app` (or your preferred name)
- **Region:** `ewr` (East US recommended)
- **Postgres database:** Choose **No** (we're using SQLite)
- **Redis cache:** Choose **No**

This generates/updates `fly.toml`.

---

## Step 3: Set Environment Secrets

```bash
flyctl secrets set \
  AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/" \
  AZURE_OPENAI_KEY="your-api-key" \
  AZURE_OPENAI_MODEL_NAME="gpt-4o-mini" \
  SECRET_KEY="your-random-secret-key"
```

**Generate a secure SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Verify secrets were set:**
```bash
flyctl secrets list
```

---

## Step 4: Deploy to Fly.io

```bash
flyctl deploy
```

This:
1. Builds the Docker image (based on `Dockerfile`)
2. Pushes to Fly.io registry
3. Deploys to a VM
4. Starts the app automatically

Monitor deployment:
```bash
flyctl logs
```

Watch for: `[INFO] Listening at: http://0.0.0.0:8080 (XXX)` ✅

---

## Step 5: Verify Deployment

Check app status:
```bash
flyctl status
```

Get your app URL:
```bash
flyctl open
```

This opens your app in the browser. You should see the login page.

---

## Step 6: Test the App

1. **Sign in:** Use test credentials from `.env`:
   - Email: `test@example.com`
   - Password: `password123`
2. **Create entry:** Add a journal entry from the homepage or `/new`
3. **View entries:** Click "View Past Entries" to see all entries
4. **Test summarization:** Select multiple entries and click "Summarize"
5. **Check logs:** `flyctl logs` to see requests and Azure OpenAI interactions

---

## Database

### Local Mode (`ENVIRONMENT=local`)
- Stores data in JSON files: `journal.json`, `users.json`, `reset_tokens.json`
- Useful for development and testing
- No database setup required

### Deployed Mode (`ENVIRONMENT=deployed`)
- Stores data in **SQLite** database: `/data/app.db`
- Database persists across app restarts
- Lightweight and requires no external database service
- Completely free (included in Fly.io free tier)

**Switching modes:**
In `.env` or `fly.toml`, set:
```
ENVIRONMENT=local      # for local development
ENVIRONMENT=deployed   # for production
```

---

## Troubleshooting

### **App won't start / 502 error**
```bash
flyctl logs
```
Check for errors. Common issues:
- Missing `AZURE_OPENAI_KEY` or `AZURE_OPENAI_ENDPOINT`
- Wrong Azure OpenAI credentials
- Database permission issues

**Fix:**
```bash
# Verify secrets
flyctl secrets list

# Update a secret if wrong
flyctl secrets set AZURE_OPENAI_KEY="new-key"

# Redeploy
flyctl deploy
```

### **Azure OpenAI 404 errors**
- Verify `AZURE_OPENAI_MODEL_NAME` matches your deployment name (should be `gpt-4o-mini`)
- Check endpoint URL format: `https://<resource>.openai.azure.com/`
- Ensure API key is valid and not expired
- Verify model is deployed in Azure

### **SQLite database locked**
- Rare issue with concurrent access
- Usually resolves on its own after app restart
- Check logs: `flyctl logs`

### **Can't log in with test account**
- Test credentials: `test@example.com` / `password123`
- Create a new account at `/register` page instead
- Check app logs for authentication issues

---

## Useful Commands

```bash
# View logs in real-time
flyctl logs --follow

# View last 100 log lines
flyctl logs --no-tail

# SSH into running app
flyctl ssh console

# Restart app gracefully
flyctl apps restart my-journal-app

# View app status
flyctl status

# List all secrets
flyctl secrets list

# Update a single secret
flyctl secrets set SECRET_KEY="new-value"

# Monitor resources
flyctl resources

# Rollback to previous deployment
flyctl releases list
flyctl releases rollback <version>

# Destroy app (delete everything)
flyctl apps destroy my-journal-app
```

---

## Costs

**Fly.io free tier includes:**
- Up to **3 shared-cpu-1x VMs** (256 MB RAM each)
- **160 GB outbound bandwidth/month**
- Unlimited inbound bandwidth

**Your app:**
- Uses **1 VM** (within free tier)
- Uses **~100-500 MB bandwidth/month** (depending on traffic)
- No database fees (SQLite is local)

**Additional costs:**
- **Azure OpenAI:** ~$0.00015 per 1K input tokens, ~$0.0006 per 1K output tokens
  - Typical summarization request: ~$0.001-0.01
  - Estimate: $10-20/month if using summarization feature regularly
- **Total:** **Fly.io: Free | Azure: $10-20/month**

**Cost optimization:**
- Delete unused app: `flyctl apps destroy my-journal-app`
- Scale down if not using: `flyctl scale count 1`
- Use cheaper LLM models if available

---

## Deployment Checklist

- [ ] Fly.io CLI installed and authenticated
- [ ] `.env` file configured locally (for development)
- [ ] `fly.toml` configured with app name and region
- [ ] Azure OpenAI endpoint and key obtained
- [ ] `SECRET_KEY` generated (secure random string)
- [ ] All secrets set on Fly.io: `flyctl secrets list`
- [ ] `Dockerfile` present and correct
- [ ] `requirements.txt` up to date
- [ ] App tested locally: `python3 app.py`
- [ ] Deployed: `flyctl deploy`
- [ ] App verified working: `flyctl open`
- [ ] Test login with credentials
- [ ] Test entry creation and summarization

---

## Next Steps

1. **Deploy:** `flyctl deploy`
2. **Monitor:** `flyctl logs --follow`
3. **Test:** Open app URL from `flyctl open`
4. **Add custom domain** (optional):
   ```bash
   flyctl certs add your-domain.com
   ```
5. **Regular monitoring:**
   ```bash
   flyctl status
   flyctl apps list
   ```

---

## Documentation

- **Fly.io:** https://fly.io/docs/
- **Flask:** https://flask.palletsprojects.com/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **Azure OpenAI:** https://learn.microsoft.com/en-us/azure/ai-services/openai/

---

## Recent Updates (Jan 2026)

- ✅ Migrated from Azure SQL to **SQLite** (simpler, free)
- ✅ Removed Azure SQL/ODBC dependencies (simplified Docker image)
- ✅ Added persistent data storage at `/data/app.db`
- ✅ Updated button visibility on entries page (UI fix)
- ✅ Generated secure `SECRET_KEY` for Flask sessions
- ✅ App fully deployed and tested on Fly.io

