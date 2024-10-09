from flask import Flask, render_template, request, session, redirect, url_for
from models import Quiz, Question, User  # Assuming you have a models file with these classes
from your_database import db  # Import your db instance (SQLAlchemy)
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for session management

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    # Fetch the first quiz (modify if you have multiple quizzes)
    quiz = Quiz.query.first()
    
    if not quiz:
        return "No quiz available."

    # Fetch all the questions related to this quiz
    questions = quiz.questions
    random.shuffle(questions)  # Shuffle questions randomly for quiz

    if request.method == 'POST':
        # Save username in session
        session['username'] = request.form['username']
        
        # Initialize user answers and score
        user_answers = []
        score = 0

        # Evaluate the answers
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

        # Store the user's score in the database
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            user = User(username=session['username'], score=score)
            db.session.add(user)
        else:
            if score > user.score:  # Update score only if it's better
                user.score = score

        db.session.commit()

        # Show results page
        return render_template('result.html', score=score, user_answers=user_answers)

    return render_template('quiz.html', questions=questions, enumerate=enumerate)

if __name__ == '__main__':
    # Make sure the database is created
    with app.app_context():
        db.create_all()  # This ensures tables are created if not already
    app.run(debug=True)