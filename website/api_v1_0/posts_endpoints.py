from website.models import db
from website.models import Post, DogInfo
from flask import request, jsonify, url_for, Blueprint
from .utils import pagination_data, is_admin, credentials_check



api_posts = Blueprint('api_posts', __name__)

@api_posts.route('/')
def get_posts():
    name = 'posts'
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.paginate(page=page, per_page= 5)
    posts = pagination_data(pagination, page, name)
    return jsonify(posts)

@api_posts.route('/<int:id>')
def get_post(id):
    post = Post.query.filter_by(id=id).first()
    if not post:
        return jsonify(f"Post not found for id {id}"), 404
    return jsonify(post.to_json())

@api_posts.route('/<int:id>/dog-info/')
def get_dog_info(id):
    dog_info = DogInfo.query.filter_by(post_id=id).first()
    if not dog_info:
        return jsonify(f"Dog info not found for post id {id}"), 404
    else:
        return jsonify(dog_info.to_json())
    
@api_posts.route('/', methods=['POST'])
def create_post():
    user, _ = credentials_check()
    if user:
        try:
            post = Post.from_json(request.json)
            post_info = DogInfo.from_json(request.json)
            post.author = user
            post.dog_info = post_info
            db.session.add(post)
            db.session.add(post_info)
            db.session.commit()
            json_post = post.to_json()
            response = json_post, \
            {'Location': url_for('api_posts.get_post', id=post.id, _external=True)}
            return jsonify(response), 201
        except:
            message = "Bad request."
            return jsonify(message), 400
    return jsonify('You must be logged in for this action.'), 401
        

@api_posts.route('/<int:id>', methods=['DELETE'])
def delete_post(id):
    post = Post.query.filter_by(id=id).first()
    if not post:
        return jsonify(f"Post not found for id {id}"), 404
    user, admin = credentials_check()
    if user == post.author or admin:
        db.session.delete(post)
        db.session.commit()
        message = f"Successfully deleted post {id}."
        return jsonify(message),200
    else:
        message = f"Method not allowed."
        return jsonify(message), 403
