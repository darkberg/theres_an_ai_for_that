from google.cloud import storage
from methods import routes
from flask import render_template, url_for, flash, request, redirect, jsonify
from database_setup import User, Project, Version
import logging
import sys
import re
import json
from helpers import sessionMaker
from helpers.permissions import LoggedIn, defaultRedirect, getUserID, get_current_project


@routes.route('/workspace/new', methods=['GET'])
def project_get():       
    if LoggedIn():
        return render_template('/workspace/newWorkspace.html')
    else:
        return defaultRedirect()


def project_new(session):

    train_credits = 3
    test_credits = 3

    new_project = Project(train_credits=train_credits,
                            test_credits=test_credits)
    session.add(new_project)
    session.commit()  # May be better way to use a session scope here
    user = session.query(User).filter_by(id=getUserID()).first()
    user.project_id_current = new_project.id
    session.add(user)



def version_new(session):
    
    project = get_current_project(session)
    new_version = Version(project_id=project.id)
    session.add(new_version)
    session.commit()

    project.version_id_current = new_version.id
    project.version_ids = [new_version.id]
    session.add(project)
            



