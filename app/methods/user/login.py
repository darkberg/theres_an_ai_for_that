from flask import render_template, flash
from flask import session as login_session
from methods import routes

from google.cloud import storage
from methods import routes
from flask import render_template, url_for, flash, request, redirect, jsonify
from database_setup import User
import logging
import sys
import re
import json
from helpers import sessionMaker
from . import hashing_functions
from helpers.permissions import setSecureCookie

session = sessionMaker.newSession()

@routes.route('/user/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
       return render_template('/user/login.html')

    if request.method == 'POST':

        data = request.get_json(force=True)   # Force = true if not set as application/json' 
        user = data['user']

        have_error = False
        params = {}

        if user['email'] is None:
            params['error_email'] = "Invalid email"
            have_error = True

        if user['password'] is None:
            params['error_password'] = "Invalid password"
            have_error = True

        if user['email'] is not None:

            user_email = user['email'].lower()

            user_db = session.query(User).filter_by(email=user_email).first()

            if user_db is None:
                params['error_email'] = "Invalid email"
                have_error = True
                # Could add other @ checking to avoid db call if needed

            if user_db is not None and have_error is False:
                        
                password_result = hashing_functions.valid_pw(user_email, 
		                user['password'], user_db.password_hash)

                if password_result is False:
                    params['error_password'] = "Invalid password"
                    have_error = True


        if have_error:
            return json.dumps(params), 200, {'ContentType':'application/json'}

        else: 

            setSecureCookie(user_db)

            return json.dumps({'success':True}), 200, {'ContentType':'application/json'}


