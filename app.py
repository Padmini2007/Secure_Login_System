import os
import re
import pyotp
import qrcode
import io
import base64
from datetime import timedelta
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.exc import IntegrityError
from markupsafe import escape

app = Flask(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(32))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# ── Model ─────────────────────────────────────────────────────────────────────
class User(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80),  unique=True, nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password     = db.Column(db.String(200), nullable=False)
    totp_secret  = db.Column(db.String(32),  nullable=True)
    two_fa_enabled = db.Column(db.Boolean, default=False)

# ── Helpers ───────────────────────────────────────────────────────────────────
USERNAME_RE = re.compile(r'^[A-Za-z0-9_]{3,30}$')
EMAIL_RE    = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

def validate_username(u):
    return bool(USERNAME_RE.match(u))

def validate_email(e):
    return bool(EMAIL_RE.match(e))

def validate_password(p):
    """Min 8 chars, 1 upper, 1 lower, 1 digit, 1 special."""
    return (
        len(p) >= 8 and
        re.search(r'[A-Z]', p) and
        re.search(r'[a-z]', p) and
        re.search(r'\d', p) and
        re.search(r'[!@#$%^&*(),.?":{}|<>]', p)
    )

def gen_qr_base64(uri):
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()

def logged_in():
    return 'user_id' in session and session.get('authenticated')

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if logged_in():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# ── Register ──────────────────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def register():
    if logged_in():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = escape(request.form.get('username', '').strip())
        email    = escape(request.form.get('email', '').strip())
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        errors = []
        if not validate_username(username):
            errors.append('Username must be 3–30 characters (letters, numbers, _).')
        if not validate_email(email):
            errors.append('Enter a valid email address.')
        if not validate_password(password):
            errors.append('Password needs 8+ chars, uppercase, lowercase, digit & special character.')
        if password != confirm:
            errors.append('Passwords do not match.')

        if errors:
            return render_template('register.html', errors=errors,
                                   username=username, email=email)

        pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=str(username), email=str(email), password=pw_hash)
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return render_template('register.html',
                                   errors=['Username or email already exists.'],
                                   username=username, email=email)

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# ── Login ─────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("20 per hour")
def login():
    if logged_in():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identifier = escape(request.form.get('identifier', '').strip())
        password   = request.form.get('password', '')

        user = User.query.filter(
            (User.username == str(identifier)) | (User.email == str(identifier))
        ).first()

        if user and bcrypt.check_password_hash(user.password, password):
            if user.two_fa_enabled:
                # Store temp state for 2FA step
                session['pre_2fa_user_id'] = user.id
                session['pre_2fa_username'] = user.username
                return redirect(url_for('verify_2fa'))
            # Full login
            session.permanent = True
            session['user_id']      = user.id
            session['username']     = user.username
            session['authenticated'] = True
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html',
                                   errors=['Invalid credentials. Please try again.'])

    return render_template('login.html')

# ── 2FA Verify ────────────────────────────────────────────────────────────────
@app.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    uid = session.get('pre_2fa_user_id')
    if not uid:
        return redirect(url_for('login'))

    if request.method == 'POST':
        code = request.form.get('totp_code', '').strip()
        user = User.query.get(uid)
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code, valid_window=1):
            session.permanent = True
            session['user_id']       = user.id
            session['username']      = user.username
            session['authenticated'] = True
            session.pop('pre_2fa_user_id', None)
            session.pop('pre_2fa_username', None)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            return render_template('verify_2fa.html',
                                   errors=['Invalid code. Please try again.'])

    return render_template('verify_2fa.html')

# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    if not logged_in():
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

# ── 2FA Setup ─────────────────────────────────────────────────────────────────
@app.route('/setup-2fa', methods=['GET', 'POST'])
def setup_2fa():
    if not logged_in():
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        code   = request.form.get('totp_code', '').strip()
        secret = session.get('totp_secret_temp')
        if not secret:
            flash('Session expired. Retry setup.', 'warning')
            return redirect(url_for('setup_2fa'))
        totp = pyotp.TOTP(secret)
        if totp.verify(code, valid_window=1):
            user.totp_secret   = secret
            user.two_fa_enabled = True
            db.session.commit()
            session.pop('totp_secret_temp', None)
            flash('Two-Factor Authentication enabled!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Code mismatch. Scan the QR again.', 'danger')

    secret = pyotp.random_base32()
    session['totp_secret_temp'] = secret
    uri    = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email, issuer_name='SecureVault'
    )
    qr_b64 = gen_qr_base64(uri)
    return render_template('setup_2fa.html', qr_b64=qr_b64, secret=secret)

# ── Disable 2FA ───────────────────────────────────────────────────────────────
@app.route('/disable-2fa', methods=['POST'])
def disable_2fa():
    if not logged_in():
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    user.two_fa_enabled = False
    user.totp_secret    = None
    db.session.commit()
    flash('Two-Factor Authentication disabled.', 'info')
    return redirect(url_for('dashboard'))

# ── Logout ────────────────────────────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('login'))

# ── Init DB & Run ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
