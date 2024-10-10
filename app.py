from flask import Flask, render_template, request, session
from flask import render_template, request, redirect, url_for
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'  # SQLite database path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'  # Set a secret key for session management

# Initialize the SQLAlchemy object
db = SQLAlchemy(app)

# Define models directly in app.py

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    score = db.Column(db.Integer, nullable=False)

# Quiz model
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy=True)

# Question model
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(255), nullable=False)
    correct_answer = db.Column(db.String(100), nullable=False)
    choices = db.Column(db.String(255), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)

    def get_choices(self):
        return self.choices.split(',')

# Route for the home page (root URL)
@app.route('/')
def home():
    quizzes = Quiz.query.all()  # Fetch all quizzes from the database
    return render_template('home.html', quizzes=quizzes)
# Route to render the admin page
@app.route('/admin', methods=['GET'])
def admin():
    quizzes = Quiz.query.all()  # Fetch all quizzes for the dropdown
    return render_template('admin.html', quizzes=quizzes)

# Route to handle quiz creation
@app.route('/admin/add-quiz', methods=['POST'])
def add_quiz():
    title = request.form['title']
    new_quiz = Quiz(title=title)
    db.session.add(new_quiz)
    db.session.commit()
    return redirect(url_for('admin'))
@app.route('/teacher/add-module', methods=['POST'])
def add_module():
    module_title = request.form['module_title']
    terms_and_conditions = request.form['terms_conditions']
    # Add students to the module based on selection
    new_module = Module(title=module_title, terms_conditions=terms_and_conditions)
    db.session.add(new_module)
    db.session.commit()
    return redirect(url_for('teacher_dashboard'))
@app.route('/student/module/<int:module_id>', methods=['GET', 'POST'])
def view_module(module_id):
    module = Module.query.get(module_id)
    if request.method == 'POST':
        # Start quiz after accepting terms
        return redirect(url_for('start_quiz', module_id=module.id))
    return render_template('terms_conditions.html', module=module)
@app.route('/student/result/<int:quiz_id>')
def view_result(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    student_score = get_student_score(current_user.id, quiz_id)
    return render_template('student_result.html', score=student_score)

# Route to handle adding questions
@app.route('/admin/add-question', methods=['POST'])
def add_question():
    quiz_id = request.form['quiz_id']
    question_text = request.form['question_text']
    choices = request.form['choices']
    correct_answer = request.form['correct_answer']

    # Add the new question to the selected quiz
    new_question = Question(
        question_text=question_text,
        choices=choices,  # Choices are comma-separated
        correct_answer=correct_answer,
        quiz_id=quiz_id
    )
    db.session.add(new_question)
    db.session.commit()
    return redirect(url_for('admin'))
# Route for the quiz page
@app.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)  # Fetch quiz by ID
    questions = quiz.questions

    if request.method == 'POST':
        session['username'] = request.form['username']
        user_answers = []
        score = 0

        for i, q in enumerate(questions):
            user_answer = request.form.get(f'question-{i}')
            correct = user_answer == q.correct_answer
            user_answers.append({
                'question': q.question_text,
                'correct': correct,
                'user_answer': user_answer,
                'correct_answer': q.correct_answer
            })
            if correct:
                score += 1

        return render_template('result.html', score=score, user_answers=user_answers)

    return render_template('quiz.html', questions=questions, enumerate=enumerate)
@app.route('/leaderboard')
def leaderboard():
    users = User.query.order_by(User.score.desc()).limit(10).all()  # Top 10 users
    return render_template('leaderboard.html', users=users)
@app.route('/api/quiz/<int:quiz_id>', methods=['GET'])
def get_quiz_api(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions
    return jsonify({
        'quiz': quiz.title,
        'questions': [
            {
                'question_text': q.question_text,
                'choices': q.get_choices()
            }
            for q in questions
        ]
    })

# This command ensures the database tables are created
with app.app_context():
    db.create_all()

# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)