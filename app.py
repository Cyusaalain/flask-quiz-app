from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizapp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'

# Initialize DB and Flask-Login
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'teacher' or 'student'

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    terms_conditions = db.Column(db.Text, nullable=False)
    quizzes = db.relationship('Quiz', backref='module', lazy=True)

student_module = db.Table('student_module',
    db.Column('student_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('module_id', db.Integer, db.ForeignKey('module.id'))
)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
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

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

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
    return render_template('teacher_dashboard.html')
# Student Dashboard Route
@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied!')
        return redirect(url_for('login'))
    return render_template('student_dashboard.html')

# Create a New Module (Teacher Action)
@app.route('/teacher/add-module', methods=['POST'])
@login_required
def add_module():
    if current_user.role != 'teacher':
        return redirect(url_for('student_dashboard'))
    
    module_title = request.form['module_title']
    terms_conditions = request.form['terms_conditions']
    new_module = Module(title=module_title, terms_conditions=terms_conditions)
    db.session.add(new_module)
    db.session.commit()
    return redirect(url_for('teacher_dashboard'))

# Assign Students to Module (Teacher Action)
@app.route('/teacher/assign-students', methods=['POST'])
@login_required
def assign_students():
    if current_user.role != 'teacher':
        return redirect(url_for('student_dashboard'))
    
    module_id = request.form['module_id']
    student_ids = request.form.getlist('students')

    module = Module.query.get(module_id)
    students = User.query.filter(User.id.in_(student_ids)).all()

    for student in students:
        module.students.append(student)

    db.session.commit()
    return redirect(url_for('teacher_dashboard'))
@app.route('/teacher/module/<int:module_id>/leaderboard')
@login_required
def leaderboard(module_id):
    if current_user.role != 'teacher':
        return redirect(url_for('student_dashboard'))

    # Fetch the module
    module = Module.query.get(module_id)
    quizzes = module.quizzes

    # Fetch all results for quizzes in this module
    results = QuizResult.query.join(Quiz).filter(Quiz.module_id == module_id).order_by(QuizResult.score.desc()).all()

    return render_template('leaderboard.html', results=results, module=module)

# Student Dashboard
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('teacher_dashboard'))
    
    # Fetch the modules assigned to the student
    assigned_modules = current_user.modules
    return render_template('student_dashboard.html', modules=assigned_modules)

# View Module and Start Quiz (Student)
@app.route('/student/module/<int:module_id>', methods=['GET', 'POST'])
@login_required
def view_module(module_id):
    if current_user.role != 'student':
        return redirect(url_for('teacher_dashboard'))
    
    module = Module.query.get(module_id)
    if request.method == 'POST':
        # Start quiz after accepting terms
        return redirect(url_for('start_quiz', module_id=module.id))
    
    return render_template('terms_conditions.html', module=module)

# Start Quiz (Student)
# Route to start the quiz
@app.route('/student/module/<int:module_id>/quiz', methods=['GET', 'POST'])
@login_required
def start_quiz(module_id):
    module = Module.query.get(module_id)
    quiz = module.quizzes[0]  # Fetch the first quiz for simplicity
    time_limit = 300  # Example: 5 minutes (300 seconds)

    if request.method == 'POST':
        # Evaluate the quiz submission
        score = 0
        total_questions = len(quiz.questions)
        user_answers = []
        
        for index, question in enumerate(quiz.questions):
            user_answer = request.form.get(f'question-{index}')
            correct_answer = question.correct_answer
            if user_answer == correct_answer:
                score += 1
            new_result = QuizResult(student_id=current_user.id, quiz_id=quiz.id, score=score)
        db.session.add(new_result)
        db.session.commit()

        return render_template('student_result.html', score=score, total=total_questions)

    return render_template('quiz.html', quiz=quiz, time_limit=time_limit)

# View Result after Quiz (Student)
@app.route('/student/result/<int:module_id>')
@login_required
def view_result(module_id):
    module = Module.query.get(module_id)
    student_score = 90  # Placeholder: Calculate score logic
    return render_template('student_result.html', score=student_score)

# Create DB Tables if not exists
with app.app_context():
    db.create_all()

# Run the App
if __name__ == '__main__':
    app.run(debug=True)