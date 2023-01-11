from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user, login_user, logout_user
from .models import db
from .models import User, Note
from werkzeug.security import generate_password_hash, check_password_hash
from .user_form import UserFormSignUp


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
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category = 'success') 
                login_user(user, remember = True) 
                return redirect(url_for('home'))
            else:
                flash('Incorrect password, try again', category = 'error')
        else:
            flash('Email does not exist.', category = 'error')
         
    
    return render_template("login.html", user = current_user)

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
        

        user = User.query.filter_by(email = email).first()
        if user:
            flash('Email already exists.', category = 'error')
        
        else:
            new_user = User(email = email, first_name = first_name, password = generate_password_hash(password1, method = 'sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('home'))

    return render_template("sign_up.html", user = current_user, form = form)

def show_all():
   return render_template('show_all.html', user = current_user, users = User.query.all())