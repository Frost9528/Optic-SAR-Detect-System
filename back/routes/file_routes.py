import os
from flask import Blueprint, send_from_directory, request, jsonify, current_app
from services.file_service import file_service
from utils.preview_utils import convert_image_to_jpeg_base64


file_bp = Blueprint('file', __name__)

@file_bp.route('', methods=['POST'])
def upload_route():
    images = request.files.getlist("images")
    labels = request.files.getlist("labels")
    label_status = request.form.get('label_status', default='unlabeled')

    import os
    label_dict = {os.path.splitext(label.filename)[0]: label for label in labels}

    results, errors = file_service.upload_files_batch(images, label_dict, label_status, target_subdir="")

    if errors:
        return jsonify({
            'code': 1,
            'message': 'Some files failed to upload or process',
            'errors': errors,
            'data': results
        }), 400
    else:
        return jsonify({
            'code': 0,
            'message': 'Files uploaded successfully',
            'data': results
        }), 200


@file_bp.route('/preview', methods=['POST'])
def upload_preview_route():
    files = request.files.getlist("file")
    results = []

    for file in files:
        try:
            base64_image = convert_image_to_jpeg_base64(file.stream, size=(128, 128), quality=75)
            results.append({
                "filename": file.filename,
                "preview": base64_image
            })
        except Exception as e:
            current_app.logger.error(f"Error processing preview for {file.filename}: {e}")
            results.append({
                "filename": file.filename,
                "error": str(e)
            })

    return jsonify({
        'code': 0,
        'message': 'Preview generated successfully',
        'data': results
    }), 200


@file_bp.route('', methods=['GET'])
def list_files_route():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    filename_search = request.args.get('filename_search', type=str)

    try:
        files_data = file_service.get_all_images(
            page=page,
            per_page=per_page,
            imagename_search=filename_search
        )
        return jsonify({
            'code': 0,
            'message': 'Files retrieved successfully',
            'data': files_data
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error listing files: {e}")
        return jsonify({'code': 1, 'message': f'Failed to retrieve files: {str(e)}'}), 500


@file_bp.route('/<int:file_id>', methods=['GET'])
def get_image_details_route(file_id):
    try:
        file_details = file_service.get_image_details(file_id)
        if file_details:
            return jsonify({
                'code': 0,
                'message': 'File details retrieved successfully',
                'data': file_details
            }), 200
        else:
            return jsonify({'code': 1, 'message': 'File not found'}), 404
    except Exception as e:
        current_app.logger.error(f"Error getting file details for ID {file_id}: {e}")
        return jsonify({'code': 1, 'message': f'Failed to retrieve file details: {str(e)}'}), 500


@file_bp.route('/labels/<path:filename>', methods=['GET'])
def get_label_file(filename):
    label_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    label_path = os.path.join(label_dir, filename)

    if not os.path.exists(label_path):
        return jsonify({'code': 1, 'message': 'Label file not found'}), 404

    try:
        return send_from_directory(label_dir, filename, mimetype='text/plain')
    except Exception as e:
        current_app.logger.error(f"Error getting label {filename}: {e}")
        return jsonify({'code': 1, 'message': f'Failed to read labels from file: {str(e)}'}), 500

@file_bp.route('/copy', methods=['POST'])
def copy_file_route():
    data = request.get_json()
    file_id = data.get('file_id')
    target_subdir = data.get('target_dir', '')

    try:
        result = file_service.copy_file(file_id, target_subdir)
        return jsonify({'code': 0, 'message': 'File copied successfully', 'data': result}), 200
    except (FileNotFoundError, ValueError, FileExistsError) as e:
        status_code = 404 if isinstance(e, FileNotFoundError) else (409 if isinstance(e, FileExistsError) else 400)
        return jsonify({'code': 1, 'message': str(e)}), status_code
    except Exception as e:
        current_app.logger.error(f"Error in copy_file_route: {e}")
        return jsonify({'code': 1, 'message': f'Failed to copy file: {str(e)}'}), 500


@file_bp.route('/move', methods=['POST'])
def move_file_route():
    data = request.get_json()
    file_id = data.get('file_id')
    target_subdir = data.get('target_dir', '')

    try:
        result = file_service.move_file(file_id, target_subdir)
        return jsonify({'code': 0, 'message': 'File moved successfully', 'data': result}), 200
    except (FileNotFoundError, ValueError, FileExistsError) as e:
        status_code = 404 if isinstance(e, FileNotFoundError) else (409 if isinstance(e, FileExistsError) else 400)
        return jsonify({'code': 1, 'message': str(e)}), status_code
    except Exception as e:
        current_app.logger.error(f"Error in move_file_route: {e}")
        return jsonify({'code': 1, 'message': f'Failed to move file: {str(e)}'}), 500


@file_bp.route('/<int:file_id>', methods=['DELETE'])
def delete_file_route(file_id):
    try:
        result = file_service.delete_file(file_id)
        return jsonify({'code': 0, 'message': 'File deleted successfully', 'data': result}), 200
    except FileNotFoundError as e:
        return jsonify({'code': 1, 'message': str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error in delete_file_route: {e}")
        return jsonify({'code': 1, 'message': f'Failed to delete file: {str(e)}'}), 500


@file_bp.route('/delete', methods=['POST'])
def delete_files_batch():
    try:
        data = request.get_json()
        ids = data.get('ids', [])

        if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
            return jsonify({'code': 1, 'message': 'Invalid input. "ids" should be a list of integers'}), 400

        deleted_files = []
        for file_id in ids:
            try:
                result = file_service.delete_file(file_id)
                deleted_files.append(result)
            except FileNotFoundError:
                continue  # 忽略不存在的文件
            except Exception as e:
                current_app.logger.error(f"Failed to delete file {file_id}: {e}")
                continue

        return jsonify({
            'code': 0,
            'message': f'{len(deleted_files)} files deleted successfully',
            'data': deleted_files
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in delete_files_batch: {e}")
        return jsonify({'code': 1, 'message': f'Failed to batch delete files: {str(e)}'}), 500