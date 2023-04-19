from flask import request, jsonify
import os
from website.analytics.analytics import analytics_db, visited_urls, active_users

def credentials_check():
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        username = (request.json).get('username')
        password = (request.json).get('password')
        admin = is_admin(username, password)
    else:
        admin = False
    return admin

def is_admin(username, password):
    if username == os.environ.get('ADMIN_USERNAME') and password == os.environ.get('ADMIN_PASSWORD'):
        return True
    else:
        return False

def get_most_active_user():
    pipeline = [
        {
            "$project": {
                "name": 1,
                "email": 1,
                "_id": 0,
                "total_number_of_visits": {
                    "$size": "$visited_links"
                },
                "visited_links": 1
            }
        },
        {
            "$sort": {"total_number_of_visits": -1}
        },
        {
            "$limit": 1
        },
        {
            "$unwind": "$visited_links"
        },
        {
            "$group": {
                "_id": "$visited_links.url",
                "visits_to_users_most_visited_url": {"$sum": 1},
                "most_active_user": {"$first": "$name"},
                "total_number_of_visits": {"$first": "$total_number_of_visits"}
            }
        },
        {
            "$sort": {"visits_to_users_most_visited_url": -1}
        },
        {
            "$limit": 1
        },
        {   
            "$project": {
                "most_active_user": 1,
                "total_number_of_visits":1,
                "most_visited_url": "$_id",
                "visits_to_users_most_visited_url": 1,
                "_id": 0,
                  
            }
        }
    ]

    most_active_user = active_users.aggregate(pipeline)
    message = ("Info about the most active user on the website:", list(most_active_user))
    return message
    

def get_anonymous_visits_number():
    pipeline = [
    {   "$match": {
            "name" : "Anonymous"
        }

    },
    {   "$project" : {
            "_id": 0,
            "anonymous_visits": {
                "$size": "$visited_links"
            }
    }

    }]
    anonymous_visits = active_users.aggregate(pipeline)
    message = ("Info about the anonymous users on the website:",list(anonymous_visits))
    return message


def get_most_visited_link():
    pipeline = [
        {
            "$project": {
                "title": 1,
                "url": 1,
                "_id": 0,
                "total_number_of_visits": {
                    "$size": "$visitors"
                },
              
            }
        },
        {
            "$sort": {"total_number_of_visits": -1}
        },
        {
            "$limit": 1
        },
        
    
    ]

    most_visited_url = visited_urls.aggregate(pipeline)
    message = ("Info about the most visited link on the website:", list(most_visited_url))
    return message




def get_most_visited_post():
    pipeline = [
    
    {   "$match": {
            "url" : {"$regex":"post{1}"}
    }

    },

    {   "$project" : {
            "_id": 0,
            "url": 1,
            "title": 1,
            "total_number_of_visits": {
                "$size": "$visitors"
            },
            "visitors" :1
    }

    },
    {
        "$sort": {"total_number_of_visits": -1}
    },
    {
        "$limit": 1
    },
    {
        "$unwind": "$visitors"
    },
    {   "$group": {
            "_id" : "$visitors.user_id",
            "visits_from_most_interested_user" : {"$sum":1},
            "url": {"$first": "$url"},
            "title": {"$first": "$title"},
            "total_numbers_of_visits": {"$first": "$total_number_of_visits"},   
            "most_visits_from": {"$first": "$visitors.username"}}
    },
    {
        "$sort": {"visits": -1}
    },
    {
        "$limit": 1
    },
    {   "$project":{
            "most_visits_from" : "$_id",
            "visits" : 1,
            "url": 1,
            "title": 1,
            "total_numbers_of_visits": 1,
            "_id":0,
            "most_visits_from" :1
    }}
    ]
    most_visited_post = visited_urls.aggregate(pipeline)
    message = ("Info about the most visited post on the website:", list(most_visited_post))
    return message
    

