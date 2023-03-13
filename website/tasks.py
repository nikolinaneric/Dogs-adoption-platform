from celery import shared_task
from flask_mail import Mail
from flask_mail import Message
from . import mail

@shared_task(bind = True)
def send_mail(self, subject, sender, recipients, message_body, reply_to = 'dogs.people.connect@gmail.com'):
    msg = Message(subject = subject, sender = sender , recipients= recipients, reply_to=reply_to)
    msg.html = message_body
    mail.send(msg) 
    