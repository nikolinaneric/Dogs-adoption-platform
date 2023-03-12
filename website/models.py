from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func
from flask import current_app
import jwt
import datetime

from flask import flash, redirect, url_for



db = SQLAlchemy()

class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(150))
    gender = db.Column(db.String(150))
    city = db.Column(db.String(150))
    data = db.Column(db.String(10000))
    image_file = db.Column(db.String(150), nullable=False)
    date_posted = db.Column(db.DateTime(timezone = True), default = func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dog_info = db.relationship('DogInfo', backref = 'user', uselist = False)



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(150), unique = True)
    is_verified = db.Column(db.Boolean(150), default = False)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    image_file = db.Column(db.String(150), nullable=False, default='default.jpg')
    posts = db.relationship('Post', backref ='author', lazy = True)
    user_info = db.relationship('UserInfo', backref = 'info', uselist = False)
    saved_dogs = db.Column(db.JSON, default = {"saved":[]})
    


    def get_reset_token(self):

        secret_key = 'mysecretkey'
        payload = {
            'user_id': self.id,
            'username': self.first_name,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        return jwt.encode(payload, secret_key, algorithm='HS256')

        # ovo nije staticna metoda jer se poziva na user objektu kog dobijamo preko mejla iz reset request forme 

    @staticmethod
    def verify_reset_token(token):
        secret_key = 'mysecretkey'
        
        try:
            user_id = jwt.decode(token, secret_key, algorithms=['HS256'])['user_id']
        except:
            None
            return redirect(url_for('login'))
        return User.query.get(user_id)
    # ovo je staticna metoda jer nemamo pristup useru u tom trenutku jer nije ulogovan i nismo u aplikaciji u trenutku primanja mejla za verifikaciju
    
    
    def __repr__(self):
        return f"User('{self.first_name}', '{self.email}', '{self.image_file}')"

class UserInfo(db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    prefered_breed = db.Column(db.JSON)
    prefers_mixed_breed = db.Column(db.Boolean(150))
    age_preference = db.Column(db.JSON)
    size_preference = db.Column(db.JSON)
    color_preference = db.Column(db.JSON)
    spay_needed = db.Column(db.Boolean)
    coat_length_preference = db.Column(db.String())
    dog_with_children = db.Column(db.Boolean)
    dog_with_dogs = db.Column(db.Boolean)
    dog_with_cats = db.Column(db.Boolean)
    dog_with_sm_animals = db.Column(db.Boolean)
    dog_with_big_animals = db.Column(db.Boolean)
    dog_in_house = db.Column(db.Boolean)
    yard = db.Column(db.Boolean)
    park = db.Column(db.Boolean)
    activity_level = db.Column(db.String(150))
    special_need_dog = db.Column(db.Boolean)
    

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
   
class DogInfo(db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    primary_breed = db.Column(db.String(150))
    mixed_breed = db.Column(db.Boolean())
    age = db.Column(db.String(150))
    size = db.Column(db.String(150))
    color = db.Column(db.String(150))
    spayed = db.Column(db.Boolean)
    coat_length = db.Column(db.String(150))
    dog_with_children = db.Column(db.Boolean())
    dog_with_dogs = db.Column(db.Boolean)
    dog_with_cats = db.Column(db.Boolean)
    dog_with_sm_animals = db.Column(db.Boolean)
    dog_with_big_animals = db.Column(db.Boolean)
    activity_level = db.Column(db.String(150))
    special_need_dog = db.Column(db.Boolean)

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    

