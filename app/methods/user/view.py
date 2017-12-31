from flask import render_template, flash
from flask import session as login_session
from methods import routes
from flask import render_template, url_for, flash, request, redirect, jsonify
from database_setup import User
from helpers import sessionMaker
from helpers.permissions import LoggedIn, getUserID

session = sessionMaker.newSession()

@routes.route('/user/view', methods=['GET'])
def user_view():        
    if LoggedIn() == True:

        user_id=getUserID()
        user = session.query(User).filter_by(id=getUserID()).first()

        out = jsonify(user=user.serialize())

        return out, 200, {'ContentType':'application/json'}

    else:
        flash("Please login")
        return "Error, Please login", 400
