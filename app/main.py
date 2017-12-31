# Main entry point for application.
from flask import Flask, Blueprint, render_template, abort
import os, logging

from methods.home import home

from methods.storage.fileUpload import upload

from methods.user.new import user_new
from methods.user.login import login
from methods.user.logout import logout
from methods.user.view import user_view

from methods.project.newProject import project_get

from methods.annotation.yamlNew import yamlNew
from methods.annotation.annotation import annotate
from methods.annotation.labels import labelNew

from methods.machine_learning.tfrecordsNew import tfrecordsNew
from methods.machine_learning.runTraining import runTraining
from methods.machine_learning.runInference import runInferenceSingle
from methods.machine_learning.ml_settings import machine_learning_settings_new

from methods import routes
from settings import settings

app = Flask(__name__, template_folder="static/templates/")
app.register_blueprint(routes)
app.secret_key = settings.SECRET_KEY


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
