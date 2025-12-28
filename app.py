from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
from functools import wraps
import os
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  
    'database': 'research_hub_db',
    'charset': 'utf8mb4'
}

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    """Create and return a database connection"""
    return mysql.connector.connect(**DB_CONFIG)

def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يرجى تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] != role_name:
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'Admin':
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============= Authentication Routes =============

@app.route('/')
def index():
    """Redirect to login page"""
    if 'user_id' in session:
        # إذا كان المستخدم مسجل دخول، توجيهه حسب دوره
        if session['role'] == 'Supervisor':
            return redirect(url_for('supervisor_dashboard'))
        elif session['role'] == 'DepartmentHead':
            return redirect(url_for('department_head_dashboard'))
        elif session['role'] == 'Admin':
            return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT u.*, r.RoleName 
            FROM Users u
            JOIN Roles r ON u.RoleID = r.RoleID
            WHERE u.Username = %s AND u.Password = %s AND u.IsActive = TRUE
        """, (username, password))
        
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user['UserID']
            session['username'] = user['Username']
            session['role'] = user['RoleName']
            
            # Update last login
            cursor.execute("UPDATE Users SET LastLogin = %s WHERE UserID = %s", 
                         (datetime.now(), user['UserID']))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            flash('تم تسجيل الدخول بنجاح', 'success')
            
            # Redirect based on role
            if user['RoleName'] == 'Supervisor':
                return redirect(url_for('supervisor_dashboard'))
            elif user['RoleName'] == 'DepartmentHead':
                return redirect(url_for('department_head_dashboard'))
            else:
                return redirect(url_for('home'))
        else:
            cursor.close()
            conn.close()
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """Register new user - public registration only allows Researcher role"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role_id = int(request.form['role_id'])
        
        is_admin = session.get('role') == 'Admin'
        
        # إذا لم يكن المستخدم مدير نظام ويحاول إنشاء حساب بصلاحيات خاصة
        if not is_admin and role_id != 4:  # 4 = Researcher
            cursor.execute("SELECT RoleName FROM Roles WHERE RoleID = %s", (role_id,))
            role = cursor.fetchone()
            role_name = role['RoleName'] if role else 'غير معروف'
            flash(f'ليس لديك صلاحية لإنشاء حساب من نوع "{role_name}". يمكنك فقط إنشاء حساب باحث.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('register_user'))
        
        # Check if username already exists
        cursor.execute("SELECT UserID FROM Users WHERE Username = %s", (username,))
        if cursor.fetchone():
            flash('اسم المستخدم موجود بالفعل', 'danger')
        else:
            cursor.execute("""
                INSERT INTO Users (Username, Password, RoleID, IsActive)
                VALUES (%s, %s, %s, TRUE)
            """, (username, password, role_id))
            
            conn.commit()
            flash('تم إنشاء المستخدم بنجاح! يمكنك الآن تسجيل الدخول', 'success')
            cursor.close()
            conn.close()
            
            # إذا كان المستخدم مدير، العودة لصفحة إدارة المستخدمين
            if is_admin:
                return redirect(url_for('manage_users'))
            else:
                return redirect(url_for('login'))
    
    # GET request - show form
    cursor.execute("SELECT RoleID, RoleName FROM Roles ORDER BY RoleName")
    all_roles = cursor.fetchall()
    
    is_admin = session.get('role') == 'Admin'
    if is_admin:
        roles = all_roles  # المدير يرى جميع الأدوار
    else:
        roles = [r for r in all_roles if r['RoleID'] == 4]  # غير المدير يرى فقط دور الباحث
    
    cursor.close()
    conn.close()
    
    return render_template('register.html', roles=roles, is_admin=is_admin)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if request.method == 'POST':
        username = request.form['username']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # التحقق من وجود المستخدم
        cursor.execute("SELECT UserID, Username FROM Users WHERE Username = %s", (username,))
        user = cursor.fetchone()
        
        if user:
            # إنشاء رمز آمن
            token = secrets.token_urlsafe(32)
            expiry_date = datetime.now() + timedelta(hours=1)  # صالح لمدة ساعة
            
            # حفظ الرمز في قاعدة البيانات
            cursor.execute("""
                INSERT INTO PasswordResetTokens (UserID, Token, ExpiryDate)
                VALUES (%s, %s, %s)
            """, (user['UserID'], token, expiry_date))
            
            conn.commit()
            
            # في نظام حقيقي، سيتم إرسال الرابط عبر البريد الإلكتروني
            # هنا سنعرض الرابط مباشرة للمستخدم
            reset_link = url_for('reset_password', token=token, _external=True)
            
            cursor.close()
            conn.close()
            
            flash(f'تم إنشاء رابط إعادة تعيين كلمة المرور. الرابط: {reset_link}', 'success')
            return render_template('forgot_password.html', reset_link=reset_link, show_link=True)
        else:
            cursor.close()
            conn.close()
            flash('اسم المستخدم غير موجود', 'danger')
    
    return render_template('forgot_password.html', show_link=False)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password page"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # التحقق من صلاحية الرمز
    cursor.execute("""
        SELECT prt.*, u.Username
        FROM PasswordResetTokens prt
        JOIN Users u ON prt.UserID = u.UserID
        WHERE prt.Token = %s AND prt.IsUsed = FALSE AND prt.ExpiryDate > %s
    """, (token, datetime.now()))
    
    token_data = cursor.fetchone()
    
    if not token_data:
        cursor.close()
        conn.close()
        flash('الرابط غير صالح أو منتهي الصلاحية', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('كلمتا المرور غير متطابقتين', 'danger')
        else:
            # تحديث كلمة المرور
            cursor.execute("""
                UPDATE Users SET Password = %s WHERE UserID = %s
            """, (new_password, token_data['UserID']))
            
            # تعليم الرمز كمستخدم
            cursor.execute("""
                UPDATE PasswordResetTokens SET IsUsed = TRUE WHERE TokenID = %s
            """, (token_data['TokenID'],))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('تم تغيير كلمة المرور بنجاح! يمكنك الآن تسجيل الدخول', 'success')
            return redirect(url_for('login'))
    
    cursor.close()
    conn.close()
    
    return render_template('reset_password.html', token=token, username=token_data['Username'])

# ============= Public Routes =============

@app.route('/home')
@login_required
def home():
    """Home page with search bar and statistics"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) as total_papers FROM ResearchPapers")
    total_papers = cursor.fetchone()['total_papers']
    
    cursor.execute("SELECT COUNT(*) as total_supervisors FROM Supervisors")
    total_supervisors = cursor.fetchone()['total_supervisors']
    
    cursor.close()
    conn.close()
    
    return render_template('home.html', 
                         total_papers=total_papers, 
                         total_supervisors=total_supervisors)

@app.route('/search')
@login_required
def search():
    """Search results page"""
    query = request.args.get('q', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    sql = """
        SELECT 
            rp.PaperID, rp.Title, rp.PublicationYear,
            CONCAT(s.FirstName, ' ', s.LastName) as StudentName,
            CONCAT(sup.FirstName, ' ', sup.LastName) as SupervisorName,
            d.DepartmentName
        FROM ResearchPapers rp
        JOIN Students s ON rp.StudentID = s.StudentID
        JOIN Supervisors sup ON rp.SupervisorID = sup.SupervisorID
        JOIN Departments d ON rp.DepartmentID = d.DepartmentID
        WHERE rp.Title LIKE %s OR rp.Abstract LIKE %s
        ORDER BY rp.PublicationYear DESC
    """
    
    search_term = f'%{query}%'
    cursor.execute(sql, (search_term, search_term))
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('search_results.html', results=results, query=query)

@app.route('/research/<int:paper_id>')
@login_required
def research_details(paper_id):
    """Research details page"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get paper details
    sql = """
        SELECT 
            rp.*,
            CONCAT(s.FirstName, ' ', s.LastName) as StudentName,
            s.Email as StudentEmail,
            CONCAT(sup.FirstName, ' ', sup.LastName) as SupervisorName,
            sup.Email as SupervisorEmail,
            sup.AcademicRank,
            d.DepartmentName,
            d.Faculty
        FROM ResearchPapers rp
        JOIN Students s ON rp.StudentID = s.StudentID
        JOIN Supervisors sup ON rp.SupervisorID = sup.SupervisorID
        JOIN Departments d ON rp.DepartmentID = d.DepartmentID
        WHERE rp.PaperID = %s
    """
    
    cursor.execute(sql, (paper_id,))
    paper = cursor.fetchone()
    
    if not paper:
        cursor.close()
        conn.close()
        flash('البحث غير موجود', 'danger')
        return redirect(url_for('home'))
    
    # Get topics
    cursor.execute("""
        SELECT t.TopicName
        FROM Research_Topics rt
        JOIN Topics t ON rt.TopicID = t.TopicID
        WHERE rt.PaperID = %s
    """, (paper_id,))
    
    topics = [row['TopicName'] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return render_template('research_details.html', paper=paper, topics=topics)

@app.route('/advanced-search')
@login_required
def advanced_search():
    """Advanced search page"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all supervisors for dropdown
    cursor.execute("SELECT SupervisorID, CONCAT(FirstName, ' ', LastName) as Name FROM Supervisors ORDER BY FirstName")
    supervisors = cursor.fetchall()
    
    # Get all departments for dropdown
    cursor.execute("SELECT DepartmentID, DepartmentName FROM Departments ORDER BY DepartmentName")
    departments = cursor.fetchall()
    
    # Get all topics for dropdown
    cursor.execute("SELECT TopicID, TopicName FROM Topics ORDER BY TopicName")
    topics = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('advanced_search.html', 
                         supervisors=supervisors, 
                         departments=departments,
                         topics=topics)

@app.route('/advanced-search-results')
@login_required
def advanced_search_results():
    """Process advanced search"""
    title = request.args.get('title', '')
    supervisor_id = request.args.get('supervisor_id', '')
    department_id = request.args.get('department_id', '')
    year = request.args.get('year', '')
    topic_id = request.args.get('topic_id', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Build dynamic query
    sql = """
        SELECT DISTINCT
            rp.PaperID, rp.Title, rp.PublicationYear,
            CONCAT(s.FirstName, ' ', s.LastName) as StudentName,
            CONCAT(sup.FirstName, ' ', sup.LastName) as SupervisorName,
            d.DepartmentName
        FROM ResearchPapers rp
        JOIN Students s ON rp.StudentID = s.StudentID
        JOIN Supervisors sup ON rp.SupervisorID = sup.SupervisorID
        JOIN Departments d ON rp.DepartmentID = d.DepartmentID
        LEFT JOIN Research_Topics rt ON rp.PaperID = rt.PaperID
        WHERE 1=1
    """
    
    params = []
    
    if title:
        sql += " AND rp.Title LIKE %s"
        params.append(f'%{title}%')
    
    if supervisor_id:
        sql += " AND rp.SupervisorID = %s"
        params.append(supervisor_id)
    
    if department_id:
        sql += " AND rp.DepartmentID = %s"
        params.append(department_id)
    
    if year:
        sql += " AND rp.PublicationYear = %s"
        params.append(year)
    
    if topic_id:
        sql += " AND rt.TopicID = %s"
        params.append(topic_id)
    
    sql += " ORDER BY rp.PublicationYear DESC"
    
    cursor.execute(sql, params)
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('search_results.html', results=results, query='بحث متقدم')

# ============= Admin Routes =============

@app.route('/admin/users')
@login_required
@admin_required
def manage_users():
    """Manage users page (Admin only)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT u.UserID, u.Username, r.RoleName, u.IsActive, u.LastLogin
        FROM Users u
        JOIN Roles r ON u.RoleID = r.RoleID
        ORDER BY u.UserID DESC
    """)
    
    users = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('manage_users.html', users=users)

@app.route('/admin/users/toggle/<int:user_id>')
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("UPDATE Users SET IsActive = NOT IsActive WHERE UserID = %s", (user_id,))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    flash('تم تحديث حالة المستخدم بنجاح', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/users/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    """Delete user"""
    if user_id == session.get('user_id'):
        flash('لا يمكنك حذف حسابك الخاص', 'danger')
        return redirect(url_for('manage_users'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("DELETE FROM Users WHERE UserID = %s", (user_id,))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    flash('تم حذف المستخدم بنجاح', 'success')
    return redirect(url_for('manage_users'))

# ============= Supervisor Routes =============

@app.route('/supervisor/dashboard')
@login_required
@role_required('Supervisor')
def supervisor_dashboard():
    """Supervisor dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get supervisor info - try to find by matching username pattern
    cursor.execute("""
        SELECT s.*, d.DepartmentName
        FROM Supervisors s
        JOIN Departments d ON s.DepartmentID = d.DepartmentID
        WHERE s.Email LIKE CONCAT('%', %s, '%')
        OR CONCAT(s.FirstName, '.', s.LastName) = %s
        OR CONCAT(s.FirstName, s.LastName) = %s
        LIMIT 1
    """, (session['username'], session['username'], session['username'].replace('.', '')))
    
    supervisor = cursor.fetchone()
    
    if not supervisor:
        cursor.close()
        conn.close()
        flash('لم يتم العثور على بيانات المشرف', 'danger')
        return redirect(url_for('login'))
    
    # Get supervisor's papers
    cursor.execute("""
        SELECT 
            rp.PaperID, rp.Title, rp.PublicationYear,
            CONCAT(s.FirstName, ' ', s.LastName) as StudentName
        FROM ResearchPapers rp
        JOIN Students s ON rp.StudentID = s.StudentID
        WHERE rp.SupervisorID = %s
        ORDER BY rp.PublicationYear DESC
    """, (supervisor['SupervisorID'],))
    
    papers = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('supervisor_dashboard.html', 
                         supervisor=supervisor, 
                         papers=papers)

@app.route('/supervisor/add-research', methods=['GET', 'POST'])
@login_required
@role_required('Supervisor')
def add_research():
    """Add new research"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        title = request.form['title']
        abstract = request.form['abstract']
        year = request.form['year']
        student_id = request.form['student_id']
        department_id = request.form['department_id']
        topics = request.form.getlist('topics')
        
        # Get supervisor ID
        cursor.execute("""
            SELECT s.SupervisorID
            FROM Supervisors s
            WHERE s.Email LIKE CONCAT('%', %s, '%')
            OR CONCAT(s.FirstName, '.', s.LastName) = %s
            OR CONCAT(s.FirstName, s.LastName) = %s
            LIMIT 1
        """, (session['username'], session['username'], session['username'].replace('.', '')))
        
        supervisor = cursor.fetchone()
        
        if not supervisor:
            flash('خطأ في تحديد المشرف', 'danger')
            return redirect(url_for('supervisor_dashboard'))
        
        # Handle file upload
        file_path = None
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
        
        # Insert research paper
        cursor.execute("""
            INSERT INTO ResearchPapers 
            (Title, Abstract, PublicationYear, FilePath, StudentID, SupervisorID, DepartmentID)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (title, abstract, year, file_path, student_id, supervisor['SupervisorID'], department_id))
        
        paper_id = cursor.lastrowid
        
        # Insert topics
        for topic_id in topics:
            if topic_id:
                cursor.execute("""
                    INSERT INTO Research_Topics (PaperID, TopicID)
                    VALUES (%s, %s)
                """, (paper_id, topic_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('تم إضافة البحث بنجاح', 'success')
        return redirect(url_for('supervisor_dashboard'))
    
    # GET request - show form
    cursor.execute("SELECT StudentID, CONCAT(FirstName, ' ', LastName) as Name FROM Students ORDER BY FirstName")
    students = cursor.fetchall()
    
    cursor.execute("SELECT DepartmentID, DepartmentName FROM Departments ORDER BY DepartmentName")
    departments = cursor.fetchall()
    
    cursor.execute("SELECT TopicID, TopicName FROM Topics ORDER BY TopicName")
    topics = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('add_edit_research.html', 
                         students=students, 
                         departments=departments,
                         topics=topics,
                         mode='add')

@app.route('/supervisor/edit-research/<int:paper_id>', methods=['GET', 'POST'])
@login_required
@role_required('Supervisor')
def edit_research(paper_id):
    """Edit existing research"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verify ownership
    cursor.execute("""
        SELECT s.SupervisorID
        FROM Supervisors s
        WHERE s.Email LIKE CONCAT('%', %s, '%')
        OR CONCAT(s.FirstName, '.', s.LastName) = %s
        OR CONCAT(s.FirstName, s.LastName) = %s
        LIMIT 1
    """, (session['username'], session['username'], session['username'].replace('.', '')))
    
    supervisor = cursor.fetchone()
    
    if request.method == 'POST':
        title = request.form['title']
        abstract = request.form['abstract']
        year = request.form['year']
        student_id = request.form['student_id']
        department_id = request.form['department_id']
        topics = request.form.getlist('topics')
        
        # Handle file upload
        file_path = request.form.get('existing_file_path')
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
        
        # Update research paper
        cursor.execute("""
            UPDATE ResearchPapers 
            SET Title = %s, Abstract = %s, PublicationYear = %s, 
                FilePath = %s, StudentID = %s, DepartmentID = %s
            WHERE PaperID = %s AND SupervisorID = %s
        """, (title, abstract, year, file_path, student_id, department_id, paper_id, supervisor['SupervisorID']))
        
        # Delete old topics
        cursor.execute("DELETE FROM Research_Topics WHERE PaperID = %s", (paper_id,))
        
        # Insert new topics
        for topic_id in topics:
            if topic_id:
                cursor.execute("""
                    INSERT INTO Research_Topics (PaperID, TopicID)
                    VALUES (%s, %s)
                """, (paper_id, topic_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('تم تحديث البحث بنجاح', 'success')
        return redirect(url_for('supervisor_dashboard'))
    
    # GET request - show form with existing data
    cursor.execute("""
        SELECT * FROM ResearchPapers 
        WHERE PaperID = %s AND SupervisorID = %s
    """, (paper_id, supervisor['SupervisorID']))
    
    paper = cursor.fetchone()
    
    if not paper:
        cursor.close()
        conn.close()
        flash('البحث غير موجود أو ليس لديك صلاحية لتعديله', 'danger')
        return redirect(url_for('supervisor_dashboard'))
    
    cursor.execute("SELECT StudentID, CONCAT(FirstName, ' ', LastName) as Name FROM Students ORDER BY FirstName")
    students = cursor.fetchall()
    
    cursor.execute("SELECT DepartmentID, DepartmentName FROM Departments ORDER BY DepartmentName")
    departments = cursor.fetchall()
    
    cursor.execute("SELECT TopicID, TopicName FROM Topics ORDER BY TopicName")
    all_topics = cursor.fetchall()
    
    cursor.execute("SELECT TopicID FROM Research_Topics WHERE PaperID = %s", (paper_id,))
    selected_topics = [row['TopicID'] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return render_template('add_edit_research.html', 
                         paper=paper,
                         students=students, 
                         departments=departments,
                         topics=all_topics,
                         selected_topics=selected_topics,
                         mode='edit')

@app.route('/supervisor/delete-research/<int:paper_id>')
@login_required
@role_required('Supervisor')
def delete_research(paper_id):
    """Delete research"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verify ownership
    cursor.execute("""
        SELECT s.SupervisorID
        FROM Supervisors s
        WHERE s.Email LIKE CONCAT('%', %s, '%')
        OR CONCAT(s.FirstName, '.', s.LastName) = %s
        OR CONCAT(s.FirstName, s.LastName) = %s
        LIMIT 1
    """, (session['username'], session['username'], session['username'].replace('.', '')))
    
    supervisor = cursor.fetchone()
    
    cursor.execute("""
        DELETE FROM ResearchPapers 
        WHERE PaperID = %s AND SupervisorID = %s
    """, (paper_id, supervisor['SupervisorID']))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('تم حذف البحث بنجاح', 'success')
    return redirect(url_for('supervisor_dashboard'))

# ============= Department Head Routes =============

@app.route('/department-head/dashboard')
@login_required
@role_required('DepartmentHead')
def department_head_dashboard():
    """Department head dashboard with analytics"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get department head info
    cursor.execute("""
        SELECT s.*, d.DepartmentID, d.DepartmentName
        FROM Supervisors s
        JOIN Departments d ON s.DepartmentID = d.DepartmentID
        WHERE s.Email LIKE CONCAT('%', %s, '%')
        OR CONCAT(s.FirstName, '.', s.LastName) = %s
        OR CONCAT(s.FirstName, s.LastName) = %s
        LIMIT 1
    """, (session['username'], session['username'], session['username'].replace('.', '')))
    
    dept_head = cursor.fetchone()
    
    if not dept_head:
        cursor.close()
        conn.close()
        flash('لم يتم العثور على بيانات رئيس القسم', 'danger')
        return redirect(url_for('login'))
    
    # Get papers count per supervisor in department
    cursor.execute("""
        SELECT 
            CONCAT(sup.FirstName, ' ', sup.LastName) as SupervisorName,
            COUNT(rp.PaperID) as PaperCount
        FROM Supervisors sup
        LEFT JOIN ResearchPapers rp ON sup.SupervisorID = rp.SupervisorID
        WHERE sup.DepartmentID = %s
        GROUP BY sup.SupervisorID, sup.FirstName, sup.LastName
        ORDER BY PaperCount DESC
    """, (dept_head['DepartmentID'],))
    
    supervisor_stats = cursor.fetchall()
    
    # Get top 5 topics in department
    cursor.execute("""
        SELECT 
            t.TopicName,
            COUNT(rt.PaperID) as TopicCount
        FROM Topics t
        JOIN Research_Topics rt ON t.TopicID = rt.TopicID
        JOIN ResearchPapers rp ON rt.PaperID = rp.PaperID
        WHERE rp.DepartmentID = %s
        GROUP BY t.TopicID, t.TopicName
        ORDER BY TopicCount DESC
        LIMIT 5
    """, (dept_head['DepartmentID'],))
    
    topic_stats = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('department_head_dashboard.html', 
                         dept_head=dept_head,
                         supervisor_stats=supervisor_stats,
                         topic_stats=topic_stats)

@app.route('/download/<int:paper_id>')
def download_file(paper_id):
    """Download research file"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT FilePath, Title FROM ResearchPapers WHERE PaperID = %s", (paper_id,))
    paper = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if paper and paper['FilePath'] and os.path.exists(paper['FilePath']):
        return send_file(paper['FilePath'], as_attachment=True)
    else:
        flash('الملف غير موجود', 'danger')
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)