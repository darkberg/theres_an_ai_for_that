from database_setup import User, Project, Version, Image, Box, Label, Machine_learning_settings
from flask import session as login_session
from flask import request, redirect, url_for, flash
from methods import userMethods
from helpers import sessionMaker
from methods.user import hashing_functions
import sys, os

from settings import settings

# True means has permission, False means doesn't.

def LoggedIn():
    if login_session.get('user_id', None) is not None:
        out = hashing_functions.check_secure_val(login_session['user_id'])
        if out is not None:
            return True
        else:
            return False
    else:
        return False


def defaultRedirect():
    flash("Please login")
    return redirect(url_for('routes.login'))


def getUserID():
    out = hashing_functions.check_secure_val(login_session['user_id'])
    if out is not None:
        return out
    else:
        return None


def setSecureCookie(user_db):
    cookie_hash = hashing_functions.make_secure_val(str(user_db.id))
    login_session['user_id'] = cookie_hash


def get_current_version(session):
    user = session.query(User).filter_by(id=getUserID()).first()
    project = session.query(Project).filter_by(id=user.project_id_current).first()
    version = session.query(Version).filter_by(id=project.version_id_current).first()

    return version


def get_current_project(session):

    user = session.query(User).filter_by(id=getUserID()).first()
    project = session.query(Project).filter_by(id=user.project_id_current).first()

    return project


def get_ml_settings(session, version):

    machine_learning_settings = session.query(Machine_learning_settings).filter_by(id=version.machine_learning_settings_id).first()
    return machine_learning_settings


def get_gcs_service_account(gcs):
    path = os.path.dirname(os.path.realpath(__file__)) + "/" + settings.SERVICE_ACCOUNT
    return gcs.from_service_account_json(path)