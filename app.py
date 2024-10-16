from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_login import UserMixin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizapp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'

# Initialize DB and Flask-Login
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define the student_module table
student_module = db.Table('student_module',
    db.Column('student_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('module_id', db.Integer, db.ForeignKey('module.id')),
    extend_existing=True
)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'
    modules = db.relationship('Module', secondary=student_module, backref='students')

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    terms_conditions = db.Column(db.Text, nullable=False)
    quizzes = db.relationship('Quiz', backref='module', lazy=True)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    time_limit = db.Column(db.Integer, default=300)  # In seconds (5 minutes by default)
    questions = db.relationship('Question', backref='quiz', lazy=True)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(255), nullable=False)
    choices = db.Column(db.String(255), nullable=False)  # Comma-separated choices
    correct_answer = db.Column(db.String(100), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    score = db.Column(db.Integer, nullable=False)

    student = db.relationship('User', backref='quiz_results')
    quiz = db.relationship('Quiz', backref='results')

# Routes

@app.route('/')
def home():
    return render_template('home.html')

# Student Login Route
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, role='student').first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('student_dashboard_view'))
        flash('Invalid username or password')
    return render_template('student_login.html')

# Teacher Login Route
@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, role='teacher').first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('teacher_dashboard'))
        flash('Invalid username or password')
    return render_template('teacher_login.html')

# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Teacher Dashboard Route
@app.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash('Access denied!')
        return redirect(url_for('login'))

    # Fetch all modules
    modules = Module.query.all()
    # Fetch all students
    students = User.query.filter_by(role='student').all()

    return render_template('teacher_dashboard.html', modules=modules, students=students)

# Student Dashboard Route
@app.route('/student_dashboard')
@login_required
def student_dashboard_view():
    if current_user.role != 'student':
        return redirect(url_for('teacher_dashboard'))

    # Fetch the modules assigned to the student
    assigned_modules = current_user.modules
    return render_template('student_dashboard.html', modules=assigned_modules)

# Create a New Module (Teacher Action)
@app.route('/teacher/add-module', methods=['POST'])
@login_required
def add_module():
    if current_user.role != 'teacher':
        return redirect(url_for('student_dashboard_view'))

    module_title = request.form['module_title']
    terms_conditions = request.form['terms_conditions']
    new_module = Module(title=module_title, terms_conditions=terms_conditions)
    db.session.add(new_module)
    db.session.commit()
    return redirect(url_for('teacher_dashboard'))

# Manage Module (Teacher)
@app.route('/teacher/module/<int:module_id>', methods=['GET'])
def manage_module(module_id):
    # Fetch the module from the database
    module = Module.query.get(module_id)
    
    if not module:
        # Handle the case where the module doesn't exist
        return "Module not found", 404

    return render_template('manage_module.html', module=module)

# Assign Students to a Module
@app.route('/teacher/module/<int:module_id>/assign-students', methods=['POST'])
@login_required
def assign_students(module_id):
    if current_user.role != 'teacher':
        return redirect(url_for('login'))

    # Get the module by ID
    module = Module.query.get(module_id)
    if not module:
        flash('Module not found.', 'error')
        return redirect(url_for('teacher_dashboard'))

    # Get the list of student IDs from the form
    student_ids = request.form.getlist('students')
    if not student_ids:
        flash('No students selected.', 'error')
        return redirect(url_for('manage_module', module_id=module_id))

    # Fetch the students by their IDs and add them to the module
    students = User.query.filter(User.id.in_(student_ids)).all()
    for student in students:
        if student not in module.students:
            module.students.append(student)
    db.session.commit()
    flash('Students successfully assigned!', 'success')
    return redirect(url_for('manage_module', module_id=module_id))

# Remove Student from Module
@app.route('/teacher/module/<int:module_id>/student/<int:student_id>/remove', methods=['POST'])
@login_required
def remove_student(module_id, student_id):
    if current_user.role != 'teacher':
        flash('Access denied!', 'error')
        return redirect(url_for('login'))

    module = Module.query.get(module_id)
    student = User.query.get(student_id)
    if student in module.students:
        module.students.remove(student)
        db.session.commit()

    flash(f'Student {student.username} removed from module {module.title}', 'info')
    return redirect(url_for('manage_module', module_id=module_id))

# Assign Quiz to a Module
@app.route('/teacher/module/<int:module_id>/assign-quiz', methods=['POST'])
@login_required
def assign_quiz(module_id):
    if current_user.role != 'teacher':
        return redirect(url_for('login'))

    quiz_id = request.form.get('quiz_id')
    module = Module.query.get(module_id)
    quiz = Quiz.query.get(quiz_id)
    module.quizzes.append(quiz)
    db.session.commit()
    flash(f"Quiz '{quiz.title}' assigned to module '{module.title}'", 'success')
    return redirect(url_for('manage_module', module_id=module_id))

# Add Question to a Quiz
@app.route('/teacher/module/<int:module_id>/add-question', methods=['POST'])
@login_required
def add_question(module_id):
    if current_user.role != 'teacher':
        return redirect(url_for('login'))

    module = Module.query.get(module_id)
    if not module:
        flash('Module not found.', 'error')
        return redirect(url_for('teacher_dashboard'))

    question_text = request.form.get('question_text')
    choices = request.form.get('choices')  # Comma-separated
    correct_answer = request.form.get('correct_answer')

    if not question_text or not choices or not correct_answer:
        flash('All fields are required.', 'error')
        return redirect(url_for('manage_module', module_id=module_id))

    new_question = Question(
        question_text=question_text,
        choices=choices,  # Assuming choices is a comma-separated string
        correct_answer=correct_answer,
        quiz_id=module.quizzes[0].id  # Assuming there's a quiz in the module
    )
    db.session.add(new_question)
    db.session.commit()

    flash('Question added successfully!', 'success')
    return redirect(url_for('manage_module', module_id=module_id))

#timer handle
@app.route('/teacher/module/<int:module_id>/set-timer', methods=['POST'])
@login_required
def set_timer(module_id):
    if current_user.role != 'teacher':
        return redirect(url_for('login'))

    module = Module.query.get(module_id)
    if not module:
        flash('Module not found.', 'error')
        return redirect(url_for('teacher_dashboard'))

    time_limit = request.form['time_limit']
    try:
        quiz.time_limit = int(time_limit)  # Assuming you are setting the time limit for a quiz in this module
        db.session.commit()
        flash(f'Timer set to {time_limit} seconds.', 'success')
    except ValueError:
        flash('Invalid timer value.', 'error')

    # Remove the extra closing parenthesis here
    return redirect(url_for('manage_module', module_id=module_id))

# Leaderboard (Teacher)
@app.route('/teacher/module/<int:module_id>/leaderboard')
@login_required
def leaderboard(module_id):
    if current_user.role != 'teacher':
        return redirect(url_for('student_dashboard_view'))

    module = Module.query.get(module_id)
    quizzes = module.quizzes
    results = QuizResult.query.join(Quiz).filter(Quiz.module_id == module_id).order_by(QuizResult.score.desc()).all()

    return render_template('leaderboard.html', results=results, module=module)

# View Module and Start Quiz (Student)
@app.route('/student/module/<int:module_id>', methods=['GET', 'POST'])
@login_required
def view_module(module_id):
    if current_user.role != 'student':
        return redirect(url_for('teacher_dashboard'))

    module = Module.query.get(module_id)

    if request.method == 'POST':
        quiz_id = request.form['quiz_id']
        quiz = Quiz.query.get(quiz_id)
        return redirect(url_for('start_quiz', quiz_id=quiz_id))

    return render_template('student_module_view.html', module=module)

# Start Quiz (Student)
@app.route('/student/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def start_quiz(quiz_id):
    if current_user.role != 'student':
        return redirect(url_for('teacher_dashboard'))

    quiz = Quiz.query.get(quiz_id)

    if request.method == 'POST':
        score = 0
        for index, question in enumerate(quiz.questions):
            user_answer = request.form.get(f'question-{index}')
            if user_answer == question.correct_answer:
                score += 1

        new_result = QuizResult(student_id=current_user.id, quiz_id=quiz.id, score=score)
        db.session.add(new_result)
        db.session.commit()

        return render_template('student_result.html', score=score, total=len(quiz.questions))

    time_limit = quiz.time_limit
    return render_template('start_quiz.html', quiz=quiz, time_limit=time_limit)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)