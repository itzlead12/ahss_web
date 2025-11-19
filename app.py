from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' 

# Configuration for file uploads - MUST be after app definition
app.config['UPLOAD_FOLDER'] = 'static/uploads/schools'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def init_db():
    conn = sqlite3.connect('site.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS admin_users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS contact_messages
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Updated schools table
    c.execute('''CREATE TABLE IF NOT EXISTS schools
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                logo_filename TEXT,
                website_link TEXT,
                students_count INTEGER DEFAULT 0,
                active_clubs INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect('site.db')
    conn.row_factory = sqlite3.Row
    return conn

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    conn = get_db_connection()
    schools = conn.execute('''
        SELECT * FROM schools 
        WHERE is_active = 1 
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template('main/index.html', schools=schools)

# ============ ADMIN LOGIN =========================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM admin_users WHERE username = ? AND password = ?', 
                           (username, password)).fetchone()
        conn.close()
        
        if user:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin/login.html')

# ========================= SCHOOLS MANAGEMENT ==================

@app.route('/admin/schools')
@admin_required
def admin_schools():
    conn = get_db_connection()
    schools = conn.execute('SELECT * FROM schools ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('admin/schools.html', schools=schools)

@app.route('/admin/schools/new', methods=['GET', 'POST'])
@admin_required
def new_school():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        website_link = request.form['website_link']
        students_count = request.form['students_count']
        active_clubs = request.form['active_clubs']
        
        # Handle file upload
        logo_filename = None
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '' and allowed_file(file.filename):
                # Create uploads directory if it doesn't exist
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                filename = secure_filename(file.filename)
                # Create unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                filename = timestamp + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                logo_filename = filename
        
        conn = get_db_connection()
        conn.execute('''INSERT INTO schools (name, description, logo_filename, website_link, students_count, active_clubs) 
                        VALUES (?, ?, ?, ?, ?, ?)''',
                    (name, description, logo_filename, website_link, students_count, active_clubs))
        conn.commit()
        conn.close()
        
        flash('School added successfully!', 'success')
        return redirect(url_for('admin_schools'))
    
    return render_template('admin/new_school.html')

@app.route('/admin/schools/edit/<int:school_id>', methods=['GET', 'POST'])
@admin_required
def edit_school(school_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        website_link = request.form['website_link']
        students_count = request.form['students_count']
        active_clubs = request.form['active_clubs']
        is_active = 'is_active' in request.form
        remove_logo = 'remove_logo' in request.form
        
        # Get current school data
        current_school = conn.execute('SELECT logo_filename FROM schools WHERE id = ?', (school_id,)).fetchone()
        
        # Handle file upload/removal
        logo_filename = current_school['logo_filename']
        
        if remove_logo and logo_filename:
            # Remove the old logo file
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))
            except:
                pass
            logo_filename = None
        
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '' and allowed_file(file.filename):
                # Create uploads directory if it doesn't exist
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # Remove old logo if exists
                if logo_filename:
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))
                    except:
                        pass
                
                # Save new logo
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                filename = timestamp + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                logo_filename = filename
        
        conn.execute('''UPDATE schools SET 
                        name = ?, description = ?, logo_filename = ?, website_link = ?, 
                        students_count = ?, active_clubs = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?''',
                    (name, description, logo_filename, website_link, students_count, active_clubs, is_active, school_id))
        conn.commit()
        conn.close()
        
        flash('School updated successfully!', 'success')
        return redirect(url_for('admin_schools'))
    
    school = conn.execute('SELECT * FROM schools WHERE id = ?', (school_id,)).fetchone()
    conn.close()
    
    if not school:
        flash('School not found!', 'error')
        return redirect(url_for('admin_schools'))
    
    return render_template('admin/edit_school.html', school=school)

@app.route('/admin/schools/delete/<int:school_id>')
@admin_required
def delete_school(school_id):
    conn = get_db_connection()
    
    # Get school logo filename before deletion
    school = conn.execute('SELECT logo_filename FROM schools WHERE id = ?', (school_id,)).fetchone()
    
    # Delete the logo file if exists
    if school and school['logo_filename']:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], school['logo_filename']))
        except:
            pass
    
    conn.execute('DELETE FROM schools WHERE id = ?', (school_id,))
    conn.commit()
    conn.close()
    
    flash('School deleted successfully!', 'success')
    return redirect(url_for('admin_schools'))

# ========================= CONTACT MANAGEMENT ===========================================
@app.route('/contact', methods=['POST'])
def contact_submit():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)',
                    (name, email, message))
        conn.commit()
        conn.close()
        
        flash('Your message has been sent successfully! We will get back to you soon.', 'success')
        return redirect(url_for('index') + '#contact')
    
    return redirect(url_for('index'))

@app.route('/admin/messages')
@admin_required
def admin_messages():
    conn = get_db_connection()
    messages = conn.execute('''
        SELECT * FROM contact_messages 
        ORDER BY created_at DESC
    ''').fetchall()
    
    total_messages = len(messages)
    unread_messages = sum(1 for m in messages if not m['is_read'])
    read_messages = total_messages - unread_messages
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_messages = sum(1 for m in messages if m['created_at'].startswith(today))
    
    conn.close()
    
    return render_template('admin/messages.html', 
                         messages=messages,
                         total_messages=total_messages,
                         unread_messages=unread_messages,
                         read_messages=read_messages,
                         today_messages=today_messages)

@app.route('/admin/messages/view/<int:message_id>')
@admin_required
def view_message(message_id):
    conn = get_db_connection()
    message = conn.execute('''
        SELECT * FROM contact_messages 
        WHERE id = ?
    ''', (message_id,)).fetchone()
    
    # Mark as read when viewing
    if message and not message['is_read']:
        conn.execute('UPDATE contact_messages SET is_read = 1 WHERE id = ?', (message_id,))
        conn.commit()
    
    conn.close()
    
    if message:
        return render_template('admin/view_message.html', message=message)
    else:
        flash('Message not found!', 'error')
        return redirect(url_for('admin_messages'))

@app.route('/admin/messages/delete/<int:message_id>')
@admin_required
def delete_message(message_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM contact_messages WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()
    
    flash('Message deleted successfully!', 'success')
    return redirect(url_for('admin_messages'))

@app.route('/admin/messages/mark_read/<int:message_id>')
@admin_required
def mark_message_read(message_id):
    conn = get_db_connection()
    conn.execute('UPDATE contact_messages SET is_read = 1 WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()
    
    flash('Message marked as read!', 'success')
    return redirect(url_for('admin_messages'))

@app.route('/admin/messages/mark_unread/<int:message_id>')
@admin_required
def mark_message_unread(message_id):
    conn = get_db_connection()
    conn.execute('UPDATE contact_messages SET is_read = 0 WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()
    
    flash('Message marked as unread!', 'success')
    return redirect(url_for('admin_messages'))

# ========================= ADMIN DASHBOARD ==================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    
    # Get counts
    messages_count = conn.execute('SELECT COUNT(*) FROM contact_messages').fetchone()[0]
    schools_count = conn.execute('SELECT COUNT(*) FROM schools').fetchone()[0]
    
    # Get recent messages (last 5)
    recent_messages = conn.execute('''
        SELECT * FROM contact_messages 
        ORDER BY created_at DESC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         messages_count=messages_count,
                         schools_count=schools_count,
                         recent_messages=recent_messages)

# ========================= LOGOUT ==================
@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    # Create uploads directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)