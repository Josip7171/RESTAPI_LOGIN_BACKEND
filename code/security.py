from user import User
from flask_bcrypt import check_password_hash


def authenticate(email, password):
    user = User.find_by_email(email)
    if user and check_password_hash(user.password, password):
        return user


def identity(payload):
    print("payload: ", payload)
    user_id = payload['identity']
    return User.find_by_id(user_id)
