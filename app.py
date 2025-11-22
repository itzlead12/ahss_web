from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' 

app.config['UPLOAD_FOLDER'] = 'static/uploads/schools'
app.config['UPLOAD_FOLDER_EVENTS'] = 'static/uploads/events'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg','webp'}

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
    
    c.execute('''CREATE TABLE IF NOT EXISTS schools
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                logo_filename TEXT,
                website_link TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS events
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            event_date DATE NOT NULL,
            event_type TEXT NOT NULL, -- 'upcoming' or 'past'
            registration_link TEXT,
            image_filenames TEXT, -- JSON string of uploaded image filenames
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS team_members
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT NOT NULL,
            description TEXT NOT NULL,
            image_filename TEXT,
            social_links TEXT, -- JSON string for multiple social links
            display_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Hero Section Table
    c.execute('''CREATE TABLE IF NOT EXISTS hero_section
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                agency_name TEXT NOT NULL,
                main_title TEXT NOT NULL,
                description TEXT NOT NULL,
                button_text TEXT NOT NULL,
                image_filename TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # About Section Table
    c.execute('''CREATE TABLE IF NOT EXISTS about_section
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                main_title TEXT NOT NULL,
                lead_text TEXT NOT NULL,
                description TEXT NOT NULL,
                image_filename TEXT,
                feature1_title TEXT NOT NULL,
                feature1_description TEXT NOT NULL,
                feature2_title TEXT NOT NULL,
                feature2_description TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Footer Section Table
    c.execute('''CREATE TABLE IF NOT EXISTS footer_section
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                instagram_url TEXT,
                telegram_url TEXT,
                youtube_url TEXT,
                tiktok_url TEXT,
                contact_email TEXT,
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
    
    # Dynamic sections
    hero = conn.execute('SELECT * FROM hero_section WHERE is_active = 1').fetchone()
    about = conn.execute('SELECT * FROM about_section WHERE is_active = 1').fetchone()
    footer = conn.execute('SELECT * FROM footer_section WHERE is_active = 1').fetchone()
    
    # Existing dynamic content
    schools = conn.execute('SELECT * FROM schools WHERE is_active = 1 ORDER BY created_at DESC').fetchall()
    events = conn.execute('SELECT * FROM events WHERE is_active = 1 ORDER BY event_date DESC').fetchall()
    team_members = conn.execute('SELECT * FROM team_members WHERE is_active = 1 ORDER BY display_order ASC, created_at DESC').fetchall()
    
    conn.close()
    
    # Process events
    processed_events = []
    for event in events:
        event_dict = dict(event)
        if event_dict['image_filenames'] and event_dict['image_filenames'] != '[]':
            try:
                filenames_str = event_dict['image_filenames'].strip('[]').replace("'", "").replace('"', '')
                event_dict['processed_images'] = [f.strip() for f in filenames_str.split(',') if f.strip()]
            except:
                event_dict['processed_images'] = []
        else:
            event_dict['processed_images'] = []
        processed_events.append(event_dict)
    
    return render_template('main/index.html', 
                         hero=hero,
                         about=about, 
                         footer=footer,
                         schools=schools, 
                         events=processed_events,
                         team_members=team_members)
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

# ========================= HERO SECTION MANAGEMENT ==================

@app.route('/admin/hero', methods=['GET', 'POST'])
@admin_required
def admin_hero():
    conn = get_db_connection()
    
    if request.method == 'POST':
        agency_name = request.form['agency_name']
        main_title = request.form['main_title']
        description = request.form['description']
        button_text = request.form['button_text']
        
        # Handle image upload
        image_filename = None
        if 'hero_image' in request.files:
            file = request.files['hero_image']
            if file and file.filename != '' and allowed_file(file.filename):
                os.makedirs('static/uploads/hero', exist_ok=True)
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                filename = timestamp + filename
                file.save(os.path.join('static/uploads/hero', filename))
                image_filename = filename
        
        # Check if hero section exists
        existing_hero = conn.execute('SELECT * FROM hero_section').fetchone()
        
        if existing_hero:
            # Update existing
            conn.execute('''UPDATE hero_section SET 
                          agency_name = ?, main_title = ?, description = ?, 
                          button_text = ?, image_filename = ?, updated_at = CURRENT_TIMESTAMP 
                          WHERE id = ?''',
                       (agency_name, main_title, description, button_text, image_filename, existing_hero['id']))
        else:
            # Insert new
            conn.execute('''INSERT INTO hero_section 
                          (agency_name, main_title, description, button_text, image_filename) 
                          VALUES (?, ?, ?, ?, ?)''',
                       (agency_name, main_title, description, button_text, image_filename))
        
        conn.commit()
        conn.close()
        flash('Hero section updated successfully!', 'success')
        return redirect(url_for('admin_hero'))
    
    # GET request - fetch current hero data
    hero = conn.execute('SELECT * FROM hero_section').fetchone()
    conn.close()
    
    return render_template('admin/hero.html', hero=hero)

# ========================= ABOUT SECTION MANAGEMENT ==================

@app.route('/admin/about', methods=['GET', 'POST'])
@admin_required
def admin_about():
    conn = get_db_connection()
    
    if request.method == 'POST':
        main_title = request.form['main_title']
        lead_text = request.form['lead_text']
        description = request.form['description']
        feature1_title = request.form['feature1_title']
        feature1_description = request.form['feature1_description']
        feature2_title = request.form['feature2_title']
        feature2_description = request.form['feature2_description']
        
        # Handle image upload
        image_filename = None
        if 'about_image' in request.files:
            file = request.files['about_image']
            if file and file.filename != '' and allowed_file(file.filename):
                os.makedirs('static/uploads/about', exist_ok=True)
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                filename = timestamp + filename
                file.save(os.path.join('static/uploads/about', filename))
                image_filename = filename
        
        # Check if about section exists
        existing_about = conn.execute('SELECT * FROM about_section').fetchone()
        
        if existing_about:
            # Update existing
            conn.execute('''UPDATE about_section SET 
                          main_title = ?, lead_text = ?, description = ?, image_filename = ?,
                          feature1_title = ?, feature1_description = ?,
                          feature2_title = ?, feature2_description = ?, updated_at = CURRENT_TIMESTAMP 
                          WHERE id = ?''',
                       (main_title, lead_text, description, image_filename,
                        feature1_title, feature1_description,
                        feature2_title, feature2_description, existing_about['id']))
        else:
            # Insert new
            conn.execute('''INSERT INTO about_section 
                          (main_title, lead_text, description, image_filename,
                           feature1_title, feature1_description, feature2_title, feature2_description) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                       (main_title, lead_text, description, image_filename,
                        feature1_title, feature1_description, feature2_title, feature2_description))
        
        conn.commit()
        conn.close()
        flash('About section updated successfully!', 'success')
        return redirect(url_for('admin_about'))
    
    # GET request - fetch current about data
    about = conn.execute('SELECT * FROM about_section').fetchone()
    conn.close()
    
    return render_template('admin/about.html', about=about)

# ========================= FOOTER SECTION MANAGEMENT ==================

@app.route('/admin/footer', methods=['GET', 'POST'])
@admin_required
def admin_footer():
    conn = get_db_connection()
    
    if request.method == 'POST':
        description = request.form['description']
        instagram_url = request.form['instagram_url']
        telegram_url = request.form['telegram_url']
        youtube_url = request.form['youtube_url']
        tiktok_url = request.form['tiktok_url']
        contact_email = request.form['contact_email']
        
        # Check if footer section exists
        existing_footer = conn.execute('SELECT * FROM footer_section').fetchone()
        
        if existing_footer:
            # Update existing
            conn.execute('''UPDATE footer_section SET 
                          description = ?, instagram_url = ?, telegram_url = ?, 
                          youtube_url = ?, tiktok_url = ?, contact_email = ?, updated_at = CURRENT_TIMESTAMP 
                          WHERE id = ?''',
                       (description, instagram_url, telegram_url, youtube_url, tiktok_url, contact_email, existing_footer['id']))
        else:
            # Insert new
            conn.execute('''INSERT INTO footer_section 
                          (description, instagram_url, telegram_url, youtube_url, tiktok_url, contact_email) 
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (description, instagram_url, telegram_url, youtube_url, tiktok_url, contact_email))
        
        conn.commit()
        conn.close()
        flash('Footer section updated successfully!', 'success')
        return redirect(url_for('admin_footer'))
    
    # GET request - fetch current footer data
    footer = conn.execute('SELECT * FROM footer_section').fetchone()
    conn.close()
    
    return render_template('admin/footer.html', footer=footer)


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
        conn.execute('''INSERT INTO schools (name, description, logo_filename, website_link) 
                        VALUES (?, ?, ?, ?)''', 
                    (name, description, logo_filename, website_link))
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
                        is_active = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?''',
                    (name, description, logo_filename, website_link, is_active, school_id))
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

@app.route('/admin/schools/toggle-status/<int:school_id>', methods=['POST'])
@admin_required
def toggle_school_status(school_id):
    conn = get_db_connection()
    
    # Get current school status
    school = conn.execute('SELECT name, is_active FROM schools WHERE id = ?', (school_id,)).fetchone()
    
    if not school:
        flash('School not found!', 'error')
        return redirect(url_for('admin_schools'))
    
    # Toggle the status
    new_status = not school['is_active']
    
    conn.execute('UPDATE schools SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (new_status, school_id))
    conn.commit()
    conn.close()
    
    status_text = "activated" if new_status else "deactivated"
    flash(f"School '{school['name']}' has been {status_text}!", 'success')
    return redirect(url_for('admin_schools'))


# ========================= TEAM MANAGEMENT ==================

@app.route('/admin/team')
@admin_required
def admin_team():
    conn = get_db_connection()
    team_members = conn.execute('''
        SELECT * FROM team_members 
        ORDER BY display_order ASC, created_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template('admin/team.html', team_members=team_members)

@app.route('/admin/team/new', methods=['GET', 'POST'])
@admin_required
def new_team_member():
    if request.method == 'POST':
        name = request.form['name']
        position = request.form['position']
        description = request.form['description']
        display_order = request.form.get('display_order', 0)
        
        # Handle file upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                os.makedirs('static/uploads/team', exist_ok=True)
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                filename = timestamp + filename
                file.save(os.path.join('static/uploads/team', filename))
                image_filename = filename
        
        conn = get_db_connection()
        conn.execute('''INSERT INTO team_members 
                        (name, position, description, image_filename, display_order) 
                        VALUES (?, ?, ?, ?, ?)''',
                    (name, position, description, image_filename, display_order))
        conn.commit()
        conn.close()
        
        flash('Team member added successfully!', 'success')
        return redirect(url_for('admin_team'))
    
    return render_template('admin/new_team_member.html')

@app.route('/admin/team/edit/<int:member_id>', methods=['GET', 'POST'])
@admin_required
def edit_team_member(member_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        position = request.form['position']
        description = request.form['description']
        display_order = request.form.get('display_order', 0)
        is_active = 'is_active' in request.form
        remove_image = 'remove_image' in request.form
        
        # Get current member data
        current_member = conn.execute('SELECT image_filename FROM team_members WHERE id = ?', (member_id,)).fetchone()
        
        # Handle file upload/removal
        image_filename = current_member['image_filename']
        
        if remove_image and image_filename:
            try:
                os.remove(os.path.join('static/uploads/team', image_filename))
            except:
                pass
            image_filename = None
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                os.makedirs('static/uploads/team', exist_ok=True)
                
                # Remove old image if exists
                if image_filename:
                    try:
                        os.remove(os.path.join('static/uploads/team', image_filename))
                    except:
                        pass
                
                # Save new image
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                filename = timestamp + filename
                file.save(os.path.join('static/uploads/team', filename))
                image_filename = filename
        
        conn.execute('''UPDATE team_members SET 
                        name = ?, position = ?, description = ?, image_filename = ?, 
                        display_order = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?''',
                    (name, position, description, image_filename, display_order, is_active, member_id))
        conn.commit()
        conn.close()
        
        flash('Team member updated successfully!', 'success')
        return redirect(url_for('admin_team'))
    
    member = conn.execute('SELECT * FROM team_members WHERE id = ?', (member_id,)).fetchone()
    conn.close()
    
    if not member:
        flash('Team member not found!', 'error')
        return redirect(url_for('admin_team'))
    
    return render_template('admin/edit_team_member.html', member=member)

@app.route('/admin/team/delete/<int:member_id>')
@admin_required
def delete_team_member(member_id):
    conn = get_db_connection()
    
    # Get member image filename before deletion
    member = conn.execute('SELECT image_filename FROM team_members WHERE id = ?', (member_id,)).fetchone()
    
    # Delete the image file if exists
    if member and member['image_filename']:
        try:
            os.remove(os.path.join('static/uploads/team', member['image_filename']))
        except:
            pass
    
    conn.execute('DELETE FROM team_members WHERE id = ?', (member_id,))
    conn.commit()
    conn.close()
    
    flash('Team member deleted successfully!', 'success')
    return redirect(url_for('admin_team'))

@app.route('/admin/team/toggle-status/<int:member_id>', methods=['POST'])
@admin_required
def toggle_team_member_status(member_id):
    conn = get_db_connection()
    
    # Get current member status
    member = conn.execute('SELECT name, is_active FROM team_members WHERE id = ?', (member_id,)).fetchone()
    
    if not member:
        flash('Team member not found!', 'error')
        return redirect(url_for('admin_team'))
    
    # Toggle the status
    new_status = not member['is_active']
    
    conn.execute('UPDATE team_members SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (new_status, member_id))
    conn.commit()
    conn.close()
    
    status_text = "activated" if new_status else "deactivated"
    flash(f"Team member '{member['name']}' has been {status_text}!", 'success')
    return redirect(url_for('admin_team'))


# ========================= EVENTS MANAGEMENT ==================

@app.route('/admin/events')
@admin_required
def admin_events():
    conn = get_db_connection()
    events = conn.execute('SELECT * FROM events ORDER BY event_date DESC').fetchall()
    conn.close()
    
    # Process image filenames for the template
    processed_events = []
    for event in events:
        event_dict = dict(event)
        # Safely parse the image_filenames string
        if event_dict['image_filenames'] and event_dict['image_filenames'] != '[]':
            try:
                # Remove brackets and quotes, then split
                filenames_str = event_dict['image_filenames'].strip('[]').replace("'", "").replace('"', '')
                image_filenames = [f.strip() for f in filenames_str.split(',') if f.strip()]
                event_dict['image_count'] = len(image_filenames)
            except:
                event_dict['image_count'] = 0
        else:
            event_dict['image_count'] = 0
        processed_events.append(event_dict)
    
    return render_template('admin/events.html', events=processed_events)

@app.route('/admin/events/new', methods=['GET', 'POST'])
@admin_required
def new_event():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        event_date = request.form['event_date']
        event_type = request.form['event_type']
        registration_link = request.form['registration_link']
        # gallery_link removed
        
        # Handle multiple file uploads
        image_filenames = []
        if 'event_images' in request.files:
            files = request.files.getlist('event_images')
            for file in files:
                if file and file.filename != '' and allowed_file(file.filename):
                    # Create uploads directory if it doesn't exist
                    os.makedirs(app.config['UPLOAD_FOLDER_EVENTS'], exist_ok=True)
                    
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                    filename = timestamp + filename
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_EVENTS'], filename))
                    image_filenames.append(filename)
        
        conn = get_db_connection()
        conn.execute('''INSERT INTO events (title, description, event_date, event_type, registration_link, image_filenames) 
                        VALUES (?, ?, ?, ?, ?, ?)''',  # 6 columns now
                    (title, description, event_date, event_type, registration_link, str(image_filenames)))  # 6 values
        conn.commit()
        conn.close()
        
        flash('Event added successfully!', 'success')
        return redirect(url_for('admin_events'))
    
    return render_template('admin/new_event.html')

@app.route('/admin/events/edit/<int:event_id>', methods=['GET', 'POST'])
@admin_required
def edit_event(event_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        event_date = request.form['event_date']
        event_type = request.form['event_type']
        registration_link = request.form['registration_link']
        is_active = 'is_active' in request.form
        remove_images = request.form.getlist('remove_images')
        
        # Get current event data
        current_event = conn.execute('SELECT image_filenames FROM events WHERE id = ?', (event_id,)).fetchone()
        
        # Handle image removal and new uploads
        current_images = []
        if current_event['image_filenames'] and current_event['image_filenames'] != '[]':
            try:
                filenames_str = current_event['image_filenames'].strip('[]').replace("'", "").replace('"', '')
                current_images = [f.strip() for f in filenames_str.split(',') if f.strip()]
            except:
                current_images = []
        
        # Remove selected images
        if remove_images:
            for filename in remove_images:
                if filename in current_images:
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER_EVENTS'], filename))
                    except:
                        pass
                    current_images.remove(filename)
        
        # Handle new file uploads
        if 'event_images' in request.files:
            files = request.files.getlist('event_images')
            for file in files:
                if file and file.filename != '' and allowed_file(file.filename):
                    os.makedirs(app.config['UPLOAD_FOLDER_EVENTS'], exist_ok=True)
                    
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                    filename = timestamp + filename
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_EVENTS'], filename))
                    current_images.append(filename)
        
        conn.execute('''UPDATE events SET 
                        title = ?, description = ?, event_date = ?, event_type = ?, 
                        registration_link = ?, image_filenames = ?, 
                        is_active = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?''',
                    (title, description, event_date, event_type, registration_link, 
                    str(current_images), is_active, event_id))
        conn.commit()
        conn.close()
        
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin_events'))
    
    event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
    conn.close()
    
    if not event:
        flash('Event not found!', 'error')
        return redirect(url_for('admin_events'))
    
    # Process image filenames for the template
    event_dict = dict(event)
    if event_dict['image_filenames'] and event_dict['image_filenames'] != '[]':
        try:
            filenames_str = event_dict['image_filenames'].strip('[]').replace("'", "").replace('"', '')
            event_dict['processed_images'] = [f.strip() for f in filenames_str.split(',') if f.strip()]
        except:
            event_dict['processed_images'] = []
    else:
        event_dict['processed_images'] = []
    
    return render_template('admin/edit_event.html', event=event_dict)

@app.route('/admin/events/delete/<int:event_id>')
@admin_required
def delete_event(event_id):
    conn = get_db_connection()
    
    # Get event images before deletion
    event = conn.execute('SELECT image_filenames FROM events WHERE id = ?', (event_id,)).fetchone()
    
    # Delete the image files if they exist
    if event and event['image_filenames']:
        image_filenames = eval(event['image_filenames'])
        for filename in image_filenames:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER_EVENTS'], filename))
            except:
                pass
    
    conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()
    
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('admin_events'))

@app.route('/admin/events/toggle-status/<int:event_id>', methods=['POST'])
@admin_required
def toggle_event_status(event_id):
    conn = get_db_connection()
    
    # Get current event status
    event = conn.execute('SELECT title, is_active FROM events WHERE id = ?', (event_id,)).fetchone()
    
    if not event:
        flash('Event not found!', 'error')
        return redirect(url_for('admin_events'))
    
    # Toggle the status
    new_status = not event['is_active']
    
    conn.execute('UPDATE events SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (new_status, event_id))
    conn.commit()
    conn.close()
    
    status_text = "activated" if new_status else "deactivated"
    flash(f"Event '{event['title']}' has been {status_text}!", 'success')
    return redirect(url_for('admin_events'))



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
    events_count = conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    upcoming_events_count = conn.execute('SELECT COUNT(*) FROM events WHERE event_type = "upcoming" AND is_active = 1').fetchone()[0]
    
    # Get recent messages (last 5)
    recent_messages = conn.execute('''
        SELECT * FROM contact_messages 
        ORDER BY created_at DESC 
        LIMIT 5
    ''').fetchall()
    
    # Get upcoming events (next 3)
    upcoming_events = conn.execute('''
        SELECT * FROM events 
        WHERE event_type = "upcoming" AND is_active = 1
        ORDER BY event_date ASC 
        LIMIT 3
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         messages_count=messages_count,
                         schools_count=schools_count,
                         events_count=events_count,
                         upcoming_events_count=upcoming_events_count,
                         recent_messages=recent_messages,
                         upcoming_events=upcoming_events)

# ========================= LOGOUT ==================
@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_EVENTS'], exist_ok=True)
    os.makedirs('static/uploads/team', exist_ok=True)
    app.run(debug=True)