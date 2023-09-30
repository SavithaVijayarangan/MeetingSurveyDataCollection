from app import db

class SurveyResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question1 = db.Column(db.String(255), nullable=False)
    question2 = db.Column(db.String(255), nullable=False)
    question3 = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.String(255), nullable=False)

    def __init__(self, question1, question2, question3, user_id):
        self.question1 = question1
        self.question2 = question2
        self.question3 = question3
        self.user_id = user_id
