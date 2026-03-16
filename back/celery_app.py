from celery import Celery
from flask import Flask
from config import Config
from extensions import db
import os


REDIS_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
REDIS_BACKEND_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')

celery_app = Celery(
    'model_trainer',
    broker=REDIS_BROKER_URL,
    backend=REDIS_BACKEND_URL,
    include=['utils.train_utils']
)


def create_app_for_celery():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    return app


celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    broker_connection_retry_on_startup=True
)