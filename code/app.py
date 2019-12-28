from flask import Flask, request, render_template
from flask_restful import Resource, Api, reqparse
from flask_jwt import JWT, jwt_required, current_identity
from datetime import timedelta
from flask_bcrypt import Bcrypt

from security import authenticate, identity
from user import UserRegister, User, User2

app = Flask(__name__)
app.secret_key = 'SECREEET KEYYY'
app.config['JWT_EXPIRATION_DELTA'] = timedelta(seconds=3600)
app.config['JWT_AUTH_USERNAME_KEY'] = 'email'
api = Api(app)
bcrypt = Bcrypt(app)

jwt = JWT(app, authenticate, identity)  # creates endpoint /auth


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


@app.route('/')
def home():
    return render_template('index.html')


api.add_resource(User2, '/user')  # http://127.0.0.1:500/user
api.add_resource(UserRegister, '/user_register')  # http://127.0.0.1:500/user_register

app.run(debug=True)
