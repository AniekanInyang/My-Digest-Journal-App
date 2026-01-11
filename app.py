from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from ai_service import get_summary, get_insights
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# load .env from project root (python-dotenv)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ============================================
# Environment & Configuration
# ============================================
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'local').lower()  # 'local' or 'deployed'
IS_DEPLOYED = ENVIRONMENT == 'deployed'

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY')

# ============================================
# Rate Limiting Setup
# ============================================
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# ============================================
# Input Validation Functions
# ============================================
def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None

def validate_password(password):
    """Validate password strength (min 8 chars)."""
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters"
    return True, None

def sanitize_name(name):
    """Sanitize user name (max 100 chars, strip whitespace)."""
    return name.strip()[:100]

def sanitize_text(text, max_length=1000):
    """Sanitize text input (strip, limit length)."""
    return text.strip()[:max_length]

# Simple test credentials (for local testing)
TEST_USER = {
    'email': os.environ.get('TEST_EMAIL'),
    'password': os.environ.get('TEST_PASSWORD'),
    'name': os.environ.get('TEST_NAME')
}

# JSON file paths (used in local mode)
DATA_FILE = os.path.join(os.path.dirname(__file__), 'journal.json')

# ============================================
# Database Setup (SQLAlchemy for deployed mode)
# ============================================
if IS_DEPLOYED:
    from flask_sqlalchemy import SQLAlchemy
    from models import db as models_db, User, Entry, ResetToken
    
    # Use SQLite on Fly.io (stored in /data/app.db which persists across restarts)
    db_path = '/data/app.db' if os.path.exists('/data') or True else 'app.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = models_db
    db.init_app(app)
    
    # Create tables on startup (only if they don't already exist)
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            # Tables might already exist, which is fine
            print(f"Note: db.create_all() raised an exception (likely tables exist): {e}")
else:
    # In local mode, we don't use SQLAlchemy - use JSON files instead
    db = None
    User = None
    Entry = None
    ResetToken = None


def load_entries():
    """Load entries from JSON (local mode only)."""
    if IS_DEPLOYED:
        return None
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            entries = json.load(f)
            # Repair: ensure all IDs are unique and sequential
            seen_ids = set()
            next_id = 1
            for e in entries:
                if e.get('id') in seen_ids:
                    # Duplicate ID found, assign a new one
                    e['id'] = next_id
                    while e['id'] in seen_ids:
                        next_id += 1
                        e['id'] = next_id
                else:
                    seen_ids.add(e.get('id'))
                    next_id = max(next_id, (e.get('id') or 0) + 1)
            # If IDs were fixed, save the corrected file
            if len(seen_ids) != len(entries):
                save_entries(entries)
            return entries
        except json.JSONDecodeError:
            return []


def save_entries(entries):
    """Save entries to JSON (local mode only)."""
    if IS_DEPLOYED:
        return
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def generate_reset_token():
    """Generate a unique reset token for password reset."""
    import uuid
    return str(uuid.uuid4())


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
        title = sanitize_text(request.form.get('title', ''), max_length=200)
        content = sanitize_text(request.form.get('content', ''), max_length=10000)
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
        title = sanitize_text(request.form.get('title', ''), max_length=200)
        content = sanitize_text(request.form.get('content', ''), max_length=10000)
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
    """Summarize selected entries using Azure OpenAI and show a summary page."""
    if not session.get('user'):
        return redirect(url_for('login'))
    selected = request.form.getlist('selected')
    # Persist the selection so Past can re-check them when user returns
    session['selected_ids'] = selected
    
    # Convert selected IDs to integers for comparison
    try:
        selected_ids = set(int(x) for x in selected)
    except (ValueError, TypeError):
        selected_ids = set()
    
    entries = load_entries()
    # Match entries by ID only
    chosen = [e for e in entries if e.get('id') in selected_ids]
    
    # Sort chosen by created_at desc and compute display_time like elsewhere
    chosen = sorted(chosen, key=lambda e: e['created_at'], reverse=True)
    for e in chosen:
        try:
            ts = datetime.fromisoformat(e['created_at'].replace('Z', ''))
            e['display_time'] = ts.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            e['display_time'] = e['created_at']

    # Combine selected entries' text
    texts = [(e.get('title') or '') + '. ' + (e.get('content') or '') for e in chosen]
    combined_text = '\n\n'.join(texts)
    
    # Get summary and insights from Azure OpenAI
    summary = get_summary(combined_text)
    insights_data = get_insights(combined_text)
    
    return render_template(
        'summary.html',
        summary=summary,
        sentiment=insights_data.get('sentiment', 'unknown'),
        insights=insights_data.get('insights', []),
        entries=chosen
    )


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    # If already logged in, redirect to index
    if session.get('user'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        # Basic validation
        if not email or not password:
            return render_template('login.html', error='Email and password required')
        
        if IS_DEPLOYED:
            # In deployed mode, check database
            user = db.session.query(User).filter_by(email=email.lower()).first()
            if user and user.check_password(password):
                session['user'] = {'email': user.email, 'name': user.name}
                return redirect(url_for('index'))
        else:
            # In local mode, only check TEST_USER
            if email == TEST_USER.get('email') and password == TEST_USER.get('password'):
                session['user'] = {'email': email, 'name': TEST_USER.get('name')}
                return redirect(url_for('index'))
        
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def register():
    # Registration only available in deployed mode
    if not IS_DEPLOYED:
        return redirect(url_for('login'))
    
    if session.get('user'):
        return redirect(url_for('index'))
    
    error = None
    success = None
    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        # Input validation
        if not email or not password:
            error = 'Email and password required'
        elif not validate_email(email):
            error = 'Invalid email format'
        elif db.session.query(User).filter_by(email=email).first():
            error = 'Account already exists'
        else:
            valid, err_msg = validate_password(password)
            if not valid:
                error = err_msg
            else:
                new_user = User(name=sanitize_name(name) or email.split('@')[0].title(), email=email)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                success = 'Account created. You can sign in.'
    
    return render_template('register.html', error=error, success=success)


@app.route('/forgot', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def forgot():
    # Password reset only available in deployed mode
    if not IS_DEPLOYED:
        return redirect(url_for('login'))
    
    if session.get('user'):
        return redirect(url_for('index'))
    
    error = None
    success = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        # Validate email format
        if not email or not validate_email(email):
            error = 'Please enter a valid email'
        else:
            user = db.session.query(User).filter_by(email=email).first()
            if user:
                # Create a reset token
                token = generate_reset_token()
                reset_token = ResetToken(user_id=user.id, token=token)
                db.session.add(reset_token)
                db.session.commit()
                # In production, you'd send this via email
                success = f'Password reset token: {token} (check your email in production)'
            else:
                error = 'Email not found'
    
    return render_template('forgot.html', error=error, success=success)


@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token):
    # Password reset only available in deployed mode
    if not IS_DEPLOYED:
        return redirect(url_for('login'))
    
    if session.get('user'):
        return redirect(url_for('index'))
    
    reset_token = db.session.query(ResetToken).filter_by(token=token).first()
    if not reset_token or not reset_token.is_valid():
        return render_template('reset.html', error='Invalid or expired token')
    
    error = None
    success = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if not password:
            error = 'Password required'
        else:
            user = reset_token.user
            user.set_password(password)
            db.session.delete(reset_token)
            db.session.commit()
            success = 'Password reset successful. You can now sign in.'
    
    return render_template('reset.html', error=error, success=success)


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('selected_ids', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
