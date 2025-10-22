from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import jwt
import datetime
import os
import sqlite3
import socket
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Get local IP for network access
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

LOCAL_IP = get_local_ip()

# CORS configuration - Allow all origins for development
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Allow all origins for development
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

bcrypt = Bcrypt(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database setup
def init_db():
    conn = sqlite3.connect('jobtracker.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if applications table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applications'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # Check if new columns exist
        cursor.execute("PRAGMA table_info(applications)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add new columns if they don't exist
        if 'accepted_date' not in columns:
            cursor.execute('ALTER TABLE applications ADD COLUMN accepted_date DATE')
        if 'rejected_date' not in columns:
            cursor.execute('ALTER TABLE applications ADD COLUMN rejected_date DATE')
        if 'interview_date' not in columns:
            cursor.execute('ALTER TABLE applications ADD COLUMN interview_date DATE')
    else:
        # Create applications table with all columns
        cursor.execute('''
            CREATE TABLE applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company TEXT NOT NULL,
                application_date DATE NOT NULL,
                cover_letter TEXT,
                cv_filename TEXT,
                status TEXT DEFAULT 'pending',
                accepted_date DATE,
                rejected_date DATE,
                interview_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
    
    conn.commit()
    conn.close()

init_db()

# FIXED: Auth decorator that allows OPTIONS requests
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Allow OPTIONS requests without token
        if request.method == 'OPTIONS':
            return f(None, *args, **kwargs)
        
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401
        except Exception as e:
            return jsonify({'message': 'Token validation failed'}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated

# Add OPTIONS handler for CORS preflight
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin:
        response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,PATCH,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Routes

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'Job Tracker API',
        'version': '1.0',
        'status': 'running',
        'timestamp': datetime.datetime.now(datetime.UTC).isoformat(),
        'local_ip': LOCAL_IP,
        'user': 'zmikicdroin'
    }), 200

@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 204
        
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'message': 'Missing required fields: username, email, password'}), 400
    
    if len(password) < 6:
        return jsonify({'message': 'Password must be at least 6 characters long'}), 400
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    try:
        conn = sqlite3.connect('jobtracker.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                      (username, email, hashed_password))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'message': 'User created successfully',
            'user_id': user_id,
            'username': username
        }), 201
    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        if 'username' in error_msg:
            return jsonify({'message': 'Username already exists'}), 409
        elif 'email' in error_msg:
            return jsonify({'message': 'Email already exists'}), 409
        else:
            return jsonify({'message': 'User already exists'}), 409

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204
        
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400
    
    conn = sqlite3.connect('jobtracker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and bcrypt.check_password_hash(user[2], password):
        # FIXED: Use timezone-aware datetime
        token = jwt.encode({
            'user_id': user[0],
            'username': user[1],
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'message': 'Login successful',
            'username': user[1]
        }), 200
    
    return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/api/applications', methods=['GET', 'POST', 'OPTIONS'])
@token_required
def applications_route(current_user_id):
    if request.method == 'OPTIONS':
        return '', 204
    elif request.method == 'POST':
        return create_application(current_user_id)
    else:  # GET
        return get_applications(current_user_id)

def create_application(current_user_id):
    company = request.form.get('company')
    application_date = request.form.get('application_date')
    cover_letter = request.form.get('cover_letter', '')
    status = request.form.get('status', 'pending')
    accepted_date = request.form.get('accepted_date')
    rejected_date = request.form.get('rejected_date')
    interview_date = request.form.get('interview_date')
    
    if not company or not application_date:
        return jsonify({'message': 'Missing required fields: company, application_date'}), 400
    
    # Validate status
    if status not in ['pending', 'accepted', 'rejected', 'interview']:
        status = 'pending'
    
    # Validate date format
    try:
        datetime.datetime.strptime(application_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    cv_filename = None
    if 'cv' in request.files:
        file = request.files['cv']
        if file and file.filename:
            # Validate file type
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({'message': 'Only PDF files are allowed for CV'}), 400
            
            filename = secure_filename(file.filename)
            timestamp = datetime.datetime.now(datetime.UTC).timestamp()
            cv_filename = f"{current_user_id}_{timestamp}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], cv_filename))
    
    try:
        conn = sqlite3.connect('jobtracker.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO applications (user_id, company, application_date, cover_letter, cv_filename, status, accepted_date, rejected_date, interview_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (current_user_id, company, application_date, cover_letter, cv_filename, status, accepted_date, rejected_date, interview_date))
        conn.commit()
        app_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'message': 'Application created successfully',
            'application_id': app_id
        }), 201
    except Exception as e:
        return jsonify({'message': f'Failed to create application: {str(e)}'}), 500

def get_applications(current_user_id):
    try:
        conn = sqlite3.connect('jobtracker.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, company, application_date, cover_letter, cv_filename, status, 
                   accepted_date, rejected_date, interview_date, created_at
            FROM applications
            WHERE user_id = ?
            ORDER BY application_date DESC
        ''', (current_user_id,))
        applications = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(applications), 200
    except Exception as e:
        return jsonify({'message': f'Failed to fetch applications: {str(e)}'}), 500

@app.route('/api/applications/<int:app_id>', methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])
@token_required
def handle_application(current_user_id, app_id):
    if request.method == 'OPTIONS':
        return '', 204
        
    if request.method == 'GET':
        return get_application(current_user_id, app_id)
    elif request.method == 'PUT':
        return update_application(current_user_id, app_id)
    elif request.method == 'DELETE':
        return delete_application(current_user_id, app_id)

def get_application(current_user_id, app_id):
    try:
        conn = sqlite3.connect('jobtracker.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, company, application_date, cover_letter, cv_filename, status,
                   accepted_date, rejected_date, interview_date, created_at
            FROM applications
            WHERE id = ? AND user_id = ?
        ''', (app_id, current_user_id))
        application = cursor.fetchone()
        conn.close()
        
        if application:
            return jsonify(dict(application)), 200
        else:
            return jsonify({'message': 'Application not found'}), 404
    except Exception as e:
        return jsonify({'message': f'Failed to fetch application: {str(e)}'}), 500

def update_application(current_user_id, app_id):
    company = request.form.get('company')
    application_date = request.form.get('application_date')
    cover_letter = request.form.get('cover_letter', '')
    status = request.form.get('status', 'pending')
    accepted_date = request.form.get('accepted_date') or None
    rejected_date = request.form.get('rejected_date') or None
    interview_date = request.form.get('interview_date') or None
    
    if not company or not application_date:
        return jsonify({'message': 'Missing required fields: company, application_date'}), 400
    
    # Validate status
    if status not in ['pending', 'accepted', 'rejected', 'interview']:
        status = 'pending'
    
    # Validate date format
    try:
        datetime.datetime.strptime(application_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    try:
        conn = sqlite3.connect('jobtracker.db')
        cursor = conn.cursor()
        
        # Check if new CV is uploaded
        if 'cv' in request.files:
            file = request.files['cv']
            if file and file.filename:
                # Get old CV filename
                cursor.execute('SELECT cv_filename FROM applications WHERE id = ? AND user_id = ?', 
                              (app_id, current_user_id))
                result = cursor.fetchone()
                old_cv = result[0] if result else None
                
                # Delete old CV
                if old_cv:
                    old_cv_path = os.path.join(app.config['UPLOAD_FOLDER'], old_cv)
                    if os.path.exists(old_cv_path):
                        os.remove(old_cv_path)
                
                # Save new CV
                if not file.filename.lower().endswith('.pdf'):
                    return jsonify({'message': 'Only PDF files are allowed for CV'}), 400
                
                filename = secure_filename(file.filename)
                timestamp = datetime.datetime.now(datetime.UTC).timestamp()
                cv_filename = f"{current_user_id}_{timestamp}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], cv_filename))
                
                cursor.execute('''
                    UPDATE applications 
                    SET company = ?, application_date = ?, cover_letter = ?, status = ?,
                        accepted_date = ?, rejected_date = ?, interview_date = ?, cv_filename = ?
                    WHERE id = ? AND user_id = ?
                ''', (company, application_date, cover_letter, status, accepted_date, rejected_date, interview_date, cv_filename, app_id, current_user_id))
            else:
                cursor.execute('''
                    UPDATE applications 
                    SET company = ?, application_date = ?, cover_letter = ?, status = ?,
                        accepted_date = ?, rejected_date = ?, interview_date = ?
                    WHERE id = ? AND user_id = ?
                ''', (company, application_date, cover_letter, status, accepted_date, rejected_date, interview_date, app_id, current_user_id))
        else:
            cursor.execute('''
                UPDATE applications 
                SET company = ?, application_date = ?, cover_letter = ?, status = ?,
                    accepted_date = ?, rejected_date = ?, interview_date = ?
                WHERE id = ? AND user_id = ?
            ''', (company, application_date, cover_letter, status, accepted_date, rejected_date, interview_date, app_id, current_user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'message': 'Application not found'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Application updated successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'Failed to update application: {str(e)}'}), 500

def delete_application(current_user_id, app_id):
    try:
        conn = sqlite3.connect('jobtracker.db')
        cursor = conn.cursor()
        
        # Get CV filename before deleting
        cursor.execute('SELECT cv_filename FROM applications WHERE id = ? AND user_id = ?', 
                      (app_id, current_user_id))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'message': 'Application not found'}), 404
        
        cv_filename = result[0]
        
        # Delete from database
        cursor.execute('DELETE FROM applications WHERE id = ? AND user_id = ?', 
                      (app_id, current_user_id))
        conn.commit()
        conn.close()
        
        # Delete CV file if exists
        if cv_filename:
            cv_path = os.path.join(app.config['UPLOAD_FOLDER'], cv_filename)
            if os.path.exists(cv_path):
                os.remove(cv_path)
        
        return jsonify({'message': 'Application deleted successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'Failed to delete application: {str(e)}'}), 500

@app.route('/api/applications/<int:app_id>/status', methods=['PATCH', 'OPTIONS'])
@token_required
def update_application_status(current_user_id, app_id):
    if request.method == 'OPTIONS':
        return '', 204
        
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    status = data.get('status')
    
    if not status:
        return jsonify({'message': 'Missing status field'}), 400
    
    if status not in ['pending', 'accepted', 'rejected', 'interview']:
        return jsonify({'message': 'Invalid status. Must be: pending, accepted, rejected, or interview'}), 400
    
    try:
        conn = sqlite3.connect('jobtracker.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE applications 
            SET status = ? 
            WHERE id = ? AND user_id = ?
        ''', (status, app_id, current_user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'message': 'Application not found'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Status updated successfully', 'status': status}), 200
    except Exception as e:
        return jsonify({'message': f'Failed to update status: {str(e)}'}), 500

@app.route('/api/uploads/<filename>', methods=['GET', 'OPTIONS'])
@token_required
def download_file(current_user_id, filename):
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # Verify that the file belongs to the current user
        conn = sqlite3.connect('jobtracker.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM applications WHERE user_id = ? AND cv_filename = ?', 
                      (current_user_id, filename))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'message': 'File not found or unauthorized'}), 404
        
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        return jsonify({'message': f'Failed to download file: {str(e)}'}), 500

@app.route('/api/stats', methods=['GET', 'OPTIONS'])
@token_required
def get_stats(current_user_id):
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        conn = sqlite3.connect('jobtracker.db')
        cursor = conn.cursor()
        
        # Total applications
        cursor.execute('SELECT COUNT(*) FROM applications WHERE user_id = ?', (current_user_id,))
        total = cursor.fetchone()[0]
        
        # Status counts
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM applications 
            WHERE user_id = ? 
            GROUP BY status
        ''', (current_user_id,))
        status_counts = dict(cursor.fetchall())
        
        # Applications this month
        cursor.execute('''
            SELECT COUNT(*) 
            FROM applications 
            WHERE user_id = ? 
            AND strftime('%Y-%m', application_date) = strftime('%Y-%m', 'now')
        ''', (current_user_id,))
        this_month = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total': total,
            'pending': status_counts.get('pending', 0),
            'accepted': status_counts.get('accepted', 0),
            'rejected': status_counts.get('rejected', 0),
            'interview': status_counts.get('interview', 0),
            'this_month': this_month
        }), 200
    except Exception as e:
        return jsonify({'message': f'Failed to fetch stats: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'message': 'File too large. Maximum size is 16MB'}), 413

if __name__ == '__main__':
    print("=" * 60)
    print("Job Tracker API Server")
    print("=" * 60)
    print(f"Server starting at: {datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"User: zmikicdroin")
    print(f"Local IP: {LOCAL_IP}")
    print(f"Backend URL (localhost): http://localhost:5000")
    print(f"Backend URL (network): http://{LOCAL_IP}:5000")
    print(f"API Endpoints: http://{LOCAL_IP}:5000/api/")
    print("=" * 60)
    print("Access from network devices:")
    print(f"  Frontend: http://{LOCAL_IP}:3000")
    print(f"  Backend:  http://{LOCAL_IP}:5000")
    print("=" * 60)
    app.run(debug=True, port=5000, host='0.0.0.0')