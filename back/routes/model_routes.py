from flask import Blueprint, request, jsonify
from services.model_service import model_service
from flask import current_app


model_bp = Blueprint('model', __name__)


@model_bp.route('', methods=['POST'])
def create_model_route():
    data = request.get_json()
    name = data.get('name')
    model_path = data.get('model_path')
    model_type = data.get('model_type')
    targets = data.get('targets')
    accuracy = data.get('accuracy')
    false_rate = data.get('false_rate')

    try:
        new_model = model_service.create_model(name, model_path, model_type, targets, accuracy, false_rate)
        return jsonify({
            "code": 0,
            "message": "Model created successfully.",
            "data": new_model
        }), 200
    except (ValueError, FileNotFoundError) as e:
        return jsonify({
            "code": 1,
            "message": str(e),
            "data": None
        }), 400
    except RuntimeError as e:
        current_app.logger.error(f"Server error creating model: {e}")
        return jsonify({
            "code": 1,
            "message": f"Server error: {e}",
            "data": None
        }), 500
    except Exception as e:
        current_app.logger.exception("An unexpected error occurred while creating model.")
        return jsonify({
            "code": 1,
            "message": f"An unexpected error occurred: {e}",
            "data": None
        }), 500

@model_bp.route('', methods=['GET'])
def get_all_models_route():
    try:
        models = model_service.get_all_models()
        return jsonify({
            "code": 0,
            "message": "Models retrieved successfully.",
            "data": models
        }), 200
    except RuntimeError as e:
        current_app.logger.error(f"Server error getting all models: {e}")
        return jsonify({
            "code": 1,
            "message": f"Server error: {e}",
            "data": None
        }), 500
    except Exception as e:
        current_app.logger.exception("An unexpected error occurred while getting all models.")
        return jsonify({
            "code": 1,
            "message": f"An unexpected error occurred: {e}",
            "data": None
        }), 500

@model_bp.route('/<int:model_id>', methods=['GET'])
def get_model_route(model_id: int):
    try:
        model = model_service.get_model_by_id(model_id)
        if not model:
            return jsonify({
                "code": 0,
                "message": "Model not found.",
                "data": None
            }), 404
        return jsonify({
            "code": 1,
            "message": "Model retrieved successfully.",
            "data": model
        }), 200
    except RuntimeError as e:
        current_app.logger.error(f"Server error getting model by ID {model_id}: {e}")
        return jsonify({
            "code": 1,
            "message": f"Server error: {e}",
            "data": None
        }), 500
    except Exception as e:
        current_app.logger.exception(f"An unexpected error occurred while getting model by ID {model_id}.")
        return jsonify({
            "code": 1,
            "message": f"An unexpected error occurred: {e}",
            "data": None
        }), 500

@model_bp.route('/<int:model_id>', methods=['PUT'])
def update_model_route(model_id: int):
    data = request.get_json()
    name = data.get('name')
    model_path = data.get('model_path')
    model_type = data.get('model_type')
    targets = data.get('targets')
    accuracy = data.get('accuracy')
    false_rate = data.get('false_rate')

    try:
        updated_model = model_service.update_model(model_id, name, model_path, model_type, targets, accuracy, false_rate)
        return jsonify({
            "code": 0,
            "message": "Model updated successfully.",
            "data": updated_model
        }), 200
    except (ValueError, FileNotFoundError) as e:
        return jsonify({
            "code": 1,
            "message": str(e),
            "data": None
        }), 400
    except RuntimeError as e:
        current_app.logger.error(f"Server error updating model {model_id}: {e}")
        return jsonify({
            "code": 1,
            "message": f"Server error: {e}",
            "data": None
        }), 500
    except Exception as e:
        current_app.logger.exception(f"An unexpected error occurred while updating model {model_id}.")
        return jsonify({
            "code": 1,
            "message": f"An unexpected error occurred: {e}",
            "data": None
        }), 500

@model_bp.route('/<int:model_id>', methods=['DELETE'])
def delete_model_route(model_id: int):
    try:
        result = model_service.delete_model(model_id)
        return jsonify({
            "code": 0,
            "message": "Model deleted successfully.",
            "data": result
        }), 200
    except FileNotFoundError as e:
        return jsonify({
            "code": 1,
            "message": str(e),
            "data": None
        }), 404
    except RuntimeError as e:
        current_app.logger.error(f"Server error deleting model {model_id}: {e}")
        return jsonify({
            "code": 1,
            "message": f"Server error: {e}",
            "data": None
        }), 500
    except Exception as e:
        current_app.logger.exception(f"An unexpected error occurred while deleting model {model_id}.")
        return jsonify({
            "code": 1,
            "message": f"An unexpected error occurred: {e}",
            "data": None
        }), 500