from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
import sqlite3
import os
import time
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.secret_key = 'sbtet_c23_secret_key_0106'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'pdf'}
ADMIN_SECRET_CODE = 'plpt$155$551'  # Simple secret code for admin access, can be changed as needed 
ADMIN_USERNAME = 'sbtet admin'
ADMIN_PASSWORD = 'sbtet@155@dcme'  # Simple password for admin access, can be changed as needed

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ─── DB ───────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect('sbtet.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS semesters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        sort_order INTEGER NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        name TEXT NOT NULL,
        branch_code TEXT NOT NULL,
        semester TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS question_papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        original_name TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        download_count INTEGER DEFAULT 0,
        FOREIGN KEY (subject_id) REFERENCES subjects(id)
    )''')

    conn.commit()
    seed_data(conn)
    conn.close()

def seed_data(conn):
    c = conn.cursor()

    # Branches
    branches = [
        ('CME', 'Computer Engineering'),
        ('ECE', 'Electrical & Communication Engineering'),
        ('ME',  'Mechanical Engineering'),
        ('CIVIL', 'Civil Engineering'),
    ]
    for code, name in branches:
        c.execute('INSERT OR IGNORE INTO branches (code, name) VALUES (?, ?)', (code, name))

    # Semesters
    semesters = [('1 YEAR', 1), ('3 SEM', 2), ('4 SEM', 3), ('5 SEM', 4)]
    for name, order in semesters:
        c.execute('INSERT OR IGNORE INTO semesters (name, sort_order) VALUES (?, ?)', (name, order))

    # Subjects
    subjects =    [
        # CME – 1 YEAR
        ('C23-CM-101', 'English',                             'CME',   '1 YEAR'),
        ('C23-CM-102', 'Engineering Mathematics - I',         'CME',   '1 YEAR'),
        ('C23-CM-103', 'Engineering Physics',                 'CME',   '1 YEAR'),
        ('C23-CM-104', 'Engineering Chemistry',               'CME',   '1 YEAR'),
        ('C23-CM-105', 'Basics of computer enineering',        'CME',   '1 YEAR'),
        ('C23-CM-106', 'Programming in C',                     'CME',   '1 YEAR'),
        ('C23-CM-107', 'Engineering drawing',                     'CME',   '1 YEAR'),
        # CME – 3 SEM
        ('C23-CM-301', 'Engineering mathematics',                'CME',   '3 SEM'),
        ('C23-CM-302', 'Digital electronics  ',                 'CME',   '3 SEM'),
        ('C23-CM-303', 'Operating Systems',                     'CME',   '3 SEM'),
        ('C23-CM-304', 'Data Structures',                      'CME',   '3 SEM'),
        ('C23-CM-305', 'Database Management Systems',         'CME',   '3 SEM'),
        # CME – 4 SEM
        ('C23-CM-401', 'Software Engineering',          'CME',   '4 SEM'),
        ('C23-CM-402', 'Web Technologies',               'CME',   '4 SEM'),
        ('C23-CM-403', 'Computer Organization & micro processor',               'CME',   '4 SEM'),
        ('C23-CM-404', 'Oops through java',                 'CME',   '4 SEM'),
        ('C23-CM-405', 'Computer network and cyber security',              'CME',   '4 SEM'),
        # CME – 5 SEM
        ('C23-CM-501', 'Industrial management enterpreneurship',            'CME',   '5 SEM'),
        ('C23-CM-502', 'Big data & colud computing',                     'CME',   '5 SEM'),
        ('C23-CM-503', 'Android programming',     'CME',   '5 SEM'),
        ('C23-CM-504', 'internet of things',                       'CME',   '5 SEM'),
        ('C23-CM-505', 'python programming',                       'CME',   '5 SEM'),

        # ECE – 1 YEAR
        ('C23-EC-101', 'English',                            'ECE',   '1 YEAR'),
        ('C23-EC-102', 'Engineering Mathematics - I',        'ECE',   '1 YEAR'),
        ('C23-EC-103', 'Engineering Physics',                'ECE',   '1 YEAR'),
        ('C23-EC-104', 'Engineering Chemistry',              'ECE',   '1 YEAR'),
        ('C23-EC-105', 'Electronics component & devices',       'ECE',   '1 YEAR'),
        ('C23-EC-106', 'Element of Electrical Engineering',  'ECE',   '1 YEAR'),
        ('C23-EC-107', 'Engineering Drawing',                'ECE',   '1 YEAR'),
        # ECE – 3 SEM
        ('C23-EC-301', 'Engineering Mathematics - II',      'ECE',   '3 SEM'),
        ('C23-EC-302', 'ELECTRONIC CIRCUITS-1',              'ECE',   '3 SEM'),
        ('C23-EC-303', 'Digital Electronics',                   'ECE',   '3 SEM'),
        ('C23-EC-304', 'ANALOG AND DIGITAL COMMUNICATION SYSTEM',                'ECE',   '3 SEM'),
        ('C23-EC-305', 'NETWORK ANALYSIS',            'ECE',   '3 SEM'),
        ('C23-EC-306', 'PROGRAMMING C & MAT LAB',            'ECE',   '3 SEM'),

        # ECE – 4 SEM
        ('C23-EC-401', 'ELECTRONIC CIRCUITS-2',               'ECE',   '4 SEM'),
        ('C23-EC-402', ' Microcontrollers & INTERFACING', 'ECE',   '4 SEM'),
        ('C23-EC-403', 'MICROWAVE & SATELITE COMMUNICATION SYSTEM',         'ECE',   '4 SEM'),
        ('C23-EC-404', 'IOT SENSORS',         'ECE',   '4 SEM'),
        ('C23-EC-405', 'DIGITAL LOGIC DESIGN THROUGH VERILOG DESIGN ',         'ECE',   '4 SEM'),
        # ECE – 5 SEM
        ('C23-EC-501', 'Industrial management enterpreneurship',              'ECE',   '5 SEM'),
        ('C23-EC-502', 'Embedded Systems',                   'ECE',   '5 SEM'),
        ('C23-EC-503', 'OPTICAL & MOBILE COMMUNICATION',                        'ECE',   '5 SEM'),
        ('C23-EC-504', 'INDUSTRIAL ELECTRONICS AND AUTOMATION',                 'ECE',   '5 SEM'),
        ('C23-EC-505', 'DATA COMMUNIATION AND COMMUNICATION NETWORKS',                 'ECE',   '5 SEM'),

        # ME – 1 YEAR
        ('C23-M-101', 'English',                            'ME',    '1 YEAR'),
        ('C23-M-102', 'Engineering Mathematics - I',        'ME',    '1 YEAR'),
        ('C23-M-103', 'Engineering Physics',                'ME',    '1 YEAR'),
        ('C23-M-104', 'Engineering Chemistry',              'ME',    '1 YEAR'),
        ('C23-M-105', 'ENGINEERING MECHANICS',                'ME',    '1 YEAR'),
        ('C23-M-106', 'BASIC MANUFACTURING PROCESS',                'ME',    '1 YEAR'),
         ('C23-M-107', 'Engineering Drawing',                'ME',    '1 YEAR'),

        # ME – 3 SEM
        ('C23-M-301', 'Engineering Mathematics - II',              'ME',    '3 SEM'),
        ('C23-M-302', 'APPLIED ELECTRICAL & ELECTRONICS',                 'ME',    '3 SEM'),
        ('C23-M-303', 'THERMAL ENGINEERING-1',                    'ME',    '3 SEM'),
        ('C23-M-304', 'STRENGTH OF MATERIALS',                     'ME',    '3 SEM'),
        ('C23-M-305', 'Manufacturing Technology',           'ME',    '3 SEM'),
        ('C23-M-306', 'MACHINE DRAWING',           'ME',    '3 SEM'),
        # ME – 4 SEM
        ('C23-M-401', 'DESIGN OF MACHINE ELEMENT',                     'ME',    '4 SEM'),
        ('C23-M-402', 'HYDRAAULIS & FLUID POWER SYSTEM',                      'ME',    '4 SEM'),
        ('C23-M-403', 'THERMAL ENGINEERING-2',        'ME',    '4 SEM'),
        ('C23-M-404', 'ENGINEERING MATERIALS',                            'ME',    '4 SEM'),
         ('C23-M-405', 'MANUFACTURING TECHNOLGY',                            'ME',    '4 SEM'),
         ('C23-M-406', 'PRODUCTION DRAWING',                            'ME',    '4 SEM'),

        # ME – 5 SEM
        ('C23-M-501', 'Industrial management enterpreneurship',             'ME',    '5 SEM'),
        ('C23-M-502', 'INDUSTRIAL ENGINEERING AND QUAALITY CONTROL',   'ME',    '5 SEM'),
        ('C23-M-503', 'GREEN ENERGY & THERMAL SYSTEMS',             'ME',    '5 SEM'),
        ('C23-M-504', 'INDUSTRIAL AUTOMATION & 3D PRINTING',                       'ME',    '5 SEM'),
        ('C23-M-505', 'REFRIGERATION & AIR CONDITIONING',                       'ME',    '5 SEM'),

        # CIVIL – 1 YEAR
        ('C23-C-101', 'English',                            'CIVIL', '1 YEAR'),
        ('C23-C-102', 'Engineering Mathematics - I',        'CIVIL', '1 YEAR'),
        ('C23-C-103', 'Engineering Physics',                'CIVIL', '1 YEAR'),
        ('C23-C-104', 'Engineering Chemistry',              'CIVIL', '1 YEAR'),
        ('C23-C-105', 'ENGINEERING MECHANICS',                'CIVIL', '1 YEAR'),
        ('C23-C-106', 'SURVEYING',                            'CIVIL', '1 YEAR'),
        ('C23-C-107', 'Engineering Drawing',                'CIVIL', '1 YEAR'),
        # CIVIL – 3 SEM
        ('C23-C-301', 'Engineering Mathematics - II',                          'CIVIL', '3 SEM'),
        ('C23-C-302', 'MECHANICS OF SOLIDS AND THEORY OF STRUCTURES',              'CIVIL', '3 SEM'),
        ('C23-C-303', 'HYDRAULICS',                    'CIVIL', '3 SEM'),
        ('C23-C-304', 'SURVEYING - 2',  'CIVIL', '3 SEM'),
        ('C23-C-305', 'CONSTRUCTION MATERIALS',                     'CIVIL', '3 SEM'),
         ('C23-C-306', 'CIVIL DRAWING',                     'CIVIL', '3 SEM'),
        # CIVIL – 4 SEM
        ('C23-C-401', 'CONSTRUCTION TECHNOLOGY AND VALUATION',                'CIVIL', '4 SEM'),
        ('C23-C-402', 'DESIGN AND DETAILING OF  R.C STRUCTURES',                'CIVIL', '4 SEM'),
        ('C23-C-403', 'Transportation Engineering',         'CIVIL', '4 SEM'),
        ('C23-C-404', 'Irrigation Engineering',             'CIVIL', '4 SEM'),  
            ('C23-C-405', 'CIVIL Engineering DRAWING - 2',             'CIVIL', '4 SEM'),
    

        # CIVIL – 5 SEM
        ('C23-C-501', 'STEEL STRUCTURES',               'CIVIL', '5 SEM'),
        ('C23-C-502', 'Environmental Engineering',          'CIVIL', '5 SEM'),
        ('C23-C-503', 'Quantity Surveying',     'CIVIL', '5 SEM'),
        ('C23-C-504', 'ADVACED CIVIL ENGINEERING TEHNOLOGIES',              'CIVIL', '5 SEM'),
        ('C23-C-505', 'CONSTRUCTION MANAGEMENT & ENTERPRENEURSHIP',              'CIVIL', '5 SEM'),
        ('C23-C-506', 'STRUCTURAL ENGINEERING DRAWING',               'CIVIL', '5 SEM'),
      ]

    for code, name, branch, sem in subjects:
        c.execute('SELECT id FROM subjects WHERE code = ? AND branch_code = ?', (code, branch))
        if not c.fetchone():
            c.execute('INSERT INTO subjects (code, name, branch_code, semester) VALUES (?, ?, ?, ?)',
                      (code, name, branch, sem))

    conn.commit()

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ─── STUDENT ROUTES ───────────────────────────────────────────────────────────

@app.route('/')
def index():
    conn = get_db()
    branches = conn.execute('SELECT * FROM branches').fetchall()
    semesters = conn.execute('SELECT * FROM semesters ORDER BY sort_order').fetchall()
    conn.close()
    return render_template('index.html', branches=branches, semesters=semesters)

@app.route('/papers')
def papers():
    conn = get_db()
    branches = conn.execute('SELECT * FROM branches').fetchall()
    semesters = conn.execute('SELECT * FROM semesters ORDER BY sort_order').fetchall()
    conn.close()
    return render_template('papers.html', branches=branches, semesters=semesters)

@app.route('/get-subjects')
def get_subjects():
    branch = request.args.get('branch', '')
    semester = request.args.get('semester', '')
    if not branch or not semester:
        return jsonify({'subjects': []})
    conn = get_db()
    subjects = conn.execute(
        'SELECT * FROM subjects WHERE branch_code = ? AND semester = ? ORDER BY code',
        (branch, semester)
    ).fetchall()
    conn.close()
    return jsonify({'subjects': [dict(s) for s in subjects]})

@app.route('/get-papers', methods=['POST'])
def get_papers():
    data = request.get_json()
    subject_id = data.get('subject_id')
    if not subject_id:
        return jsonify({'papers': []})
    conn = get_db()
    papers = conn.execute('''
        SELECT qp.id, qp.file_path, qp.original_name, qp.upload_date, qp.download_count,
               s.name as subject_name, s.code as subject_code
        FROM question_papers qp
        JOIN subjects s ON qp.subject_id = s.id
        WHERE qp.subject_id = ?
        ORDER BY qp.upload_date DESC
    ''', (subject_id,)).fetchall()
    conn.close()
    return jsonify({'papers': [dict(p) for p in papers]})

@app.route('/download/<int:paper_id>')
def download_paper(paper_id):
    conn = get_db()
    paper = conn.execute('SELECT * FROM question_papers WHERE id = ?', (paper_id,)).fetchone()
    if not paper:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    conn.execute('UPDATE question_papers SET download_count = download_count + 1 WHERE id = ?', (paper_id,))
    conn.commit()
    conn.close()
    filename = os.path.basename(paper['file_path'])
    return send_from_directory(
        os.path.abspath(app.config['UPLOAD_FOLDER']),
        filename,
        as_attachment=True,
        download_name=paper['original_name'] or filename
    )

# ─── ADMIN ROUTES ─────────────────────────────────────────────────────────────

@app.route('/admin-0106-secret', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        secret   = request.form.get('secret_code', '')
        if secret == ADMIN_SECRET_CODE or (username == ADMIN_USERNAME and password == ADMIN_PASSWORD):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid credentials. Access denied.'
    return render_template('admin_login.html', error=error)

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db()
    branches = conn.execute('SELECT * FROM branches').fetchall()
    semesters = conn.execute('SELECT * FROM semesters ORDER BY sort_order').fetchall()
    papers = conn.execute('''
        SELECT qp.id, qp.file_path, qp.original_name, qp.upload_date, qp.download_count,
               s.name as subject_name, s.code as subject_code,
               b.name as branch_name, qp.subject_id
        FROM question_papers qp
        JOIN subjects s ON qp.subject_id = s.id
        JOIN branches b ON s.branch_code = b.code
        ORDER BY qp.upload_date DESC
    ''').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', branches=branches, semesters=semesters, papers=papers)

@app.route('/upload-paper', methods=['POST'])
@admin_required
def upload_paper():
    subject_id = request.form.get('subject_id')
    file = request.files.get('file')
    if not subject_id or not file:
        return jsonify({'success': False, 'message': 'Missing subject or file'})
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Only PDF files allowed'})
    original_name = secure_filename(file.filename)
    timestamp = str(int(time.time() * 1000))
    new_filename = f"{timestamp}_{original_name}"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
    file.save(save_path)
    db_path = f"static/uploads/{new_filename}"
    conn = get_db()
    conn.execute(
        'INSERT INTO question_papers (subject_id, file_path, original_name) VALUES (?, ?, ?)',
        (subject_id, db_path, original_name)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Paper uploaded successfully!'})

@app.route('/delete-paper', methods=['POST'])
@admin_required
def delete_paper():
    data = request.get_json()
    paper_id = data.get('paper_id')
    if not paper_id:
        return jsonify({'success': False, 'message': 'Missing paper ID'})
    conn = get_db()
    conn.execute('DELETE FROM question_papers WHERE id = ?', (paper_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Paper removed from database. File retained in storage.'})

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin/get-subjects')
@admin_required
def admin_get_subjects():
    branch = request.args.get('branch', '')
    semester = request.args.get('semester', '')
    conn = get_db()
    if branch and semester:
        subjects = conn.execute(
            'SELECT * FROM subjects WHERE branch_code = ? AND semester = ? ORDER BY code',
            (branch, semester)
        ).fetchall()
    else:
        subjects = []
    conn.close()
    return jsonify({'subjects': [dict(s) for s in subjects]})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
