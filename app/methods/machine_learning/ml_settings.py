from google.cloud import storage
from flask import render_template, url_for, flash, request, redirect, jsonify, copy_current_request_context
import logging, sys, re, json, time, threading

from methods import routes
from helpers import sessionMaker
from database_setup import User, Project, Version, Image, Box, Label, Machine_learning_settings
from helpers.permissions import LoggedIn, defaultRedirect, getUserID, get_current_version, get_current_project, get_ml_settings


@routes.route('/machine_learning/settings/new', methods=['GET'])
def machine_learning_settings_new(session):

    if LoggedIn() != True:
        return defaultRedirect()

    project = get_current_project(session)
    version = get_current_version(session)

    iterations = 2000 # Could get from user
    previous_goal_iterations = iterations
    ml_compute_engine_id = 0

    new_ml_settings = Machine_learning_settings(iterations=iterations,
                                                previous_goal_iterations=previous_goal_iterations,
                                                ml_compute_engine_id=ml_compute_engine_id)
    session.add(new_ml_settings)
    session.commit()

    version.machine_learning_settings_id = new_ml_settings.id
    session.add(version)
    session.commit()

    return "Success", 200


@routes.route('/machine_learning/settings/edit', methods=['GET'])
def machine_learning_settings_edit(session, next_id=False):

    if LoggedIn() != True:
        return defaultRedirect()

    project = get_current_project(session)
    version = get_current_version(session)
    machine_learning_settings = get_ml_settings(session, version)

    if next_id is True: 
        machine_learning_settings.ml_compute_engine_id += 1

    session.add(machine_learning_settings)
    session.commit()

    return "Success", 200
    

