from celery_app import celery_app, create_app_for_celery
from services.model_service import model_service
from database_models import Dataset
from flask import current_app
import subprocess
import tempfile
import redis
import time
import json
import yaml
import sys
import os


app = create_app_for_celery()
CANCEL_SIGNAL_KEY_PREFIX = "task_cancel_signal:"
LOG_CHANNEL_PREFIX = "training_log_"
STATUS_CHANNEL_PREFIX = "training_status_"
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
TRAIN_SUBPROCESS_SCRIPT = os.path.join(os.path.dirname(__file__), 'train_script.py')


def get_dataset_config(dataset, base_model):
    config = {
        'path': dataset.dataset_path,
        'train': 'train/images',
        'val': 'val/images',
    }
    # TODO: model_type & targets
    if base_model["model_type"] == 'SAR图像':
        config['names'] = {
            '0': 'ship',
            '1': 'aircraft',
            '2': 'car',
            '3': 'tank',
        }
    elif base_model["model_type"] == '光学图像':
        config['names'] = {
            '0': 'aircraft carrier',
            '1': 'destroyer',
            '2': 'cruiser',
            '3': 'other warship',
            '4': 'civilian ship',
            '5': 'SMV',
            '6': 'LMV',
            '7': 'AFV',
            '8': 'CV',
            '9': 'MCV',
            '10': 'aircraft',
        }

    return config


@celery_app.task(bind=True, track_started=True)
def start_model_training_task(self, task_name, model_id, dataset_id, training_params: dict):
    # TODO: 输出到前端
    task_id = self.request.id
    with app.app_context():
        try:
            current_app.logger.info(f"Celery task for task {task_name} is starting in Flask app context.")

            current_app.logger.info(
                f"Training task {task_name} started. Status updated to RUNNING.")

            dataset = Dataset.query.get(dataset_id)
            if not dataset:
                raise FileNotFoundError(f"Dataset {dataset_id} for task {task_name} not found.")
            current_app.logger.info(
                f"Loading dataset: {dataset.name} with {dataset.image_count} images for task {task_name}.")

            total_epochs = training_params.get('epochs', 1)
            batch_size = training_params.get('batch_size', 32)
            lr = training_params.get('learning_rate', 0.001)
            conf_thres = training_params.get('confidence_threshold', 0.25)

            base_model = model_service.get_model_by_id(model_id)
            config = get_dataset_config(dataset, base_model)
            data_config_path = f"{dataset.dataset_path}/config.yaml"
            with open(data_config_path, 'w') as f:
                yaml.dump(config, f)

            with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as tmp_result_file:
                output_result_path = tmp_result_file.name

            current_app.logger.info(
                f"Task {task_name}: Training results will be saved to temporary file: {output_result_path}")

            command = [
                sys.executable,
                TRAIN_SUBPROCESS_SCRIPT,
                '--task_name', task_name,
                '--model_path', base_model["model_path"],
                '--data_config_path', data_config_path,
                '--epochs', str(total_epochs),
                '--batch_size', str(batch_size),
                '--learning_rate', str(lr),
                '--confidence_threshold', str(conf_thres),
                '--output_result_path', output_result_path,
            ]

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            current_app.logger.info(f"Task {task_name}: Training subprocess started with PID: {process.pid}")
            redis_client.publish(f'{LOG_CHANNEL_PREFIX}{task_id}',
                                 f"Task {task_name}: Training subprocess (PID: {process.pid}) started.")

            while process.poll() is None:
                if redis_client.exists(f"{CANCEL_SIGNAL_KEY_PREFIX}{task_id}"):
                    current_app.logger.warning(
                        f"Task {task_name}: Received stop signal. Terminating subprocess PID {process.pid}.")
                    redis_client.publish(f'{LOG_CHANNEL_PREFIX}{task_id}',
                                         f"Task {task_name}: Received stop signal. Terminating subprocess.")

                    process.kill()
                    process.wait()
                    status_message = {
                        'task_id': task_id,
                        'status': 'CANCELLED',
                        'message': 'Training task was cancelled by request via Redis signal.'
                    }
                    redis_client.publish(f"{STATUS_CHANNEL_PREFIX}{task_id}", json.dumps(status_message))

                    return {
                        'status': 'CANCELLED',
                        'task_id': task_id,
                        'task_name': task_name,
                    }

                line = process.stdout.readline()
                current_app.logger.info(f"Task {task_id} (Subprocess): {line.strip()}")
                redis_client.publish(f'{LOG_CHANNEL_PREFIX}{task_id}', line.strip())

                time.sleep(0.3)

            return_code = process.wait()

            if return_code == 0:
                with open(output_result_path, 'r', encoding='utf-8') as f:
                    final_task_result = json.load(f)
                final_task_result['model_id'] = model_id
                final_task_result['dataset_id'] = dataset_id
                current_app.logger.info(f"Task {task_name}: Subprocess completed successfully. Result loaded.")
                status_message = {
                    'task_id': task_id,
                    'status': 'COMPLETED',
                    'results': final_task_result
                }
            else:
                current_app.logger.error(f"Task {task_id}: Subprocess exited with error code {return_code}.")
                with open(output_result_path, 'r', encoding='utf-8') as f:
                    error_data = json.load(f)
                    final_task_result = error_data
                status_message = {
                    'task_id': task_id,
                    'status': 'FAILED',
                    'error_message': error_data.get('error_message', 'Unknown error occurred during training.'),
                    'traceback': error_data.get('traceback', '')
                }
            redis_client.publish(f"{STATUS_CHANNEL_PREFIX}{task_id}", json.dumps(status_message))

            return final_task_result

        except FileNotFoundError as e:
            current_app.logger.error(f"Celery task failed for task {task_name} (FileNotFoundError): {str(e)}")
        except Exception as e:
            current_app.logger.exception(
                f"Celery task failed for task {task_name} (Unhandled Exception): {str(e)}")
        finally:
            os.remove(output_result_path)
            current_app.logger.info(f"Task {task_id}: Cleaned up temporary result file: {output_result_path}")
            process.kill()