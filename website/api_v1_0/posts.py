from website.models import db
from website.models import Post, DogInfo, User
from flask import request, jsonify, url_for
from flask import Blueprint
from .utils import pagination_data
from flask_restful import Api
from .login_api import LoginAPI


api = Blueprint('api', __name__)
api_resources = Api(api)

api_resources.add_resource(LoginAPI, '/login')

@api.route('/posts/')
def get_posts():
    name = 'posts'
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.paginate(page=page, per_page= 5)
    posts = pagination_data(pagination, page, name)
    return jsonify(posts)

@api.route('/posts/<int:id>')
def get_post(id):
    post = Post.query.get_or_404(id, description=f"Post not found for id {id}")
    return jsonify(post.to_json())

@api.route('/dog-info/<int:id>')
def get_dog_info(id):
    dog_info = DogInfo.query.filter_by(post_id=id).first_or_404(description=f"Dog info not found for post id {id}")
    return jsonify(dog_info.to_json())


@api.route('/users/')
def get_users():
    page = request.args.get('page', 1, type=int)
    name = 'users'
    pagination = User.query.paginate(page=page, per_page= 5)
    users = pagination_data(pagination, page, name)
    return jsonify(users)

@api.route('/users/<int:id>')
def get_user(id):
    user = User.query.get_or_404(id, description=f"User not found for id {id}")
    return jsonify(user.to_json())

@api.route('/posts/users/<int:id>')
def get_user_posts(id):
    name = 'posts'
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(user_id=id).paginate(page=page, per_page=5)
    posts = pagination_data(pagination, page, name)
    return jsonify(posts)

   
@api.route('/users/<int:id>/saved-posts')
def get_user_saved_posts(id):
    user = User.query.get_or_404(id)
    saved_posts_ids = [int(id) for id in user.saved_dogs['saved'] if id]
    print(saved_posts_ids)
    name = 'saved posts'
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter(Post.id.in_(saved_posts_ids)).paginate(page=page, per_page=5)
    posts = pagination_data(pagination, page, name)
    return jsonify(posts)

@api.route('/posts/', methods=['POST'])
def new_post():
    access_token = request.headers.get('Authorization').split()[1]
    user = User.verify_token(access_token)
    if user:
        post = Post.from_json(request.json)
        post.author = user
        db.session.add(post)
        db.session.commit()
    return jsonify(post.to_json()), 201, \
    {'Location': url_for('api.get_post', id=post.id, _external=True)}
