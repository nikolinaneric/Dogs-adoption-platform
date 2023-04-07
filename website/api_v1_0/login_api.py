from flask_restful import Resource, reqparse
from werkzeug.security import check_password_hash
from website.models import User

class LoginAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('email', type=str, required=True, help='Email address is required')
        self.parser.add_argument('password', type=str, required=True, help='Password is required')

    def post(self):
        args = self.parser.parse_args()
        email = args['email']
        password = args['password']
        user = User.query.filter_by(email=email).first()
        if user:
            if user.is_verified:
                if check_password_hash(user.password, password):
                    token = user.get_reset_token()
                    return {'access token': token}
                else:
                    return {'message': 'Incorrect password, try again'}, 401
            else:
                return {'message': 'Email is not verified.'}, 401
        else:
            return {'message': 'Account does not exist.'}, 401
 
