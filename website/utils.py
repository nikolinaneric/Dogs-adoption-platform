import os
import jwt
import datetime
from PIL import Image
import secrets
from flask import request, url_for, current_app
from flask_login import current_user
from .tasks import send_mail
from .models import Post
from sqlalchemy import case

def verification_mail(email, first_mail_adress = True):
    """
    Sends a verification email to the specified email address with a verification link
    to confirm the account. The verification link expires in 30 minutes.
    Sending mails is handled by celery task.

    Parameters:
    email (str): The email address to which the verification link is to be sent
    first_mail_adress (bool): If True, then the verification link is sent to the original email address
    associated with the account, otherwise it is sent to a new email address associated with the account
    """
    secret_key = os.environ.get('secret_key')
    print(secret_key)
    verification_token = jwt.encode({'email': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, secret_key, algorithm='HS256')
    verification_url = ""
    if first_mail_adress:
        verification_url = url_for('verify_email', token=verification_token, _external=True)
    else:
         verification_url = url_for('verify_new_email', token=verification_token, _external=True)
    subject = 'Email Verification' 
    recipients=[email]
    message_body = f'''To verify your account, please visit the following link: {verification_url}   
                If you did not make this request then simply ignore this email and no changes will be made.
            '''
    send_mail.delay(subject, recipients, message_body)

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
    message_body = f" <p> {message} </p> <h4> This message was sent to you via <a href= {url_for('welcome', _external=True)}> dope connect <a/> app.</h4>"
    send_mail.delay(subject, recipients, message_body, reply_to)

def send_reset_email(user):
    """
    Sends an email to the specified user with a link to reset their password.

    Parameters:
    user (User): The user to whom the password reset email is to be sent.
    """
 
    token = user.get_reset_token()
    subject = 'Password Reset Request'
    recipients=[user.email]
    message_body = f'''To reset your password, visit the following link:
    {url_for('reset_token', token=token, _external=True)}  
    If you did not make this request then simply ignore this email and no changes will be made.
    '''
    send_mail.delay(subject, recipients, message_body)
    

def save_picture(form_picture):
    """
    Saves a picture uploaded via a form to the file system and returns the name of the file.

    Parameters:
    form_picture: The picture to be saved

    Returns:
    str: The name of the saved picture file
    """
    picture_name = ""
    random_hex = secrets.token_hex(8)  # za naziv slike u bazi kako ne bi doslo do overrajdovanja
    if form_picture:
        _, f_ext = os.path.splitext(form_picture.filename)  # f_ext je ekstenzija fajla slike iz forme (npr jpg ili png)
        picture_name = random_hex + f_ext
        picture_path = os.path.join(current_app.root_path,'static/profile_pics/', picture_name)  # napravljen path za cuvanje slike

    # smanjivanje velicine slike radi ustede memorije u bazi pomocu pillow paketa:

        output_size = (1200,630)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)   # cuvanje slike na picture_pathu

    return picture_name

def get_dog_data(response, post):
    """
    Extracts data about a dog from a submitted form and associates it with a post.
    Parameters:
    response (dict): submitted form data
    post (Post): The post object to which the dog data is to be associated

    Returns:
    dict: A dictionary containing the dog data
    """
    dog_data = {
        "primary_breed" : (response.get('a1')).lower() if response.get('a1') else None,
        "mixed_breed" : bool(int(response.get('a2'))) if response.get('a2') is not None else None,
        "age" : response.get('a3'),
        "size" : response.get('a4'),
        "color" : response.get('a5'),
        "spayed" : bool(int(response.get('a6'))),
        "coat_length" : response.get('a7'),
        "dog_with_children" : bool(int(response.get('a8'))) if response.get('a8') is not None else None ,
        "dog_with_dogs" : bool(int(response.get('a9'))) if response.get('a9') is not None else None,
        "dog_with_cats" : bool(int(response.get('a10'))) if response.get('a10') is not None else None,
        "dog_with_sm_animals" : bool(int(response.get('a11'))) if response.get('a11') is not None else None,
        "dog_with_big_animals" : bool(int(response.get('a12'))) if response.get('a12') is not None else None,
        "activity_level" : response.get('a13'),
        "special_need_dog" : bool(int(response.get('a14'))) if response.get('a14') is not None else None,
        "post_id": post.id
        }
    dog_data = {k: v for k, v in dog_data.items() if v is not None}
    return dog_data

def get_dog_info(dog):
    """
    Formats dog data for display on a post page.

    Parameters:
    dog (Dog): The dog for which the data is to be formatted

    Returns:
    dict: A dictionary containing the formatted dog data
    """
    d_compatibility = ['children' if dog.dog_with_children else '', 'dogs' if dog.dog_with_dogs else '', 'cats' if dog.dog_with_cats else '',\
            'small animals' if dog.dog_with_sm_animals else '', 'big animals' if dog.dog_with_big_animals else '']
    d_compatibility = [comp for comp in d_compatibility if comp != '']
    

    dog_info = {
        "d_mixed_breed" : dog.mixed_breed,
        "d_primary_breed" : dog.primary_breed,
        "d_size" : dog.size,
        "d_age" : dog.age,
        "d_color" : dog.color,
        "d_coat_length" : dog.coat_length,
        "d_spayed" : dog.spayed,
        "d_compatibility": d_compatibility,
        "d_special_need" : dog.special_need_dog,
        "d_activity" : dog.activity_level,
    }
    return dog_info


def get_user_data(response):
    """
    Constructs a dictionary of user adoption preferences for dog.

    Parameters:
    response (obj): response object containing user input data.

    Returns:
    dict: A dictionary of user preferences and data.
    """
    user_data = {
        "prefered_breed" : {"prefered_breed": response.getlist('q1')},
        "prefers_mixed_breed" : bool(int(response.get('q2'))) if response.get('q2') is not None else None,
        "age_preference" : {"age_preference": response.getlist('q3')},
        "size_preference" : {"size_preference": response.getlist('q4')},
        "color_preference" : {"color_preference":response.getlist('q5')},
        "spay_needed" : bool(int(response.get('q6'))) if response.get('q6') is not None else None,
        "coat_length_preference" : response.get('q7'),
        "dog_with_children" : bool(int(response.get('q8'))) if response.get('q8') is not None else None,
        "dog_with_dogs" : bool(int(response.get('q9'))) if response.get('q9') is not None else None,
        "dog_with_cats" : bool(int(response.get('q10'))) if response.get('q10') is not None else None,
        "dog_with_sm_animals" : bool(int(response.get('q11'))) if response.get('q11') is not None else None,
        "dog_with_big_animals" : bool(int(response.get('q12'))) if response.get('q12') is not None else None,
        "dog_in_house" : bool(int(response.get('q13'))) if response.get('q13') is not None else None,
        "yard" : bool(int(response.get('q14'))) if response.get('q14') is not None else None,
        "park" : bool(int(response.get('q15'))) if response.get('q15') is not None else None,
        "activity_level" : response.get('q16'),
        "special_need_dog" : bool(int(response.get('q17'))) if response.get('q17') is not None else None,
        "user_id" : current_user.id
        }
    return user_data

def get_user_info(user):
    """
    Formats user data for display on a preferences page.

    Parameters:
    dog (Dog): The user for which the data is to be formatted

    Returns:
    dict: A dictionary containing the formatted user data
    """
    u_needs= ['children' if user.dog_with_children else '', 'dogs' if user.dog_with_dogs else '', 'cats' if user.dog_with_cats else '',\
            'small animals' if user.dog_with_sm_animals else '', 'big animals' if user.dog_with_big_animals else '']
    u_needs = [need for need in u_needs if need != '']
    
    u_info = {
        "u_mixed_breed" : user.prefers_mixed_breed,
        "u_prefered_breed" : user.prefered_breed['prefered_breed'][:],
        "u_prefered_size" : user.size_preference['size_preference'][:],
        "u_prefered_age" : user.age_preference['age_preference'][:],
        "u_prefered_color" : user.color_preference['color_preference'][:],
        "u_prefered_coat_length" : user.coat_length_preference,
        "u_spay_needed" : user.spay_needed,
        "u_needs": u_needs,
        "u_special_need" : user.special_need_dog,
        "u_activity" : user.activity_level,
        "u_dog_in_house" : user.dog_in_house,
        "u_yard": user.yard,
        "u_park": user.park
    }
    return u_info

def remove_none_values(dictionary):
    """
    Recursively removes all key-value pairs in a dictionary where the value is None or an empty list.
    """
    return {key: remove_none_values(value) if isinstance(value, dict) else value for key, value in dictionary.items() if value is not None and value != [] }

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
    genders = ['male','female']

    chosen_cities=[]
    if request.method == "GET":
        chosen_cities = request.args.getlist('city') if request.args.getlist('city') else []
        chosen_gender = request.args.get('gender') if request.args.get('gender') else None
        
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