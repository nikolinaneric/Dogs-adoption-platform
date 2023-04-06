
from flask import request, url_for
from flask_login import current_user
from website.tasks import send_mail
from website.models import Post
from sqlalchemy import case
from flask_babel import gettext

def email():
    """
    Sends an email message to the specified recipient with the specified message, subject, and reply-to author.
    """
    author = current_user.email
    recipient = request.form.get('recipient')
    message = request.form.get('message')
    subject = request.form.get('subject')
    recipients= [recipient]
    reply_to = author
    message_body = f" <p> {message} </p> <h4> This message was sent to you via <a href= {url_for('main.welcome', _external=True)}> dope connect <a/> app.</h4>"
    send_mail.delay(subject, recipients, message_body, reply_to)


def filtering(query_object, page):
    """
    Filters a query object based on user-selected filters and pagination options.

    Parameters:
    query_object (obj): A SQLAlchemy query object containing Post objects to filter.
    page (int): The page number to paginate the filtered results.

    Returns:
    tuple: A tuple containing a list of saved post IDs, a list of gender options, a filtered query object, a list of selected cities, and a selected gender.
    """
    saved_posts = []
    if current_user.is_authenticated:
        saved_dogs = current_user.saved_dogs
        if saved_dogs:
            saved_posts = saved_dogs['saved']
            saved_posts = [int(id) for id in saved_posts]
    genders = [gettext('male'), gettext('female')]

    chosen_cities=[]
    if request.method == "GET":
        chosen_cities = request.args.getlist('city') if request.args.getlist('city') else []
        chosen_gender = request.args.get('gender') if request.args.get('gender') else None
        if chosen_gender == 'ženski':
            chosen_gender = 'female'
        if chosen_gender == 'muški':
            chosen_gender = 'male'
        
        if chosen_cities and chosen_gender:
            filtered_posts = query_object.filter(case(('all' not in chosen_cities, Post.city.in_(chosen_cities)), else_= True))\
                    .filter(case((chosen_gender != 'all', Post.gender == chosen_gender), else_= True))\
                    .order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
        elif chosen_cities:
            filtered_posts = query_object.filter(case(('all' not in chosen_cities, Post.city.in_(chosen_cities)), else_= True))\
                .order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
        elif chosen_gender:
            filtered_posts = query_object.filter(case((chosen_gender != 'all', Post.gender == chosen_gender), else_= True))\
                .order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
        else:
            filtered_posts = None
    return saved_posts, genders, filtered_posts, chosen_cities, chosen_gender


def get_dog_info(dog):
    """
    Formats dog data for display on a post page.

    Parameters:
    dog (Dog): The dog for which the data is to be formatted

    Returns:
    dict: A dictionary containing the formatted dog data
    """
    d_compatibility = [gettext('children') if dog.dog_with_children else '', gettext('dogs') if dog.dog_with_dogs else '', gettext('cats') if dog.dog_with_cats else '',\
            gettext('small animals') if dog.dog_with_sm_animals else '', gettext('big animals') if dog.dog_with_big_animals else '']
    d_compatibility = [comp for comp in d_compatibility if comp != '']
    

    dog_info = {
        "d_mixed_breed" : dog.mixed_breed,
        "d_primary_breed" : gettext(dog.primary_breed),
        "d_size" : gettext(dog.size),
        "d_age" : gettext(dog.age),
        "d_color" : gettext(dog.color),
        "d_coat_length" : gettext(dog.coat_length),
        "d_spayed" : dog.spayed,
        "d_compatibility": d_compatibility,
        "d_special_need" : dog.special_need_dog,
        "d_activity" : gettext(dog.activity_level),
    }
    return dog_info

def get_user_info(user):
    """
    Formats user data for display on a preferences page.

    Parameters:
    dog (Dog): The user for which the data is to be formatted

    Returns:
    dict: A dictionary containing the formatted user data
    """
    u_needs= [gettext('children') if user.dog_with_children else '', gettext('dogs') if user.dog_with_dogs else '', gettext('cats') if user.dog_with_cats else '',\
            gettext('small animals') if user.dog_with_sm_animals else '', gettext('big animals') if user.dog_with_big_animals else '']
    u_needs = [need for need in u_needs if need != '']
    
    u_info = {
        "u_mixed_breed" : user.prefers_mixed_breed,
        "u_prefered_breed" : [gettext(breed).lower() for breed in user.prefered_breed['prefered_breed'][:]],
        "u_prefered_size" : [gettext(size) for size in user.size_preference['size_preference'][:]],
        "u_prefered_age" : [gettext(age) for age in user.age_preference['age_preference'][:]],
        "u_prefered_color" : [gettext(color) for color in user.color_preference['color_preference'][:]],
        "u_prefered_coat_length" : gettext(user.coat_length_preference),
        "u_spay_needed" : user.spay_needed,
        "u_needs": u_needs,
        "u_special_need" : user.special_need_dog,
        "u_activity" : gettext(user.activity_level),
        "u_dog_in_house" : user.dog_in_house, 
        "u_yard": user.yard,
        "u_park": user.park
    }
    return u_info