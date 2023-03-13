import os
import jwt
import datetime
from PIL import Image
import secrets
from flask import request, url_for, current_app
from flask_login import current_user
from .tasks import send_mail

def verification_mail(email):
    secret_key = os.environ.get('secret_key')
    print(secret_key)
    verification_token = jwt.encode({'email': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, secret_key, algorithm='HS256')
    verification_url = url_for('verify_new_email', token=verification_token, _external=True)
    subject = 'Email Verification' 
    sender = "dogs.people.connect@gmail.com" 
    recipients=[email]
    message_body = f'''To verify your account, please visit the following link: {verification_url}   
                If you did not make this request then simply ignore this email and no changes will be made.
            '''
    send_mail.delay(subject, sender, recipients, message_body)

def email():
    author = current_user.email
    recipient = request.form.get('recipient')
    message = request.form.get('message')
    subject = request.form.get('subject')
    
    sender = 'dogs.people.connect@gmail.com'
    recipients= [recipient]
    reply_to = author
    message_body = f" <p> {message} </p> <h4> This message was sent to you via <a href= {url_for('welcome', _external=True)}> dope connect <a/> app.</h4>"
    send_mail.delay(subject, sender, recipients, message_body, reply_to)
    
def remove_none_values(dictionary):
    return {key: remove_none_values(value) if isinstance(value, dict) else value for key, value in dictionary.items() if value is not None and value != [] }



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