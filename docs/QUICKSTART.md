# Quick Start Guide - Phase 1 RAG Features

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start the App
```bash
python app.py
```

### Step 3: Migrate Your Entries
1. Navigate to http://127.0.0.1:5000
2. Login with your credentials
3. Click "💬 Ask My Journal" button
4. Click "🔄 Migrate Existing Entries"
5. Click "Start Migration" and wait

---

## 💡 Try These Queries

Once migration is complete, try asking:

**Reflection Questions:**
- "What have I been grateful for this month?"
- "What challenges did I face recently?"
- "When did I feel most productive?"

**Pattern Discovery:**
- "What patterns do you see in my mood?"
- "What topics do I write about most?"
- "How has my mindset changed over time?"

**Memory Recall:**
- "When did I last write about [topic]?"
- "What did I think about [event]?"
- "Find entries where I felt happy"

**Planning & Goals:**
- "What goals have I mentioned?"
- "What am I working towards?"
- "What progress have I made on [goal]?"

---

## 📊 Understanding the Interface

### Chat Page Elements:

1. **Stats Box** (top)
   - Shows total entries in vector database
   - Appears as: "🔍 Searching across X journal entries"

2. **Chat Messages** (center)
   - Your questions in purple (right side)
   - AI responses in gray (left side)
   - Timestamp on each message

3. **Context Entries** (expandable)
   - Click "📝 Based on X entries" to see sources
   - Shows which entries informed the answer
   - Date and preview of each source entry

4. **Input Box** (bottom)
   - Type your question
   - Press Enter or click ➤ to send

### Migration Page Elements:

1. **Current Status Card**
   - Total Journal Entries: Your full entry count
   - In Vector Database: Already migrated entries

2. **What is Migration? Card**
   - Explains benefits of RAG

3. **Important Notes Card**
   - Migration time estimates
   - Safety information

---

## 🔧 Testing Checklist

After setup, verify these work:

- [ ] Migration completes without errors
- [ ] Stats show correct entry count
- [ ] Search returns relevant results
- [ ] Chat responses reference correct entries
- [ ] New entry is immediately searchable
- [ ] Deleted entry removed from search
- [ ] Bulk upload entries are searchable

---

## ⚠️ Troubleshooting

### "No entries in vector database" Warning
**Problem:** Vector DB is empty  
**Solution:** Run migration first

### Migration Fails
**Check:**
1. Azure OpenAI credentials in .env
2. Internet connection
3. API rate limits not exceeded
4. Console for error messages

### Search Not Working
**Check:**
1. Migration completed successfully
2. Stats show entries > 0
3. Query is specific enough
4. Entries contain relevant content

### Chat Gives Generic Answers
**Likely cause:** Not enough relevant entries found  
**Solutions:**
- Try more specific queries
- Add more journal entries
- Check if migration included all entries

---

## 📈 Performance Notes

### Migration Speed
- ~1-2 seconds per entry
- 50 entries ≈ 1-2 minutes
- 100 entries ≈ 2-3 minutes
- 500 entries ≈ 10-15 minutes

### API Costs (Azure OpenAI)
Per query:
- 1 embedding call (~$0.0001)
- 1 chat completion call (~$0.001-0.002)
- Total: ~$0.001-0.002 per question

Per migration:
- 1 embedding per entry
- 100 entries ≈ $0.01
- 1000 entries ≈ $0.10

### Storage
- ChromaDB: ~1-5 MB per 1000 entries
- Local storage only (no cloud)
- Backed up with journal files

---

## 🎯 Best Practices

### Writing Better Queries

**❌ Too Vague:**
- "Tell me about last week"
- "What did I do?"

**✅ Specific:**
- "What was I worried about last week?"
- "What did I learn from my project?"

### Managing Entry Count

- More entries = better context
- Quality > quantity (detailed entries better than brief)
- Regular journaling improves AI responses
- Migration needed only once

### Chat History

- Saved during session
- Cleared on logout (by design)
- Can clear manually anytime
- Last 20 messages kept (10 exchanges)

---

## 🔐 Privacy & Security

- All data stored **locally** (no cloud database)
- ChromaDB in `./chroma_db/` directory
- Chat history in session (temporary)
- Embeddings sent to Azure OpenAI (as configured)
- No third-party vector database service

---

## 🐛 Known Issues

1. **Chat history lost on logout**
   - By design (session-based)
   - Future: Optional persistence

2. **Migration required for old entries**
   - One-time operation
   - New entries auto-indexed

3. **Search quality varies**
   - Depends on entry count and content
   - More entries = better results

---

## 📞 Need Help?

1. Read [PHASE1_README.md](PHASE1_README.md) for detailed info
2. Run `python test_rag.py` to verify setup
3. Check console logs for errors
4. Verify .env configuration

---

**Enjoy your AI-powered journal! 🎉**
