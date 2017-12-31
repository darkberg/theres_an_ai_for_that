from google.cloud import storage
from methods import routes
from flask import render_template, url_for, flash, request, redirect, jsonify
from database_setup import User, Project, Version
import logging
import sys
import re
import json
from helpers import sessionMaker
from helpers.permissions import LoggedIn, defaultRedirect, getUserID


@routes.route('/workspace/new', methods=['GET'])
def project_get():       
    if LoggedIn():
        return render_template('/workspace/newWorkspace.html')
    else:
        return defaultRedirect()


@routes.route('/project/new', methods=['POST'])
def project_new():
        
    session = sessionMaker.newSession()

    user_id = getUserID()
    if user_id is None:
        return defaultRedirect()

    train_credits = 3
    test_credits = 3

    new_project = Project(train_credits=train_credits,
                            test_credits=test_credits
                            )
    session.add(new_project)
    session.commit()

    new_version = Version(project_id=new_project.id)
    session.add(new_version)
    session.commit()

    new_project.version_id_current = new_version.id
    new_project.version_ids = [new_version.id]
            
    user = session.query(User).filter_by(id=getUserID()).first()

    user.project_id_current = new_project.id

    session.add(new_project, user)
    session.commit()

    print("New project created, new_project.id", new_project.id, 
            "new_version.id", new_version.id, "user.id", user.id, file=sys.stderr)

    flash("Project created, on default version")

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}