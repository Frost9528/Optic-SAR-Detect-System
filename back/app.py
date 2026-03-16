import eventlet
eventlet.monkey_patch()


from flask import Flask
from utils.model_utils import ModelManager
from config import Config
from routes.file_routes import file_bp
from routes.dataset_routes import dataset_bp
from routes.detect_routes import detect_bp
from routes.model_routes import model_bp
from routes.training_routes import training_bp
from extensions import db
from utils.listener import redis_pubsub_listener
from flask_socketio import SocketIO
import threading
import redis

socketio = SocketIO()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(file_bp, url_prefix='/files')
    app.register_blueprint(dataset_bp, url_prefix='/datasets')
    app.register_blueprint(detect_bp, url_prefix='/detect')
    app.register_blueprint(model_bp, url_prefix='/models')
    app.register_blueprint(training_bp, url_prefix='/training')

    db.init_app(app)
    socketio.init_app(app,
                      cors_allowed_origins="*",  # 允许所有跨域请求，生产环境请限制为你的前端域名
                      message_queue=f'redis://{app.config["REDIS_HOST"]}:{app.config["REDIS_PORT"]}/{app.config["REDIS_DB"]}')
    with app.app_context():
        db.create_all()

        app.model_manager = ModelManager(max_cached_models=1)
        app.model_manager.preload_model()
        app.redis_client = redis.StrictRedis(
            host=app.config['REDIS_HOST'],
            port=app.config['REDIS_PORT'],
            db=app.config['REDIS_DB'],
            decode_responses=True
        )

        if not hasattr(app, 'redis_pubsub_listener_started'):
            app.redis_pubsub_listener_started = True
            listener_thread = threading.Thread(target=redis_pubsub_listener, args=(socketio, app,), daemon=True)
            listener_thread.start()
            app.logger.info("Started Redis Pub/Sub listener thread for training logs.")

    return app


if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True, use_reloader=False, port=5050, allow_unsafe_werkzeug=True)