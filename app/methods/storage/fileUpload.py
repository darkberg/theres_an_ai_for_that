from google.cloud import storage
from flask import render_template, url_for, flash, request, redirect, copy_current_request_context, jsonify
import sys, os, re, time, logging, requests
import scipy.misc
from io import BytesIO
import tempfile, zipfile, threading
from werkzeug.utils import secure_filename

from methods import routes
from helpers import sessionMaker
from database_setup import Image, Project, Version
from helpers.permissions import LoggedIn, defaultRedirect, getUserID, get_current_version, get_current_project, get_gcs_service_account
from settings import settings

gcs = storage.Client()
gcs = get_gcs_service_account(gcs)
bucket = gcs.get_bucket(settings.CLOUD_STORAGE_BUCKET)


@routes.route('/upload')
def upload():
    if LoggedIn() != True:
        return defaultRedirect()
    
    return render_template('/storage/uploadView.html')


allowed_file_names = [".jpg", ".jpeg", ".png", ".zip"]


def process_one_image_file(file, name, content_type, session, extension, project, version):
    
    new_image = Image(version_id=version.id, 
                    original_filename=name)
    session.add(new_image)
    session.commit()

    base_dir = str(project.id)+"/"+str(version.id)+"/" + "images/"+ str(new_image.id)
    blob = bucket.blob(base_dir)

    blob.upload_from_string(file.read(),
	    content_type=content_type)

    bytes_image = blob.download_as_string()
    image = scipy.misc.imread(BytesIO(bytes_image))
    if image is None:
        raise IOError("Could not open")
    new_image.height = image.shape[0]
    new_image.width = image.shape[1]

    # TODO maintain aspect ratio
    if image.shape[0] > 1280 or image.shape[1] > 1280:
        image = scipy.misc.imresize(image, (720, 1280))
    
    expiration_time = int(time.time() + 2592000)  # 1 month

    # Save File
    temp = tempfile.mkdtemp()
    new_temp_filename = temp + "/resized" + str(extension)
    scipy.misc.imsave(new_temp_filename, image)
    new_image.height = image.shape[0]
    new_image.width = image.shape[1]
    blob.upload_from_filename(new_temp_filename, content_type="image/jpg")
    url_signed = blob.generate_signed_url(expiration=expiration_time)

    # Save Thumb
    blob = bucket.blob(base_dir+"_thumb")
    thumbnail_image = scipy.misc.imresize(image, (160, 160))
    temp = tempfile.mkdtemp()
    new_temp_filename = temp + "/resized" + str(extension)
    scipy.misc.imsave(new_temp_filename, thumbnail_image)
    blob.upload_from_filename(new_temp_filename, content_type="image/jpg")

    # Build URLS
    url_signed_thumb = blob.generate_signed_url(expiration=expiration_time)
    new_image.url_signed = url_signed
    new_image.url_signed_thumb = url_signed_thumb
    new_image.url_signed_expiry = expiration_time

    session.commit()
    session.close()

    return {"files": [{"name": "Success. Please allow time for images to be processed."}]}


def multi_thread_task_manager(temp_dir, filename, Thread_session, project, version):
    with open(temp_dir + "/" + filename, "rb") as file: 
        if not file:
            print("No file loaded from zip", file=sys.stderr)

        extension = os.path.splitext(file.name)[1].lower()
        if extension in allowed_file_names:
            content_type = "image/" + str(extension)

            thread_session = Thread_session()
            process_one_image_file(file=file, name=filename, content_type=content_type, 
                    session=thread_session, extension=extension, project=project, version=version)

            Thread_session.remove()
            thread = threading.current_thread()
            thread.cancel()



@routes.route('/upload-action', methods=['POST'])
def uploadPOST():
    if LoggedIn() != True:
        return defaultRedirect()
 
    @copy_current_request_context
    def task_manager(name, extension):  # Function is defined here to so as to use request context decorator with scopped session.

        session = sessionMaker.newSession()
        project = get_current_project(session)
        version = get_current_version(session)
        counter = 0

        out = ""
        with open(name, "rb") as file:              
            if extension == ".zip":
                try:                        
                    zip_ref = zipfile.ZipFile(BytesIO(file.read()), 'r')
                    temp_dir = tempfile.mkdtemp()
                    zip_ref.extractall(temp_dir)
                    zip_ref.close()

                    filenames = sorted(os.listdir(temp_dir))
                    len_filenames = len(filenames)  # Variable used in loop below so storing here
                    print("[ZIP processor] Found", len_filenames, file=sys.stderr)
                    version.train_length += len_filenames
                    session.add(version)
                    session.commit()

                    Thread_session = sessionMaker.scoppedSession()  # Threadsafe

                    for filename in filenames:

                        t_2 = threading.Timer(0, multi_thread_task_manager, 
                                            args=(temp_dir, filename, Thread_session, project, version))
                        t_2.start()

                        # Slow down new threads if too many open
                        len_threads = len(threading.enumerate())
                        if len_threads > settings.MAX_UPLOAD_THREADS:
                            time.sleep(settings.MAX_UPLOAD_THREADS * 25)          
                        if len_threads > settings.TARGET_UPLOAD_THREADS:
                            time.sleep(settings.TARGET_UPLOAD_THREADS * 5)

                        counter += 1
                        if counter % 10 == 0:
                            print("[ZIP processor]", (counter / len(filenames) ) * 100, "% done." , file=sys.stderr)

                except zipfile.BadZipFile:
                    out = {"files": [{"name": "Error bad zip file"}]}
        
            else:
                content_type = "image/" + str(extension)
                file_name = os.path.split(file.name)[1]
                version.train_length += 1
                session.add(version)
                session.commit()

                out = process_one_image_file(file=file, name=file_name, 
                                    content_type=content_type, extension=extension, 
                                    session=session, project=project, version=version)


        out = {"files": [{"name": "Processed files"}]}
        print(out, file=sys.stderr)
        t.cancel()


    file = request.files.get('files[]')
    if not file:
        return "No file", 400
        
    extension = os.path.splitext(file.filename)[1].lower()
    if extension in allowed_file_names:

        file.filename = secure_filename(file.filename) # http://flask.pocoo.org/docs/0.12/patterns/fileuploads/          
        temp_dir = tempfile.mkdtemp()
        name = temp_dir + "/" + file.filename
        file.save(name)

        t = threading.Timer(0, task_manager, args=(name, extension))  # https://stackoverflow.com/questions/29330982/python-timer-nonetype-object-is-not-callable-error
        t.daemon = True
        t.start()

        out = {"files": [{"name": "Success"}]}
    else:
        out = {"files": [{"name": "Invalid file extension"}]}


    return jsonify(out)



