import random
import re
import string

import psycopg2
from config import config
from flask_jwt import jwt_required, current_identity
from flask_restful import Resource, reqparse
from flask_bcrypt import generate_password_hash

params = config()
regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
whitelist = set('abcčćžšđdefghijklmnopqrstuvwxyz ABCČĆŽŠĐDEFGHIJKLMNOPQRSTUVWXYZ')


def check(email):
    # pass the regualar expression
    # and the string in search() method
    if re.search(regex, email):
        return True
    else:
        return False


def randomStringDigits(stringLength=7):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


class User(Resource):
    def __init__(self, _id, fullname, email, password):
        self.id = _id
        self.fullname = fullname
        self.email = email
        self.password = password

    # ova metoda je nuzna za security identity method da bi se ustanovio identitet usera
    @classmethod
    def find_by_id(cls, _id):
        connection = None
        try:
            connection = psycopg2.connect(**params)
            cursor = connection.cursor()

            query = "SELECT * FROM person WHERE id=%s"
            cursor.execute(query, (_id,))
            row = cursor.fetchone()
            if row:
                user = cls(row[0], row[1], row[2], row[3])
            else:
                user = None

            cursor.close()
            return user

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            connection.close()
            return error
        finally:
            if connection is not None:
                connection.close()

    @classmethod
    def find_by_email(cls, email):
        connection = None
        try:
            connection = psycopg2.connect(**params)
            cursor = connection.cursor()
            query = "SELECT * FROM person WHERE email=%s"
            cursor.execute(query, (email,))
            row = cursor.fetchone()
            if row:
                user = cls(row[0], row[1], row[2], row[3])
            else:
                user = None

            cursor.close()
            return user

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            connection.close()
            return error
        finally:
            if connection is not None:
                connection.close()


class User2(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument(
        'fullname',
        type=str
    )
    parser.add_argument(
        'email',
        type=str
    )
    parser.add_argument(
        'password',
        type=str
    )

    @jwt_required()
    def get(self):
        connection = None
        try:
            connection = psycopg2.connect(**params)
            cursor = connection.cursor()
            query = "SELECT * FROM person WHERE id=%s"
            cursor.execute(query, (current_identity.id,))
            row = cursor.fetchone()
            if row:
                user = {
                    "fullname": row[1],
                    "email": row[2]
                }
            else:
                user = None

            cursor.close()
            return user

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            connection.close()
            return error
        finally:
            if connection is not None:
                connection.close()

    @jwt_required()
    def put(self):
        data = User2.parser.parse_args()

        connection = None
        try:
            connection = psycopg2.connect(**params)
            cursor = connection.cursor()
            cursor.execute('select email from person where id <> %s', (current_identity.id,))
            result = cursor.fetchall()
            email_list = [list(i) for i in result]
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            connection.close()
        finally:
            if connection:
                connection.close()

        for e in email_list:
            if data["email"] in e:
                return {"message": "Email already exists."}

        connection = None
        try:
            connection = psycopg2.connect(**params)
            cursor = connection.cursor()
            if data["email"]:
                pwd = generate_password_hash(data["password"]).decode('utf-8')
                query = "update person " \
                        "set fullname = %s," \
                        "email = %s," \
                        "password = %s," \
                        "updated_on = NOW() WHERE id=%s;"
                cursor.execute(query, (data["fullname"], data["email"],
                                       pwd, current_identity.id,))

            connection.commit()
            cursor.close()
            return {"message": "User updated.",
                    "fullname": data["fullname"],
                    "email": data["email"],
                    "password": data["password"]}

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            connection.close()
            return error
        finally:
            if connection is not None:
                connection.close()

    @jwt_required()
    def delete(self):
        connection = None
        try:
            connection = psycopg2.connect(**params)
            cursor = connection.cursor()
            query = "DELETE FROM person WHERE id=%s"
            cursor.execute(query, (current_identity.id,))
            connection.commit()
            cursor.close()
            return {"message": "User deleted."}

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            connection.close()
            return error
        finally:
            if connection is not None:
                connection.close()


class UserRegister(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument(
        'fullname',
        type=str,
        required=True,
        help="This field cannot be left blank!"
    )
    parser.add_argument(
        'email',
        type=str,
        required=True,
        help="This field cannot be left blank!"
    )

    def post(self):
        data = UserRegister.parser.parse_args()

        connection = None
        try:
            connection = psycopg2.connect(**params)
            cursor = connection.cursor()
            cursor.execute('select email from person')
            result = cursor.fetchall()
            email_list = [list(i) for i in result]
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            connection.close()
        finally:
            if connection:
                connection.close()

        for e in email_list:
            if data["email"] in e:
                return {"message": "Email already exists."}

        if not check(data["email"]):
            return {"message": "Wrong email format."}

        if ''.join(filter(whitelist.__contains__, data["fullname"])) != data["fullname"]:
            return {"message": "Wrong username input."}

        connection = None
        try:
            connection = psycopg2.connect(**params)
            cursor = connection.cursor()
            pwd = randomStringDigits(10)
            print("----->", pwd)
            cursor.execute('insert into person (fullname, email, password) '
                           'values (%s, %s, %s)'
                           , (data["fullname"], data["email"]
                              , generate_password_hash(pwd).decode('utf-8')))

            connection.commit()
            cursor.close()
            return {"message": "User created."}
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            connection.close()
            return {"message": error}
        finally:
            if connection is not None:
                connection.close()
