"""
SQLAlchemy ORM models for the Journal App.

Tables:
- User: user accounts with email/password or Google OAuth
- Entry: journal entries authored by users
- ResetToken: password reset tokens with expiry
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """
    User account model.
    Supports both email/password auth (with hashed password)
    and Google OAuth (with google_id).
    """
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # NULL for Google OAuth users
    google_id = db.Column(db.String(255), unique=True, nullable=True)  # Google OAuth ID
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    entries = db.relationship('Entry', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    reset_tokens = db.relationship('ResetToken', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class Entry(db.Model):
    """
    Journal entry model.
    Each entry belongs to a user.
    """
    __tablename__ = 'entries'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Entry {self.title[:30]}...>"


class ResetToken(db.Model):
    """
    Password reset token model.
    Tokens expire after 24 hours.
    """
    __tablename__ = 'reset_tokens'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc) + timedelta(hours=24))

    def is_valid(self):
        """Check if token has not expired."""
        return datetime.now(timezone.utc) < self.expires_at

    def __repr__(self):
        return f"<ResetToken {self.token[:10]}...>"
