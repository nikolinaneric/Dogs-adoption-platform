import secrets
import os
from PIL import Image
from flask import render_template, request, flash, redirect, url_for, current_app, abort, jsonify, make_response
from flask_login import login_required, current_user, login_user, logout_user
from .models import db
from .models import User, Post, UserInfo, DogInfo
from werkzeug.security import generate_password_hash, check_password_hash
from .user_form import UserFormSignUp, UserFormLogIn, UserSetUp, RequestResetForm, ResetPasswordForm, PostForm, RequestVerificationForm
from flask_mail import Message
from . import mail, session
from sqlalchemy import  update,and_, case, or_, func
import jwt
import datetime
from .tasks import send_mail




def welcome():
    return render_template('welcome.html')

def home(page = 1):
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
    cities = set()
    saved_posts = []
    if current_user.is_authenticated:
        saved_dogs = current_user.saved_dogs
        if saved_dogs:
            saved_posts = saved_dogs['saved']
            saved_posts = [int(id) for id in saved_posts]
    for post in session.query(Post.city).distinct():
        cities.add(post.city)
    genders = ['male','female']
    chosen_cities=[]
    if request.method == "GET":
        chosen_cities = request.args.getlist('city') if request.args.getlist('city') else []
        chosen_gender = request.args.get('gender') if request.args.get('gender') else None
        
        if chosen_cities and chosen_gender:
            posts = Post.query.filter(case(('all' not in chosen_cities, Post.city.in_(chosen_cities)), else_= True))\
                    .filter(case((chosen_gender != 'all', Post.gender == chosen_gender), else_= True))\
                    .order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
        elif chosen_cities:
            posts = Post.query.filter(case(('all' not in chosen_cities, Post.city.in_(chosen_cities)), else_= True))\
                .order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
        elif chosen_gender:
            posts = Post.query.filter(case((chosen_gender != 'all', Post.gender == chosen_gender), else_= True))\
                .order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
        
    
    return render_template("home.html", user = current_user, posts = posts, cities = cities, genders = genders, chosen_cities = chosen_cities, chosen_gender = chosen_gender, saved_posts = saved_posts)
    

def login():
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
                    flash('Logged in successfully!', category = 'success') 
                    login_user(user, remember = True) 
                    next_page = request.args.get('next') 
                    return redirect(next_page) if next_page else redirect(url_for('home'))
                    
                else:
                    flash('Incorrect password, try again', category = 'error')
            else:
                flash('Email is not verified.', category = 'error')
        else:
            flash('Account does not exist.', category = 'error')
  
    return render_template("login.html", user = current_user, form = form)

def resend_verification():
    form = RequestVerificationForm()
    if request.method == 'POST':
        email = form.email.data
        if (User.query.filter_by(email = email).first()):
                    secret_key = 'mysecretkey'
                    verification_token = jwt.encode({'email': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, secret_key, algorithm='HS256')
                    verification_url = url_for('verify_email', token=verification_token, _external=True)
                    subject = 'Email Verification'
                    sender = "dogs.people.connect@gmail.com" 
                    recipients=[email]
                    message_body = f'''To verify your account, please visit the following link: {verification_url}   
                        If you did not make this request then simply ignore this email and no changes will be made.
                    '''
                    send_mail.delay(subject, sender, recipients, message_body)
                    flash('Verification email sent! Please check your inbox.','info')
    return render_template('reset_request.html', form = form, user = current_user, title = "Request verification mail")
@login_required    
def logout():
    logout_user()
    return redirect(url_for('welcome'))

def sign_up():
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
            flash('The email address you\'re trying to add has been registered with the account already.','error')
        else:
            if email:
                secret_key = 'mysecretkey'
                verification_token = jwt.encode({'email': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, secret_key, algorithm='HS256')
                verification_url = url_for('verify_email', token=verification_token, _external=True)
                subject = 'Email Verification'
                sender = "dogs.people.connect@gmail.com" 
                recipients=[email]
                message_body = f'''To verify your account, please visit the following link: {verification_url}   
                    If you did not make this request then simply ignore this email and no changes will be made.
                '''
                send_mail.delay(subject, sender, recipients, message_body)
                flash('Verification email sent! Please check your inbox.','info')
                try:
                    new_user = User(email = email, first_name = first_name, password = generate_password_hash(password1, method = 'sha256'), image_file = image_file)
                    db.session.add(new_user)
                    db.session.commit()
                    flash('Account created!', category='success')
                except:
                    flash('Check your inbox for the verification mail')
            return redirect(url_for('login'))
        
    return render_template("sign_up.html", user = current_user, form = form)

def verify_email(token):
    secret_key = 'mysecretkey'
    try:
        email = jwt.decode(token, secret_key, algorithms=['HS256'])['email']
    except:
        flash('Your token is either invalid or expired.','error')
        return redirect(url_for('login'))
    if email:
        user = User.query.filter_by(email = email).first()
        user.is_verified = True
        db.session.commit()
        flash('Your account has been verified. You may log in now.','success')
    return redirect(url_for('login'))

def save_picture(form_picture):
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

@login_required
def set_profile():
    form = UserSetUp()
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    if form.validate_on_submit():
        if form.data['email'] != current_user.email:
            email = form.data['email']
            secret_key = 'mysecretkey'
            verification_token = jwt.encode({'email': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, secret_key, algorithm='HS256')
            verification_url = url_for('verify_new_email', token=verification_token, _external=True)
            subject = 'Email Verification' 
            sender = "dogs.people.connect@gmail.com" 
            recipients=[email]
            message_body = f'''To verify your account, please visit the following link: {verification_url}   
                        If you did not make this request then simply ignore this email and no changes will be made.
                    '''
            send_mail.delay(subject, sender, recipients, message_body)
            flash('Verification email sent! Please check your inbox.','info') # ne radi flash
            return redirect(url_for('my_profile'))
        if form.data['picture']:
            profile_pic = save_picture(form.picture.data)
            previous_pic = current_user.image_file
            if previous_pic != "default.jpg":
                os.remove(current_app.root_path + '/static/profile_pics/' + previous_pic)
            current_user.image_file = profile_pic
            flash('Your account has been updated!', 'success')
        if form.data['first_name'] != current_user.first_name:
            current_user.first_name = form.data['first_name']
            flash('Your account has been updated!', 'success')
        db.session.commit()
        return redirect(url_for('my_profile'))

    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.email.data = current_user.email
        
    return render_template('set_profile.html', user = current_user, form= form, image_file = image_file)

@login_required
def verify_new_email(token):
    secret_key = 'mysecretkey'
    try:
        email = jwt.decode(token, secret_key, algorithms=['HS256'])['email']
    except:
        flash('Your token is either invalid or expired.','error')
        return redirect(url_for('set_profile'))
    if email:
        current_user.email = email
        current_user.is_verified = True
        db.session.commit()
        flash('Your new email has been verified.','info')
        return redirect(url_for('my_profile'))

def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
   
    return render_template('reset_request.html', form = form, user = current_user, title = "Request password reset")


def send_reset_email(user):
    token = user.get_reset_token()
    subject = 'Password Reset Request'
    sender='dogs.people.connect@gmail.com'
    recipients=[user.email]
    message_body = f'''To reset your password, visit the following link:
    {url_for('reset_token', token=token, _external=True)}  
    If you did not make this request then simply ignore this email and no changes will be made.
    '''
    send_mail.delay(subject, sender, recipients, message_body)


def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)  # vraca nam odgovarajuci user objekat na osnovu id iz tokena
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password1.data, method = 'sha256')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', form=form, user = current_user)

@login_required
def new_post():
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
        dog_data = {
        "primary_breed" : (response.get('a1')).lower(),
        "mixed_breed" : bool(int(response.get('a2'))),
        "age" : response.get('a3'),
        "size" : response.get('a4'),
        "color" : response.get('a5'),
        "spayed" : bool(int(response.get('a6'))),
        "coat_length" : response.get('a7'),
        "dog_with_children" : bool(int(response.get('a8'))),
        "dog_with_dogs" : bool(int(response.get('a9'))),
        "dog_with_cats" : bool(int(response.get('a10'))),
        "dog_with_sm_animals" : bool(int(response.get('a11'))), 
        "dog_with_big_animals" : bool(int(response.get('a12'))), 
        "activity_level" : response.get('a13'),
        "special_need_dog" : bool(int(response.get('a14'))),
        "post_id": post.id
        }

        dog = DogInfo(**dog_data)
        db.session.add(dog)
        db.session.commit()

        return redirect(url_for('home'))
    return render_template('new_post.html', user = current_user, form = form)

def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post = post, user = current_user)

def comparison(post_id):
    dog = DogInfo.query.filter(DogInfo.post_id == post_id).first()
    if current_user.is_authenticated: 
        user = UserInfo.query.filter_by(user_id = current_user.id).first()
        if not user:
            return redirect(url_for('user_info'))       
    else:
        return redirect(url_for('login'))
    d_compatibility = ['children' if dog.dog_with_children else '', 'dogs' if dog.dog_with_dogs else '', 'cats' if dog.dog_with_cats else '',\
            'small animals' if dog.dog_with_sm_animals else '', 'big animals' if dog.dog_with_big_animals else '']
    d_compatibility = [comp for comp in d_compatibility if comp != '']
    u_needs= ['children' if user.dog_with_children else '', 'dogs' if user.dog_with_dogs else '', 'cats' if user.dog_with_cats else '',\
            'small animals' if user.dog_with_sm_animals else '', 'big animals' if user.dog_with_big_animals else '']
    u_needs = [need for need in u_needs if need != '']

    comparison = {
        "d_mixed_breed" : dog.mixed_breed,
        "u_mixed_breed" : user.prefers_mixed_breed,
        "d_primary_breed" : dog.primary_breed,
        "u_prefered_breed" : user.prefered_breed['prefered_breed'][:],
        "d_size" : dog.size,
        "u_prefered_size" : user.size_preference['size_preference'][:],
        "d_age" : dog.age,
        "u_prefered_age" : user.age_preference['age_preference'][:],
        "d_color" : dog.color,
        "u_prefered_color" : user.color_preference['color_preference'][:],
        "d_coat_length" : dog.coat_length,
        "u_prefered_coat_length" : user.coat_length_preference,
        "d_spayed" : dog.spayed,
        "u_spay_needed" : user.spay_needed,
        "d_compatibility": d_compatibility,
        "u_needs": u_needs,
        "d_special_need" : dog.special_need_dog,
        "u_special_need" : user.special_need_dog,
        "d_activity" : dog.activity_level,
        "u_activity" : user.activity_level,
        "u_dog_in_house" : user.dog_in_house,
        "u_yard": user.yard,
        "u_park": user.park

    }
    comparison = {k: v for k, v in comparison.items() if v}
    return render_template('comparison.html', comparison = comparison)

@login_required
def email_form(post_id):
    post = Post.query.filter(Post.id == post_id).first()
    if request.method == 'POST':
        author = current_user.email
        recipient = request.form.get('recipient')
        message = request.form.get('message')
        subject = request.form.get('subject')
        sender = 'dogs.people.connect@gmail.com',
        recipients= [recipient],
        reply_to = author
        message_body = f" <p> {message} </p> <h4> This message was sent to you via <a href= {url_for('welcome', _external=True)}> dope connect <a/> app.</h4>"
        send_mail.delay(subject, sender, recipients, message_body, reply_to)
        flash('Your email has been sent!','success')
        
    return render_template('email_form.html', user = current_user, post = post)
    
@login_required
def dog_info(post_id):
    dog = DogInfo.query.filter(DogInfo.post_id == post_id).first()
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
        
    return render_template('dog_info.html', dog_info = dog_info)
    
    
@login_required
def update_post(post_id):   
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
        flash('Your post has been updated!', 'success')

        response = request.form
        dog_update_data = {
        "primary_breed" : (response.get('a1')).lower() if response.get('a1') else None,
        "mixed_breed" : bool(int(response.get('a2'))) if response.get('a2') is not None else None,
        "age" : response.get('a3'),
        "size" : response.get('a4'),
        "color" : response.get('a5'),
        "spayed" : response.get('a6'),
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
        dog_update_data = {k: v for k, v in dog_update_data.items() if v is not None}
        print("DOG UPDATE",dog_update_data)
        db.session.query(DogInfo).filter(DogInfo.post_id==post.id).update(dog_update_data)
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
    post = Post.query.get_or_404(post_id)
    dog = DogInfo.query.filter_by(post_id = post_id).first()
    if post.user_id != current_user.id:
        abort(403)
    current_image = post.image_file
    os.remove(current_app.root_path + '/static/profile_pics/' + current_image)
    db.session.delete(post)
    db.session.delete(dog)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))



@login_required
def user_info():
    if request.method == 'GET':
        posts = Post.query.filter(Post.user_id != current_user.id).order_by(Post.date_posted.asc()).limit(10).all()
        breeds = set()
        for dog in session.query(DogInfo.primary_breed).filter(DogInfo.primary_breed != ('unknown' or 'Unknown')).distinct():
            breeds.add((dog.primary_breed).lower())
        info = UserInfo.query.filter_by(user_id = current_user.id).first()
        if info:
            flash('You have already filled the questionnaire.','warning')
            return redirect(url_for('show_matches'))
    if request.method == 'POST':
        response = request.form
        user_data = {
        "prefered_breed" : {"prefered_breed": response.getlist('q1')},
        "prefers_mixed_breed" : bool(int(response.get('q2'))),
        "age_preference" : {"age_preference": response.getlist('q3')},
        "size_preference" : {"size_preference": response.getlist('q4')},
        "color_preference" : {"color_preference":response.getlist('q5')},
        "spay_needed" : bool(int(response.get('q6'))),
        "coat_length_preference" : response.get('q7'),
        "dog_with_children" : bool(int(response.get('q8'))),
        "dog_with_dogs" : bool(int(response.get('q9'))),
        "dog_with_cats" : bool(int(response.get('q10'))),
        "dog_with_sm_animals" : bool(int(response.get('q11'))),
        "dog_with_big_animals" : bool(int(response.get('q12'))),
        "dog_in_house" : bool(int(response.get('q13'))),
        "yard" : bool(int(response.get('q14'))),
        "park" : bool(int(response.get('q15'))),
        "activity_level" : response.get('q16'),
        "special_need_dog" : bool(int(response.get('q17'))),
        "user_id" : current_user.id
        }
        flash('You successfully submited your answers. Here are your matches!', 'success')
    
        info = UserInfo(**user_data)
        db.session.add(info)
        db.session.commit()
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('show_matches'))

    return render_template('user_info.html', user = current_user, breeds = breeds, posts = posts)

@login_required
def edit_user_info():
    info = UserInfo.query.filter_by(user_id = current_user.id).first()
    if request.method == 'GET':
        if not info:
            abort(403)
        posts = Post.query.filter(Post.user_id != current_user.id).order_by(Post.date_posted.asc()).limit(8).all()
        breeds = set()
        for dog in session.query(DogInfo.primary_breed).filter(DogInfo.primary_breed != ('unknown' or 'Unknown')).distinct():
            breeds.add((dog.primary_breed).lower())
    if request.method == 'POST':
        response = request.form
        user_update_data = {
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
        flash('You successfully submited your new answers. Here are your matches!', 'success')
        
        user_update_data = remove_none_values(user_update_data)
        user_update_data = {k:v for k,v in user_update_data.items() if v != {}}
        db.session.query(UserInfo).filter(UserInfo.user_id==current_user.id).update(user_update_data)
        db.session.commit()
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('show_matches'))

    return render_template('edit_user_info.html', user = current_user, breeds = breeds, posts = posts)

def remove_none_values(dictionary):
    return {key: remove_none_values(value) if isinstance(value, dict) else value for key, value in dictionary.items() if value is not None and value != [] }

@login_required
def show_matches(page = 1):
    user_info = UserInfo.query.filter_by(user_id = current_user.id).first()
    if not user_info:
        return redirect(url_for('user_info'))
    
    page = int(request.args.get('page', 1))
    prefered_breeds = (session.query(UserInfo.prefered_breed).filter(UserInfo.user_id == current_user.id).all())[0][0]['prefered_breed']
    print(prefered_breeds, 'rase')
    age_preference = (session.query(UserInfo.age_preference).filter(UserInfo.user_id == current_user.id).all())[0][0]['age_preference']
    print(age_preference)
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
                    #(and_(UserInfo.yard == True , UserInfo.park == True, UserInfo.activity_level == 'high'), UserInfo.activity_level.in_(['low','medium','high'])),
                    (and_(or_(UserInfo.yard == True , UserInfo.park == True),UserInfo.activity_level == 'high'),DogInfo.activity_level.in_(['low','medium','high'])),
                    (and_(UserInfo.yard == False , UserInfo.park == False, UserInfo.activity_level == 'high'), DogInfo.activity_level != 'high'),
                    #(and_(UserInfo.yard == True , UserInfo.park == True, UserInfo.activity_level == 'medium'), DogInfo.activity_level.in_(['medium','low'])),
                    (and_(or_(UserInfo.yard == True , UserInfo.park == True), UserInfo.activity_level == 'medium'), DogInfo.activity_level.in_(['medium','low'])),
                    (and_(UserInfo.yard == False , UserInfo.park == False, UserInfo.activity_level == 'medium'), DogInfo.activity_level.in_(['medium','low'])), 
                    else_= (UserInfo.activity_level == DogInfo.activity_level)
                )
                )       
  
    city_query = result.with_entities(Post.city).distinct()
    cities = set()
    for post in city_query:
        cities.add(post.city)  

    warning = None
    result1 = result.order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
    if not result1.items:
        flash('Oops, it seems there aren\'t matches for your preferences...', category='error')
        warning = "Check if there are preferences that can be modified or take a look at some of the our random choices."
    else:   
        result1, warning = result.filter(case((and_(UserInfo.dog_in_house == False, UserInfo.yard == False), False), else_=True))\
        .order_by(Post.date_posted.desc()).paginate(page=page, per_page=8), None
        
        if not result1.items:
            warning = "If you would not keep a dog in the house and if there is no yard, then where would the dog live?\
            Please check your answers."
            flash('Oops, it seems there aren\'t matches for your preferences...', category='error')
    
    alternative_results = db.session.query(Post, DogInfo, UserInfo).join(DogInfo, Post.id == DogInfo.post_id)\
            .join(UserInfo, UserInfo.user_id == current_user.id, isouter=True)\
            .filter(Post.user_id != current_user.id).order_by(func.random()).limit(8)

    saved_posts = []
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
            result1 = result.filter(case(('all' not in chosen_cities, Post.city.in_(chosen_cities)), else_= True))\
                    .filter(case((chosen_gender != 'all', Post.gender == chosen_gender), else_= True))\
                    .order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
        elif chosen_cities:
            result1 = result.filter(case(('all' not in chosen_cities, Post.city.in_(chosen_cities)), else_= True))\
                .order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
        elif chosen_gender:
            result1 = result.filter(case((chosen_gender != 'all', Post.gender == chosen_gender), else_= True))\
                .order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
         
    return render_template('show_matches.html', alternative_posts = alternative_results,warning = warning ,user = current_user, posts = result1, cities = cities, genders = genders, chosen_cities = chosen_cities, chosen_gender = chosen_gender, saved_posts = saved_posts )

@login_required
def my_profile(page=1):
    posts = Post.query.filter_by(user_id = current_user.id).order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
    page = request.args.get('page', 1, type=int)
    profile = User.query.filter_by(id = current_user.id).first()
    saved = []
    if profile:
        saved_dogs = profile.saved_dogs
        print(saved_dogs)
        if saved_dogs:
            saved_dogs = set(saved_dogs['saved'])
            for id in saved_dogs:
                dog = Post.query.filter_by(id = id).first()
                if dog != None:
                    saved.append(dog)

    return render_template('user.html', posts = posts, user = current_user, author = profile, saved = saved)

def user(user_id, page = 1):
    author = User.query.filter_by(id = user_id).first()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(user_id = user_id).order_by(Post.date_posted.desc()).paginate(page=page, per_page=8)
    return render_template('user.html', posts = posts, user = current_user, author = author)


@login_required
def contact_foster(foster_id):
    foster_parent = User.query.filter_by(id = foster_id).first()
    
    if request.method == 'POST':
        author = current_user.email
        recipient = request.form.get('recipient')
        message = request.form.get('message')
        subject = request.form.get('subject')
        
        sender = 'dogs.people.connect@gmail.com'
        recipients= [recipient]
        reply_to = author
        message_body = f" <p> {message} </p> <h4> This message was sent to you via <a href= {url_for('welcome', _external=True)}> dope connect <a/> app.</h4>"
        send_mail.delay(subject, sender, recipients, message_body, reply_to)
        flash('Your email has been sent!','success')

    return render_template('email_form.html', foster_parent = foster_parent)



def saved():
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
    res = make_response(jsonify({"message":'did it'}),200)
    return res

def user_preferences(user_id):
    user = UserInfo.query.filter_by(user_id = user_id).first()
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
    return render_template('user_preferences.html', u_info = u_info)