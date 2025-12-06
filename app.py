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


@app.route('/')
def index():
    if not session.get('user'):
        return redirect(url_for('login'))
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to index
    if session.get('user'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if email == TEST_USER['email'] and password == TEST_USER['password']:
            # set both email and name in session
            session['user'] = {
                'email': email,
                'name': TEST_USER.get('name', email.split('@')[0].title())
            }
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
