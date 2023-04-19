import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort
from flask_login import login_required, current_user
from website.models import db
from website import session
from website.models import Post, DogInfo
from website.posts.forms import  PostForm
from website.tasks import send_mail
from website.posts.utils import save_picture, get_dog_data,\
                    get_dog_info, querying_breeds, remove_none_values, query_cities
from flask_babel import gettext

posts = Blueprint('posts', __name__)

@posts.route("/post/new", methods = ['GET','POST'])
@login_required
def new_post():
    """
    View function for creating a new adoption post.
    """
    form = PostForm()
    breeds = querying_breeds()
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

        return redirect(url_for('main.home'))
    return render_template('new_post.html', user = current_user, form = form, breeds = sorted(breeds))

@posts.route("/post/<int:post_id>")
def post(post_id):
    """
    View function for displaying an adoption post with given post_id. 
    If the user is author contains update, delete and dog info buttons.
    Otherwise contains buttons for contacting foster parent and checking the fit with the dog.
    """
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post = post, user = current_user)

@posts.route("/post/<int:post_id>/update", methods = ['GET','POST'])
@login_required
def update_post(post_id):  
    """
    View function for updating an existing adoption post with given post_id.
    """ 
    post = Post.query.get_or_404(post_id)
    breeds = querying_breeds()
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
        dog_update_data = get_dog_data(response, post)
        dog_update_data = remove_none_values(dog_update_data)
        dog_update_data = {k:v for k,v in dog_update_data.items() if v != {}}
        
        db.session.query(DogInfo).filter(DogInfo.post_id==post.id).update(dog_update_data)
        db.session.commit()
       
        return redirect(url_for('posts.post', post_id = post.id, user = current_user))
    
    elif request.method == 'GET':
        image_file = url_for('static', filename='profile_pics/' + post.image_file)
        form1.title.data = post.title
        form1.data.data = post.data
        form1.city.data = post.city
        form1.gender.data = post.gender
        form1.picture.data = image_file
    return render_template('update_post.html', form = form1, user = current_user, breeds = sorted(breeds))

@posts.route("/post/<int:post_id>/delete", methods = ['GET','POST'])
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
    return redirect(url_for('main.home'))

@posts.route("/dog-info/<int:post_id>")
@login_required
def dog_info(post_id):
    """Displays information about a dog associated with the post.

    Args:
        post_id (int): The ID of the post to display dog information about.
    """
    dog = DogInfo.query.filter(DogInfo.post_id == post_id).first()
    dog_info = get_dog_info(dog)
        
    return render_template('dog_info.html', dog_info = dog_info)