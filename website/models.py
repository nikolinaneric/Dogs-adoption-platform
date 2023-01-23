from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app



db = SQLAlchemy()



class Note(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(150))
    data = db.Column(db.String(10000))
    date_posted = db.Column(db.DateTime(timezone = True), default = func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(150), unique = True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    image_file = db.Column(db.String(150), nullable=False, default='default.jpg')
    notes = db.relationship('Note')

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')        
        # ovo nije staticna metoda jer se poziva na user objektu kog dobijamo preko mejla iz reset request forme 

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)
    # ovo je staticna metoda jer nemamo pristup useru u tom trenutku jer nije ulogovan i nismo u aplikaciji u trenutku primanja mejla za verifikaciju
    
    
    def __repr__(self):
        return f"User('{self.first_name}', '{self.email}', '{self.image_file}')"




