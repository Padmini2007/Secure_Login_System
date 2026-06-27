# 🔐 SecureVault — Secure Login System

A production-ready secure authentication web application built with Python and Flask.

## 🌐 Live Demo
https://secure-login-system-2-l7h0.onrender.com

## Demo Video
https://drive.google.com/file/d/13SSDArBC0L7YPgdoiEhA7bRgCO0LDEy0/view?usp=drivesdk

## ✨ Features
- 🔒 Bcrypt Password Hashing — Passwords never stored in plain text
- 🛡 SQL Injection Protection — SQLAlchemy ORM with parameterised queries
- 🎫 Session Management — HttpOnly cookies with 30-minute auto expiry
- ✅ Input Validation — Regex-based validation on all form fields
- 🚦 Rate Limiting — Blocks brute force attacks (20 attempts/hour)
- 📱 Two-Factor Authentication — TOTP-based 2FA with Google Authenticator

## 🛠 Tech Stack
- Backend: Python, Flask
- Database: SQLite + SQLAlchemy ORM
- Auth: Flask-Bcrypt, PyOTP
- Security: Flask-Limiter, Markupsafe
- Frontend: HTML, CSS, Vanilla JS
- Hosting: Render

## 🚀 Quick Start

### 1. Clone the repository
git clone https://github.com/Padmini2007/Secure_Login_System.git
cd Secure_Login_System

### 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Run the app
python app.py

### 5. Open browser
http://127.0.0.1:5000

## 🛡 Security Overview
- Password Theft → Bcrypt hashing protects stored passwords
- SQL Injection → SQLAlchemy ORM blocks all injection attacks
- XSS Attack → Jinja2 auto-escaping on all inputs
- Brute Force → Rate limiter blocks after 20 attempts/hour
- Session Hijacking → HttpOnly + SameSite cookies
- Account Takeover → 2FA requires phone even if password stolen
- 

## 👩‍💻 Developed By
PADMINI J
