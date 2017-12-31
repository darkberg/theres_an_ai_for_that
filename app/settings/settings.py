

DATABASE_URL = "postgresql+psycopg2://USER_NAME:PASSWORD@/DATABASE_NAME?host=/cloudsql/PROJECT_NAME:REGION:INSTANCE"
CREATE_TABLES = False  # Set to True to create tables

CLOUD_STORAGE_BUCKET = 'demo-bucket'
GOOGLE_PROJECT_NAME = 'demo'

SERVICE_ACCOUNT = "service_account.json"
DB_SECRET = 'abc123'
SECRET_KEY = 'abc123\x'
SIGNUP_CODE = '123'

LIB_OBJECT_DETECTION_PYTHON = 'dist/object_detection-0.1.tar.gz'
LIB_SLIM_PYTHON = 'dist/slim-0.1.tar.gz'

PUB_SUB_TOPIC = 'abc'
PUB_SUB_SUBSCRIPTION = 'my_subscription'  # not implemented

RESNET_PRE_TRAINED_MODEL = 'transfer_learning/model.ckpt'

MAX_UPLOAD_THREADS = 8
TARGET_UPLOAD_THREADS = 5