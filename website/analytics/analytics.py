import os
from pymongo import MongoClient
from bson import ObjectId
from flask import Blueprint, request, make_response,jsonify
from flask_login import current_user
import datetime


mongodb = os.environ.get('MONGODB')


try:
    connection_string = f"{mongodb}"
    client = MongoClient(connection_string)
    analytics_db = client.analytics_db 
    visited_urls = analytics_db.visited_urls
    active_users = analytics_db.active_users
    
except Exception as e:
    print(e)


analytics = Blueprint('analytics', __name__)

@analytics.route("/analytics", methods = ['POST'])
def clicked():
    data = request.get_json()
    clicked = data.get('linkClick')
    url = clicked.get('url')
    title = clicked.get('title')

    if current_user.is_anonymous:
        name = "Anonymous"
        email = None
    else:
        name = current_user.first_name
        email = current_user.email

    user_doc = {
        "name" : name,
        "email": email,
        "last_active": datetime.datetime.now(),
        
    }

    url_doc = {
        "url" : url,
        "title" : title,
        "last_visited_at" : datetime.datetime.now(),
       
    }

    active_user = active_users.find_one({"email": email}, {"_id": 1})
    visited_url = visited_urls.find_one({"url": url}, {"_id": 1})

    if active_user is None:
        _id = active_users.insert_one(user_doc).inserted_id
        user_id = _id
    else:
        user_id = active_user['_id']

    if visited_url is None:
        _id = visited_urls.insert_one(url_doc).inserted_id
        url_id = _id
    else:
        url_id = visited_url['_id']

    active_users.update_one({"_id": ObjectId(user_id)}, 
                            {"$push": {"visited_links": {"url_id": ObjectId(url_id),
                                                        "url":url,
                                                        "title": title,
                                                        "visited_at": datetime.datetime.now()}},
                            "$set": {"last_active": datetime.datetime.now()}})
    
    visited_urls.update_one({"_id": ObjectId(url_id)}, 
                            {"$push": {"visitors": {"user_id" : ObjectId(user_id),
                                                    "username" : name,
                                                    "visited_at": datetime.datetime.now()}},
                            "$set": {"last_visited_at": datetime.datetime.now()}})   
    
    res = make_response(jsonify({"message":'successful'}), 200)
    return res


@analytics.route("/analytics-results", methods = ['GET'])
def analytics_results():
    from website.analytics.utils import get_anonymous_visits_number, get_most_active_user,\
          get_most_visited_link, get_most_visited_post,\
          credentials_check, is_admin
    
    admin = credentials_check()
    if admin :
        r1 = get_most_active_user()
        r2 = get_anonymous_visits_number()
        r3 = get_most_visited_link()
        r4 = get_most_visited_post()
        res = make_response(jsonify(r1, r2, r3, r4), 200)
        return res
    return jsonify('You don\'t have permissions for this action.'), 401