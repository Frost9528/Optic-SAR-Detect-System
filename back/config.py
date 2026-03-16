import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:011024@127.0.0.1:3306/sar'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))

    CURRENT_FOLDER = os.path.abspath(os.path.dirname(__file__))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'tif', 'txt', 'csv', 'json'}


class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True