import os
from PIL import Image
import secrets
from flask import current_app
from website.models import DogInfo, Post
from flask_babel import gettext
from website import session


def get_dog_data(response, post):
    """
    Extracts data about a dog from a submitted form and associates it with a post.
    Parameters:
    response (dict): submitted form data
    post (Post): The post object to which the dog data is to be associated

    Returns:
    dict: A dictionary containing the dog data
    """
    dog_data = {
        "primary_breed" : (response.get('a1')).lower() if response.get('a1') else None,
        "mixed_breed" : bool(int(response.get('a2'))) if response.get('a2') is not None else None,
        "age" : response.get('a3') if response.get('a3') else None,
        "size" : response.get('a4') if response.get('a4') else None,
        "color" : response.get('a5') if response.get('a5') else None,
        "spayed" : bool(int(response.get('a6'))) if response.get('a6') else None,
        "coat_length" : response.get('a7') if response.get('a7') else None,
        "dog_with_children" : bool(int(response.get('a8'))) if response.get('a8') is not None else None ,
        "dog_with_dogs" : bool(int(response.get('a9'))) if response.get('a9') is not None else None,
        "dog_with_cats" : bool(int(response.get('a10'))) if response.get('a10') is not None else None,
        "dog_with_sm_animals" : bool(int(response.get('a11'))) if response.get('a11') is not None else None,
        "dog_with_big_animals" : bool(int(response.get('a12'))) if response.get('a12') is not None else None,
        "activity_level" : response.get('a13') if response.get('a13') else None,
        "special_need_dog" : bool(int(response.get('a14'))) if response.get('a14') is not None else None,
        "post_id": post.id
        }
    dog_data = {k: v for k, v in dog_data.items() if v is not None}
    return dog_data

def get_dog_info(dog):
    """
    Formats dog data for display on a post page.

    Parameters:
    dog (Dog): The dog for which the data is to be formatted

    Returns:
    dict: A dictionary containing the formatted dog data
    """
    d_compatibility = [gettext('children') if dog.dog_with_children else '', gettext('dogs') if dog.dog_with_dogs else '', gettext('cats') if dog.dog_with_cats else '',\
            gettext('small animals') if dog.dog_with_sm_animals else '', gettext('big animals') if dog.dog_with_big_animals else '']
    d_compatibility = [comp for comp in d_compatibility if comp != '']
    

    dog_info = {
        "d_mixed_breed" : dog.mixed_breed,
        "d_primary_breed" : gettext(dog.primary_breed),
        "d_size" : gettext(dog.size),
        "d_age" : gettext(dog.age),
        "d_color" : gettext(dog.color),
        "d_coat_length" : gettext(dog.coat_length),
        "d_spayed" : dog.spayed,
        "d_compatibility": d_compatibility,
        "d_special_need" : dog.special_need_dog,
        "d_activity" : gettext(dog.activity_level),
    }
    return dog_info

def remove_none_values(dictionary):
    """
    Recursively removes all key-value pairs in a dictionary where the value is None or an empty list.
    """
    return {key: remove_none_values(value) if isinstance(value, dict) else value for key, value in dictionary.items() if value is not None and value != [] }

def querying_breeds():
    breeds = set()
    for dog in session.query(DogInfo.primary_breed).filter(DogInfo.primary_breed != 'unknown').distinct():
        breeds.add((dog.primary_breed).capitalize())
    return breeds

def save_picture(form_picture):
    """
    Saves a picture uploaded via a form to the file system and returns the name of the file.

    Parameters:
    form_picture: The picture to be saved

    Returns:
    str: The name of the saved picture file
    """
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


def remove_none_values(dictionary):
    """
    Recursively removes all key-value pairs in a dictionary where the value is None or an empty list.
    """
    return {key: remove_none_values(value) if isinstance(value, dict) else value for key, value in dictionary.items() if value is not None and value != [] }

def query_cities(query):
        cities = set()
        for post in query(Post.city).distinct():
            cities.add(post.city)
        return cities
