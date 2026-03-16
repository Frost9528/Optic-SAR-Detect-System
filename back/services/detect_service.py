import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from extensions import db
from database_models import DetectionTask, DetectionRecord
from utils.preview_utils import convert_image_to_jpeg_base64

DETECTION_IMAGE_BASE = 'Data/detection/images'
DETECTION_RESULT_BASE = 'Data/detection/results'

class DetectService:
    def __init__(self):
        pass

    def create_task(self, model_id):
        new_task = DetectionTask(
            model_id=model_id,
            created_at=datetime.now(),
            status='pending'
        )
        db.session.add(new_task)
        db.session.commit()
        return new_task.id

    def upload_images(self, image_files, task_id):
        """将图像保存到磁盘，以任务ID为文件夹。"""
        saved_files = []
        errors = []
        task_dir = os.path.join(DETECTION_IMAGE_BASE, f"task_{task_id}")
        os.makedirs(task_dir, exist_ok=True)

        for image_file in image_files:
            try:
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(task_dir, filename)
                target_dir_on_disk = os.path.dirname(image_path)
                if not os.path.exists(target_dir_on_disk):
                    os.makedirs(target_dir_on_disk, exist_ok=True)

                image_file.save(image_path)

                new_detect_instance = DetectionRecord(
                    task_id = task_id,
                    image_name=image_file.filename,
                    image_path=image_path,
                    status ='undetected'
                )
                db.session.add(new_detect_instance)
                db.session.commit()

                saved_files.append({
                    'id': new_detect_instance.id,
                    'task_id' : task_id,
                    'filename': filename,
                    'path': image_path,
                })
            except Exception as e:
                current_app.logger.error(f"Error uploading file {image_file.filename}: {e}")
                errors.append({
                    'filename': image_file.filename,
                    'error': str(e)
                })

        return saved_files, errors

    def save_task(self, task_id):
        try:
            # 更新数据库中对应记录
            task = DetectionTask.query.filter_by(id=task_id).first()
            task.status = 'completed'
            db.session.commit()

        except Exception as e:
            current_app.logger.error(f"Error update task status for {task_id}: {e}")
            db.session.rollback()
            return False

    def save_detection_result(self, task_id, images_id, filename, detections):
        """
        将某图像的检测结果保存为 JSON 文件。
        """
        try:
            # 检测结果保存路径
            task_dir = os.path.join(DETECTION_RESULT_BASE, f"task_{task_id}")
            result_filename = f"{os.path.splitext(filename)[0]}.json"
            result_path = os.path.join(task_dir, result_filename)

            # 保存 JSON 文件
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(detections, f, ensure_ascii=False, indent=2)

            # 更新数据库中对应记录
            record = DetectionRecord.query.filter_by(id=images_id, task_id=task_id).first()
            if record:
                record.created_at = datetime.now()
                record.result_path = result_path  # 如果你在模型中加了这个字段
                record.status = 'detected'
                db.session.commit()
            else:
                current_app.logger.warning(f"No DetectionRecord found for task {task_id}, image {filename}")

            return True

        except Exception as e:
            current_app.logger.error(f"Error saving detection result for {filename}: {e}")
            db.session.rollback()
            return False

    def get_task_results(self, task_id):
        """根据 task_id 获取任务的检测结果"""
        try:
            # 1. 获取检测任务记录
            task = DetectionTask.query.filter_by(id=task_id).first()

            if not task:
                return None  # 任务不存在

            # 2. 获取与任务相关的检测记录
            detection_records = DetectionRecord.query.filter_by(task_id=task_id).all()

            if not detection_records:
                return None  # 如果没有检测记录

            # 3. 组合检测结果数据
            result_list = []
            for record in detection_records:
                try:
                    result = {
                        'image_name': record.image_name,
                        'image_path': record.image_path,
                        'status': record.status,
                        'detections': self.get_detections(record.result_path),  # 假设你有方法来提取检测结果
                        'preview': self.get_image_preview(record.image_path)  # 假设你有方法来生成图像的预览
                    }
                    result_list.append(result)
                except Exception as e:
                    result_list.append({
                        'image_name': record.image_name,
                        'status': 'error',
                        'error': f"Failed to load detection result: {str(e)}"
                    })

            return {
                'task_id': task.id,
                'created_at': task.created_at,
                'status': task.status,
                'results': result_list
            }

        except Exception as e:
            current_app.logger.error(f"Error while fetching task results for {task_id}: {e}")
            return None

    def get_detections(self, detection_result_path):
        """提取检测框结果，假设从文件中获取检测数据"""
        try:
            # 读取存储的检测结果（例如存储为 JSON 文件或数据库表）
            with open(detection_result_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            current_app.logger.error(f"Error reading detection file for {detection_result_path}: {e}")
            return []

    def get_image_preview(self, image_path):
        """返回图像预览"""
        # 假设你有一个方法生成图像的 base64 编码预览图
        try:
            preview = convert_image_to_jpeg_base64(image_path)
            return preview
        except Exception as e:
            current_app.logger.error(f"Error generating preview for {image_path}: {e}")
            return None


detect_service = DetectService()