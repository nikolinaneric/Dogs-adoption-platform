from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, make_response
from flask_login import login_required, current_user
from website.models import db
from website.models import User, Post, UserInfo, DogInfo
from website import session
from sqlalchemy import and_, case, or_, func
from website.tasks import send_mail
from website.main.utils import  email, get_dog_info, get_user_info, filtering
from flask_babel import gettext

main = Blueprint('main', __name__)
@main.route("/")
def welcome():
    """
    Displays a welcome page to the user.
    If the user is already authenticated, it redirects the user to the home page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    response=make_response(render_template('welcome.html'))
    language = request.args.get('lang')
    if language:
        response = make_response(redirect("/"))
        response.set_cookie('lang', language, max_age = 604800)
    return response
    

@main.route("/mail/<int:foster_id>", methods = ['GET', 'POST'])
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


@main.route("/home", methods = ['GET', 'POST'])
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

@main.route("/comparison/<int:post_id>")
def comparison(post_id):
    """
    Returns a comparison of user preferences and dog traits 
    for a given post ID and current user.
    """
    dog = DogInfo.query.filter(DogInfo.post_id == post_id).first()
    if current_user.is_authenticated: 
        user = UserInfo.query.filter_by(user_id = current_user.id).first()
        if not user:
            return redirect(url_for('users.user_info'))       
    else:
        return redirect(url_for('users.login'))
    
    user_info = get_user_info(user)
    dog_info = get_dog_info(dog)
    comparison = {**user_info, **dog_info}
    comparison = {k: v for k, v in comparison.items() if v}
    return render_template('comparison.html', comparison = comparison)


@main.route("/contact-foster/<int:post_id>", methods = ['GET', 'POST'])
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

@main.route("/matches", methods = ['GET', 'POST'])
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
        return redirect(url_for('users.user_info'))
    
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

@main.route("/saved", methods = ['POST'])
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

