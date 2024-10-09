from flask import Flask, render_template, request, session
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

# Route for the quiz page
@app.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
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

    # Render quiz form
    return render_template('quiz.html', questions=questions, enumerate=enumerate)

# This command ensures the database tables are created
with app.app_context():
    db.create_all()

# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)