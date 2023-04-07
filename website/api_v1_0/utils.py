from flask import url_for

def pagination_data(pagination, page, name):
    items = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_{name}'.format(name=name), page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_{name}'.format(name=name), page=page+1, _external=True)
    json_posts ={
    f'{name}': [item.to_json() for item in items],
    'prev': prev,
    'next': next,
    'count': pagination.total
    }
    return json_posts