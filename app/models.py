from app.extensions import db

class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(120), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return '<ApiKey %r>' % self.api_key

    def deduct_cost(self, cost):
        """Deduct the cost of a job from the balance."""
        if self.balance >= cost:
            self.balance -= cost
            db.session.commit()
            return True
        return False