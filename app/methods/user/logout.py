from flask import session as login_session
from flask import redirect, url_for
from methods import routes


@routes.route('/user/logout')
def logout():

    login_session['user_id'] = ''
    return redirect(url_for('routes.home'))
