# My-Digest-Journal-App
Personal journal web app with AI-powered summaries, insights, and semantic search

## ✨ New in Phase 1: RAG Integration

**Ask My Journal** - Chat with your journal using natural language! Phase 1 adds:
- 💬 Semantic search across all entries
- 🤖 AI-powered Q&A about your journal
- 🔍 Find entries by meaning, not just keywords
- 📊 Pattern detection and insights

**See [PHASE1_README.md](PHASE1_README.md) for full details!**

---

## Features

- 📝 Create and manage journal entries
- 📅 Calendar date picker for backdated entries
- 📄 Bulk import from PDF, DOCX, and TXT files
- 🤖 AI-generated summaries and insights (Azure OpenAI)
- 💬 **NEW:** Natural language chat with your journal
- 🔍 **NEW:** Semantic search across entries
- 🔐 User authentication and registration
- 📊 Entry selection and batch operations

### For the initial setup
- Clone git repo
- CD to repo directory
- Run `pip install -r requirements.txt` in the terminal 
- Create .env file (copy from .env.example)
- Set environment variables in .env (Azure OpenAI credentials required)

### To run app
- CD to repo directory
- Run `python app.py` in the terminal
- Open http://127.0.0.1:5000 in browser
- Login with test user email and password set in .env 

### First-time RAG Setup
1. Start the app
2. Click "Ask My Journal" button
3. Wait for migration to complete
4. Start asking questions!

