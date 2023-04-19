import os
from flask import Blueprint, render_template, request, abort, flash, redirect, url_for, current_app
from flask_login import login_required, current_user, login_user, logout_user
from website.models import db
from website.models import User, Post, UserInfo 
from werkzeug.security import generate_password_hash, check_password_hash
from website.users.forms import UserFormSignUp, UserFormLogIn, UserSetUp, RequestResetForm,\
      ResetPasswordForm, RequestVerificationForm
import jwt
from website.tasks import send_mail
from website.users.utils import verification_mail, save_picture, send_reset_email,\
      remove_none_values, querying_breeds, get_user_info, get_user_data               
from flask_babel import gettext

users = Blueprint('users', __name__)

@users.route("/sign-up", methods = ['GET','POST'])
def sign_up():
    """
    Handles the sign-up process of a new user.
    If the user is already authenticated, it redirects the user to the home page.
    It creates a new user account if the form data is valid and the email does not exist already in the database.
    It sends a verification email to the user's email address to confirm the email.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
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
                new_user = User(email = email, first_name = first_name, password = \
                                generate_password_hash(password1, method = 'sha256'), image_file = image_file)
                db.session.add(new_user)
                db.session.commit()
                message3 = gettext('Account created!')
                flash(message3,'success')
            return redirect(url_for('users.login'))
        
    return render_template("sign_up.html", user = current_user, form = form)

@users.route("/verify_email/<token>")
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
        return redirect(url_for('users.login'))
    if email:
        user = User.query.filter_by(email = email).first()
        user.is_verified = True
        db.session.commit()
        message2 = gettext('Your account has been verified. You may log in now.')
        flash(message2,'success')
    return redirect(url_for('users.login'))

@users.route("/login", methods = ['GET', 'POST'])
def login():
    """
    This function handles the user login process.
    If the user is already authenticated, it redirects the user to the home page.
    It validates the login form data and logs in the user if the email and password are correct.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = UserFormLogIn()
    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user:
            if user.is_verified:
                if check_password_hash(user.password, password):
                    message1 = gettext('Logged in successfully!')
                    flash(message1, category = 'success') 
                    login_user(user, remember = True) 
                    next_page = request.args.get('next') 
                    return redirect(next_page) if next_page else redirect(url_for('main.home'))
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

@users.route("/reverification", methods = ['GET', 'POST'])
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
        else:
            message2 = gettext('Account does not exist.')
            flash(message2, 'warning')

    title = gettext("Request verification mail")
    return render_template('reset_request.html', form = form, user = current_user, title = title)

@users.route("/logout")
@login_required    
def logout():
    """
    Logs out the current user and redirect to the welcome page.
    """
    logout_user()
    return redirect(url_for('main.welcome'))

@users.route("/set-profile", methods=['GET', 'POST'])
@login_required
def set_profile():
    """
    Renders and handles the set profile form.

    GET: Renders the set profile form with the user's current information.
    POST: Handles form submission. If the form is valid, updates the user's first name,
    email address, and/or profile pictureand shows a success message. If a new email address 
    is entered, sends a verification email and redirects to the My Profile page.
    If the form is invalid, show the same form with errors.
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
            return redirect(url_for('users.my_profile'))
        if form.data['picture']:
            profile_pic = save_picture(form.picture.data)
            previous_pic = current_user.image_file
            current_user.image_file = profile_pic
            if previous_pic != "default.jpg":
                os.remove(current_app.root_path + '/static/profile_pics/' + previous_pic)
            message3 = gettext('Your account has been updated!')
            flash(message3, 'success')
        db.session.commit()
        return redirect(url_for('users.my_profile'))

    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.email.data = current_user.email
    return render_template('set_profile.html', user = current_user, form= form, image_file = image_file)

@users.route("/verify_new_email/<token>")
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
        return redirect(url_for('users.set_profile'))
    if email:
        current_user.email = email
        current_user.is_verified = True
        db.session.commit()
        message2 = gettext('Your new email has been verified. You may log in now.')
        flash(message2,'success')
        return redirect(url_for('users.my_profile'))

@users.route("/reset-password", methods=['GET', 'POST'])
def reset_request():
    """
    Sends an email with instructions for resetting a user's password.

    If the user is already authenticated, redirects to the home page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        message1 = gettext('An email has been sent with instructions to reset your password.')
        flash(message1, 'success')
        return redirect(url_for('users.login'))
    title = gettext('Request password reset')
   
    return render_template('reset_request.html', form = form, user = current_user, title = title)

@users.route("/reset-password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    """Resets a user's password.

    Args:
        token (str): A JWT token containing the user's information.

    If the user is already authenticated, redirects to the home page.
    If the user's password is updated, redirects to the login page with a success message.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_token(token)  
    if user is None:
        message1 = gettext('Your token is either invalid or expired.')
        flash(message1,'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password1.data, method = 'sha256')
        user.password = hashed_password
        db.session.commit()
        message2 = gettext('Your password has been updated! You are now able to log in')
        flash(message2,'success')
        return redirect(url_for('users.login'))
    
    return render_template('reset_password.html', form=form, user = current_user)

@users.route("/profile")
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

@users.route("/profile/<int:user_id>")
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

@users.route("/questionnaire", methods=['GET', 'POST'])
@login_required
def user_info():
    """
    Displays a form for the user to provide information about themselves
    in order system to propose the best matches for adoption. 
    
    Also includes a list of dogs waiting for adoption the longest.
    """
    if request.method == 'GET':
        posts = Post.query.filter(Post.user_id != current_user.id).order_by(Post.date_posted.asc()).limit(8).all()
        breeds = querying_breeds()
        info = UserInfo.query.filter_by(user_id = current_user.id).first()
        if info:
            message1 = gettext('You have already filled out the questionnaire.')
            flash(message1,'warning')
            return redirect(url_for('main.show_matches'))
    if request.method == 'POST':
        response = request.form
        user_data = get_user_data(response)
        message2 = gettext('You successfully submited your answers. Here are your matches!')
        flash(message2, 'success')
    
        info = UserInfo(**user_data)
        db.session.add(info)
        db.session.commit()
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('main.show_matches'))

    return render_template('user_info.html', user = current_user, breeds = sorted(breeds), posts = posts)

@users.route("/edit", methods=['GET', 'POST'])
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
        breeds = querying_breeds()
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
        return redirect(next_page) if next_page else redirect(url_for('main.show_matches'))

    return render_template('edit_user_info.html', user = current_user, breeds = sorted(breeds), posts = posts)

@users.route("/user-info/<int:user_id>")
def user_preferences(user_id):
    """
    View function for displaying the user's submitted adoption preferences.

    Args:
        user_id (int): The ID of the user whose preferences are being displayed.
    """
    user = UserInfo.query.filter_by(user_id = user_id).first()
    u_info = get_user_info(user)
    return render_template('user_preferences.html', u_info = u_info)