from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func
import jwt
import datetime
from flask import redirect, url_for, request, jsonify
import os
from wtforms.validators import ValidationError


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

    def to_json(self):
        images_path='static/profile_pics/'
        json_post = {
        'url': url_for('api.get_post', id=self.id, _external=True),
        'dog name': self.title,
        'gender': self.gender,
        'city': self.city,
        'description': self.data,
        'image' : f'{request.host_url}{images_path}{self.image_file}',
        'author': url_for('api.get_user', id=self.user_id, _external=True),
        'dog info': url_for('api.get_dog_info', id=self.id, _external=True)
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body = json_post
        print(json_post)
        if body is None or body == {}:
            #raise  ValidationError('Post body is empty')
            return jsonify({'error':'Post body is empty'}), 400
        else:
            title = body['dog name']
            gender = body['gender']
            city = body['city']
            data = body['description']
            image_file = body['image']
            return Post(title = title, gender = gender, city = city, data = data, image_file = image_file)


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
    
    def to_json(self):
        images_path = 'static/profile_pics/'
        json_user = {
        'url': url_for('api.get_user', id=self.id, _external=True),
        'username': self.first_name,
        'image' : f'{request.host_url}{images_path}{self.image_file}',
        'posts': url_for('api.get_user_posts', id=self.id, _external=True),
        'saved_posts': url_for('api.get_user_saved_posts', id=self.id, _external=True)
        }
        return json_user
    
    


    def get_reset_token(self):

        secret_key = os.environ.get('secret_key')
        payload = {
            'user_id': self.id,
            'username': self.first_name,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        return jwt.encode(payload, secret_key, algorithm='HS256')


    @staticmethod
    def verify_token(token):
        secret_key = os.environ.get('secret_key')
        
        try:
            user_id = jwt.decode(token, secret_key, algorithms=['HS256'])['user_id']
        except:
            error_message = {'error':'Post body is empty'}
            response = jsonify(error_message)
            response.status_code = 400
            raise ValidationError(error_message)
        return User.query.get(user_id)
    
    @staticmethod
    def verify_reset_token(token):
        secret_key = os.environ.get('secret_key')
        
        try:
            user_id = jwt.decode(token, secret_key, algorithms=['HS256'])['user_id']
        except:
            None
            return redirect(url_for('login'))
        return User.query.get(user_id)
   
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
    

    def to_json(self):
        json_dog_info = {
        'url': url_for('api.get_dog_info', id=self.post_id, _external=True),
        'primary breed': self.primary_breed,
        'mixed breed': self.mixed_breed,
        'age': self.age,
        'size': self.size,
        'color' : self.color,
        'spayed': self.spayed,
        'coat_length': self.coat_length,
        'dog with children': self.dog_with_children,
        'dog with dogs' : self.dog_with_dogs,
        'dog with cats': self.dog_with_cats,
        'dog with small animals': self.dog_with_sm_animals,
        'dog with big animals': self.dog_with_big_animals,
        'activity level': self.activity_level,
        'special needs dog': self.special_need_dog
        }
        return json_dog_info