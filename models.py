from your_database import db  # Import SQLAlchemy instance from your database setup

# Define a User model to store user data
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    score = db.Column(db.Integer, nullable=False)

# Define a Quiz model to store quiz data
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)

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