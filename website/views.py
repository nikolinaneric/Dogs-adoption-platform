import secrets
import os
from PIL import Image
from flask import render_template, request, flash, redirect, url_for, current_app, abort, jsonify, make_response
from flask_login import login_required, current_user, login_user, logout_user
from .models import db
from .models import User, Post, UserInfo, DogInfo
from werkzeug.security import generate_password_hash, check_password_hash
from .user_form import UserFormSignUp, UserFormLogIn, UserSetUp, RequestResetForm, ResetPasswordForm, PostForm
from flask_mail import Message
from . import mail, session
from sqlalchemy import  update,and_, case, or_, func
import jwt
import datetime
import logging

   
def home(page = 1):
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
    # if request.method == 'POST':
    #     if current_user.is_authenticated:
    #         user_info = UserInfo.query.filter_by(user_id = current_user.id).first()
    #         if not user_info: 
    #             flash('You must fill the adoption preferences questionnaire first','error')

    #         saved_posts =  request.form.getlist('saved[]')
    #         print(saved_posts)
    #     else:
    #         flash('You must be signed in for this action','error')
        

    cities = set()
    for post in session.query(Post.city).distinct():
        cities.add(post.city)
    genders = ['male','female']
    chosen_cities=[]
    if request.method == "POST":
        chosen_cities = request.form.getlist('city')
        chosen_gender = (request.form.get('gender')).lower() if request.form.get('gender') else False
        
        if chosen_cities and chosen_gender:
            posts = Post.query.filter(case(('all' not in chosen_cities, Post.city.in_(chosen_cities)), else_= True))\
                    .filter(case((chosen_gender != 'all', Post.gender == chosen_gender), else_= True))\
                    .order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
        elif chosen_cities:
            posts = Post.query.filter(case(('all' not in chosen_cities, Post.city.in_(chosen_cities)), else_= True))\
                .order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
        elif chosen_gender:
            posts = Post.query.filter(case((chosen_gender != 'all', Post.gender == chosen_gender), else_= True))\
                .order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
        
    
    return render_template("home.html", user = current_user, posts = posts, cities = cities, genders = genders, chosen_cities = chosen_cities)
    

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
                    next_page = request.args.get('next')  # ako je neulogovan korisnik pokusao pristupiti nekoj stranici ona postaje next nakon logina
                    return redirect(next_page) if next_page else redirect(url_for('home'))
                    
                else:
                    flash('Incorrect password, try again', category = 'error')
            else:
                flash('Email is not verified.', category = 'error')
        else:
            flash('Account does not exist.', category = 'error')
  
    return render_template("login.html", user = current_user, form = form)

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
        password2 = form.data['password2']
        image_file = 'default.jpg'

        email_exists = User.query.filter_by(email = email).first()
        if email_exists:
            flash('The email address you\'re trying to add has been registered with the account already.','error')
        else:
            if email:
                secret_key = 'mysecretkey'
                verification_token = jwt.encode({'email': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, secret_key, algorithm='HS256')
                verification_url = url_for('verify_email', token=verification_token, _external=True)
                msg = Message('Email Verification', sender = "dogs.people.connect@gmail.com" , recipients=[email])
                msg.body = f'''To verify your account, please visit the following link: {verification_url}   
                    If you did not make this request then simply ignore this email and no changes will be made.
                '''
                mail.send(msg)
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
        return None
    if email:
        user = User.query.filter_by(email = email).first()
        user.is_verified = True
        db.session.commit()
    return redirect(url_for('login'))

def welcome():
    return render_template('welcome.html')

def save_picture(form_picture):
    picture_name = ""
    random_hex = secrets.token_hex(8)  # za naziv slike u bazi kako ne bi doslo do overrajdovanja
    if form_picture:
        _, f_ext = os.path.splitext(form_picture.filename)  # f_ext je ekstenzija fajla slike iz forme (npr jpg ili png)
        picture_name = random_hex + f_ext
        picture_path = os.path.join(current_app.root_path,'static/profile_pics/', picture_name)  # napravljen path za cuvanje slike

    # smanjivanje velicine slike radi ustede memorije u bazi pomocu pillow paketa:

        output_size = (900,450)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)   # cuvanje slike na picture_pathu

    return picture_name

@login_required
def set_profile():
    form = UserSetUp()
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    if form.validate_on_submit():
        if form.data['picture']:
            profile_pic = save_picture(form.picture.data)
            previous_pic = current_user.image_file
            if previous_pic != "default.jpg":
                os.remove(current_app.root_path + '/static/profile_pics/' + previous_pic)
            current_user.image_file = profile_pic
        current_user.email = form.data['email']
        current_user.first_name = form.data['first_name']
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('my_profile'))

    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.email.data = current_user.email
        
    return render_template('set_profile.html', user = current_user, form= form, image_file = image_file)


def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
   
    return render_template('reset_request.html', form = form, user = current_user)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
    {url_for('reset_token', token=token, _external=True)}  
    If you did not make this request then simply ignore this email and no changes will be made.
    '''
    mail.send(msg)
    #external = True znaci da se salje apsolutno url kao npr https://example.com/my-page, a ne relativni -/mypage


def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)  # vracamo nam odgovarajuci user objekat na osnovu id iz tokena
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
    else:
        print(form.errors)
    return render_template('reset_password.html', form=form, user = current_user)

@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        photo = form.picture.data
        image_name = save_picture(photo)
        city = form.city.data
        gender = form.gender.data
        #image_file = url_for('static', filename='profile_pics/' + image_name)
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

        print(dog_data)
        dog = DogInfo(**dog_data)
        db.session.add(dog)
        db.session.commit()

        print(dog.primary_breed, dog.activity_level, dog.dog_with_cats, 'cats')

        return redirect(url_for('home'))
    return render_template('new_post.html', user = current_user, form = form)

def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post, user = current_user)

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
    d_compatibility = d_compatibility if any(c != "" for c in d_compatibility) else False
    u_needs= ['children' if user.dog_with_children else '', 'dogs' if user.dog_with_dogs else '', 'cats' if user.dog_with_cats else '',\
            'small animals' if user.dog_with_sm_animals else '', 'big animals' if user.dog_with_big_animals else '']
    u_needs = u_needs if any(n != "" for n in u_needs) else False

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
    print(comparison)
    return render_template('comparison.html', comparison = comparison)

@login_required
def email_form(post_id):
    post = Post.query.filter(Post.id == post_id).first()
    if request.method == 'POST':
        author = current_user.email
        recipient = request.form.get('recipient')
        message = request.form.get('message')
        subject = request.form.get('subject')

        msg = Message(subject,
                    sender = 'dopeconnect@admin.com',
                    recipients= [recipient],
                    reply_to = author)
        msg.html = f" <p> {message} </p> <h4> This message was sent to you via <a href= {url_for('welcome', _external=True)}> dope connect <a/> app.</h4>"
        mail.send(msg)
        flash('Your email has been sent!','success')

        
    return render_template('email_form.html', user = current_user, post = post)
    
@login_required
def dog_info(post_id):
    dog = DogInfo.query.filter(DogInfo.post_id == post_id).first()
    d_compatibility = ['children' if dog.dog_with_children else '', 'dogs' if dog.dog_with_dogs else '', 'cats' if dog.dog_with_cats else '',\
            'small animals' if dog.dog_with_sm_animals else '', 'big animals' if dog.dog_with_big_animals else '']
    d_compatibility = d_compatibility if any(c != "" for c in d_compatibility) else False
    

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
        photo = form1.picture.data 
        post.image_name = save_picture(photo)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been updated!', 'success')

        response = request.form
        dog_update_data = {
        "primary_breed" : (response.get('a1')).lower(),
        "mixed_breed" : bool(int(response.get('a2'))) if response.get('a2') else '',
        "age" : response.get('a3'),
        "size" : response.get('a4'),
        "color" : response.get('a5'),
        "spayed" : bool(int(response.get('a6'))) if response.get('a6') else '',
        "coat_length" : response.get('a7'),
        "dog_with_children" :int(response.get('a8')) ,
        "dog_with_dogs" : int(response.get('a9')) ,
        "dog_with_cats" : bool(int(response.get('a10'))) ,
        "dog_with_sm_animals" : bool(int(response.get('a11'))) if response.get('a11') is not None else '',
        "dog_with_big_animals" : bool(int(response.get('a12'))) if response.get('a12') is not None else '',
        "activity_level" : response.get('a13'),
        "special_need_dog" : bool(int(response.get('a14')))if response.get('a14') else '',
        "post_id": post.id
        }
        dog_update_data = {k: v for k, v in dog_update_data.items() if v}
        print(post.id)
        print("DOG UPDATE",dog_update_data)


        # sql = text("UPDATE dog_info SET dog_with_cats = :dog_with_cats WHEpost_id post_id")

        # conn = engine.connect()
        # conn.execute(sql, dog_with_cats = bool(int(response.get('a10'))) if response.get('a10') else 'post_id=post.id) 
        update = db.session.query(DogInfo).filter(DogInfo.post_id==post.id).update(dog_update_data)
        #session.execute(update)
        db.session.commit()
        # print(doggo_info.first().dog_with_cats, 'macke')
        # dog = DogInfo.query.filter_post_id = post.id).first()
        # print(dog.primary_breed, dog.activity_level, dog.dog_with_cats,dog.dog_with_sm_animals, "small an")



        return redirect(url_for('post', post_id = post.id, user = current_user))
    elif request.method == 'GET':
        image_file = url_for('static', filename='profile_pics/' + post.image_file)
        form1.title.data = post.title
        form1.data.data = post.data
        form1.city.data = post.city
        form1.gender.data = post.gender
        form1.picture.data = image_file
    return render_template('update_post.html',
                           form=form1, user = current_user)


@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))



@login_required
def user_info():
    if request.method == 'GET':
        posts = Post.query.order_by(Post.date_posted.asc()).limit(8).all()
        breeds = set()
        for dog in session.query(DogInfo.primary_breed).filter(DogInfo.primary_breed != ('unknown' or 'Unknown')).distinct():
            breeds.add((dog.primary_breed).lower())
        info = UserInfo.query.filter_by(user_id = current_user.id).first()
        if info:
            flash('You have already filled the questionnaire.','sucess')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('show_matches'))
            
    if request.method == 'POST':
        response = request.form
        
        prefered_breed = {"prefered_breed": response.getlist('q1')}
        prefers_mixed_breed = bool(int(response.get('q2')) )
        age_preference = {"age_preference": response.getlist('q3')}
        size_preference = {"size_preference": response.getlist('q4')}
        color_preference = {"color_preference":response.getlist('q5')}
        spay_needed = bool(int(response.get('q6')))
        coat_length_preference = response.get('q7')
        dog_with_children = bool(int(response.get('q8')))
        dog_with_dogs = bool(int(response.get('q9')))
        dog_with_cats = bool(int(response.get('q10')))
        dog_with_sm_animals = bool(int(response.get('q11')))
        dog_with_big_animals = bool(int(response.get('q12')))
        dog_in_house = bool(int(response.get('q13')))
        yard = bool(int(response.get('q14')))
        park = bool(int(response.get('q15')))
        activity_level = response.get('q16')
        special_need_dog = bool(int(response.get('q17')))
        flash('You successfully submited your answers. Here are your matches!', 'success')
    
        info = UserInfo(prefered_breed = prefered_breed, prefers_mixed_breed = prefers_mixed_breed, age_preference = age_preference,
            size_preference = size_preference, color_preference = color_preference, spay_needed = spay_needed, coat_length_preference = coat_length_preference,
            dog_with_children = dog_with_children, dog_with_dogs = dog_with_dogs, dog_with_cats = dog_with_cats, dog_with_sm_animals = dog_with_sm_animals, 
            dog_with_big_animals = dog_with_big_animals, dog_in_house = dog_in_house, yard = yard, park = park, 
            activity_level = activity_level, special_need_dog = special_need_dog, user_id = current_user.id)
        db.session.add(info)
        db.session.commit()
  
        return redirect(url_for('show_matches') )

    return render_template('user_info.html', user = current_user, breeds = breeds, posts = posts)

@login_required
def edit_user_info():
    info = UserInfo.query.filter_by(user_id = current_user.id).first()
    if request.method == 'GET':
        if not info:
            abort(403)
        posts = Post.query.order_by(Post.date_posted.asc()).limit(8).all()
        breeds = set()
        for dog in session.query(DogInfo.primary_breed).filter(DogInfo.primary_breed != ('unknown' or 'Unknown')).distinct():
            breeds.add((dog.primary_breed).lower())
    if request.method == 'POST':
        response = request.form
        
        prefered_breed = {"prefered_breed": response.getlist('q1')}
        prefers_mixed_breed = bool(int(response.get('q2')) )
        age_preference = {"age_preference": response.getlist('q3')}
        size_preference = {"size_preference": response.getlist('q4')}
        color_preference = {"color_preference":response.getlist('q5')}
        spay_needed = bool(int(response.get('q6')))
        coat_length_preference = response.get('q7')
        dog_with_children = bool(int(response.get('q8')))
        dog_with_dogs = bool(int(response.get('q9')))
        dog_with_cats = bool(int(response.get('q10')))
        dog_with_sm_animals = bool(int(response.get('q11')))
        dog_with_big_animals = bool(int(response.get('q12')))
        dog_in_house = bool(int(response.get('q13')))
        yard = bool(int(response.get('q14')))
        park = bool(int(response.get('q15')))
        activity_level = response.get('q16')
        special_need_dog = bool(int(response.get('q17')))
        flash('You successfully submited your new answers. Here are your matches!', 'success')
        
        
        if info:
            info.prefered_breed = prefered_breed
            info.prefers_mixed_breed = prefers_mixed_breed 
            info.age_preference = age_preference
            info.size_preference = size_preference 
            info.color_preference = color_preference 
            info.spay_needed = spay_needed 
            info.coat_length_preference = coat_length_preference
            info.dog_with_children = dog_with_children 
            info.dog_with_dogs = dog_with_dogs 
            info.dog_with_cats = dog_with_cats 
            info.dog_with_sm_animals = dog_with_sm_animals 
            info.dog_with_big_animals = dog_with_big_animals 
            info.dog_in_house = dog_in_house 
            info.yard = yard
            info.park = park 
            info.activity_level = activity_level
            info.special_need_dog = special_need_dog 
            info.user_id = current_user.id
        
            db.session.commit()
    
        return redirect(url_for('show_matches') )

    return render_template('user_info.html', user = current_user, breeds = breeds, posts = posts)

@login_required
def show_matches(page = 1):
        user_info = UserInfo.query.filter_by(user_id = current_user.id).first()
        if not user_info:
            return redirect(url_for('user_info'))
    #with session:  
        
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
        (and_(UserInfo.yard == True , UserInfo.park == True, UserInfo.activity_level == 'high'), UserInfo.activity_level.in_(['low','medium','high'])),
        (and_(or_(UserInfo.yard == True , UserInfo.park == True),UserInfo.activity_level == 'high'),DogInfo.activity_level.in_(['low','medium','high'])),
        (and_(UserInfo.yard == False , UserInfo.park == False, UserInfo.activity_level == 'high'), DogInfo.activity_level != 'high'),
        (and_(UserInfo.yard == False , UserInfo.park == False, UserInfo.activity_level != 'high'), UserInfo.activity_level == DogInfo.activity_level), else_= True
    )
)
        
        
        print(result)
        city_query = result.with_entities(Post.city).distinct()
        cities = set()
        for post in city_query:
           cities.add(post.city)      

        warning = None
        result1 = result.order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
        if not result1.items:
            flash('Oops, it seems there aren\'t matches for your preferences...', category='error')
            warning = "Check if there are preferences that can be modified or take a look at some of the our random choices."
        else:   
            result1, warning = result.filter(case((and_(UserInfo.dog_in_house == False, UserInfo.yard == False), False), else_=True))\
            .order_by(Post.date_posted.desc()).paginate(page=page, per_page=10), None
        
            if not result1.items:
                warning = "If you would not keep a dog in the house and if there is no yard, then where would the dog live?\
                Please check your answers."
                flash('Oops, it seems there aren\'t matches for your preferences...', category='error')
    
        alternative_results = db.session.query(Post, DogInfo, UserInfo).join(DogInfo, Post.id == DogInfo.post_id)\
                .join(UserInfo, UserInfo.user_id == current_user.id, isouter=True)\
                .order_by(Post.date_posted.desc())\
                .filter(Post.user_id != current_user.id).order_by(func.random()).limit(8)
        

        genders = ['male','female']
        chosen_cities=[]
        if request.method == "POST":
            chosen_cities = request.form.getlist('city')
            chosen_gender = (request.form.get('gender')).lower() if request.form.get('gender') else False
            
            if chosen_cities and chosen_gender:
                result1 = result.filter(case(('all' not in chosen_cities, Post.city.in_(chosen_cities)), else_= True))\
                        .filter(case((chosen_gender != 'all', Post.gender == chosen_gender), else_= True))\
                        .order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
            elif chosen_cities:
                result1 = result.filter(case(('all' not in chosen_cities, Post.city.in_(chosen_cities)), else_= True))\
                    .order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
            elif chosen_gender:
                result1 = Post.query.filter(case((chosen_gender != 'all', Post.gender == chosen_gender), else_= True))\
                    .order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
                

        return render_template('show_matches.html', alternative_posts = alternative_results,warning = warning ,user = current_user, posts = result1, cities = cities, genders = genders )

@login_required
def my_profile(page=1):
    posts = Post.query.filter_by(user_id = current_user.id).order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
    page = request.args.get('page', 1, type=int)
    author = User.query.filter_by(id = current_user.id).first()
    profile = UserInfo.query.filter_by(user_id = current_user.id).first()
    saved = []
    if profile:
        saved_dogs = set(profile.saved_dogs['saved'])
        for id in saved_dogs:
            dog = Post.query.filter_by(id = id).first()
            if dog != None:
                saved.append(dog)
        print(saved)
        print(posts, 'postovi')
    return render_template('user.html', posts = posts, user = current_user, author = author, saved = saved)

def user(user_id, page = 1):
    author = User.query.filter_by(id = user_id).first()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(user_id = user_id).order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('user.html', posts = posts, user = current_user, author = author)


@login_required
def contact_foster(foster_id):
    
    
    foster_parent = User.query.filter_by(id = foster_id).first()
    
    if request.method == 'POST':
        author = current_user.email
        recipient = request.form.get('recipient')
        message = request.form.get('message')
        subject = request.form.get('subject')

        msg = Message(subject,
                    sender = 'dopeconnect@admin.com',
                    recipients= [recipient],
                    reply_to = author)
        msg.html = f" <p> {message} </p> <h4> This message was sent to you via <a href= {url_for('welcome', _external=True)}> dope connect <a/> app.</h4>"
        mail.send(msg)
        flash('Your email has been sent!','success')

        
    return render_template('email_form.html', foster_parent = foster_parent)


saved_dogs = {"saved": []}
def saved():

    data = request.get_json()
    print(data)
    saved = data.get('saved')
    post_id = saved.get('postId')
        
    if "saved" in saved_dogs:
        saved_dogs["saved"].append(post_id)
    else:
        saved_dogs["saved"] = post_id
        
    print(saved_dogs, 'provjera')
    user = UserInfo.query.filter_by(user_id = current_user.id).first() 
    if user:   # prebaciti na usera
        user.saved_dogs = saved_dogs
        db.session.commit()
    else:
        flash('You must first fill the adoption preferences','info')
    print(user.saved_dogs)
    res = make_response(jsonify({"message":'did it'}),200)
    
    return res