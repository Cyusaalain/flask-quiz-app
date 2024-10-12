from your_database import db  # Import SQLAlchemy instance from your database setup
from werkzeug.security import generate_password_hash, check_password_hash

# Define a User model to store user data
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Hashed password
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'

    # Method to set the password (hash the password)
    def set_password(self, password):
        self.password = generate_password_hash(password)

    # Method to check the password (verify it)
    def check_password(self, password):
        return check_password_hash(self.password, password)

# Define a Quiz model to store quiz data
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy=True)

    # Relationship to the Question model (one quiz has many questions)
    questions = db.relationship('Question', backref='quiz', lazy=True)

# Define a Question model to store questions for each quiz
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(255), nullable=False)
    correct_answer = db.Column(db.String(100), nullable=False)
    
    # Storing choices as a simple comma-separated string (you can enhance this later)
    choices = db.Column(db.String(255), nullable=False)
    
    # Foreign key to reference the Quiz
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)

    # Method to convert choices back to a list
    def get_choices(self):
        return self.choices.split(',')