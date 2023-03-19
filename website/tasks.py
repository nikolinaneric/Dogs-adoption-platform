from celery import shared_task
from flask_mail import Message
from flask import current_app
from . import mail


@shared_task(bind = True)
def send_mail(self, subject, recipients, message_body, reply_to = 'dogs.people.connect@gmail.com'):
    msg = Message(subject = subject, sender = current_app.config['MAIL_DEFAULT_SENDER'], recipients= recipients, reply_to=reply_to)
    msg.html = message_body
    mail.send(msg) 
    