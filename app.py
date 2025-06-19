from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Subject, Result, ResultItem
from utils import newPassword, checkPassword, save_image
from functools import wraps
import os
import datetime


app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static/uploads')

# --- Decorators ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'admin':
            flash("Admin access required.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# --- Routes ---

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# --- Register ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            roll_no = request.form['roll_no']
            password = newPassword(request.form['password'])
            image_file = request.files['image']
            filename = save_image(image_file, app.config['UPLOAD_FOLDER'])

            User.create(name=name, email=email, roll_no=roll_no, password=password, image=filename)
            flash("Registration successful!", "success")
            return redirect(url_for('login'))
        except:
            flash("User already exists or error occurred.", "danger")
    return render_template('register.html')

# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        entered_pass = request.form['password']
        try:
            user = User.get(User.email == email)
            if checkPassword(user.password, entered_pass):
                session['user_id'] = user.id
                session['user_type'] = user.user_type
                flash("Login successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Incorrect password.", "danger")
        except:
            flash("User not found.", "danger")
    return render_template('login.html')

# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

# --- Student Dashboard ---
@app.route('/dashboard')
@login_required
def dashboard():
    user = User.get_by_id(session['user_id'])
    results = Result.select().where(Result.student == user)
    return render_template('dashboard.html', user=user, results=results)

# --- Admin Dashboard ---
@app.route('/admin')
@admin_required
def admin_dashboard():
    subjects = Subject.select()
    students = User.select().where(User.user_type == 'user')
    return render_template('admin_dashboard.html', subjects=subjects, students=students)

# --- Add Subject ---
@app.route('/subjects/add', methods=['POST'])
@admin_required
def add_subject():
    sub_code = request.form['sub_code']
    sub_name = request.form['sub_name']
    try:
        Subject.create(sub_code=sub_code, sub_name=sub_name)
        flash("Subject added successfully.", "success")
    except:
        flash("Subject already exists or error occurred.", "danger")
    return redirect(url_for('admin_dashboard'))

# --- Delete Subject ---
@app.route('/subjects/delete/<int:id>')
@admin_required
def delete_subject(id):
    try:
        subject = Subject.get_by_id(id)
        subject.delete_instance()
        flash("Subject deleted.", "info")
    except:
        flash("Subject not found.", "danger")
    return redirect(url_for('admin_dashboard'))

# --- Declare Result ---
@app.route('/results/declare', methods=['POST'])
@admin_required
def declare_result():
    student_id = request.form['student_id']
    try:
        result = Result.create(student=student_id, declaration_date=datetime.date.today())
        for subject in Subject.select():
            marks = int(request.form.get(f"marks_{subject.id}", 0))
            total = int(request.form.get(f"total_{subject.id}", 100))
            ResultItem.create(result=result, subject=subject, marks_obtained=marks, total_marks=total)
        flash("Result declared successfully.", "success")
    except Exception as e:
        flash(f"Error declaring result: {e}", "danger")
    return redirect(url_for('admin_dashboard'))

# --- View Results ---
@app.route('/results/<int:student_id>')
@login_required
def view_results(student_id):
    user = User.get_by_id(student_id)
    results = Result.select().where(Result.student == user)
    return render_template('results.html', user=user, results=results)

@app.route('/profile/update', methods=['GET', 'POST'])
@login_required
def update_profile():
    user = User.get_by_id(session['user_id'])

    if request.method == 'POST':
        try:
            user.name = request.form['name']
            user.roll_no = request.form['roll_no']
            user.email = request.form['email']

            # If a new image is uploaded
            image_file = request.files.get('image')
            if image_file and image_file.filename:
                filename = save_image(image_file, app.config['UPLOAD_FOLDER'])
                user.image = filename

            user.save()
            flash("Profile updated successfully.", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f"Update failed: {e}", "danger")

    return render_template('update_profile.html', user=user)



# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)

