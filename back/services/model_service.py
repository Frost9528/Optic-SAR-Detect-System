from extensions import db
from database_models import Model
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask import current_app
import os


class ModelService:
    def __init__(self):
        pass

    @staticmethod
    def _format_model_data(model: Model):
        if not model:
            return None
        return {
            "id": model.id,
            "name": model.name,
            "model_path": model.model_path,
            "model_type": model.model_type,
            "targets": model.targets,
            "accuracy": f"{model.accuracy * 100:.2f}%",
            "false_rate": f"{model.false_rate * 100:.2f}%",
            "create_time": model.create_time.isoformat() if model.create_time else None,
        }

    def _get_model_by_id(self, model_id: int):
        return Model.query.get(model_id)

    def create_model(self, name: str, model_path: str, model_type: str = "default", targets: str = "default", accuracy: float = None, false_rate: float = None):
        if not name or not model_path:
            raise ValueError("Model name and model_path are required.")

        if Model.query.filter((Model.name == name) | (Model.model_path == model_path)).first():
            raise ValueError(f"Model with name '{name}' or path '{model_path}' already exists.")

        try:
            new_model = Model(
                name=name,
                model_path=model_path,
                model_type=model_type,
                targets=targets,
                accuracy=accuracy if accuracy is not None else 0.0,
                false_rate=false_rate if false_rate is not None else 0.0
            )
            db.session.add(new_model)
            db.session.commit()
            return self._format_model_data(new_model)
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error creating model {name}: {e}")
            raise RuntimeError("Failed to create model due to a unique constraint violation.")
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error creating model {name}: {e}")
            raise RuntimeError("Failed to create model due to a database error.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error creating model {name}: {e}")
            raise RuntimeError("An unexpected error occurred while creating the model.")

    def get_model_by_id(self, model_id: int):
        model = self._get_model_by_id(model_id)
        if not model:
            raise FileNotFoundError(f"Model with ID {model_id} not found.")
        return self._format_model_data(model)

    def get_all_models(self):
        models = Model.query.all()
        return [self._format_model_data(model) for model in models]

    def update_model(self, model_id: int, name: str = None, model_path: str = None, model_type: str = None, targets: str = None, accuracy: float = None, false_rate: float = None):
        model = self._get_model_by_id(model_id)
        if not model:
            raise FileNotFoundError(f"Model with ID {model_id} not found.")

        try:
            if Model.query.filter(Model.name == name, Model.id != model_id).first():
                raise ValueError(f"Model name '{name}' already exists for another model.")
            model.name = name if name else model.name
            model.model_path = model_path if model_path else model.model_path
            model.model_type = model_type if model_type else model.model_type
            model.targets = targets if targets else model.targets
            model.accuracy = accuracy if accuracy is not None else model.accuracy
            model.false_rate = false_rate if false_rate is not None else model.false_rate
            db.session.add(model)
            db.session.commit()
            return self._format_model_data(model)
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error updating model {model_id}: {e}")
            raise RuntimeError("Failed to update model due to a unique constraint violation.")
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error updating model {model_id}: {e}")
            raise RuntimeError("Failed to update model due to a database error.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error updating model {model_id}: {e}")
            raise RuntimeError("An unexpected error occurred while updating the model.")

    def delete_model(self, model_id: int):
        model = self._get_model_by_id(model_id)
        if not model:
            raise FileNotFoundError(f"Model with ID {model_id} not found.")

        try:
            db.session.delete(model)
            os.remove(model.model_path)
            db.session.commit()
            return {
                "status": "success",
                "model_id": model_id,
                "model_name": model.name,
                "model_path": model.model_path
            }
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error deleting model {model_id}: {e}")
            raise RuntimeError("Failed to delete model due to a database error.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error deleting model {model_id}: {e}")
            raise RuntimeError("An unexpected error occurred while deleting the model.")


model_service = ModelService()