
### Setup instructions

## Info
These instructions are specific to Google's cloud implementation. With various modifications this code should work with other providers like Microsoft or your own server.

## Warning
This is a *prototype* system with known bugs. Use at your own risk.

## Contributions welcome, for example:
* Polygon capture and ground truth creation for semantic segmentation
* Add other object detection configurations
* More functions around projects and adding users to the same project
* Better error handling
* Test cases and test coverage
* UI work (vue js)


## Quick start instructions
0. Download code


1. Create storage bucket. 
* Suggest regional, us-central1 for speed with machine learning file transfer.


2. Create postgres sql instance
 * Wait to enable apis
 * Save password and id you choose
 * Go to config options -> machine type and storage
 * Slide cores left for development machine
 * Wait for various running tasks things to finish
 * Create a new database. While you should be able to use the default one
this lets you choose an appropriate name, and appears to avoid some strange issues with
google's psql implementation (specifically connection limits).


4. Transfer object detection files into cloud storage bucket
* [object_detection](https://storage.googleapis.com/object-demo-bucket/dist/object_detection-0.1.tar.gz)
* [slim](https://storage.googleapis.com/object-demo-bucket/dist/slim-0.1.tar.gz)
You can use any python tensorflow file but this demo is optimized for the object detection research.
If you do use your own you will need to [package](https://python-packaging.readthedocs.io/en/latest/minimal.html) your code.
	

5. Change variables and paths as needed in settings/settings.py
* In settings/settings.py
* In app.yaml
* Especially change secret keys
* Set create tables to true


6. Various google setup stuff
* Download and install google cloud sdk
* Enable machine learning engine api
* In google api browser you may need to search for, Enable cloud SQL API (there are two of them, other is enabled automatically)
* Create pubsub topic


7. You need to deploy your app once for the option to create 
an app engine service account to come up
* Once you have done this you can create a service account
* Go to API -> Credentials -> Create -> Service account -> JSON 
* Service account -> App engine default service account
* Place service account file in helpers folder
* Check name == service account name in settings


Helpful commands
* `cloud_sql_proxy -instances=your-project:your-region:your-instance=tcp:5432`
* for local `pip install -r requirements.txt`
* set [default deploy](https://cloud.google.com/sdk/gcloud/reference/config/set)
* cd your_working_directory && gcloud app deploy
* database scheme is `project:zone:instance`


# Offline usage
1. Download YAML files from cloud storage
2. Use as you wish
* For example, update paths in local_files/create_tf_records_local.py and run
* Download config file, modify as needed
* Then run training locally
* OR simply use annotations with custom setup
3. For video / prediction
* If using object detection API, download model file
* Then create frozen weights (By default online system creates frozen weights in different format  than is preferred by local system)
* Update paths and run predict.py
* Run images to video if you wish


# Examples
spacex trained example
* [video](https://youtu.be/ekl87JspBJs)
* [tf_events](https://storage.googleapis.com/object-demo-bucket/example_models/spacex/events.out.tfevents)
* [model](https://storage.googleapis.com/object-demo-bucket/example_models/spacex/model.ckpt-3000.data-00000-of-00001)
* [frozen model](https://storage.googleapis.com/object-demo-bucket/example_models/spacex/frozen_inference_graph.pb)

## To dos
* Display status of training from publisher
* More training options, ability to tune hyper parameters from UI





