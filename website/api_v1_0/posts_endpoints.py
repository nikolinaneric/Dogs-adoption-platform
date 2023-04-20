from website.models import db
from website.models import Post, DogInfo
from flask import request, jsonify, url_for, Blueprint
from .utils import pagination_data, is_admin, credentials_check, get_object_or_404



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
    post = get_object_or_404(Post, id)
    if isinstance(post, tuple):  
        return post
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
        post = Post.from_json(request.json)
        if isinstance(post, tuple):
            return post
        post_info = DogInfo.from_json(request.json)
        if isinstance(post_info, tuple):
            return post_info
        try:
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
    return jsonify('You must have valid access token for this action.'), 401

@api_posts.route('/<int:id>', methods=['PATCH'])
def update_post(id):
    post = get_object_or_404(Post, id)
    if isinstance(post, tuple):  
        return post
    user, admin = credentials_check()
    if user == post.author or admin:
        update_post = Post.update_from_json(request.json)
        if isinstance(update_post, tuple):
            return update_post
        update_post_info = DogInfo.update_from_json(request.json)
        if isinstance(update_post_info, tuple):
            return update_post_info
        try:
            update_post = {k:v for k,v in update_post.items() if v != None}
            update_post_info = {k:v for k,v in update_post_info.items() if v != None}
            print(update_post_info)
            if update_post:
                db.session.query(Post).filter(Post.id==id).update(update_post)
            if update_post_info:
                db.session.query(DogInfo).filter(DogInfo.post_id==id).update(update_post_info)
            db.session.commit()
            json_post = post.to_json()
            response = json_post, \
            {'Location': url_for('api_posts.get_post', id=post.id, _external=True)}
            return jsonify(response), 201
        except Exception as e:
            print(e)
            message = "Bad request."
            return jsonify(message), 400
    return jsonify('You must have valid access token for this action.'), 401
        

@api_posts.route('/<int:id>', methods=['DELETE'])
def delete_post(id):
    post = get_object_or_404(Post, id)
    if isinstance(post, tuple):  
        return post
    user, admin = credentials_check()
    if user == post.author or admin:
        db.session.delete(post)
        db.session.commit()
        message = f"Successfully deleted post {id}."
        return jsonify(message),200
    else:
        message = f"You don't have permissions for this action."
        return jsonify(message), 403
