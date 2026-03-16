from flask import Blueprint, request, jsonify, current_app
from services.training_service import training_service
from utils.train_utils import start_model_training_task
from datetime import datetime
from celery_app import celery_app


CANCEL_SIGNAL_KEY_PREFIX = "task_cancel_signal:"
training_bp = Blueprint('training', __name__)


@training_bp.route('/tasks', methods=['POST'])
def create_training_task_route():
    data = request.get_json()
    model_id = data.get('model')
    dataset_id = data.get('dataset')
    training_params = {
        'epochs': data.get('epochs', 1),
        'batch_size': data.get('batchSize', 32),
        'learning_rate': data.get('learningRate', 0.001),
        'confidence_threshold': data.get('confidence_threshold', 0.25)
    }
    task_name = data.get('task_name')
    if not task_name:
        task_name = f"model_{model_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    if not model_id or not dataset_id:
        return jsonify({
            "code": 1,
            "message": "model and dataset are required.",
            "data": None
        }), 400

    try:
        task = start_model_training_task.delay(task_name, model_id, dataset_id, training_params)

        return jsonify({
            "code": 0,
            "message": "Training task created and started successfully.",
            "data": task.task_id
        }), 202
    except Exception as e:
        current_app.logger.exception("An unexpected error occurred while creating training task.")
        return jsonify({
            "code": 1,
            "message": f"An unexpected error occurred: {e}",
            "data": None
        }), 500


@training_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_training_task(task_id):
    try:
        task = training_service.get_task_by_id(task_id)
        if not task:
            return jsonify({
                "code": 1,
                "message": "Training task not found.",
                "data": None
            }), 404

        return jsonify({
            "code": 0,
            "message": "Training task details retrieved successfully.",
            "data": task
        }), 200
    except RuntimeError as e:
        current_app.logger.error(f"Server error getting training task status: {e}")
        return jsonify({
            "code": 1,
            "message": f"Server error: {e}",
            "data": None
        }), 500
    except Exception as e:
        current_app.logger.exception("An unexpected error occurred while getting training task status.")
        return jsonify({
            "code": 1,
            "message": f"An unexpected error occurred: {e}",
            "data": None
        }), 500


@training_bp.route('/tasks', methods=['GET'])
def list_training_tasks():
    status = request.args.get('status')
    model_name = request.args.get('model_name')
    dataset_id = request.args.get('dataset_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 40, type=int)

    try:
        results = training_service.get_all_tasks(
            status=status, model_name=model_name, dataset_id=dataset_id,
            page=page, per_page=per_page
        )

        return jsonify({
            "code": 0,
            "message": "Training tasks retrieved successfully.",
            "data": results
        }), 200
    except RuntimeError as e:
        current_app.logger.error(f"Server error listing training tasks: {e}")
        return jsonify({
            "code": 1,
            "message": f"Server error: {e}",
            "data": None
        }), 500
    except Exception as e:
        current_app.logger.exception("An unexpected error occurred while listing training tasks.")
        return jsonify({
            "code": 1,
            "message": f"An unexpected error occurred: {e}",
            "data": None
        }), 500


@training_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_training_task(task_id):
    try:
        result = training_service.delete_task(task_id)
        return jsonify({
            "code": 0,
            "message": result["message"],
            "data": None
        }), 200
    except FileNotFoundError as e:
        return jsonify({
            "code": 1,
            "message": str(e),
            "data": None
        }), 404
    except RuntimeError as e:
        current_app.logger.error(f"Server error deleting training task: {e}")
        return jsonify({
            "code": 1,
            "message": f"Server error: {e}",
            "data": None
        }), 500
    except Exception as e:
        current_app.logger.exception("An unexpected error occurred while deleting training task.")
        return jsonify({
            "code": 1,
            "message": f"An unexpected error occurred: {e}",
            "data": None
        }), 500


@training_bp.route('/tasks/<task_id>/save', methods=['POST'])
def save_training_task(task_id):
    task_name = request.json.get('model_name')
    task_result = celery_app.AsyncResult(task_id)
    if task_result.state != 'SUCCESS':
        return jsonify({
            "code": 1,
            "message": "Task is not completed successfully.",
            "data": {"task_id": task_id}
        }), 400

    try:
        result_data = task_result.get()
        result = training_service.save_task(task_name, result_data)
        return jsonify({
            "code": 0,
            "message": "Training task saved successfully.",
            "data": result
        }), 200
    except RuntimeError as e:
        current_app.logger.error(f"Server error saving training task: {e}")
        return jsonify({
            "code": 1,
            "message": f"Server error: {e}",
            "data": None
        }), 500
    except Exception as e:
        current_app.logger.exception("An unexpected error occurred while saving training task.")
        return jsonify({
            "code": 1,
            "message": f"An unexpected error occurred: {e}",
            "data": None
        }), 500


@training_bp.route('/tasks/<task_id>/cancel', methods=['POST'])
def cancel_training_task(task_id):
    task_result = celery_app.AsyncResult(task_id)
    if task_result.state not in ['PENDING', 'STARTED']:
        return jsonify({
            "code": 1,
            "message": "Task is not running or already completed.",
            "data": {"task_id": task_id}
        }), 400

    try:
        current_app.redis_client.set(f"{CANCEL_SIGNAL_KEY_PREFIX}{task_id}", "1")
        task_result.revoke(terminate=True)

        return jsonify({
            "code": 0,
            "message": "Training task cancelled successfully.",
            "data": {"task_id": task_id}
        }), 200
    except Exception as e:
        current_app.logger.exception("An unexpected error occurred while cancelling training task.")
        return jsonify({
            "code": 1,
            "message": f"An unexpected error occurred: {e}",
            "data": None
        }), 500


@training_bp.route('/tasks/<task_id>/result', methods=['GET'])
def get_training_task_result_from_redis(task_id):
    task_result = celery_app.AsyncResult(task_id)

    if task_result.state == 'PENDING':
        return jsonify({
            "code": 0,
            "message": "Task is still pending or unknown.",
            "data": {"status": "PENDING", "task_id": task_id}
        }), 202
    elif task_result.state == 'STARTED':
        return jsonify({
            "code": 0,
            "message": "Task is currently running.",
            "data": {"status": "RUNNING", "task_id": task_id}
        }), 202
    elif task_result.state == 'SUCCESS':
        result_data = task_result.get()
        return jsonify({
            "code": 0,
            "message": "Task completed successfully.",
            "data": result_data
        }), 200
    elif task_result.state == 'FAILURE':
        error_info = task_result.get(propagate=False)
        return jsonify({
            "code": 0,
            "message": "Task failed.",
            "data": {"status": "FAILED", "task_id": task_id, "error": str(error_info)}
        }), 500
    else:
        return jsonify({
            "code": 0,
            "message": f"Task status: {task_result.state}",
            "data": {"status": task_result.state, "task_id": task_id}
        }), 202