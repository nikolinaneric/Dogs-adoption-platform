import secrets
import os
from PIL import Image
from flask import render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user, login_user, logout_user
from .models import db
from .models import User, Note
from werkzeug.security import generate_password_hash, check_password_hash
from .user_form import UserFormSignUp, UserFormLogIn, UserSetUp


@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note)<1:
            flash('Note is too short', category = 'error')
        else:
            new_note = Note

    return render_template("home.html", user = current_user)

def login():
    form = UserFormLogIn()
    if form.validate_on_submit():
        email = form.email['email']
        password = form.data['password']

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category = 'success') 
                login_user(user, remember = True) 
                next_page = request.args.get('next')  # ako je neulogovan korisnik pokusao pristupiti nekoj stranici ona postaje next nakon logina
                return redirect(next_page) if next_page else redirect(url_for('home'))
                
            else:
                flash('Incorrect password, try again', category = 'error')
        else:
            flash('Email does not exist.', category = 'error')
         
    
    return render_template("login.html", user = current_user, form = form)

@login_required    
def logout():
    logout_user()
    return redirect(url_for('login'))

def sign_up():
    form = UserFormSignUp()
    if form.validate_on_submit():
        email = form.data['email']
        first_name = form.data['first_name']
        password1 = form.data['password1']
        password2 = form.data['password2']
        image_file = 'default.jpg'
    
        new_user = User(email = email, first_name = first_name, password = generate_password_hash(password1, method = 'sha256'), image_file = image_file)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        flash('Account created!', category='success')
        return redirect(url_for('set_profile'))

    return render_template("sign_up.html", user = current_user, form = form)

def show_all():
   return render_template('show_all.html', user = current_user, users = User.query.all())

def welcome():
    return render_template('welcome.html')

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)  # za naziv slike u bazi kako ne bi doslo do overrajdovanja
    _, f_ext = os.path.splitext(form_picture.filename)  # f_ext je ekstenzija fajla slike iz forme (npr jpg ili png)
    picture_name = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path,'static/profile_pics/', picture_name)  # napravljen path za cuvanje slike

    # smanjivanje velicine slike radi ustede memorije u bazi pomocu pillow paketa:

    output_size = (150,150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)   # cuvanje slike na picture_pathu

    return picture_name


@login_required
def set_profile():
    form = UserSetUp()
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
        return redirect(url_for('set_profile'))

    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.email.data = current_user.email
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('set_profile.html', user = current_user, form= form, image_file = image_file)

def reset_request():
    return("Reset password")
