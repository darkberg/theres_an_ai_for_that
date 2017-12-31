from flask import render_template
from methods import routes

@routes.route('/')
def home():
    return render_template('/home/home.html')
