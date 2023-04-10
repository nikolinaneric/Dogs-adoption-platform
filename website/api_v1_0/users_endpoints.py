from website.models import db
from website.models import Post, User
from flask import request, jsonify, url_for, Blueprint
from .utils import pagination_data, is_admin, credentials_check
from flask_restful import reqparse
from werkzeug.security import check_password_hash



api_users = Blueprint('api_users', __name__)

@api_users.route('/login/', methods=["POST"])
def login():
    parser = reqparse.RequestParser()
    parser.add_argument('email', type=str, required=True, help='Email address is required.')
    parser.add_argument('password', type=str, required=True, help='Password is required.')
    args = parser.parse_args()
    email = args['email']
    password = args['password']
    user = User.query.filter_by(email=email).first()
    if user:
        if user.is_verified:
            if check_password_hash(user.password, password):
                token = user.get_token()
                message = {"access token": token,
                           "profile info": url_for('api_users.get_user', id=user.id, _external=True)}
                return jsonify(message), 200
            else:
                message = "Incorrect password, try again."
                return jsonify(message), 401
        else:
            message = "Email is not verified."
            return jsonify(message),401
    else:
        message = "Account does not exist."
        return jsonify(message),404


@api_users.route('/')
def get_users():
    _, admin = credentials_check()
    if admin:
        page = request.args.get('page', 1, type=int)
        name = 'users'
        pagination = User.query.paginate(page=page, per_page= 5)
        users = pagination_data(pagination, page, name)
        return jsonify(users)
    else:
        message = f"Method not allowed."
        return jsonify(message), 403


@api_users.route('/<int:id>')
def get_user(id):
    user = User.query.filter_by(id=id).first()
    logged_user, admin = credentials_check()
    if not user:
        return jsonify(f"User not found for id {id}"), 404
    if user == logged_user or admin:
        return jsonify(user.to_json())
    else:
        message = f"Method not allowed."
        return jsonify(message), 403


@api_users.route('/<int:id>', methods = ['DELETE'])
def delete_user(id):
    user = User.query.filter_by(id=id).first()
    if not user:
        return jsonify(f"User not found for id {id}"), 404
    logged_user, admin = credentials_check()
    if user == logged_user or admin:
        db.session.delete(user)
        db.session.commit()
        message = f"Successfully deleted user {user.first_name}."
        return jsonify(message),201
    else:
        message = f"Method not allowed."
        return jsonify(message), 403

@api_users.route('/posts/<int:id>')
def get_user_posts(id):
    name = 'posts'
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(user_id=id).paginate(page=page, per_page=5)
    posts = pagination_data(pagination, page, name)
    return jsonify(posts)

    
@api_users.route('/<int:id>/saved-posts')
def get_user_saved_posts(id):
    user = User.query.filter_by(id=id).first()
    if not user:
        return jsonify(f"User not found for id {id}"), 404
    logged_user, admin = credentials_check()
    if user == logged_user or admin:
        saved_posts_ids = [int(id) for id in user.saved_dogs['saved'] if id]
        name = 'saved posts'
        page = request.args.get('page', 1, type=int)
        pagination = Post.query.filter(Post.id.in_(saved_posts_ids)).paginate(page=page, per_page=5)
        posts = pagination_data(pagination, page, name)
        return jsonify(posts)
    else:
        message = f"Method not allowed."
        return jsonify(message), 403
