from flask import Blueprint, request, jsonify
from services.dataset_service import dataset_service


dataset_bp = Blueprint('dataset', __name__)


@dataset_bp.route('', methods=['POST'])
def create_dataset():
    data = request.get_json()
    name = data.get('name')
    type = data.get('type')
    image_ids = data.get('image_ids')

    try:
        new_dataset = dataset_service.create_dataset(name=name, type=type, image_ids=image_ids)
        return jsonify({
            "code": 0,
            "message": "Dataset created successfully",
            "data": new_dataset
        }), 200
    except ValueError as e:
        return jsonify({"code": 1, "message": str(e)}), 409
    except RuntimeError as e:
        return jsonify({"code": 1, "message": f"Server error: {e}"}), 500
    except Exception as e:
        return jsonify({"code": 1, "message": f"An unexpected error occurred: {e}"}), 500


@dataset_bp.route('/<int:dataset_id>', methods=['GET'])
def get_dataset_by_id(dataset_id):
    try:
        dataset = dataset_service.get_dataset_by_id(dataset_id)
        if not dataset:
            return jsonify({"code": 1, "message": "Dataset not found"}), 404
        return jsonify({
            "code": 0,
            "message": "Dataset retrieved successfully",
            "data": dataset
        }), 200
    except RuntimeError as e:
        return jsonify({"code": 1, "message": f"Server error: {e}"}), 500
    except Exception as e:
        return jsonify({"code": 1, "message": f"An unexpected error occurred: {e}"}), 500


@dataset_bp.route('', methods=['GET'])
def get_all_datasets():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    dataset_name_search = request.args.get('dataset_name_search', type=str)

    try:
        datasets = dataset_service.get_all_datasets(
            page=page,
            per_page=per_page,
            dataset_name_search=dataset_name_search
        )
        return jsonify({
            'code': 0,
            'message': 'Datasets retrieved successfully',
            'data': datasets
        }), 200
    except RuntimeError as e:
        return jsonify({'code': 1, "message": f"Server error: {e}"}), 500
    except Exception as e:
        return jsonify({'code': 1, "message": f"An unexpected error occurred: {e}"}), 500


@dataset_bp.route('/<int:dataset_id>', methods=['PUT'])
def update_dataset(dataset_id):
    data = request.get_json()
    new_name = data.get('dataset_name')
    new_description = data.get('description')

    try:
        result = dataset_service.update_dataset(
            dataset_id=dataset_id,
            new_name=new_name,
            new_description=new_description
        )
        return jsonify({
            "code": 0,
            "message": "Dataset updated successfully",
            "data": result
        }), 200
    except ValueError as e:
        return jsonify({"code": 1, "message": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"code": 1, "message": f"Server error: {e}"}), 500
    except Exception as e:
        return jsonify({"code": 1, "message": f"An unexpected error occurred: {e}"}), 500


@dataset_bp.route('/<int:dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    try:
        result = dataset_service.delete_dataset(dataset_id)
        return jsonify({"code": 0, "message": "Dataset deleted successfully", "data": result}), 200
    except FileNotFoundError as e:
        return jsonify({"code": 1, "message": str(e)}), 404
    except RuntimeError as e:
        return jsonify({"code": 1, "message": f"Server error: {e}"}), 500
    except Exception as e:
        return jsonify({"code": 1, "message": f"An unexpected error occurred: {e}"}), 500


@dataset_bp.route('/<int:dataset_id>/images', methods=['POST'])
def add_images_to_dataset(dataset_id):
    data = request.get_json()
    image_ids = data.get('image_ids')

    if not image_ids or not isinstance(image_ids, list):
        return jsonify({"code": 1, "message": "Image ID list is required"}), 400

    try:
        result = dataset_service.add_images_to_dataset(dataset_id=dataset_id, image_ids=image_ids)
        return jsonify({
            "code": 0,
            "message": "Images added to dataset successfully",
            "data": result
        }), 200

    except FileNotFoundError as e:
        return jsonify({"code": 1, "message": str(e)}), 404
    except ValueError as e:
        return jsonify({"code": 1, "message": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"code": 1, "message": f"Server error: {e}"}), 500
    except Exception as e:
        return jsonify({"code": 1, "message": f"An unexpected error occurred: {e}"}), 500


@dataset_bp.route('/<int:dataset_id>/images', methods=['DELETE'])
def remove_images_from_dataset(dataset_id):
    data = request.get_json()
    image_ids = data.get('image_ids')

    if not image_ids or not isinstance(image_ids, list):
        return jsonify({"code": 1, "message": "Image ID list is required"}), 400
    try:
        result = dataset_service.remove_images_from_dataset(dataset_id=dataset_id, image_ids=image_ids)
        return jsonify(result), 200
    except FileNotFoundError as e:
        return jsonify({"code": 1, "message": str(e)}), 404
    except RuntimeError as e:
        return jsonify({"code": 1, "message": f"Server error: {e}"}), 500
    except Exception as e:
        return jsonify({"code": 1, "message": f"An unexpected error occurred: {e}"}), 500


@dataset_bp.route('/<int:dataset_id>/images', methods=['GET'])
def get_images_in_dataset_route(dataset_id):
    # 根据 dataset_items 表一个个查询数据集包含的图像
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    search_image_name = request.args.get('search_image_name', type=str)

    try:
        pagination_result = dataset_service.get_images_in_dataset(
            dataset_id=dataset_id,
            page=page,
            per_page=per_page,
            search_image_name=search_image_name
        )
        return jsonify({
            "code": 0,
            "message": "Images retrieved successfully",
            "data": pagination_result
        }), 200
    except FileNotFoundError as e:
        return jsonify({"code": 1, "message": str(e)}), 404
    except RuntimeError as e:
        return jsonify({"code": 1, "message": f"Server error: {e}"}), 500
    except Exception as e:
        return jsonify({"code": 1, "message": f"An unexpected error occurred: {e}"}), 500