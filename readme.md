
## What is this?

### This is a tiny collection of web based tools for computer vision data preparation and deep learning based object detection built on top of [tensorflow object detection](https://github.com/tensorflow/models/tree/master/research/object_detection).

* Basic multi user annotation
* Integrated data prep tools (ie creating tfrecords)
* Optional cloud machine learning training manager

### Use cases?

* Rapid prototyping
* Collaboration on new dataset creation
* Rough starting point for someone looking to build a service like [clarifai](https://clarifai.com/developer/)


### What does this use?

* [Vue JS](https://vuejs.org/) for annotation UI
* Sample object detection code is [tensorflow object detection](https://github.com/tensorflow/models/tree/master/research/object_detection)
* Database is PSQL with [SQL Alchemy](https://www.sqlalchemy.org/)
* Core web app is [flask](http://flask.pocoo.org/)


## Setup instructions

### Info
These instructions are specific to Google's cloud implementation. With various modifications this code should work with other providers like Microsoft or your own server.

### Warning
This is a *prototype* system with known bugs. Use at your own risk.

### Contributions welcome, for example:
* Polygon capture and ground truth creation for semantic segmentation
* Add other object detection configurations
* More functions around projects and adding users to the same project
* Better error handling
* Test cases and test coverage
* UI work (vue js)


### Quick start instructions
0. **Download code.**


1. **Create storage bucket.**
	1. Suggest regional, us-central1 for speed with machine learning file transfer.


2. **Create postgres sql instance**
	 1. Wait to enable apis
	 2. Save password and id you choose
	 3. Go to config options -> machine type and storage
	 4. Slide cores left for development machine
	 5. Wait for various running tasks things to finish
	 6. Create a new database. While you should be able to use the default one
	this lets you choose an appropriate name, and appears to avoid some strange issues with
	google's psql implementation (specifically connection limits).


4. **Transfer object detection files into cloud storage bucket**
	1. [object_detection](https://storage.googleapis.com/object-demo-bucket/dist/object_detection-0.1.tar.gz)
	2. [slim](https://storage.googleapis.com/object-demo-bucket/dist/slim-0.1.tar.gz)
	* You can use any python tensorflow file but this demo is optimized for the object detection research.
	If you do use your own you will need to [package](https://python-packaging.readthedocs.io/en/latest/minimal.html) your code.
	

5. **Change variables and paths as needed in settings/settings.py**
	1. In settings/settings.py
	2. In app.yaml
	3. *Change secret keys*
	4. Set create tables to true


6. **Various google setup stuff**
	1. Download and install google cloud sdk
	2. Enable machine learning engine api
	3. In google api browser you may need to search for, Enable cloud SQL API (there are two of them, other is enabled automatically)
	4. Create pubsub topic


7. **You need to deploy your app once for the option to create 
an app engine service account to come up**
	1. Once you have done this you can create a service account
	2. Go to API -> Credentials -> Create -> Service account -> JSON 
	3. Service account -> App engine default service account
	4. Place service account file in helpers folder
	5. Check name == service account name in settings


8. **Helpful commands**
	* `cloud_sql_proxy -instances=your-project:your-region:your-instance=tcp:5432`
	* for local `pip install -r requirements.txt`
	* set [default deploy](https://cloud.google.com/sdk/gcloud/reference/config/set)
	* `cd your_working_directory && gcloud app deploy`
	* database scheme is `project:zone:instance`


# Offline usage
1. **Download YAML files from cloud storage**
2. **Use as you wish**
	* For example, update paths in local_files/create_tf_records_local.py and run
	* Download config file, modify as needed
	* Then run training locally
	* OR simply use annotations with custom setup
3. **For video / prediction**
	* If using object detection API, download model file
	* Then create frozen weights (By default online system creates frozen weights in different format  than is preferred by local system)
	* Update paths and run predict.py
	* Run images to video if you wish


### Examples
spacex trained example
	* [video](https://youtu.be/ekl87JspBJs)
	* [tf_events](https://storage.googleapis.com/object-demo-bucket/example_models/spacex/events.out.tfevents)
	* [model](https://storage.googleapis.com/object-demo-bucket/example_models/spacex/model.ckpt-3000.data-00000-of-00001)
	* [frozen model](https://storage.googleapis.com/object-demo-bucket/example_models/spacex/frozen_inference_graph.pb)

### To dos
* Display status of training from publisher
* More training options, ability to tune hyper parameters from UI





