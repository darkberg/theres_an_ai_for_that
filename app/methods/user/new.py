from google.cloud import storage
from methods import routes
from flask import render_template, url_for, flash, request, redirect, jsonify
from database_setup import User
import logging, sys, re, json
from helpers import sessionMaker
from . import hashing_functions
from helpers.permissions import setSecureCookie
from methods.project.newProject import project_new, version_new

from settings import settings

# Define error handling functions for user creation
# Allow a-z, A-Z, 0-0, _, - using regular expression
# 3 - 20 characters
#USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')


def valid_username(username):
    return username and USER_RE.match(username)

def valid_password(password):
    return password and PASS_RE.match(password)

def valid_email(email):
    return email and EMAIL_RE.match(email)


@routes.route('/user/new', methods=['GET', 'POST'])
def user_new():
    if request.method == 'GET':
        return render_template('/user/new.html')

    if request.method == 'POST':   
        def user_new_scope(session):
            data = request.get_json(force=True)   # Force = true if not set as application/json' 
            user = data['user']
            print(user['name'], file=sys.stderr)

            have_error = False
            params = {}

            # error handling
            # existing username check
            existing_user = session.query(User).filter_by(email=user['email']).first()
            if existing_user is not None:
                params['error_email'] = "Existing email"
                have_error = True

            if not valid_email(user['email']):
                params['error_email'] = "Invalid email"
                have_error = True

            if not valid_password(user['password']):
                params['error_password'] = "Password must be at least 3 characters"
                have_error = True

            if user['password'] != user['verify']:
                params['error_verify'] = "Passwords don't match"
                have_error = True
                flash("Password error")

            if user['code'] != settings.SIGNUP_CODE:
                params['error_code'] = "Invalid code"
                have_error = True

            if have_error:
                return [1, json.dumps(params), 200, {'ContentType':'application/json'}]
        
            else:
                # User registration
                password_hash = hashing_functions.make_pw_hash(user['email'], user['password'])
                print(password_hash, file=sys.stderr)
                project_id_current = None

                # TODO could insert logic here to attach a user to a project based on say the sigup code

                new_user = User(
                    name=user['name'],
                    email=user['email'],
                    project_id_current=project_id_current,
                    password_hash=password_hash
                    )
                session.add(new_user)
                flash("Welcome! User created")
                return [0, user['email']]
        

        """
        These transactions are split apart to increase session atomicity
        """
        user_email = None
        with sessionMaker.session_scope() as session:
            result = user_new_scope(session)
            if result[0] == 0:
                user_email = result[1]
            else:
                return result[1]

        with sessionMaker.session_scope() as session:
            user_db = session.query(User).filter_by(email=user_email).first()
            setSecureCookie(user_db)

        with sessionMaker.session_scope() as session:
            project_new(session)

        with sessionMaker.session_scope() as session:
            version_new(session)

        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}


