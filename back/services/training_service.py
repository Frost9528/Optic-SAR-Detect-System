from extensions import db
from database_models import TrainingRecord, Dataset, Model
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask import current_app
from datetime import datetime
from pathlib import Path
import shutil
import uuid
import os


class TrainingService:
    def __init__(self):
        pass
    def _serialize_model(self, model: Model):
        return {
            "id": model.id,
            "name": model.name,
            "model_path": model.model_path,
            "model_type": model.model_type,
            "targets": model.targets,
            "accuracy": model.accuracy,
            "false_rate": model.false_rate,
            "create_time": model.create_time.date().isoformat() if model.create_time else None
        }

    def _serialize_training_record(self, task: TrainingRecord):
        return {
            "id": task.id,
            "task_name": task.task_name,
            "model_id": task.model_id,
            "dataset_id": task.dataset_id,
            "training_params": task.get_training_params(),
            "performance_metrics": task.get_performance_metrics(),
            "output_path": task.output_path,
            "model_size": task.model_size,
            "create_time": task.create_time.isoformat(),
        }

    def create_training_task(self, model_id: str, dataset_id: int, training_params: dict = None, task_name: str = None):
        if not task_name:
            task_name = f"model_{model_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

        if TrainingRecord.query.filter_by(task_name=task_name).first():
            raise ValueError(f"Training task with name '{task_name}' already exists.")
        if not Dataset.query.get(dataset_id):
            raise FileNotFoundError(f"Dataset with ID {dataset_id} not found.")

        try:
            new_task = TrainingRecord(
                task_name=task_name,
                model_id=model_id,
                dataset_id=dataset_id,
                start_time=datetime.now()
            )
            if training_params:
                new_task.set_training_params(training_params)

            db.session.add(new_task)
            db.session.commit()
            return self._serialize_training_record(new_task)
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error creating training task {task_name}: {e}")
            raise RuntimeError("Failed to create training task due to a unique constraint violation.")
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error creating training task {task_name}: {e}")
            raise RuntimeError("Failed to create training task due to a database error.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error creating training task {task_name}: {e}")
            raise RuntimeError("An unexpected error occurred while creating the training task.")

    def get_task_by_id(self, task_id: int):
        task = TrainingRecord.query.get(task_id)
        return self._serialize_training_record(task) if task else None

    def get_all_tasks(self, status: str = None, model_name: str = None, dataset_id: int = None, page: int = 1, per_page: int = 10):
        query = TrainingRecord.query

        if status:
            query = query.filter_by(status=status)
        if model_name:
            query = query.filter(TrainingRecord.model_name.ilike(f'%{model_name}%'))
        if dataset_id:
            query = query.filter_by(dataset_id=dataset_id)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        tasks_data = []
        for task in pagination.items:
            tasks_data.append(self._serialize_training_record(task))

        return {
            "tasks": tasks_data,
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages
        }

    def delete_task(self, task_id: int):
        task = TrainingRecord.query.get(task_id)
        if not task:
            raise FileNotFoundError(f"Training task with ID {task_id} not found.")

        try:
            model = Model.query.get(task.model_id)
            db.session.delete(model)
            output_path = Path(task.output_path)
            parent_dir = output_path.parent
            stem = output_path.stem
            possible_dirs = [d for d in parent_dir.glob(f"{stem}*") if d.is_dir()]
            for dir_path in possible_dirs:
                shutil.rmtree(dir_path)
            db.session.delete(task)
            db.session.commit()
            return {"message": f"Training task {task_id} deleted successfully."}
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error deleting training task {task_id}: {e}")
            raise RuntimeError("Failed to delete training task due to a database error.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error deleting training task {task_id}: {e}")
            raise RuntimeError("An unexpected error occurred while deleting the training task.")

    def save_task(self, task_name, task_result):
        new_model_path = os.path.join(task_result['output_path'], 'weights/best.pt')
        if Model.query.filter((Model.name == task_name) | (Model.model_path == new_model_path)).first():
            raise ValueError(f"Model with name '{task_name}' or path '{new_model_path}' already exists.")

        try:
            base_model = Model.query.filter_by(id=task_result['model_id']).first()
            new_model = Model(
                name=task_name,
                model_path=new_model_path,
                model_type=base_model.model_type,
                targets=base_model.targets,
                accuracy=task_result['performance_metrics'].get('final_precision'),
                false_rate=1-task_result['performance_metrics'].get('final_recall'),
                create_time=datetime.now()
            )
            db.session.add(new_model)
            db.session.flush()

            record = TrainingRecord(
                task_name=task_name,
                model_id=new_model.id,
                dataset_id=task_result['dataset_id'],
                output_path=task_result['output_path'],
                model_size=task_result['model_size'],
            )
            record.set_training_params(task_result['training_params'])
            record.set_performance_metrics(task_result['performance_metrics'])
            db.session.add(record)
            db.session.commit()
            return {
                "model": self._serialize_model(new_model),
                "task": self._serialize_training_record(record)
            }
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error saving training task {task_name}: {e}")
            raise RuntimeError("Failed to save training task due to a database error.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error saving training task {task_name}: {e}")
            raise RuntimeError("An unexpected error occurred while saving the training task.")


training_service = TrainingService()