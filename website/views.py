
import os
from flask import render_template, request, flash, redirect, url_for, current_app, abort, jsonify, make_response
from flask_login import login_required, current_user, login_user, logout_user
from .models import db
from .models import User, Post, UserInfo, DogInfo
from werkzeug.security import generate_password_hash, check_password_hash
from .user_form import UserFormSignUp, UserFormLogIn, UserSetUp, RequestResetForm, ResetPasswordForm, PostForm, RequestVerificationForm
from . import session
from sqlalchemy import  update, and_, case, or_, func
import jwt
from .tasks import send_mail
from .utils import verification_mail, email, save_picture, remove_none_values, send_reset_email, get_dog_data, get_dog_info, get_user_data, get_user_info, filtering
from flask_babel import gettext, get_locale, get_translations
import time

def welcome():
    """
    Displays a welcome page to the user.
    If the user is already authenticated, it redirects the user to the home page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    response=make_response(render_template('welcome.html'))
    language = request.args.get('lang')
    if language:
        response = make_response(redirect("/"))
        response.set_cookie('lang', language, max_age = 604800)
    return response
    
def sign_up():
    """
    Handles the sign-up process of a new user.
    If the user is already authenticated, it redirects the user to the home page.
    It creates a new user account if the form data is valid and the email does not exist already in the database.
    It sends a verification email to the user's email address to confirm the email.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = UserFormSignUp()
    if form.validate_on_submit():
        email = (form.data['email']).lower()
        first_name = form.data['first_name']
        password1 = form.data['password1']
        image_file = 'default.jpg'

        email_exists = User.query.filter_by(email = email).first()
        if email_exists:
            message1 = gettext('The email address you\'re trying to add has been registered with the account already.')
            flash(message1,'error')
        else:
            if email:
                verification_mail(email)
                message2 = gettext('Verification email sent! Please check your inbox.')
                flash(message2,'success')
                new_user = User(email = email, first_name = first_name, password = generate_password_hash(password1, method = 'sha256'), image_file = image_file)
                db.session.add(new_user)
                db.session.commit()
                message3 = gettext('Account created!')
                flash(message3,'success')
            return redirect(url_for('login'))
        
    return render_template("sign_up.html", user = current_user, form = form)

    
def verify_email(token):
    """
    Verifies the user's email address by decoding the token sent to the user's email.
    It sets the user's "is_verified" attribute to True if the token is valid.
    """
    secret_key = os.environ.get('secret_key')
    try:
        email = jwt.decode(token, secret_key, algorithms=['HS256'])['email']
    except:
        message1 = gettext('Your token is either invalid or expired.')
        flash(message1,'warning')
        return redirect(url_for('login'))
    if email:
        user = User.query.filter_by(email = email).first()
        user.is_verified = True
        db.session.commit()
        message2 = gettext('Your account has been verified. You may log in now.')
        flash(message2,'success')
    return redirect(url_for('login'))

def login():
    """
    This function handles the user login process.
    If the user is already authenticated, it redirects the user to the home page.
    It validates the login form data and logs in the user if the email and password are correct.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = UserFormLogIn()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user:
            if user.is_verified:
                if check_password_hash(user.password, password):
                    message1 = gettext('Logged in successfully!')
                    flash(message1, category = 'success') 
                    login_user(user, remember = True) 
                    next_page = request.args.get('next') 
                    return redirect(next_page) if next_page else redirect(url_for('home'))
                else:
                    message2 = gettext('Incorrect password, try again')
                    flash(message2, category = 'error')
            else:
                message3 = gettext('Email is not verified.')
                flash(message3, category = 'error')
        else:
            message4 = gettext('Account does not exist.')
            flash(message4, category = 'error')
  
    return render_template("login.html", user = current_user, form = form)

def resend_verification():
    """
    Renders and handles the resend verification form.

    If the form is valid, sends a verification email to the entered email address
    and shows a success message. If the email address is not associated with an existing user, gives the error message.
    """
    form = RequestVerificationForm()
    if request.method == 'POST':
        email = form.email.data
        if User.query.filter_by(email = email).first():
                verification_mail(email)
                message1 = gettext('Verification email sent! Please check your inbox.')
                flash(message1,'success')
                title = gettext("Request verification mail")
    return render_template('reset_request.html', form = form, user = current_user, title = title)

@login_required    
def logout():
    """
    Logs out the current user and redirect to the welcome page.
    """
    logout_user()
    return redirect(url_for('welcome'))

@login_required
def set_profile():
    """
    Renders and handles the set profile form.

    GET: Renders the set profile form with the user's current information.
    POST: Handles form submission. If the form is valid, updates the user's first name, email address, and/or profile picture
    and shows a success message. If a new email address is entered, sends a verification email and redirects to the My Profile
    page. If the form is invalid, show the same form with errors.
    """
    form = UserSetUp()
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    if form.validate_on_submit():
        if form.data['first_name'] != current_user.first_name:
            current_user.first_name = form.data['first_name']
            message1 = gettext('Your account has been updated!')
            flash(message1, 'success')
        if form.data['email'] != current_user.email:
            email = form.data['email']
            verification_mail(email, first_mail_adress=False)
            message2 = gettext('Verification email sent! Please check your inbox.')
            flash(message2,'success')
            return redirect(url_for('my_profile'))
        if form.data['picture']:
            profile_pic = save_picture(form.picture.data)
            previous_pic = current_user.image_file
            current_user.image_file = profile_pic
            if previous_pic != "default.jpg":
                os.remove(current_app.root_path + '/static/profile_pics/' + previous_pic)
            message3 = gettext('Your account has been updated!')
            flash(message3, 'success')
        db.session.commit()
        return redirect(url_for('my_profile'))

    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.email.data = current_user.email
    return render_template('set_profile.html', user = current_user, form= form, image_file = image_file)

@login_required
def verify_new_email(token):
    """Verifies a new email address for the current user.

    Args:
        token: A JWT token containing the encoded email address.

    Returns:
        If the token is valid and the email address is updated: A redirection to the My Profile page with a success message.
        If the token is invalid or expired: A redirection to the Edit Profile page with an error message.
    """
    secret_key = os.environ.get('secret_key')
    try:
        email = jwt.decode(token, secret_key, algorithms=['HS256'])['email']
    except:
        message1 = gettext('Your token is either invalid or expired.')
        flash(message1,'warning')
        return redirect(url_for('set_profile'))
    if email:
        current_user.email = email
        current_user.is_verified = True
        db.session.commit()
        message2 = gettext('Your new email has been verified. You may log in now.')
        flash(message2,'success')
        return redirect(url_for('my_profile'))

def reset_request():
    """
    Sends an email with instructions for resetting a user's password.

    If the user is already authenticated, redirects to the home page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        message1 = gettext('An email has been sent with instructions to reset your password.')
        flash(message1, 'success')
        return redirect(url_for('login'))
    title = gettext('Request password reset')
   
    return render_template('reset_request.html', form = form, user = current_user, title = title)


def reset_token(token):
    """Resets a user's password.

    Args:
        token (str): A JWT token containing the user's information.

    If the user is already authenticated, redirects to the home page.
    If the user's password is updated, redirects to the login page with a success message.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)  
    if user is None:
        message1 = gettext('Your token is either invalid or expired.')
        flash(message1,'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password1.data, method = 'sha256')
        user.password = hashed_password
        db.session.commit()
        message2 = gettext('Your password has been updated! You are now able to log in')
        flash(message2,'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', form=form, user = current_user)

    
@login_required
def my_profile(page=1):
    """Displays the current user's profile page with the current user's posts, profile, and saved dogs.

    Args:
        page (int): The current page number for the paginated posts.

    """
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(user_id = current_user.id).order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
    profile = User.query.filter_by(id = current_user.id).first()
    saved = []
    if profile:
        saved_dogs = profile.saved_dogs
        if saved_dogs:
            saved_dogs = set(saved_dogs['saved'])
            for id in saved_dogs:
                dog = Post.query.filter_by(id = id).first()
                if dog != None:
                    saved.append(dog)

    return render_template('user.html', posts = posts, user = current_user, author = profile, saved = saved)

def user(user_id, page = 1):
    """
    Renders a user-foster parent profile page with their adoption posts.

    Args:
        user_id: The id of the user whose profile is being viewed.
        page: The current page number of the post pagination.
    """
    author = User.query.filter_by(id = user_id).first()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(user_id = user_id).order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
    return render_template('user.html', posts = posts, user = current_user, author = author)


@login_required
def contact_foster(foster_id):
    """
    Renders a contact form for the current user to send an email to a foster parent.

    Args:
        foster_id: The id of the foster parent being contacted.
    """
    foster_parent = User.query.filter_by(id = foster_id).first()
    
    if request.method == 'POST':
        email()
        message1 = gettext('Your email has been sent!')
        flash(message1,'success')
        
    return render_template('email_form.html', foster_parent = foster_parent)




def home(page = 1):
    """
    Renders the home page with the available dog posts and the filtering options.

    Args:
        page: The current page number of the post pagination.
    """
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
    
    cities = set()
    for post in session.query(Post.city).distinct():
        cities.add(post.city)

    query_object = Post.query 
    saved_posts, genders, filtered_posts, chosen_cities, chosen_gender = filtering(query_object, page)

    return render_template("home.html", user = current_user, posts = filtered_posts if filtered_posts else posts, cities = sorted(cities),\
                            genders = genders, chosen_cities = chosen_cities, chosen_gender = chosen_gender, saved_posts = saved_posts)

@login_required
def new_post():
    """
    View function for creating a new adoption post.
    """
    form = PostForm()
    if form.validate_on_submit():
        photo = form.picture.data
        image_name = save_picture(photo)
        city = form.city.data
        gender = (form.gender.data)
        post = Post(title=form.title.data, data=form.data.data, user_id = current_user.id, image_file = image_name, city = city, gender = gender)
        db.session.add(post)
        db.session.commit()
    
        response = request.form
        dog_data = get_dog_data(response, post)

        dog = DogInfo(**dog_data)
        db.session.add(dog)
        db.session.commit()

        return redirect(url_for('home'))
    return render_template('new_post.html', user = current_user, form = form)

def post(post_id):
    """
    View function for displaying an adoption post with given post_id. 
    If the user is author contains update, delete and dog info buttons.
    Otherwise contains buttons for contacting foster parent and checking the fit with the dog.
    """
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post = post, user = current_user)

@login_required
def update_post(post_id):  
    """
    View function for updating an existing adoption post with given post_id.
    """ 
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        abort(403)
    form1 = PostForm()
    if form1.validate_on_submit():
        post.title = form1.title.data
        post.data = form1.data.data
        post.gender = form1.gender.data
        post.city = form1.city.data
        if form1.picture.data:
            current_image = post.image_file
            os.remove(current_app.root_path + '/static/profile_pics/' + current_image)
            photo = form1.picture.data 
            post.image_file = save_picture(photo)
        db.session.add(post)
        db.session.commit()
        message1 = gettext('Your adoption post has been updated!')
        flash(message1, 'success')

        response = request.form
        dog_data = get_dog_data(response, post)
        
        db.session.query(DogInfo).filter(DogInfo.post_id==post.id).update(dog_data)
        db.session.commit()
       
        return redirect(url_for('post', post_id = post.id, user = current_user))
    
    elif request.method == 'GET':
        image_file = url_for('static', filename='profile_pics/' + post.image_file)
        form1.title.data = post.title
        form1.data.data = post.data
        form1.city.data = post.city
        form1.gender.data = post.gender
        form1.picture.data = image_file
    return render_template('update_post.html', form = form1, user = current_user)

@login_required
def delete_post(post_id):
    """
    View function for deleting an existing adoption post with given post_id.
    """
    post = Post.query.get_or_404(post_id)
    dog = DogInfo.query.filter_by(post_id = post_id).first()
    if post.user_id != current_user.id:
        abort(403)
    current_image = post.image_file
    os.remove(current_app.root_path + '/static/profile_pics/' + current_image)
    db.session.delete(post)
    db.session.delete(dog)
    db.session.commit()
    message1 = gettext('Your adoption post has been removed!')
    flash(message1, 'success')
    return redirect(url_for('home'))

def comparison(post_id):
    """
    Returns a comparison of user preferences and dog traits 
    for a given post ID and current user.
    """
    dog = DogInfo.query.filter(DogInfo.post_id == post_id).first()
    if current_user.is_authenticated: 
        user = UserInfo.query.filter_by(user_id = current_user.id).first()
        if not user:
            return redirect(url_for('user_info'))       
    else:
        return redirect(url_for('login'))
    
    user_info = get_user_info(user)
    dog_info = get_dog_info(dog)
    comparison = {**user_info, **dog_info}
    comparison = {k: v for k, v in comparison.items() if v}
    return render_template('comparison.html', comparison = comparison)

@login_required
def email_form(post_id):
    """
    Displays a form for the user to send an email to foster parent about a given post.

    Args:
        post_id (int): The ID of the post to send an email about.
    """
    post = Post.query.filter(Post.id == post_id).first()
    if request.method == 'POST':
        email()
        message1 = gettext('Your email has been sent!')
        flash(message1,'success')
        
    return render_template('email_form.html', user = current_user, post = post)
    

@login_required
def dog_info(post_id):
    """Displays information about a dog associated with the post.

    Args:
        post_id (int): The ID of the post to display dog information about.
    """
    dog = DogInfo.query.filter(DogInfo.post_id == post_id).first()
    dog_info = get_dog_info(dog)
        
    return render_template('dog_info.html', dog_info = dog_info)
    

@login_required
def user_info():
    """
    Displays a form for the user to provide information about themselves
    in order system to propose the best matches for adoption. 
    
    Also includes a list of dogs waiting for adoption the longest.
    """
    if request.method == 'GET':
        posts = Post.query.filter(Post.user_id != current_user.id).order_by(Post.date_posted.asc()).limit(10).all()
        breeds = set()
        for dog in session.query(DogInfo.primary_breed).filter(DogInfo.primary_breed != ('unknown' and 'Unknown' and 'Nepoznata' and 'nepoznata')).distinct():
            breeds.add((dog.primary_breed).capitalize())
        info = UserInfo.query.filter_by(user_id = current_user.id).first()
        if info:
            message1 = gettext('You have already filled out the questionnaire.')
            flash(message1,'warning')
            return redirect(url_for('show_matches'))
    if request.method == 'POST':
        response = request.form
        user_data = get_user_data(response)
        message2 = gettext('You successfully submited your answers. Here are your matches!')
        flash(message2, 'success')
    
        info = UserInfo(**user_data)
        db.session.add(info)
        db.session.commit()
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('show_matches'))

    return render_template('user_info.html', user = current_user, breeds = sorted(breeds), posts = posts)

@login_required
def edit_user_info():
    """
    View function for editing user information. Only authenticated users can access this view.

    If the user has not submitted any information, returns a 403 error.

    Updates the user's information in the database and redirects the user to the matches page.
    """
    info = UserInfo.query.filter_by(user_id = current_user.id).first()
    if request.method == 'GET':
        if not info:
            abort(403)
        posts = Post.query.filter(Post.user_id != current_user.id).order_by(Post.date_posted.asc()).limit(8).all()
        breeds = set()
        for dog in session.query(DogInfo.primary_breed).filter(DogInfo.primary_breed != ('unknown' or 'Unknown')).distinct():
            breeds.add((dog.primary_breed).capitalize())
    if request.method == 'POST':
        response = request.form
        user_update_data = get_user_data(response)
        message2 = gettext('You successfully submited your new answers. Here are your matches!')
        flash(message2, 'success')
        
        user_update_data = remove_none_values(user_update_data)
        user_update_data = {k:v for k,v in user_update_data.items() if v != {}}
        db.session.query(UserInfo).filter(UserInfo.user_id==current_user.id).update(user_update_data)
        db.session.commit()
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('show_matches'))

    return render_template('edit_user_info.html', user = current_user, breeds = sorted(breeds), posts = posts)

def user_preferences(user_id):
    """
    View function for displaying the user's submitted adoption preferences.

    Args:
        user_id (int): The ID of the user whose preferences are being displayed.
    """
    user = UserInfo.query.filter_by(user_id = user_id).first()
    u_info = get_user_info(user)
    return render_template('user_preferences.html', u_info = u_info)


@login_required
def show_matches(page = 1):
    """
    View function for displaying the adoption matches for the current user 
    made through sql statements and comparing different cases of user preferences and dog traits.

    Args:
        page (int): The current page number of the paginated results. Defaults to 1.

    Also has the feature of filtering posts by city and gender and saving dogs for the later review.
    """
    page = int(request.args.get('page', 1))
    user_info = UserInfo.query.filter_by(user_id = current_user.id).first()
    if not user_info:
        return redirect(url_for('user_info'))
    
    prefered_breeds = (session.query(UserInfo.prefered_breed).filter(UserInfo.user_id == current_user.id).all())[0][0]['prefered_breed']
    age_preference = (session.query(UserInfo.age_preference).filter(UserInfo.user_id == current_user.id).all())[0][0]['age_preference']
    size_preference = (session.query(UserInfo.size_preference).filter(UserInfo.user_id == current_user.id).all())[0][0]['size_preference']
    color_preference = (session.query(UserInfo.color_preference).filter(UserInfo.user_id == current_user.id).all())[0][0]['color_preference']
    
    result = db.session.query(Post, DogInfo, UserInfo).join(DogInfo, Post.id == DogInfo.post_id)\
            .join(UserInfo, UserInfo.user_id == current_user.id, isouter=True)\
            .filter( UserInfo.user_id == current_user.id)\
            .filter(case(('all' not in age_preference, DogInfo.age.in_(age_preference)), else_= True))\
            .filter(case(('all' not in prefered_breeds, DogInfo.primary_breed.in_(prefered_breeds)), else_= True))\
            .filter(case((UserInfo.prefers_mixed_breed == False, DogInfo.mixed_breed == UserInfo.prefers_mixed_breed), else_= True))\
            .filter(case(('all' not in size_preference, DogInfo.size.in_(size_preference)), else_= True))\
            .filter(case(('all' not in color_preference, DogInfo.color.in_(color_preference)), else_= True))\
            .filter(case((UserInfo.coat_length_preference != 'all', DogInfo.coat_length == UserInfo.coat_length_preference), else_= True))\
            .filter(case((UserInfo.dog_with_children == True, UserInfo.dog_with_children == DogInfo.dog_with_children), else_= True))\
            .filter(case((UserInfo.dog_with_dogs == True, UserInfo.dog_with_dogs == DogInfo.dog_with_dogs),else_= True))\
            .filter(case((UserInfo.dog_with_cats == True, UserInfo.dog_with_cats == DogInfo.dog_with_cats), else_= True))\
            .filter(case((UserInfo.dog_with_sm_animals == True, UserInfo.dog_with_sm_animals == DogInfo.dog_with_sm_animals), else_= True))\
            .filter(case((UserInfo.dog_with_big_animals == True, UserInfo.dog_with_big_animals == DogInfo.dog_with_big_animals), else_= True))\
            .filter(case((UserInfo.special_need_dog == False, UserInfo.special_need_dog == DogInfo.special_need_dog), else_= True))\
            .filter(case((UserInfo.spay_needed == True, UserInfo.spay_needed == DogInfo.spayed), else_= True))\
            .filter(case((UserInfo.dog_in_house == False,and_(DogInfo.age != "puppy", DogInfo.size != 'small')), else_= True))\
            .filter(Post.user_id != current_user.id)\
            .filter(case(
                    (and_(or_(UserInfo.yard == True , UserInfo.park == True),UserInfo.activity_level == 'high'),DogInfo.activity_level.in_(['low','medium','high'])),
                    (and_(UserInfo.yard == False , UserInfo.park == False, UserInfo.activity_level == 'high'), DogInfo.activity_level != 'high'),
                    (and_(or_(UserInfo.yard == True , UserInfo.park == True), UserInfo.activity_level == 'medium'), DogInfo.activity_level.in_(['medium','low'])),
                    (and_(UserInfo.yard == False , UserInfo.park == False, UserInfo.activity_level == 'medium'), DogInfo.activity_level.in_(['medium','low'])), 
                    else_= (UserInfo.activity_level == DogInfo.activity_level)))       

    warning = None
    result1 = result.order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
    if not result1.items:
        message1 = gettext('Oops, it seems there aren\'t matches for your preferences...')
        flash(message1, category='error')
        warning = gettext("Check if there are preferences that can be modified or take a look at some of the our random choices.")
    else:   
        result1, warning = result.filter(case((and_(UserInfo.dog_in_house == False, UserInfo.yard == False), False), else_=True))\
        .order_by(Post.date_posted.desc()).paginate(page=page, per_page=8), None
        
        if not result1.items:
            warning = gettext("If you would not keep a dog in the house and if there is no yard, then where would the dog live?\
            Please check your answers.")
            message2 = gettext('Oops, it seems there aren\'t matches for your preferences...')
            flash(message2, category='error')
    
    alternative_results = db.session.query(Post, DogInfo, UserInfo).join(DogInfo, Post.id == DogInfo.post_id)\
            .join(UserInfo, UserInfo.user_id == current_user.id, isouter=True)\
            .filter(Post.user_id != current_user.id).order_by(func.random()).limit(8)

    city_query = result.with_entities(Post.city).distinct()
    cities = set()
    for post in city_query:
        cities.add(post.city)
    saved_posts, genders, filtered_result1, chosen_cities, chosen_gender = filtering(result, page)
         
    return render_template('show_matches.html', alternative_posts = alternative_results,warning = warning ,user = current_user, posts = filtered_result1 if filtered_result1 else result1, cities = sorted(cities), genders = genders, chosen_cities = chosen_cities, chosen_gender = chosen_gender, saved_posts = saved_posts )


def saved():
    """
    Toggle saving/un-saving a post for the current user.

    Expects a JSON payload in the request with a 'saved' field containing a
    dictionary with a 'postId' field specifying the ID of the post to be saved.

    If the post is not already saved by the current user, it will be added to
    their saved posts list. Otherwise, it will be removed from the list.

    Returns a JSON response with a 'message' field indicating whether the
    operation was successful (always 'success' if no error was raised) and a
    HTTP status code of 200.
    """
    data = request.get_json()
    saved = data.get('saved')
    post_id = saved.get('postId')
    saved_dogs = current_user.saved_dogs
    if post_id not in saved_dogs['saved']:
        saved_dogs['saved'].append(post_id)
    else:
        saved_dogs['saved'].remove(post_id)
    update = {"saved_dogs":saved_dogs}
    db.session.query(User).filter(User.id==current_user.id).update(update)
    db.session.commit()
    res = make_response(jsonify({"message":'successfull'}),200)
    return res

