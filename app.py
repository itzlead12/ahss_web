from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' 

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

    # try:
    #     c.execute("INSERT INTO admin_users (username, password) VALUES (?, ?)", 
    #              ('admin', 'admin123'))
    # except sqlite3.IntegrityError:
    #     pass  
    
    conn.commit()
    conn.close()

init_db()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    conn = sqlite3.connect('site.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():    
    return render_template('main/index.html')

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

# ========================= CONTACT MANAGEMENT ===========================================
# Contact Management Routes
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
    
    from datetime import datetime
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
    
    # Get messages count
    messages_count = conn.execute('SELECT COUNT(*) FROM contact_messages').fetchone()[0]
    
    # Get recent messages (last 5)
    recent_messages = conn.execute('''
        SELECT * FROM contact_messages 
        ORDER BY created_at DESC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         messages_count=messages_count,
                         recent_messages=recent_messages)

# ========================= LOGOUT ==================
@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin_login'))


#
if __name__ == '__main__':
    app.run(debug=True)