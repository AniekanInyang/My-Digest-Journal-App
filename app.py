from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import datetime
from datetime import timedelta
from dotenv import load_dotenv

# load .env from project root (python-dotenv)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'replace-this-with-a-secure-random-key'

# Simple test credentials (replace or wire in real auth in production)
TEST_USER = {
    'email': os.environ.get('TEST_EMAIL'),
    'password': os.environ.get('TEST_PASSWORD'),
    'name': os.environ.get('TEST_NAME')
}
DATA_FILE = os.path.join(os.path.dirname(__file__), 'journal.json')
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')
TOKENS_FILE = os.path.join(os.path.dirname(__file__), 'reset_tokens.json')


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_tokens():
    if not os.path.exists(TOKENS_FILE):
        return {}
    with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_tokens(tokens):
    with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)


def load_entries():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_entries(entries):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def _simple_summarize(texts, max_sentences=5):
    """Very small extractive summarizer: score sentences by term frequency."""
    # split into sentences naively by period. Keep original punctuation where possible.
    import re
    sentences = []
    for t in texts:
        parts = re.split(r'(?<=[\.!?])\s+', t.strip())
        for p in parts:
            s = p.strip()
            if s:
                sentences.append(s)
    if not sentences:
        return ''

    # build a simple token frequency map (lowercased words, strip punctuation)
    freq = {}
    WORD_RE = re.compile(r"\b[a-zA-Z]{2,}\b")
    for s in sentences:
        for w in WORD_RE.findall(s.lower()):
            freq[w] = freq.get(w, 0) + 1

    # score sentences
    scored = []
    for s in sentences:
        score = 0
        for w in WORD_RE.findall(s.lower()):
            score += freq.get(w, 0)
        scored.append((score, s))

    # pick top-N sentences by score, preserve original order
    scored.sort(key=lambda x: x[0], reverse=True)
    top = set(s for _, s in scored[:max_sentences])
    ordered = [s for s in sentences if s in top]
    return ' '.join(ordered)


@app.route('/')
def index():
    if not session.get('user'):
        return redirect(url_for('login'))
    # clear any previous selection when returning to the homepage
    session.pop('selected_ids', None)
    # Homepage: show recent entries (no filter)
    entries = load_entries()
    entries = sorted(entries, key=lambda e: e['created_at'], reverse=True)
    # limit to recent 10 for homepage
    recent = entries[:10]

    # add a display timestamp for each entry in ISO-like format
    for e in recent:
        try:
            ts = datetime.fromisoformat(e['created_at'].replace('Z', ''))
            e['display_time'] = ts.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            e['display_time'] = e['created_at']

    # show saved modal only once after creating an entry
    saved = session.pop('saved', False)
    return render_template('index.html', entries=recent, saved=saved)


@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    if not session.get('user'):
        return redirect(url_for('login'))
    entries = load_entries()
    entries = [e for e in entries if e.get('id') != entry_id]
    save_entries(entries)
    return redirect(url_for('index'))


@app.route('/delete_bulk', methods=['POST'])
def delete_bulk():
    if not session.get('user'):
        return redirect(url_for('login'))
    # get list of selected ids from the form
    selected = request.form.getlist('selected')
    try:
        ids = set(int(x) for x in selected)
    except Exception:
        ids = set()
    entries = load_entries()
    entries = [e for e in entries if e.get('id') not in ids]
    save_entries(entries)
    # optional redirect target
    next_path = request.form.get('next')
    if next_path and isinstance(next_path, str) and next_path.startswith('/'):
        # strip queryless full_path may include '?', keep as-is
        return redirect(next_path)
    return redirect(url_for('index'))


@app.route('/edit/<int:entry_id>', methods=['GET', 'POST'])
def edit_entry(entry_id):
    if not session.get('user'):
        return redirect(url_for('login'))
    entries = load_entries()
    entry = next((e for e in entries if e.get('id') == entry_id), None)
    if not entry:
        return redirect(url_for('index'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        entry['title'] = title
        entry['content'] = content
        save_entries(entries)
        return redirect(url_for('index'))
    # GET: render new.html with entry prefilled
    return render_template('new.html', entry=entry)


@app.route('/past')
def past_entries():
    if not session.get('user'):
        return redirect(url_for('login'))

    entries = load_entries()

    # Filtering by preset range or custom start/end
    preset = request.args.get('preset', 'all')
    start = request.args.get('start')
    end = request.args.get('end')

    def in_range(e):
        ts = datetime.fromisoformat(e['created_at'].replace('Z', ''))
        now = datetime.utcnow()
        if preset and preset != 'custom' and preset != 'all':
            if preset == 'week':
                return (now - ts).days < 7
            if preset == 'month':
                return (now - ts).days < 31
            if preset == 'year':
                return (now - ts).days < 365
        if start:
            try:
                s = datetime.fromisoformat(start)
                if ts < s:
                    return False
            except Exception:
                pass
        if end:
            try:
                e_dt = datetime.fromisoformat(end)
                if ts > e_dt:
                    return False
            except Exception:
                pass
        return True

    filtered = [e for e in entries if in_range(e)]
    filtered = sorted(filtered, key=lambda e: e['created_at'], reverse=True)
    # add display_time for filtered entries
    for e in filtered:
        try:
            ts = datetime.fromisoformat(e['created_at'].replace('Z', ''))
            e['display_time'] = ts.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            e['display_time'] = e['created_at']
    return render_template('past.html', entries=filtered, preset=preset, start=start, end=end)


@app.route('/new', methods=['GET', 'POST'])
def new_entry():
    if not session.get('user'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if title or content:
            entries = load_entries()
            entry = {
                'id': len(entries) + 1,
                'title': title,
                'content': content,
                'created_at': datetime.utcnow().isoformat() + 'Z'
            }
            entries.append(entry)
            save_entries(entries)
        # set a session flag so the UI can show a saved modal once
        session['saved'] = True
        return redirect(url_for('index'))
    # GET or no content: render the new entry form
    return render_template('new.html')


@app.route('/summarize', methods=['POST'])
def summarize_selected():
    """Summarize selected entries (form field 'selected') and show a summary page."""
    if not session.get('user'):
        return redirect(url_for('login'))
    selected = request.form.getlist('selected')
    # handle ids that might be strings from the form; compare both ways
    # persist the selection so Past can re-check them when user returns
    session['selected_ids'] = selected
    selected_set = set(selected)
    entries = load_entries()
    chosen = [e for e in entries if str(e.get('id')) in selected_set or e.get('id') in (int(x) for x in selected if x.isdigit())]
    # sort chosen by created_at desc and compute display_time like elsewhere
    chosen = sorted(chosen, key=lambda e: e['created_at'], reverse=True)
    for e in chosen:
        try:
            ts = datetime.fromisoformat(e['created_at'].replace('Z', ''))
            e['display_time'] = ts.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            e['display_time'] = e['created_at']

    texts = [ (e.get('title') or '') + '. ' + (e.get('content') or '') for e in chosen ]
    summary = _simple_summarize(texts, max_sentences=5)
    return render_template('summary.html', summary=summary, entries=chosen)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user'):
        return redirect(url_for('index'))
    error = None
    success = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        users = load_users()
        if not email or not password:
            error = 'Email and password required'
        elif email in users:
            error = 'Account already exists'
        else:
            users[email] = {'name': name or email.split('@')[0].title(), 'password': password}
            save_users(users)
            success = 'Account created. You can sign in.'
    return render_template('register.html', error=error, success=success)


@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    info = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        users = load_users()
        if email in users:
            # generate a simple token
            import uuid
            token = uuid.uuid4().hex
            tokens = load_tokens()
            tokens[token] = {'email': email}
            save_tokens(tokens)
            # In a real app we'd email this. For demo, show the link.
            info = f"Reset link (demo): /reset/{token}"
        else:
            info = 'If that email exists, a reset link was generated.'
    return render_template('forgot.html', info=info)


@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token):
    tokens = load_tokens()
    data = tokens.get(token)
    if not data:
        return render_template('reset.html', error='Invalid or expired token')
    if request.method == 'POST':
        password = request.form.get('password', '')
        if not password:
            return render_template('reset.html', error='Password required')
        users = load_users()
        email = data['email']
        if email in users:
            users[email]['password'] = password
            save_users(users)
            # consume token
            tokens.pop(token, None)
            save_tokens(tokens)
            return redirect(url_for('login'))
        return render_template('reset.html', error='User not found')
    return render_template('reset.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to index
    if session.get('user'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        users = load_users()
        u = users.get(email.lower())
        if u and u.get('password') == password:
            session['user'] = {'email': email, 'name': u.get('name', email.split('@')[0].title())}
            return redirect(url_for('index'))
        # fallback to TEST_USER for demo if present
        if email == TEST_USER.get('email') and password == TEST_USER.get('password'):
            session['user'] = {'email': email, 'name': TEST_USER.get('name', email.split('@')[0].title())}
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('selected_ids', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
