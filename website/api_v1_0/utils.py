from flask import url_for, request, jsonify
import os
from website.models import User, Post

def pagination_data(pagination, page, name):
    items = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api_{name}.get_{name}'.format(name=name), page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api_{name}.get_{name}'.format(name=name), page=page+1, _external=True)
    json_posts ={
    f'{name}': [item.to_json() for item in items],
    'prev': prev,
    'next': next,
    'count': pagination.total
    }
    return json_posts

def is_admin(username, password):
    if username == os.environ.get('ADMIN_USERNAME') and password == os.environ.get('ADMIN_PASSWORD'):
        return True
    else:
        return False

def credentials_check():
    user = None
    token = request.headers.get('Authorization')
    if token:
        access_token = token.split()[1]
        if access_token:
            user = User.verify_token(access_token, api_token=True)
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        username = (request.json).get('username')
        password = (request.json).get('password')
        admin = is_admin(username, password)
    else:
        admin = False
    return user, admin

def get_object_or_404(model,id):
    obj = model.query.filter_by(id=id).first()
    if obj is None:
        return jsonify( f'{model.__name__} not found.'), 404
    return obj