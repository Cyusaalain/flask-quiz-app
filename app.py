from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizapp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # For session management
db = SQLAlchemy(app)

# Define User, Quiz, and Question models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    score = db.Column(db.Integer)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(255), nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)  # 'A', 'B', 'C', or 'D'
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)

# Route for homepage
@app.route('/')
def home():
    return render_template('index.html')

# Quiz route
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    quiz = Quiz.query.first()
    if quiz is None:
        return "No quiz found in the database."
    
    questions = quiz.questions
    if not questions:
        return "No questions found for this quiz."

    random.shuffle(questions)
    return render_template('quiz.html', questions=questions, enumerate=enumerate)
    
    if request.method == 'POST':
        session['username'] = request.form['username']  # Store username in session
        
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

        # Save or update the user's score in the database
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            user = User(username=session['username'], score=score)
            db.session.add(user)
        else:
            if score > user.score:
                user.score = score

        db.session.commit()

        return render_template('result.html', score=score, user_answers=user_answers)

    return render_template('quiz.html', questions=questions)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database tables
    app.run(debug=True)