from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func
import jwt
import datetime
from flask import redirect, url_for, request, jsonify
import os

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(150), unique = True)
    is_verified = db.Column(db.Boolean(150), default = False)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    image_file = db.Column(db.String(150), nullable=False, default='default.jpg')
    posts = db.relationship('Post', backref ='author', lazy = True, cascade="all, delete-orphan")
    user_info = db.relationship('UserInfo', backref = 'user', uselist = False, cascade="all, delete-orphan" )
    saved_dogs = db.Column(db.JSON, default = {"saved":[]})
    
    def to_json(self):
        images_path = 'static/profile_pics/'
        json_user = {
        'url': url_for('api_users.get_user', id=self.id, _external=True),
        'email': self.email,
        'username': self.first_name,
        'image' : f'{request.host_url}{images_path}{self.image_file}',
        'posts': url_for('api_users.get_user_posts', id=self.id, _external=True),
        'saved_posts': url_for('api_users.get_user_saved_posts', id=self.id, _external=True)
        }
        return json_user
    

    def get_token(self):

        secret_key = os.environ.get('secret_key')
        payload = {
            'user_id': self.id,
            'username': self.first_name,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        return jwt.encode(payload, secret_key, algorithm='HS256')


    @staticmethod
    def verify_token(token, api_token = False):
        secret_key = os.environ.get('secret_key')
        
        try:
            user_id = jwt.decode(token, secret_key, algorithms=['HS256'])['user_id']
        except:
            if api_token:
                error_message = ('Token invalid or expired')
                return jsonify(error_message), 401
            else:
                None
                return redirect(url_for('login'))

        return User.query.get(user_id)
       
    def __repr__(self):
        return f"User('{self.first_name}', '{self.email}', '{self.image_file}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(150))
    gender = db.Column(db.String(150))
    city = db.Column(db.String(150))
    data = db.Column(db.String(10000))
    image_file = db.Column(db.String(150), nullable=False)
    date_posted = db.Column(db.DateTime(timezone = True), default = func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dog_info = db.relationship('DogInfo', backref = 'dog', uselist = False, cascade="all, delete-orphan")

    def to_json(self):
        images_path='static/profile_pics/'
        json_post = {
        'url': url_for('api_posts.get_post', id=self.id, _external=True),
        'dog name': self.title,
        'gender': self.gender,
        'city': self.city,
        'description': self.data,
        'image' : f'{request.host_url}{images_path}{self.image_file}',
        'author': url_for('api_users.get_user', id=self.user_id, _external=True),
        'dog info': url_for('api_posts.get_dog_info', id=self.id, _external=True)
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body = json_post
        if not body:
            return jsonify('Request body is empty'), 400
        
        else:
            try:
                post_data = {
                "title": body['dog name'],
                "gender" : body['gender'],
                "city" : body['city'],
                "data" : body['description'],
                "image_file" : "defaultdog.jpg"
                }
        
                return Post(**post_data)
            except:
                return jsonify('Post info not provided.'), 400
            
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
        try:
            json_dog_info = {
            'url': url_for('api_posts.get_dog_info', id=self.post_id, _external=True),
            'primary breed': self.primary_breed,
            'mixed breed': self.mixed_breed,
            'age': self.age,
            'size': self.size,
            'color' : self.color,
            'spayed': self.spayed,
            'coat length': self.coat_length,
            'dog with children': self.dog_with_children,
            'dog with dogs' : self.dog_with_dogs,
            'dog with cats': self.dog_with_cats,
            'dog with small animals': self.dog_with_sm_animals,
            'dog with big animals': self.dog_with_big_animals,
            'activity level': self.activity_level,
            'special needs dog': self.special_need_dog
            }
            return json_dog_info
        except: 
            return jsonify('Bad request'), 400

    
    @staticmethod
    def from_json(json_post):
        body = json_post
        if body is None or body == {}:
            return jsonify('Request body is empty'), 400
        else:
            try:
                dog_info = {
                'primary_breed': body['primary breed'],
                'mixed_breed': bool(body['mixed breed']),
                'age': body['age'],
                'size': body['size'],
                'color' : body['color'],
                'spayed': bool(body['spayed']),
                'coat_length': body['coat length'],
                'dog_with_children': bool(body['dog with children']),
                'dog_with_dogs' : bool(body['dog with dogs']),
                'dog_with_cats': bool(body['dog with cats']),
                'dog_with_sm_animals': bool(body['dog with small animals']),
                'dog_with_big_animals': bool(['dog with big animals']),
                'activity_level': body['activity level'],
                'special_need_dog': bool(body['special need dog'])
                }
            except:
                return jsonify('Dog info not provided.'), 400
        if dog_info:
            return DogInfo(**dog_info)
    
    