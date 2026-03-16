from flask import Blueprint, request, jsonify, current_app
from utils.preview_utils import convert_image_to_jpeg_base64
from services.detect_service import detect_service


detect_bp = Blueprint('detect', __name__)


@detect_bp.route('', methods=['POST'])
def detect():
    if 'image' not in request.files:
        return jsonify({"code": 1, "data": {}, "message": "No image file provided."}), 400

    model_id = request.form.get('model_id', type=int)
    enhance = request.form.get('enhance', type=int, default=0)
    denoise = request.form.get('denoise', type=int, default=0)
    detector = current_app.model_manager.get_detector(model_identifier=model_id)
    if not detector:
        return jsonify({"code": 1, "data": {}, "message": "Model not found."}), 404

    try:
        # 步骤 1：创建任务
        task = detect_service.create_task(model_id=model_id)
        task_id = task.id

        # 步骤 2：保存图像
        image_files = request.files.getlist('image')
        saved_images, _ = detect_service.upload_images(image_files=image_files, task_id=task_id)

        detection_results = []

        # 步骤 3：执行检测 + 保存结果
        for image_info in saved_images:
            images_id = image_info['id']
            image_path = image_info['path']
            filename = image_info['filename']

            # 读取图像并预处理
            with open(image_path, 'rb') as f:
                detector.read_image(f.read())
            if enhance:
                detector.enhance_image()
            if denoise:
                detector.denoise_image()

            # 检测并保存结果
            detections = detector.detect()
            detect_service.save_detection_result(task_id=task_id, images_id=images_id, filename=filename, detections=detections)

            detection_results.append({
                "name": filename,
                "detections": detections,
                "preview": detector.get_image_base64()
            })

        detect_service.save_task(task_id)

        return jsonify({
            "code": 0,
            "data": {
                "task_id": task_id,
                "results": detection_results
            },
            "message": "Detection completed successfully."
        }), 200

    except Exception as e:
        current_app.logger.exception("Detection error:")
        return jsonify({"code": 1, "data": {}, "message": f"Internal error: {str(e)}"}), 500


@detect_bp.route('/result/<int:task_id>', methods=['GET'])
def get_detection_result(task_id):
    try:
        # 调用服务方法获取检测任务结果
        task_results = detect_service.get_task_results(task_id)

        if task_results:
            return jsonify({
                'code': 0,
                'message': 'Detection results retrieved successfully',
                'data': task_results
            }), 200
        else:
            return jsonify({
                'code': 1,
                'message': 'Task not found or results not available'
            }), 404
    except Exception as e:
        current_app.logger.error(f"Error fetching detection result for task {task_id}: {e}")
        return jsonify({
            'code': 1,
            'message': f"Failed to retrieve task results: {str(e)}"}
        ), 500
