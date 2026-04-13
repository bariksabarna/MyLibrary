# Copyright © Sabarna Barik 
# 
# This code is open-source for **educational and non-commercial purposes only**.
# 
# You may:
# - Read, study, and learn from this code.
# - Modify or experiment with it for personal learning.
# 
# You may NOT:
# - Claim this code as your own.
# - Use this code in commercial projects or for profit without written permission.
# - Distribute this code as your own work.
# 
# If you use or adapt this code, you **must give credit** to the original author: Sabarna Barik
# For commercial use or special permissions, contact: sabarnabarik@gmail.com
# 
# # Copyright © 2026 Sabarna Barik
# # Non-commercial use only. Credit required if used.
# 
# License:
# This project is open-source for learning only.
# Commercial use is prohibited.
# Credit is required if you use any part of this code.

import os, json, random, string, base64, io, re
from functools import wraps
from datetime import datetime, timedelta
import requests, qrcode, cloudinary, cloudinary.uploader
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from supabase import create_client, Client
from rapidfuzz import fuzz
from gmail_auth import send_gmail

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super_secret_library_key_123")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)
app.config['SESSION_PERMANENT'] = True

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("CRITICAL: Supabase credentials are missing! The application will not function.")
    supabase = None
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"CRITICAL: Failed to initialize Supabase: {e}")
        supabase = None
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", ""),
    api_key=os.getenv("CLOUDINARY_API_KEY", ""),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", ""),
    secure=True
)

MAX_BOOKS    = 3
FINE_PER_DAY = 5
BORROW_DAYS  = 30
APP_NAME     = "MyLibrary"

def upload_to_cloudinary(file_storage, folder="mylibrary", public_id=None):
    if not file_storage or not file_storage.filename:
        return None
    try:
        file_storage.stream.seek(0)
        file_bytes = file_storage.stream.read()
        if not file_bytes:
            print("Cloudinary: empty file")
            return None
        opts = {'folder': folder, 'resource_type': 'image', 'quality': 'auto:good', 'fetch_format': 'auto'}
        if public_id:
            opts['public_id'] = public_id
        result = cloudinary.uploader.upload(file_bytes, **opts)
        url = result.get('secure_url')
        print(f"Cloudinary upload success: {url}")
        return url
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return None

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    folder = request.form.get('folder', 'mylibrary/others')
    url = upload_to_cloudinary(file, folder=folder)
    
    if url:
        return jsonify({'url': url})
    return jsonify({'error': 'Upload failed'}), 500

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def generate_token(prefix='BORROW', length=8):
    return f"{prefix}-{''.join(random.choices(string.ascii_uppercase+string.digits, k=length))}"

def generate_qr_base64(data):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def send_email(to_email, subject, body):
    return send_gmail(to_email, subject, body)

def calculate_fine(due_date_str, return_date=None):
    if not due_date_str:
        return 0
    try:
        if isinstance(due_date_str, str):
            due = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
        else:
            due = due_date_str
        check = return_date if return_date else datetime.utcnow()
        if isinstance(check, str):
            check = datetime.fromisoformat(check.replace('Z', '+00:00')).replace(tzinfo=None)
        return max(0, (check - due).days * FINE_PER_DAY) if check > due else 0
    except:
        return 0

def get_user_borrow_count(user_id):
    try:
        r = supabase.table('borrows').select('id', count='exact').eq('user_id', user_id).in_('status', ['issued', 'approved_pending_issue', 'return_pending']).execute()
        return r.count or 0
    except:
        return 0

def fuzzy_search_books(query, books):
    if not query or not books:
        return books
    scored = []
    for b in books:
        s = max(
            fuzz.partial_ratio(query.lower(), (b.get('title') or '').lower()),
            fuzz.partial_ratio(query.lower(), (b.get('author') or '').lower()),
            fuzz.partial_ratio(query.lower(), (b.get('trade') or '').lower()),
            fuzz.partial_ratio(query.lower(), (b.get('semester') or '').lower()),
        )
        if s >= 40:
            scored.append((b, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [i[0] for i in scored]

def fmt_date(dt_str):
    if not dt_str:
        return ''
    try:
        dt = datetime.fromisoformat(str(dt_str).replace('Z', '+00:00')).replace(tzinfo=None)
        return dt.strftime('%d %b %Y')
    except:
        return str(dt_str)

app.jinja_env.globals['fmt_date']        = fmt_date
app.jinja_env.globals['calculate_fine'] = calculate_fine
app.jinja_env.globals['APP_NAME']       = APP_NAME

ES = f"""<div style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;background:linear-gradient(135deg,#0f172a,#1e293b);color:#e2e8f0;padding:30px;border-radius:16px;border:1px solid rgba(99,102,241,0.2);"><div style="text-align:center;margin-bottom:20px;"><h2 style="color:#6366f1;margin:0;">📚 {APP_NAME}</h2></div>"""
EC = "</div>"

def email_otp(otp, purpose='register'):
    t = 'Registration' if purpose == 'register' else 'Password Reset'
    return f"""{ES}<h3 style="text-align:center;">{t} OTP</h3><div style="background:rgba(99,102,241,0.1);border:1px solid #6366f1;padding:25px;border-radius:12px;text-align:center;margin:20px 0;"><p style="margin:0;color:#94a3b8;">Your OTP</p><h1 style="color:#6366f1;font-size:52px;letter-spacing:12px;margin:10px 0;">{otp}</h1><p style="margin:0;color:#64748b;font-size:13px;">Valid for 10 minutes</p></div>{EC}"""

def email_borrow_approved(name, title, token, due_date):
    return f"""{ES}<h3>Borrow Approved ✅</h3><p>Dear <strong>{name}</strong>,</p><p>Your request for <strong>"{title}"</strong> has been approved.</p><div style="background:rgba(99,102,241,0.1);border:1px solid #6366f1;padding:15px;border-radius:8px;margin:15px 0;"><p style="margin:5px 0;"><strong>Token:</strong> <span style="color:#6366f1;font-family:monospace;">{token}</span></p><p style="margin:5px 0;"><strong>Due Date:</strong> {due_date}</p></div><p style="color:#ef4444;">⚠️ Fine: ₹{FINE_PER_DAY}/day after {due_date}</p>{EC}"""

def email_return_success(name, title, fine):
    fn = f'<p style="color:#ef4444;"><strong>Fine: ₹{fine}</strong></p>' if fine > 0 else '<p style="color:#00d4aa;">✓ No fine</p>'
    return f"""{ES}<h3>Book Returned ✅</h3><p>Dear <strong>{name}</strong>,</p><p>You returned <strong>"{title}"</strong>.</p>{fn}<p>Thank you for using {APP_NAME}!</p>{EC}"""

def email_admin_approval(name):
    return f"""{ES}<h3>Account Approved 🎉</h3><p>Dear <strong>{name}</strong>,</p><p>Your {APP_NAME} account has been <strong style="color:#6366f1;">approved</strong>. You can now login and borrow books.</p>{EC}"""

def email_overdue(name, title, due_fmt, fine):
    return f"""{ES}<h3 style="color:#ef4444;">⚠️ Overdue Notice</h3><p>Dear <strong>{name}</strong>,</p><p><strong>"{title}"</strong> is overdue!</p><div style="background:rgba(239,68,68,0.1);border:1px solid #ef4444;padding:15px;border-radius:8px;margin:15px 0;"><p><strong>Due:</strong> {due_fmt}</p><p><strong>Fine:</strong> <span style="color:#ef4444;font-size:20px;font-weight:bold;">₹{fine}</span></p></div><p>Please return immediately. Fine: ₹{FINE_PER_DAY}/day.</p>{EC}"""

def email_reservation_ready(name, title, token):
    return f"""{ES}<h3>Book Available 📚</h3><p>Dear <strong>{name}</strong>,</p><p><strong>"{title}"</strong> is now available!</p><div style="background:rgba(99,102,241,0.1);border:1px solid #6366f1;padding:15px;border-radius:8px;margin:15px 0;"><p><strong>Token:</strong> <span style="color:#6366f1;font-family:monospace;">{token}</span></p></div><p>Visit within 3 days to collect.</p>{EC}"""

def login_required(f):
    @wraps(f)
    def d(*a, **k):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Session expired. Please log in again.'}), 401
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*a, **k)
    return d

def admin_required(f):
    @wraps(f)
    def d(*a, **k):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Session expired. Please log in again.'}), 401
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            if request.is_json:
                return jsonify({'error': 'Admin access required.'}), 403
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*a, **k)
    return d

def approved_required(f):
    @wraps(f)
    def d(*a, **k):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if not session.get('is_approved') and session.get('role') != 'admin':
            return redirect(url_for('pending'))
        return f(*a, **k)
    return d

@app.context_processor
def inject_globals():
    user = None
    if 'user_id' in session:
        try:
            r = supabase.table('users').select('*').eq('id', session['user_id']).execute()
            if r.data:
                user = r.data[0]
        except:
            pass
    return dict(current_user=user, max_books=MAX_BOOKS, fine_per_day=FINE_PER_DAY, app_name=APP_NAME)

# ═══ AUTH ROUTES ═══

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard') if session.get('role') == 'admin' else url_for('index'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name         = request.form.get('name', '').strip()
        email        = request.form.get('email', '').strip().lower()
        password     = request.form.get('password', '')
        confirm      = request.form.get('confirm_password', '')
        user_type    = request.form.get('user_type', '')
        year         = request.form.get('year', '')
        trade        = request.form.get('trade', '').strip()
        reg_number   = request.form.get('reg_number', '').strip()
        profile_image_url = request.form.get('profile_image_url', '').strip()
        errors = []
        if len(name) < 2:                                           errors.append('Name must be at least 2 characters.')
        if '@' not in email:                                        errors.append('Valid email required.')
        if len(password) < 8:                                       errors.append('Password: min 8 characters.')
        if not re.search(r'[A-Z]', password):                      errors.append('Password: need uppercase.')
        if not re.search(r'\d', password):                        errors.append('Password: need a number.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-]', password): errors.append('Password: need special char.')
        if password != confirm:                                     errors.append('Passwords do not match.')
        if user_type not in ['student', 'teacher']:                 errors.append('Select Student or Teacher.')
        if user_type == 'student' and not year:                     errors.append('Select your year.')
        if user_type == 'teacher' and not trade:                    errors.append('Enter your trade/subject.')
        if user_type == 'student' and not reg_number:               errors.append('Registration number required.')
        if not profile_image_url:                                   errors.append('Profile photo is required. Please upload a photo.')
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html', form_data=request.form)
        try:
            if supabase.table('users').select('id').eq('email', email).execute().data:
                flash('Email already registered.', 'danger')
                return render_template('register.html', form_data=request.form)
            # profile_image_url already set from hidden form field (browser uploaded directly)
            otp     = generate_otp()
            expires = (datetime.utcnow() + timedelta(minutes=10)).isoformat() + 'Z'
            supabase.table('otp_store').delete().eq('email', email).eq('purpose', 'register').execute()
            supabase.table('otp_store').insert({'email': email, 'otp': otp, 'purpose': 'register', 'expires_at': expires}).execute()
            session['reg_data'] = {
                'name': name, 'email': email,
                'password_hash': generate_password_hash(password),
                'user_type': user_type,
                'year': year if user_type == 'student' else None,
                'trade': trade if user_type == 'teacher' else None,
                'reg_number': reg_number if user_type == 'student' else None,
                'profile_image_url': profile_image_url
            }
            send_email(email, f'{APP_NAME} — OTP Verification', email_otp(otp, 'register'))
            flash(f'OTP sent to {email}.', 'success')
            return redirect(url_for('verify_otp', email=email, purpose='register'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
    return render_template('register.html', form_data={})

@app.route('/verify-otp/<email>/<purpose>', methods=['GET', 'POST'])
def verify_otp(email, purpose):
    if request.method == 'POST':
        entered = request.form.get('otp', '').strip()
        try:
            rec_r = supabase.table('otp_store').select('*').eq('email', email).eq('purpose', purpose).order('created_at', desc=True).limit(1).execute()
            if not rec_r.data:
                flash('OTP not found.', 'danger')
                return render_template('verify_otp.html', email=email, purpose=purpose)
            rec = rec_r.data[0]
            exp = datetime.fromisoformat(rec['expires_at'].replace('Z', '+00:00')).replace(tzinfo=None)
            if datetime.utcnow() > exp:
                supabase.table('otp_store').delete().eq('id', rec['id']).execute()
                flash('OTP expired.', 'danger')
                return redirect(url_for('register') if purpose == 'register' else url_for('forgot_password'))
            if rec['otp'] != entered:
                flash('Invalid OTP.', 'danger')
                return render_template('verify_otp.html', email=email, purpose=purpose)
            supabase.table('otp_store').delete().eq('id', rec['id']).execute()
            if purpose == 'register':
                rd = session.get('reg_data')
                if not rd:
                    flash('Session expired.', 'danger')
                    return redirect(url_for('register'))
                supabase.table('users').insert({
                    'name': rd['name'], 'email': rd['email'], 'password_hash': rd['password_hash'],
                    'role': 'user', 'user_type': rd['user_type'], 'year': rd.get('year'),
                    'trade': rd.get('trade'), 'reg_number': rd.get('reg_number'),
                    'profile_image_url': rd.get('profile_image_url'),
                    'is_verified': True, 'is_approved': False, 'is_active': True
                }).execute()
                session.pop('reg_data', None)
                flash('Registration successful! Awaiting admin approval.', 'success')
                return redirect(url_for('login'))
            elif purpose == 'forgot_password':
                session['reset_email'] = email
                session['reset_verified'] = True
                return redirect(url_for('reset_password'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
    return render_template('verify_otp.html', email=email, purpose=purpose)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        try:
            r = supabase.table('users').select('*').eq('email', email).execute()
            if not r.data or not check_password_hash(r.data[0]['password_hash'], password):
                flash('Invalid email or password.', 'danger')
                return render_template('login.html')
            u = r.data[0]
            if not u.get('is_verified'):
                flash('Please verify your email first.', 'warning')
                return render_template('login.html')
            if not u.get('is_approved') and u.get('role') != 'admin':
                flash('Account pending admin approval.', 'warning')
                return render_template('login.html')
            if not u.get('is_active', True):
                flash('Account deactivated.', 'danger')
                return render_template('login.html')
            session.permanent = True
            session.update({'user_id': u['id'], 'name': u['name'], 'email': u['email'], 'role': u['role'], 'is_approved': u.get('is_approved', False)})
            flash(f'Welcome back, {u["name"]}! 👋', 'success')
            return redirect(url_for('admin_dashboard') if u['role'] == 'admin' else url_for('index'))
        except Exception as e:
            flash(f'Login error: {e}', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        try:
            otp = generate_otp()
            exp = (datetime.utcnow() + timedelta(minutes=10)).isoformat() + 'Z'
            supabase.table('otp_store').delete().eq('email', email).eq('purpose', 'forgot_password').execute()
            supabase.table('otp_store').insert({'email': email, 'otp': otp, 'purpose': 'forgot_password', 'expires_at': exp}).execute()
            if supabase.table('users').select('id').eq('email', email).execute().data:
                send_email(email, f'{APP_NAME} — Password Reset OTP', email_otp(otp, 'forgot_password'))
            flash('If that email exists, an OTP has been sent.', 'info')
            return redirect(url_for('verify_otp', email=email, purpose='forgot_password'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('reset_verified') or not session.get('reset_email'):
        flash('Invalid reset session.', 'danger')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        pw = request.form.get('password', '')
        cf = request.form.get('confirm_password', '')
        errs = []
        if len(pw) < 8:                                          errs.append('Min 8 chars.')
        if not re.search(r'[A-Z]', pw):                        errs.append('Need uppercase.')
        if not re.search(r'\d', pw):                          errs.append('Need number.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-]', pw):  errs.append('Need special char.')
        if pw != cf:                                            errs.append('Passwords do not match.')
        if errs:
            for e in errs:
                flash(e, 'danger')
            return render_template('reset_password.html')
        supabase.table('users').update({'password_hash': generate_password_hash(pw)}).eq('email', session['reset_email']).execute()
        session.pop('reset_email', None)
        session.pop('reset_verified', None)
        flash('Password reset! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html')

@app.route('/pending')
@login_required
def pending():
    return render_template('pending.html')

# ═══ USER ROUTES ═══

@app.route('/dashboard')
@login_required
@approved_required
def index():
    uid = session['user_id']
    try:
        ab_r = supabase.table('borrows').select('*').eq('user_id', uid).in_('status', ['issued', 'approved_pending_issue', 'return_pending']).execute()
        active = ab_r.data or []
        overdue_count = sum(1 for b in active if b.get('status') == 'issued' and calculate_fine(b.get('due_date')) > 0)
        for b in active:
            bk = supabase.table('books').select('title', 'author', 'cover_url').eq('id', b['book_id']).execute()
            b['book'] = bk.data[0] if bk.data else {}
        recent = supabase.table('books').select('*').order('created_at', desc=True).limit(8).execute().data or []
        return render_template('index.html', active_borrows=active, recent_books=recent, overdue_count=overdue_count, borrow_count=len(active))
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('index.html', active_borrows=[], recent_books=[], overdue_count=0, borrow_count=0)

@app.route('/books')
@login_required
@approved_required
def books():
    page = max(1, int(request.args.get('page', 1)))
    per_page = 12
    offset = (page - 1) * per_page
    search = request.args.get('q', '').strip()
    trade_f = request.args.get('trade', '')
    semester = request.args.get('semester', '')
    try:
        if search:
            all_r = supabase.table('books').select('*').execute().data or []
            if trade_f: all_r = [b for b in all_r if trade_f.lower() in (b.get('trade') or '').lower()]
            if semester: all_r = [b for b in all_r if b.get('semester') == semester]
            filtered = fuzzy_search_books(search, all_r)
            total = len(filtered)
            books_data = filtered[offset:offset + per_page]
        else:
            q = supabase.table('books').select('*', count='exact')
            if trade_f: q = q.ilike('trade', f'%{trade_f}%')
            if semester: q = q.eq('semester', semester)
            r = q.order('title').range(offset, offset + per_page - 1).execute()
            books_data = r.data or []
            total = r.count or 0
        total_pages = max(1, (total + per_page - 1) // per_page)
        return render_template('books.html', books=books_data, page=page, total_pages=total_pages, total=total, search=search, trade=trade_f, semester=semester, per_page=per_page)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('books.html', books=[], page=1, total_pages=1, total=0, search=search, trade='', semester='', per_page=per_page)

@app.route('/book/<book_id>')
@login_required
@approved_required
def book_detail(book_id):
    try:
        r = supabase.table('books').select('*').eq('id', book_id).execute()
        if not r.data:
            flash('Book not found.', 'danger')
            return redirect(url_for('books'))
        book = r.data[0]
        uid = session['user_id']
        existing = supabase.table('borrows').select('id').eq('user_id', uid).eq('book_id', book_id).in_('status', ['issued', 'approved_pending_issue', 'return_pending']).execute()
        in_queue = supabase.table('reservations').select('id').eq('user_id', uid).eq('book_id', book_id).eq('status', 'waiting').execute()
        return render_template('book_detail.html', book=book, already_borrowed=bool(existing.data), in_queue=bool(in_queue.data), borrow_count=get_user_borrow_count(uid))
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('books'))

@app.route('/borrow/<book_id>', methods=['POST'])
@login_required
@approved_required
def borrow_book(book_id):
    uid = session['user_id']
    try:
        if get_user_borrow_count(uid) >= MAX_BOOKS:
            flash(f'Max borrow limit ({MAX_BOOKS}) reached.', 'danger')
            return redirect(url_for('book_detail', book_id=book_id))
        bk = supabase.table('books').select('*').eq('id', book_id).execute()
        if not bk.data:
            flash('Book not found.', 'danger')
            return redirect(url_for('books'))
        book = bk.data[0]
        if supabase.table('borrows').select('id').eq('user_id', uid).eq('book_id', book_id).in_('status', ['issued', 'approved_pending_issue', 'return_pending']).execute().data:
            flash('Already borrowed or requested.', 'warning')
            return redirect(url_for('book_detail', book_id=book_id))
        if book['available_quantity'] <= 0:
            if supabase.table('reservations').select('id').eq('user_id', uid).eq('book_id', book_id).eq('status', 'waiting').execute().data:
                flash('Already in queue.', 'info')
            else:
                pos = (supabase.table('reservations').select('id', count='exact').eq('book_id', book_id).eq('status', 'waiting').execute().count or 0) + 1
                supabase.table('reservations').insert({'user_id': uid, 'book_id': book_id, 'position': pos, 'status': 'waiting'}).execute()
                flash(f'Added to queue at position {pos}.', 'info')
            return redirect(url_for('book_detail', book_id=book_id))
        token = generate_token('BORROW')
        br = supabase.table('borrows').insert({'user_id': uid, 'book_id': book_id, 'token': token, 'status': 'approved_pending_issue', 'created_at': datetime.utcnow().isoformat() + 'Z'}).execute()
        borrow_id = br.data[0]['id']
        supabase.table('books').update({
            'available_quantity': max(0, book['available_quantity'] - 1)
        }).eq('id', book_id).execute()
        ur = supabase.table('users').select('name', 'email').eq('id', uid).execute().data[0]
        due = (datetime.utcnow() + timedelta(days=BORROW_DAYS)).strftime('%d %B %Y')
        send_email(ur['email'], f'Borrow Approved: {book["title"]}', email_borrow_approved(ur['name'], book['title'], token, due))
        flash('Borrow approved! Show QR at the library counter.', 'success')
        return redirect(url_for('borrow_qr', borrow_id=borrow_id))
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('book_detail', book_id=book_id))

@app.route('/borrow-qr/<borrow_id>')
@login_required
def borrow_qr(borrow_id):
    try:
        r = supabase.table('borrows').select('*').eq('id', borrow_id).eq('user_id', session['user_id']).execute()
        if not r.data:
            flash('Not found.', 'danger')
            return redirect(url_for('my_borrows'))
        b = r.data[0]
        bk = supabase.table('books').select('title', 'author', 'cover_url').eq('id', b['book_id']).execute()
        qr_url = request.host_url.rstrip('/') + url_for('admin_process_token', token=b['token'])
        return render_template('borrow_qr.html', borrow=b, book=bk.data[0] if bk.data else {}, qr_data=generate_qr_base64(qr_url))
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('my_borrows'))

@app.route('/my-borrows')
@login_required
@approved_required
def my_borrows():
    uid = session['user_id']
    try:
        br = supabase.table('borrows').select('*').eq('user_id', uid).order('created_at', desc=True).execute()
        borrows = []
        for b in (br.data or []):
            bk = supabase.table('books').select('title', 'author', 'cover_url').eq('id', b['book_id']).execute()
            b['book'] = bk.data[0] if bk.data else {}
            b['current_fine'] = calculate_fine(b.get('due_date')) if b.get('status') == 'issued' else (b.get('fine') or 0)
            borrows.append(b)
        qr = supabase.table('reservations').select('*').eq('user_id', uid).eq('status', 'waiting').execute()
        queues = []
        for q in (qr.data or []):
            bk = supabase.table('books').select('title', 'author', 'cover_url').eq('id', q['book_id']).execute()
            q['book'] = bk.data[0] if bk.data else {}
            queues.append(q)
        return render_template('my_borrows.html', borrows=borrows, queue_items=queues)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('my_borrows.html', borrows=[], queue_items=[])

@app.route('/return-request/<borrow_id>', methods=['POST'])
@login_required
def return_request(borrow_id):
    try:
        r = supabase.table('borrows').select('*').eq('id', borrow_id).eq('user_id', session['user_id']).execute()
        if not r.data or r.data[0]['status'] != 'issued':
            flash('Cannot process return.', 'warning')
            return redirect(url_for('my_borrows'))
        rt = generate_token('RETURN')
        supabase.table('borrows').update({'status': 'return_pending', 'return_token': rt}).eq('id', borrow_id).execute()
        return redirect(url_for('return_qr', borrow_id=borrow_id))
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('my_borrows'))

@app.route('/return-qr/<borrow_id>')
@login_required
def return_qr(borrow_id):
    try:
        r = supabase.table('borrows').select('*').eq('id', borrow_id).eq('user_id', session['user_id']).execute()
        if not r.data:
            flash('Not found.', 'danger')
            return redirect(url_for('my_borrows'))
        b = r.data[0]
        bk = supabase.table('books').select('title', 'author', 'cover_url').eq('id', b['book_id']).execute()
        qr_url = request.host_url.rstrip('/') + url_for('admin_process_token', token=b.get('return_token', ''))
        return render_template('return_qr.html', borrow=b, book=bk.data[0] if bk.data else {}, qr_data=generate_qr_base64(qr_url), current_fine=calculate_fine(b.get('due_date')))
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('my_borrows'))

@app.route('/library-card')
@login_required
@approved_required
def library_card():
    uid = session['user_id']
    try:
        ur = supabase.table('users').select('*').eq('id', uid).execute()
        if not ur.data:
            return redirect(url_for('login'))
        user = ur.data[0]
        br = supabase.table('borrows').select('*').eq('user_id', uid).in_('status', ['issued', 'approved_pending_issue', 'return_pending']).execute()
        qr_data = supabase.table('reservations').select('*').eq('user_id', uid).eq('status', 'waiting').execute()
        card_qr_url = request.host_url.rstrip('/') + url_for('admin_process_token', token=f'LIBCARD-{uid}')
        card_qr = generate_qr_base64(card_qr_url)
        enriched = []
        for b in (br.data or []):
            bk = supabase.table('books').select('title', 'author').eq('id', b['book_id']).execute()
            b['book'] = bk.data[0] if bk.data else {}
            enriched.append(b)
        return render_template('library_card.html', user=user, borrows=enriched, queues=qr_data.data or [], card_qr=card_qr)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('index'))

@app.route('/helpdesk')
@login_required
@approved_required
def helpdesk():
    return render_template('helpdesk.html')

@app.route('/api/helpdesk', methods=['POST'])
@login_required
def helpdesk_api():
    data    = request.json or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'Empty'}), 400
    msg = message.lower()
    responses = [
        (['hello','hi','hey','hii','helo','namaste','good morning','good afternoon','good evening'], f"Hello! Welcome to {APP_NAME} helpdesk.\n\nI can help you with:\n• How to borrow or return books\n• Fine and due date queries\n• Queue and reservation system\n• Registration and account help\n• Library rules and timings\n• Searching for books\n\nWhat do you need help with?"),
        (['how to borrow','borrow a book','borrow kaise','how do i borrow','borrow book','want to borrow','kitab kaise lu'], f"To borrow a book:\n1. Go to the Books page\n2. Click on any book\n3. Click Borrow Now\n4. A QR code and token is generated\n5. Go to the library counter\n6. Show your QR code to the librarian\n7. They scan it and hand you the book\n\nYou can borrow up to {MAX_BOOKS} books at a time."),
        (['borrow limit','how many books','maximum books','max books','kitne books','kitni kitabein'], f"You can borrow a maximum of {MAX_BOOKS} books at one time.\n\nYou must return at least one book before borrowing more once you reach the limit.\n\nCheck your current count in My Borrows."),
        (['how to return','return a book','return kaise','book return','return krna','want to return','kitab wapas'], "To return a book:\n1. Go to My Borrows from the menu\n2. Find the issued book\n3. Click the Return button\n4. A Return QR code is generated\n5. Go to the library counter\n6. Show the Return QR to the librarian\n7. They scan it and confirm the return\n\nYour fine (if any) will be shown before you return."),
        (['fine','penalty','late return','overdue','kitna fine','late fee','how much fine','fine kitna','jukrmana'], f"Fine Policy:\n• Loan period: {BORROW_DAYS} days from issue date\n• Fine: Rs.{FINE_PER_DAY} per day after the due date\n• Fine is calculated automatically\n• Check your fine in My Borrows\n• Pay fine at the library counter when returning"),
        (['due date','when to return','return date','return by','last date','kab return','due kab hai'], f"Your due date is {BORROW_DAYS} days from when the librarian issued the book.\n\nSee your exact due date in:\n• My Borrows page\n• The email sent when book was issued\n• Your Borrow QR page\n\nFine of Rs.{FINE_PER_DAY}/day applies after the due date."),
        (['qr code','qr','token','show qr','borrow qr','collect book','where is qr','qr kahan hai'], "Your QR code is in My Borrows.\n\nSteps:\n1. Click My Borrows in the menu\n2. Find your book with status Collect at Counter\n3. Click QR Code button\n4. Show this QR to the librarian\n\nThe librarian scans it with their phone camera and it opens the system automatically."),
        (['queue','waiting list','waitlist','not available','unavailable','join queue','in queue','queue mein'], "Queue System:\n\nIf a book has 0 copies available:\n1. Click Join Queue on the book page\n2. You are added to the waiting list\n3. Your position is shown immediately\n4. When another student returns the book, you get an email\n5. A new QR code is generated for you\n6. Visit the counter within 3 days to collect\n\nQueue works on first-come first-served basis."),
        (['library card','my card','id card','digital card','identity','card kahan hai'], "Your Digital Library Card is in the My Card menu.\n\nIt shows:\n• Your name and photo\n• Your role (Student or Teacher)\n• Your year and trade\n• Currently borrowed books\n• A QR code for counter verification\n\nThe librarian can scan your card QR with their phone to look up your profile."),
        (['register','sign up','registration','create account','new account','kaise register'], "Registration Steps:\n1. Go to the Register page\n2. Select Student or Teacher\n3. Fill in your details and upload a profile photo (required)\n4. Set a strong password\n5. Submit the form\n6. Check your email for the OTP\n7. Enter the OTP to verify your email\n8. Wait for admin approval\n9. You will receive an approval email\n10. Login and start borrowing!"),
        (['otp','one time password','verification code','otp nahi aaya','resend otp','otp not received'], "OTP is a 6-digit code sent to your email.\n\nIf you did not receive it:\n• Check your spam/junk folder\n• Make sure you entered the correct email\n• OTP expires in 10 minutes\n• Go back and try again to get a new OTP\n\nContact the librarian if it still does not work."),
        (['pending','approval','not approved','waiting for approval','account pending','admin approval','approved nahi'], "Your account is pending admin approval.\n\nThis is normal — every new account is reviewed by the librarian.\n\nWhat to do:\n• Wait for the approval email\n• Check your inbox and spam folder\n• If it has been more than 24 hours, visit the library counter"),
        (['forgot password','reset password','change password','password bhool gaya','lost password','password nahi pata'], "To reset your password:\n1. Go to the Login page\n2. Click Forgot Password\n3. Enter your registered email\n4. Check your email for the OTP\n5. Enter the OTP\n6. Set your new password\n\nPassword must have: 8+ chars, uppercase, number, special character."),
        (['search','find book','how to search','search kaise','book dhundna','look for book'], "To search for a book:\n1. Go to the Books page\n2. Type in the search bar (title, author, or trade)\n3. Search works even with spelling mistakes\n4. Use the Trade filter for your branch\n5. Use the Semester filter\n6. Click the microphone for voice search"),
        (['semester','trade','branch','cse','ece','mechanical','electrical','civil','electronics','computer science'], "Books are organized by Trade and Semester.\n\nTo find books for your branch:\n1. Go to the Books page\n2. Type your trade name (e.g. Computer Science)\n3. OR use the Trade filter dropdown\n4. Combine with Semester filter\n\nWorks for: CSE, ECE, Mechanical, Electrical, Civil, Electronics etc."),
        (['rules','policy','niyam','library policy','guidelines','regulations'], f"Library Rules:\n\n• Maximum {MAX_BOOKS} books at one time\n• Loan period: {BORROW_DAYS} days\n• Fine: Rs.{FINE_PER_DAY} per day for overdue books\n• Email OTP verification required\n• Admin approval required before first login\n• Profile photo required at registration\n• Books must be returned in good condition\n• Lost books must be reported immediately"),
        (['hours','timing','time','open','close','kab khulta','library time','working hours','library band'], "Library Hours:\n\nMonday to Saturday: 9:00 AM to 5:00 PM\nSunday: Closed\nPublic Holidays: Closed\n\nArrive before 4:30 PM for counter transactions."),
        (['contact','librarian','support','who to contact','kahan milenge'], "To contact the librarian:\n\n• Visit the library counter\n• Hours: Monday to Saturday, 9 AM to 5 PM\n\nFor account issues like password or registration, use the Forgot Password option on the login page."),
        (['book not issued','scan not working','counter problem','qr not scanning'], "If the QR is not scanning:\n\n1. Show the token code (BORROW-XXXXXXXX) instead\n2. The librarian can enter it manually in the admin panel\n3. Increase your screen brightness\n4. If the problem continues, ask the librarian to check directly"),
        (['book damaged','lost book','damaged book','book lost','kitab kho gayi'], "If a book is damaged or lost:\n\n• Report to the librarian immediately at the counter\n• Do NOT try to return it through the app without informing\n• Replacement cost will be decided by the librarian"),
        (['thank','thanks','thank you','shukriya','dhanyavad','tysm'], f"You are welcome!\n\nHappy to help. Visit {APP_NAME} anytime you need help. Happy reading!"),
        (['bye','goodbye','ok bye','that is all','nothing else','alvida'], f"Goodbye!\n\nHave a great day. Come back anytime you need help. Happy reading!"),
    ]
    for keywords, reply in responses:
        if any(k in msg for k in keywords):
            return jsonify({'response': reply, 'type': 'smart'})
    return jsonify({'response': f"I am the {APP_NAME} assistant. I can help you with:\n\n• Borrowing and returning books\n• Fines and due dates\n• Queue and reservation\n• Registration and account approval\n• Library rules and hours\n• Searching and finding books\n• Library card and QR codes\n\nType your question in simple words, or visit the library counter for direct help.", 'type': 'fallback'})

@app.route('/api/search-suggestions')
@login_required
def search_suggestions():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    try:
        all_r = supabase.table('books').select('title', 'author', 'trade').execute().data or []
        results = fuzzy_search_books(q, all_r)[:6]
        return jsonify([{'title': b.get('title', ''), 'author': b.get('author', ''), 'trade': b.get('trade', '')} for b in results])
    except:
        return jsonify([])

# ═══ ADMIN ROUTES ═══

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        total_users       = supabase.table('users').select('id', count='exact').eq('role', 'user').execute().count or 0
        total_books       = supabase.table('books').select('id', count='exact').execute().count or 0
        active_borrows    = supabase.table('borrows').select('id', count='exact').eq('status', 'issued').execute().count or 0
        pending_approvals = supabase.table('users').select('id', count='exact').eq('is_approved', False).eq('is_verified', True).execute().count or 0
        pending_issues    = supabase.table('borrows').select('id', count='exact').eq('status', 'approved_pending_issue').execute().count or 0
        pending_returns   = supabase.table('borrows').select('id', count='exact').eq('status', 'return_pending').execute().count or 0
        recent_br = supabase.table('borrows').select('*').order('created_at', desc=True).limit(6).execute()
        recent_borrows = []
        for b in (recent_br.data or []):
            ur = supabase.table('users').select('name', 'email').eq('id', b['user_id']).execute()
            bk = supabase.table('books').select('title').eq('id', b['book_id']).execute()
            b['user'] = ur.data[0] if ur.data else {}
            b['book'] = bk.data[0] if bk.data else {}
            b['current_fine'] = calculate_fine(b.get('due_date')) if b.get('status') == 'issued' else (b.get('fine') or 0)
            recent_borrows.append(b)
        pending_users = supabase.table('users').select('*').eq('is_approved', False).eq('is_verified', True).order('created_at', desc=True).limit(5).execute().data or []
        overdue_r = supabase.table('borrows').select('*').eq('status', 'issued').execute()
        overdue_items = []
        for b in (overdue_r.data or []):
            fine = calculate_fine(b.get('due_date'))
            if fine > 0:
                ur = supabase.table('users').select('name', 'email').eq('id', b['user_id']).execute()
                bk = supabase.table('books').select('title').eq('id', b['book_id']).execute()
                b['user'] = ur.data[0] if ur.data else {}
                b['book'] = bk.data[0] if bk.data else {}
                b['fine'] = fine
                overdue_items.append(b)
        return render_template('admin/dashboard.html', total_users=total_users, total_books=total_books, active_borrows=active_borrows, pending_approvals=pending_approvals, pending_issues=pending_issues, pending_returns=pending_returns, recent_borrows=recent_borrows, pending_users=pending_users, overdue_items=overdue_items[:5])
    except Exception as e:
        flash(f'Dashboard error: {e}', 'danger')
        return render_template('admin/dashboard.html', total_users=0, total_books=0, active_borrows=0, pending_approvals=0, pending_issues=0, pending_returns=0, recent_borrows=[], pending_users=[], overdue_items=[])

@app.route('/admin/users')
@admin_required
def admin_users():
    user_type = request.args.get('user_type', '')
    year      = request.args.get('year', '')
    trade_f   = request.args.get('trade', '')
    search    = request.args.get('q', '')
    status    = request.args.get('status', '')
    try:
        q = supabase.table('users').select('*').eq('role', 'user')
        if user_type: q = q.eq('user_type', user_type)
        if year: q = q.eq('year', year)
        users = q.order('created_at', desc=True).execute().data or []
        if search:
            sl = search.lower()
            users = [u for u in users if sl in u.get('name','').lower() or sl in u.get('email','').lower() or sl in (u.get('reg_number') or '').lower()]
        if trade_f: users = [u for u in users if trade_f.lower() in (u.get('trade') or '').lower()]
        if status == 'pending':    users = [u for u in users if not u.get('is_approved') and u.get('is_verified')]
        elif status == 'approved': users = [u for u in users if u.get('is_approved')]
        elif status == 'defaulters':
            all_br = supabase.table('borrows').select('user_id', 'due_date').eq('status', 'issued').execute().data or []
            d_ids  = set(b['user_id'] for b in all_br if calculate_fine(b.get('due_date')) > 0)
            users  = [u for u in users if u['id'] in d_ids]
        for u in users:
            cr = supabase.table('borrows').select('id', count='exact').eq('user_id', u['id']).in_('status', ['issued', 'approved_pending_issue', 'return_pending']).execute()
            u['borrow_count'] = cr.count or 0
        return render_template('admin/users.html', users=users, filters={'user_type': user_type, 'year': year, 'trade': trade_f, 'search': search, 'status': status})
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('admin/users.html', users=[], filters={})

@app.route('/admin/approve/<user_id>', methods=['POST'])
@admin_required
def admin_approve_user(user_id):
    try:
        r = supabase.table('users').select('name', 'email').eq('id', user_id).execute()
        if not r.data:
            flash('User not found.', 'danger')
            return redirect(url_for('admin_users'))
        u = r.data[0]
        supabase.table('users').update({'is_approved': True}).eq('id', user_id).execute()
        send_email(u['email'], f'{APP_NAME} — Account Approved!', email_admin_approval(u['name']))
        flash(f'{u["name"]} approved.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(request.referrer or url_for('admin_users'))

@app.route('/admin/reject/<user_id>', methods=['POST'])
@admin_required
def admin_reject_user(user_id):
    try:
        supabase.table('users').update({'is_active': False}).eq('id', user_id).execute()
        flash('User rejected.', 'info')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('admin_users'))

@app.route('/admin/user-detail/<user_id>')
@admin_required
def admin_user_detail(user_id):
    try:
        ur = supabase.table('users').select('*').eq('id', user_id).execute()
        if not ur.data:
            flash('User not found.', 'danger')
            return redirect(url_for('admin_users'))
        user = ur.data[0]
        br = supabase.table('borrows').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        borrows = []
        for b in (br.data or []):
            bk = supabase.table('books').select('title', 'author').eq('id', b['book_id']).execute()
            b['book'] = bk.data[0] if bk.data else {}
            b['current_fine'] = calculate_fine(b.get('due_date')) if b.get('status') == 'issued' else (b.get('fine') or 0)
            borrows.append(b)
        return render_template('admin/user_detail.html', user=user, borrows=borrows, card_qr=generate_qr_base64(f"LIBCARD-{user_id}"))
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('admin_users'))

@app.route('/admin/books')
@admin_required
def admin_books():
    search   = request.args.get('q', '').strip()
    page     = max(1, int(request.args.get('page', 1)))
    per_page = 15
    offset   = (page - 1) * per_page
    try:
        if search:
            all_r = supabase.table('books').select('*').execute().data or []
            filtered = fuzzy_search_books(search, all_r)
            total = len(filtered)
            books_data = filtered[offset:offset + per_page]
        else:
            r = supabase.table('books').select('*', count='exact').order('title').range(offset, offset + per_page - 1).execute()
            books_data = r.data or []
            total = r.count or 0
        return render_template('admin/books.html', books=books_data, page=page, total_pages=max(1, (total + per_page - 1) // per_page), total=total, search=search)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('admin/books.html', books=[], page=1, total_pages=1, total=0, search=search)

@app.route('/admin/add-book', methods=['GET', 'POST'])
@admin_required
def admin_add_book():
    if request.method == 'POST':
        try:
            qty = max(1, int(request.form.get('total_quantity', 1)))
            cover_file = request.files.get('cover_image')
            cover_url  = None
            if cover_file and cover_file.filename:
                cover_url = upload_to_cloudinary(cover_file, folder='mylibrary/books')
            data = {
                'title': request.form.get('title', '').strip(),
                'author': request.form.get('author', '').strip(),
                'description': request.form.get('description', '').strip(),
                'cover_url': cover_url,
                'trade': request.form.get('trade', '').strip(),
                'semester': request.form.get('semester', '').strip(),
                'total_quantity': qty,
                'available_quantity': qty
            }
            if not data['title']:
                flash('Book title is required.', 'danger')
                return render_template('admin/add_book.html', form_data=request.form)
            supabase.table('books').insert(data).execute()
            flash('Book added successfully!', 'success')
            return redirect(url_for('admin_books'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
    return render_template('admin/add_book.html', form_data={})

@app.route('/admin/edit-book/<book_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_book(book_id):
    try:
        br = supabase.table('books').select('*').eq('id', book_id).execute()
        if not br.data:
            flash('Book not found.', 'danger')
            return redirect(url_for('admin_books'))
        book = br.data[0]
        if request.method == 'POST':
            new_qty   = max(0, int(request.form.get('total_quantity', book['total_quantity'])))
            qty_diff  = new_qty - book['total_quantity']
            new_avail = max(0, book['available_quantity'] + qty_diff)
            cover_file = request.files.get('cover_image')
            cover_url  = book.get('cover_url')
            if cover_file and cover_file.filename:
                new_url = upload_to_cloudinary(cover_file, folder='mylibrary/books')
                if new_url:
                    cover_url = new_url
            data = {
                'title': request.form.get('title', '').strip(),
                'author': request.form.get('author', '').strip(),
                'description': request.form.get('description', '').strip(),
                'cover_url': cover_url,
                'trade': request.form.get('trade', '').strip(),
                'semester': request.form.get('semester', '').strip(),
                'total_quantity': new_qty,
                'available_quantity': new_avail
            }
            supabase.table('books').update(data).eq('id', book_id).execute()
            flash('Book updated!', 'success')
            return redirect(url_for('admin_books'))
        return render_template('admin/edit_book.html', book=book)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('admin_books'))

@app.route('/admin/delete-book/<book_id>', methods=['POST'])
@admin_required
def admin_delete_book(book_id):
    try:
        if (supabase.table('borrows').select('id', count='exact').eq('book_id', book_id).in_('status', ['issued', 'approved_pending_issue', 'return_pending']).execute().count or 0) > 0:
            flash('Cannot delete book with active borrows.', 'danger')
            return redirect(url_for('admin_books'))
        supabase.table('reservations').delete().eq('book_id', book_id).execute()
        supabase.table('borrows').delete().eq('book_id', book_id).execute()
        supabase.table('books').delete().eq('id', book_id).execute()
        flash('Book deleted.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('admin_books'))

@app.route('/admin/borrows')
@admin_required
def admin_borrows():
    status_f = request.args.get('status', '')
    try:
        q = supabase.table('borrows').select('*').order('created_at', desc=True)
        if status_f: q = q.eq('status', status_f)
        result = q.execute()
        borrows = []
        for b in (result.data or []):
            ur = supabase.table('users').select('name', 'email', 'reg_number', 'year', 'trade', 'user_type').eq('id', b['user_id']).execute()
            bk = supabase.table('books').select('title', 'author').eq('id', b['book_id']).execute()
            b['user'] = ur.data[0] if ur.data else {}
            b['book'] = bk.data[0] if bk.data else {}
            b['current_fine'] = calculate_fine(b.get('due_date')) if b.get('status') == 'issued' else (b.get('fine') or 0)
            borrows.append(b)
        return render_template('admin/borrows.html', borrows=borrows, status_filter=status_f)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('admin/borrows.html', borrows=[], status_filter=status_f)

@app.route('/admin/scan-qr')
@admin_required
def admin_scan_qr():
    return render_template('admin/scan_qr.html')

@app.route('/admin/check-token', methods=['POST'])
@admin_required
def admin_check_token():
    token = (request.json or {}).get('token', '').strip()
    if not token:
        return jsonify({'error': 'No token'}), 400
    try:
        if token.startswith('BORROW-'):
            r = supabase.table('borrows').select('*').eq('token', token).execute()
            if not r.data: return jsonify({'error': 'Token not found'}), 404
            b = r.data[0]
            if b['status'] != 'approved_pending_issue':
                return jsonify({'error': f'Already used (status: {b["status"]})'}), 400
            ur   = supabase.table('users').select('*').eq('id', b['user_id']).execute()
            bk   = supabase.table('books').select('*').eq('id', b['book_id']).execute()
            user = ur.data[0] if ur.data else {}
            book = bk.data[0] if bk.data else {}
            cb   = supabase.table('borrows').select('*').eq('user_id', user.get('id', '')).eq('status', 'issued').execute()
            curr = []
            for cb_item in (cb.data or []):
                b2 = supabase.table('books').select('title').eq('id', cb_item['book_id']).execute()
                curr.append(b2.data[0]['title'] if b2.data else 'Unknown')
            return jsonify({'type': 'borrow', 'borrow_id': b['id'],
                'user': {'name': user.get('name'), 'email': user.get('email'), 'user_type': user.get('user_type'), 'year': user.get('year'), 'trade': user.get('trade'), 'reg_number': user.get('reg_number'), 'profile_image_url': user.get('profile_image_url')},
                'book': {'title': book.get('title'), 'author': book.get('author'), 'cover_url': book.get('cover_url')},
                'current_books': curr, 'card_qr': generate_qr_base64(f"LIBCARD-{user.get('id', '')}"),
                'due_date': (datetime.utcnow() + timedelta(days=BORROW_DAYS)).strftime('%d %B %Y')})
        elif token.startswith('RETURN-'):
            r = supabase.table('borrows').select('*').eq('return_token', token).execute()
            if not r.data: return jsonify({'error': 'Return token not found'}), 404
            b = r.data[0]
            if b['status'] != 'return_pending': return jsonify({'error': f'Invalid status: {b["status"]}'}), 400
            ur = supabase.table('users').select('name', 'email').eq('id', b['user_id']).execute()
            bk = supabase.table('books').select('title', 'author').eq('id', b['book_id']).execute()
            return jsonify({'type': 'return', 'borrow_id': b['id'], 'user': ur.data[0] if ur.data else {}, 'book': bk.data[0] if bk.data else {}, 'due_date': fmt_date(b.get('due_date', '')), 'borrow_date': fmt_date(b.get('borrow_date', '')), 'fine': calculate_fine(b.get('due_date'))})
        elif token.startswith('LIBCARD-'):
            user_id = token[len('LIBCARD-'):]
            ur = supabase.table('users').select('*').eq('id', user_id).execute()
            if not ur.data: return jsonify({'error': 'User not found'}), 404
            user = ur.data[0]
            br = supabase.table('borrows').select('*').eq('user_id', user_id).in_('status', ['issued', 'approved_pending_issue', 'return_pending']).execute()
            active_books = []
            for b in (br.data or []):
                bk   = supabase.table('books').select('title').eq('id', b['book_id']).execute()
                fine = calculate_fine(b.get('due_date')) if b.get('status') == 'issued' else 0
                active_books.append({'title': bk.data[0]['title'] if bk.data else 'Unknown', 'status': b['status'], 'due_date': fmt_date(b.get('due_date', '')), 'fine': fine})
            return jsonify({'type': 'library_card', 'user': {'name': user.get('name'), 'email': user.get('email'), 'user_type': user.get('user_type'), 'year': user.get('year'), 'trade': user.get('trade'), 'reg_number': user.get('reg_number'), 'profile_image_url': user.get('profile_image_url')}, 'active_books': active_books, 'borrow_count': len(active_books)})
        return jsonify({'error': 'Invalid token format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/confirm-issue', methods=['POST'])
@admin_required
def admin_confirm_issue():
    borrow_id = (request.json or {}).get('borrow_id')
    try:
        r = supabase.table('borrows').select('*').eq('id', borrow_id).execute()
        if not r.data: return jsonify({'error': 'Not found'}), 404
        b = r.data[0]
        if b['status'] != 'approved_pending_issue': return jsonify({'error': 'Invalid status'}), 400
        now = datetime.utcnow()
        due = now + timedelta(days=BORROW_DAYS)
        supabase.table('borrows').update({'status': 'issued', 'borrow_date': now.isoformat(), 'due_date': due.isoformat()}).eq('id', borrow_id).execute()
        return jsonify({'success': True, 'due_date': due.strftime('%d %B %Y')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/confirm-return', methods=['POST'])
@admin_required
def admin_confirm_return():
    borrow_id = (request.json or {}).get('borrow_id')
    try:
        r = supabase.table('borrows').select('*').eq('id', borrow_id).execute()
        if not r.data: return jsonify({'error': 'Not found'}), 404
        b = r.data[0]
        if b['status'] != 'return_pending': return jsonify({'error': 'Invalid status'}), 400
        now  = datetime.utcnow()
        fine = calculate_fine(b.get('due_date'), now)
        supabase.table('borrows').update({'status': 'returned', 'return_date': now.isoformat(), 'fine': fine}).eq('id', borrow_id).execute()
        bk = supabase.table('books').select('available_quantity', 'total_quantity', 'title').eq('id', b['book_id']).execute()
        if bk.data:
            bd = bk.data[0]
            supabase.table('books').update({'available_quantity': min(bd['total_quantity'], bd['available_quantity'] + 1)}).eq('id', b['book_id']).execute()
            qr = supabase.table('reservations').select('*').eq('book_id', b['book_id']).eq('status', 'waiting').order('created_at').limit(1).execute()
            if qr.data:
                nq = qr.data[0]; tk = generate_token('BORROW')
                supabase.table('borrows').insert({'user_id': nq['user_id'], 'book_id': b['book_id'], 'token': tk, 'status': 'approved_pending_issue', 'created_at': now.isoformat() + 'Z'}).execute()
                supabase.table('reservations').update({'status': 'notified'}).eq('id', nq['id']).execute()
                ur = supabase.table('users').select('name', 'email').eq('id', nq['user_id']).execute()
                if ur.data:
                    send_email(ur.data[0]['email'], f'Book Available: {bd["title"]}', email_reservation_ready(ur.data[0]['name'], bd['title'], tk))
        ur  = supabase.table('users').select('name', 'email').eq('id', b['user_id']).execute()
        bk2 = supabase.table('books').select('title').eq('id', b['book_id']).execute()
        if ur.data and bk2.data:
            send_email(ur.data[0]['email'], 'Book Returned Successfully', email_return_success(ur.data[0]['name'], bk2.data[0]['title'], fine))
        return jsonify({'success': True, 'fine': fine})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/process/<token>')
@admin_required
def admin_process_token(token):
    token = token.strip().upper()
    try:
        if token.startswith('BORROW-'):
            r = supabase.table('borrows').select('*').eq('token', token).execute()
            if not r.data:
                return render_template('admin/process_token.html', error='Token not found. May have been already used.', token=token)
            b = r.data[0]
            if b['status'] != 'approved_pending_issue':
                return render_template('admin/process_token.html', error=f'Already processed (status: {b["status"].replace("_"," ")})', token=token)
            ur   = supabase.table('users').select('*').eq('id', b['user_id']).execute()
            bk   = supabase.table('books').select('*').eq('id', b['book_id']).execute()
            user = ur.data[0] if ur.data else {}
            book = bk.data[0] if bk.data else {}
            cb   = supabase.table('borrows').select('*').eq('user_id', user.get('id', '')).eq('status', 'issued').execute()
            curr = []
            for cb_item in (cb.data or []):
                b2 = supabase.table('books').select('title').eq('id', cb_item['book_id']).execute()
                curr.append(b2.data[0]['title'] if b2.data else 'Unknown')
            due = (datetime.utcnow() + timedelta(days=BORROW_DAYS)).strftime('%d %B %Y')
            return render_template('admin/process_token.html', action='issue', token=token, borrow_id=b['id'], user=user, book=book, current_books=curr, due_date=due)
        elif token.startswith('RETURN-'):
            r = supabase.table('borrows').select('*').eq('return_token', token).execute()
            if not r.data:
                return render_template('admin/process_token.html', error='Return token not found.', token=token)
            b = r.data[0]
            if b['status'] != 'return_pending':
                return render_template('admin/process_token.html', error=f'Already processed (status: {b["status"].replace("_"," ")})', token=token)
            ur   = supabase.table('users').select('name', 'email').eq('id', b['user_id']).execute()
            bk   = supabase.table('books').select('title', 'author').eq('id', b['book_id']).execute()
            fine = calculate_fine(b.get('due_date'))
            return render_template('admin/process_token.html', action='return', token=token, borrow_id=b['id'], user=ur.data[0] if ur.data else {}, book=bk.data[0] if bk.data else {}, due_date=fmt_date(b.get('due_date', '')), borrow_date=fmt_date(b.get('borrow_date', '')), fine=fine)
        elif token.startswith('LIBCARD-'):
            user_id = token[len('LIBCARD-'):]
            ur = supabase.table('users').select('*').eq('id', user_id).execute()
            if not ur.data:
                return render_template('admin/process_token.html', error='User not found for this card.', token=token)
            user = ur.data[0]
            # Active borrows
            br_active = supabase.table('borrows').select('*').eq('user_id', user_id).in_('status', ['issued', 'approved_pending_issue', 'return_pending']).execute()
            active = []
            for bw in (br_active.data or []):
                bk2  = supabase.table('books').select('title').eq('id', bw['book_id']).execute()
                fine = calculate_fine(bw.get('due_date')) if bw.get('status') == 'issued' else 0
                active.append({'title': bk2.data[0]['title'] if bk2.data else 'Unknown', 'status': bw['status'], 'due_date': fmt_date(bw.get('due_date', '')), 'fine': fine})
            # Full borrow history
            br_all = supabase.table('borrows').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(20).execute()
            history = []
            for bw in (br_all.data or []):
                bk2 = supabase.table('books').select('title').eq('id', bw['book_id']).execute()
                history.append({
                    'title':       bk2.data[0]['title'] if bk2.data else 'Unknown',
                    'status':      bw['status'],
                    'borrow_date': fmt_date(bw.get('borrow_date', '')),
                    'return_date': fmt_date(bw.get('return_date', '')),
                    'due_date':    fmt_date(bw.get('due_date', '')),
                    'fine':        bw.get('fine') or 0
                })
            return render_template('admin/process_token.html', action='card', token=token, user=user, active_books=active, borrow_history=history)
        return render_template('admin/process_token.html', error='Unknown token format. Must start with BORROW-, RETURN-, or LIBCARD-', token=token)
    except Exception as e:
        return render_template('admin/process_token.html', error=f'Error: {str(e)}', token=token)

@app.route('/admin/process-action', methods=['POST'])
@admin_required
def admin_process_action():
    action    = request.form.get('action')
    borrow_id = request.form.get('borrow_id')
    try:
        if action == 'issue':
            r = supabase.table('borrows').select('*').eq('id', borrow_id).execute()
            if not r.data: flash('Borrow record not found.', 'danger'); return redirect(url_for('admin_scan_qr'))
            b   = r.data[0]
            now = datetime.utcnow()
            due = now + timedelta(days=BORROW_DAYS)
            supabase.table('borrows').update({'status': 'issued', 'borrow_date': now.isoformat() + 'Z', 'due_date': due.isoformat() + 'Z'}).eq('id', borrow_id).execute()
            flash(f'Book issued! Due: {due.strftime("%d %B %Y")}', 'success')
        elif action == 'return':
            r = supabase.table('borrows').select('*').eq('id', borrow_id).execute()
            if not r.data: flash('Borrow record not found.', 'danger'); return redirect(url_for('admin_scan_qr'))
            b    = r.data[0]
            now  = datetime.utcnow()
            fine = calculate_fine(b.get('due_date'), now)
            supabase.table('borrows').update({'status': 'returned', 'return_date': now.isoformat() + 'Z', 'fine': fine}).eq('id', borrow_id).execute()
            bk = supabase.table('books').select('available_quantity', 'total_quantity', 'title').eq('id', b['book_id']).execute()
            if bk.data:
                bd = bk.data[0]
                supabase.table('books').update({'available_quantity': min(bd['total_quantity'], bd['available_quantity'] + 1)}).eq('id', b['book_id']).execute()
                qr = supabase.table('reservations').select('*').eq('book_id', b['book_id']).eq('status', 'waiting').order('created_at').limit(1).execute()
                if qr.data:
                    nq = qr.data[0]; tk = generate_token('BORROW')
                    supabase.table('borrows').insert({'user_id': nq['user_id'], 'book_id': b['book_id'], 'token': tk, 'status': 'approved_pending_issue', 'created_at': now.isoformat() + 'Z'}).execute()
                    supabase.table('reservations').update({'status': 'notified'}).eq('id', nq['id']).execute()
                    ur = supabase.table('users').select('name', 'email').eq('id', nq['user_id']).execute()
                    if ur.data:
                        send_email(ur.data[0]['email'], f'Book Available: {bd["title"]}', email_reservation_ready(ur.data[0]['name'], bd['title'], tk))
            ur  = supabase.table('users').select('name', 'email').eq('id', b['user_id']).execute()
            bk2 = supabase.table('books').select('title').eq('id', b['book_id']).execute()
            if ur.data and bk2.data:
                send_email(ur.data[0]['email'], 'Book Returned Successfully', email_return_success(ur.data[0]['name'], bk2.data[0]['title'], fine))
            flash(f'Book returned! Fine: Rs.{fine}' if fine > 0 else 'Book returned! No fine.', 'success')
        return redirect(url_for('admin_scan_qr'))
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return redirect(url_for('admin_scan_qr'))

@app.route('/admin/promote')
@admin_required
def admin_promote():
    try:
        s3 = supabase.table('users').select('*').eq('user_type', 'student').eq('year', '3rd').eq('is_active', True).execute().data or []
        s2 = supabase.table('users').select('*').eq('user_type', 'student').eq('year', '2nd').eq('is_active', True).execute().data or []
        s1 = supabase.table('users').select('*').eq('user_type', 'student').eq('year', '1st').eq('is_active', True).execute().data or []
        return render_template('admin/promote.html', students_3rd=s3, students_2nd=s2, students_1st=s1)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('admin/promote.html', students_3rd=[], students_2nd=[], students_1st=[])

@app.route('/admin/do-promote', methods=['POST'])
@admin_required
def admin_do_promote():
    from_year = request.form.get('from_year')
    excluded  = request.form.getlist('exclude')
    year_map  = {'3rd': 'passout', '2nd': '3rd', '1st': '2nd'}
    to_year   = year_map.get(from_year)
    if not to_year:
        flash('Invalid year.', 'danger')
        return redirect(url_for('admin_promote'))
    try:
        students = supabase.table('users').select('id', 'name').eq('user_type', 'student').eq('year', from_year).eq('is_active', True).execute().data or []
        promoted = 0
        for s in students:
            if s['id'] in excluded: continue
            if to_year == 'passout':
                # Check no active borrows before deleting
                active_count = supabase.table('borrows').select('id', count='exact').eq('user_id', s['id']).in_('status', ['issued', 'approved_pending_issue', 'return_pending']).execute().count or 0
                if active_count > 0:
                    flash(f'{s["name"]} has active borrows — cannot passout. Ask them to return books first.', 'warning')
                    continue
                supabase.table('reservations').delete().eq('user_id', s['id']).execute()
                supabase.table('borrows').delete().eq('user_id', s['id']).execute()
                supabase.table('users').delete().eq('id', s['id']).execute()
            else:
                supabase.table('users').update({'year': to_year}).eq('id', s['id']).execute()
            promoted += 1
        flash(f'Promoted {promoted} students from {from_year} to {to_year}.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('admin_promote'))

@app.route('/admin/delete-user/<user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    try:
        if (supabase.table('borrows').select('id', count='exact').eq('user_id', user_id).in_('status', ['issued', 'approved_pending_issue', 'return_pending']).execute().count or 0) > 0:
            ur = supabase.table('users').select('name', 'email').eq('id', user_id).execute()
            if ur.data:
                u = ur.data[0]
                send_email(u['email'], 'Pending Books — Deletion Prevented', f'<p>Dear {u["name"]}, please return all borrowed books before account deletion.</p>')
            flash('Cannot delete user with pending borrows. Reminder sent.', 'danger')
            return redirect(url_for('admin_users'))
        supabase.table('reservations').delete().eq('user_id', user_id).execute()
        supabase.table('borrows').delete().eq('user_id', user_id).execute()
        supabase.table('users').delete().eq('id', user_id).execute()
        flash('User deleted.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('admin_users'))

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    try:
        total_users   = supabase.table('users').select('id', count='exact').eq('role', 'user').execute().count or 0
        total_books   = supabase.table('books').select('id', count='exact').execute().count or 0
        total_borrows = supabase.table('borrows').select('id', count='exact').execute().count or 0
        total_fines   = sum((b.get('fine') or 0) for b in (supabase.table('borrows').select('fine').eq('status', 'returned').execute().data or []))
        return render_template('admin/analytics.html', total_users=total_users, total_books=total_books, total_borrows=total_borrows, total_fines=total_fines)
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('admin/analytics.html', total_users=0, total_books=0, total_borrows=0, total_fines=0)

@app.route('/admin/analytics-data')
@admin_required
def admin_analytics_data():
    try:
        labels, data = [], []
        for i in range(5, -1, -1):
            d  = datetime.utcnow() - timedelta(days=30 * i)
            ms = d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            me = (datetime.utcnow() - timedelta(days=30 * (i - 1))).replace(day=1, hour=0, minute=0, second=0, microsecond=0) if i > 0 else datetime.utcnow()
            cr = supabase.table('borrows').select('id', count='exact').gte('created_at', ms.isoformat()).lt('created_at', me.isoformat()).execute()
            data.append(cr.count or 0)
            labels.append(ms.strftime('%b %Y'))
        all_br = supabase.table('borrows').select('book_id').execute().data or []
        bc = {}
        for b in all_br: bc[b['book_id']] = bc.get(b['book_id'], 0) + 1
        top = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:5]
        tl, td = [], []
        for bid, cnt in top:
            bk = supabase.table('books').select('title').eq('id', bid).execute()
            if bk.data: tl.append(bk.data[0]['title'][:25]); td.append(cnt)
        students = supabase.table('users').select('id', count='exact').eq('user_type', 'student').execute().count or 0
        teachers = supabase.table('users').select('id', count='exact').eq('user_type', 'teacher').execute().count or 0
        all_bks  = supabase.table('books').select('trade').execute().data or []
        tc = {}
        for b in all_bks:
            c = b.get('trade') or 'General'; tc[c] = tc.get(c, 0) + 1
        issued   = supabase.table('borrows').select('id', count='exact').eq('status', 'issued').execute().count or 0
        returned = supabase.table('borrows').select('id', count='exact').eq('status', 'returned').execute().count or 0
        pending  = supabase.table('borrows').select('id', count='exact').eq('status', 'approved_pending_issue').execute().count or 0
        return jsonify({'monthly': {'labels': labels, 'data': data}, 'top_books': {'labels': tl, 'data': td}, 'user_types': {'students': students, 'teachers': teachers}, 'categories': {'labels': list(tc.keys()), 'data': list(tc.values())}, 'borrow_status': {'issued': issued, 'returned': returned, 'pending': pending}})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/send-reminders', methods=['POST'])
@admin_required
def admin_send_reminders():
    try:
        all_br = supabase.table('borrows').select('*').eq('status', 'issued').execute().data or []
        sent = 0
        for b in all_br:
            fine = calculate_fine(b.get('due_date'))
            if fine > 0:
                ur = supabase.table('users').select('name', 'email').eq('id', b['user_id']).execute()
                bk = supabase.table('books').select('title').eq('id', b['book_id']).execute()
                if ur.data and bk.data:
                    send_email(ur.data[0]['email'], f'Overdue: {bk.data[0]["title"]}', email_overdue(ur.data[0]['name'], bk.data[0]['title'], fmt_date(b.get('due_date', '')), fine))
                    sent += 1
        flash(f'Sent {sent} reminders.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    # Use environment port if available (Render/Heroku), default to 5000
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
