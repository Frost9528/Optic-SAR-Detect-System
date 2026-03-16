from extensions import db
from database_models import Dataset, Image, DatasetItem
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload
from flask import current_app
import random
import shutil
from pathlib import Path
from utils.preview_utils import convert_image_to_jpeg_base64


class DatasetService:
    def __init__(self):
        pass

    def _serialize_dataset(self, dataset: Dataset):
        return {
            "id": dataset.id,
            "name": dataset.name,
            "type": dataset.type,
            "dataset_path": dataset.dataset_path,
            "create_time": dataset.create_time.date().isoformat(),
            "image_count": dataset.image_count,
            "last_modified_time": dataset.last_modified_time.isoformat()
        }

    def _get_dataset_by_id(self, dataset_id):
        return Dataset.query.get(dataset_id)

    def get_dataset_by_id(self, dataset_id):
        dataset = self._get_dataset_by_id(dataset_id)
        return self._serialize_dataset(dataset)

    def get_dataset_by_name(self, name):
        return Dataset.query.filter_by(name=name).first()

    def create_dataset(self, name, type, image_ids):
        if not name:
            raise ValueError("Dataset name cannot be empty.")

        existing_dataset = self.get_dataset_by_name(name)
        if existing_dataset:
            raise ValueError(f"Dataset with name '{name}' already exists.")

        try:
            dataset_path = f"datasets/{name}"
            new_dataset = Dataset(name=name, type=type, dataset_path=dataset_path)
            db.session.add(new_dataset)
            db.session.flush()
            self.add_images_to_dataset(new_dataset.id, image_ids)
            db.session.commit()
            return self._serialize_dataset(new_dataset)
        except ValueError as e:
            db.session.rollback()
            current_app.logger.error(f"Value error creating dataset {name}: {e}")
            raise e
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error creating dataset {name}: {e}")
            raise RuntimeError("Failed to create dataset due to a database error.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error creating dataset {name}: {e}")
            raise RuntimeError("An unexpected error occurred while creating the dataset.")

    def get_all_datasets(self, page=1, per_page=10, dataset_name_search=None):
        query = Dataset.query
        if dataset_name_search:
            query = query.filter(Dataset.name.ilike(f'%{dataset_name_search}%'))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        datasets = []
        for dataset in pagination.items:
            datasets.append(self._serialize_dataset(dataset))

        return {
            "datasets": datasets,
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages
        }

    def add_images_to_dataset(self, dataset_id, image_ids):
        dataset = self._get_dataset_by_id(dataset_id)
        if not dataset:
            raise FileNotFoundError(f"Dataset with ID {dataset_id} not found.")

        images = Image.query.filter(Image.id.in_(image_ids)).all()
        if not images:
            raise FileNotFoundError(f"No images found for IDs: {image_ids}")

        try:
            existing_items = DatasetItem.query.filter(
                DatasetItem.dataset_id == dataset_id,
                DatasetItem.image_id.in_(image_ids)
            ).all()

            existing_image_ids = {item.image_id for item in existing_items}
            image_wo_label = {image.id for image in images if not image.has_label}
            new_image_ids = set(image_ids) - existing_image_ids - image_wo_label

            new_dataset_items = [
                DatasetItem(dataset_id=dataset_id, image_id=image_id)
                for image_id in new_image_ids
            ]

            db.session.bulk_save_objects(new_dataset_items)
            dataset.image_count += len(new_dataset_items)
            db.session.add(dataset)

            images = Image.query.filter(Image.id.in_(new_image_ids)).all()
            random.shuffle(images)
            train_images = images[:int(len(images) * 0.8)]
            val_images = images[int(len(images) * 0.8):]
            dataset_path = Path(dataset.dataset_path)
            for split, imgs in [("train", train_images), ("val", val_images)]:
                for subdir in ["images", "labels"]:
                    (dataset_path / split / subdir).mkdir(parents=True, exist_ok=True)
                for img in imgs:
                    shutil.copy2(img.image_path, dataset_path / split / "images")
                    shutil.copy2(img.label_path, dataset_path / split / "labels")

            db.session.commit()

            return {
                "dataset_id": dataset_id,
                "dataset_name": dataset.name,
                "dataset_type": dataset.type,
                "dataset_image_count": dataset.image_count,
                "dataset_path": dataset.dataset_path,
                "added": len(new_dataset_items),
                "existing": len(existing_items),
                "image_without_label": list(image_wo_label),
                "total": len(image_ids)
            }

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error adding images to dataset {dataset_id}: {e}")
            raise RuntimeError("Failed to add images to dataset due to a database error.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error adding images to dataset {dataset_id}: {e}")
            raise RuntimeError("An unexpected error occurred while adding images to dataset.")

    def remove_images_from_dataset(self, dataset_id, image_ids):
        dataset = self._get_dataset_by_id(dataset_id)
        if not dataset:
            raise FileNotFoundError(f"Dataset with ID {dataset_id} not found.")
        if not image_ids:
            raise ValueError("No image IDs provided for removal.")

        try:
            dataset_items = DatasetItem.query.filter(
                DatasetItem.dataset_id == dataset_id,
                DatasetItem.image_id.in_(image_ids)
            ).all()
            if not dataset_items:
                raise FileNotFoundError(f"No records found in dataset {dataset_id} for IDs: {image_ids}")
            removed_count = len(dataset_items)
            dataset.image_count = max(0, dataset.image_count - removed_count)
            db.session.add(dataset)
            for item in dataset_items:
                db.session.delete(item)
            db.session.commit()

            return {
                "removed": len(dataset_items),
                "dataset_id": dataset_id,
                "dataset_name": dataset.name,
                "image_ids": image_ids
            }
        except FileNotFoundError as e:
            db.session.rollback()
            current_app.logger.error(f"File not found error removing images from dataset {dataset_id}: {e}")
            raise e
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error removing images from dataset {dataset_id}: {e}")
            raise RuntimeError("Failed to remove images from dataset due to a database error.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error removing images from dataset {dataset_id}: {e}")
            raise RuntimeError("An unexpected error occurred while removing images from dataset.")

    def get_images_in_dataset(self, dataset_id, page=1, per_page=10, search_image_name=None):
        dataset = self._get_dataset_by_id(dataset_id)
        if not dataset:
            raise FileNotFoundError(f"Dataset with ID {dataset_id} not found.")

        query = DatasetItem.query.filter_by(dataset_id=dataset_id) \
            .options(joinedload(DatasetItem.image))
        if search_image_name:
            query = query.join(Image).filter(Image.image_name.ilike(f'%{search_image_name}%'))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        items = []
        for dataset_item in pagination.items:
            image = dataset_item.image
            image_preview = convert_image_to_jpeg_base64(image.image_path, size=None)
            items.append({
                "image_id": image.id,
                "image_name": image.image_name,
                "image_path": image.image_path,
                "label_path": image.label_path if image.has_label else None,
                "image_preview": image_preview,
                "added_to_dataset_at": dataset_item.create_time.isoformat(),
                "uploaded_at": image.upload_time.isoformat()
            })

        return {
            "items": items,
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "dataset_type": dataset.type,
            "dataset_path": dataset.dataset_path,
            "dataset_image_count": dataset.image_count,
            "dataset_create_time": dataset.create_time.date().isoformat(),
            "dataset_last_modified_time": dataset.last_modified_time.isoformat(),
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages
        }

    def delete_dataset(self, dataset_id):
        dataset = self._get_dataset_by_id(dataset_id)
        if not dataset:
            raise FileNotFoundError(f"Dataset with ID {dataset_id} not found.")

        try:
            db.session.delete(dataset)
            dataset_path = Path(dataset.dataset_path)
            shutil.rmtree(dataset_path)
            db.session.commit()
            return {
                "status": "success",
                "dataset_id": dataset_id,
                "dataset_name": dataset.name,
            }

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error deleting dataset {dataset_id}: {e}")
            raise RuntimeError("Failed to delete dataset due to a database error.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error deleting dataset {dataset_id}: {e}")
            raise RuntimeError("An unexpected error occurred while deleting the dataset.")

    def update_dataset(self, dataset_id, new_name=None):
        dataset = self._get_dataset_by_id(dataset_id)
        if not dataset:
            raise FileNotFoundError(f"Dataset with ID {dataset_id} not found.")

        if new_name is None:
            raise ValueError("'new_name' must be provided.")

        try:
            existing_dataset = self.get_dataset_by_name(new_name)
            if existing_dataset and existing_dataset.id != dataset_id:
                raise ValueError(f"Dataset with name '{new_name}' already exists.")
            dataset.name = new_name
            db.session.add(dataset)
            db.session.commit()
            return self._serialize_dataset(dataset)
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error updating dataset {dataset_id}: {e}")
            raise RuntimeError("Failed to update dataset due to a database constraint violation.")
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error updating dataset {dataset_id}: {e}")
            raise RuntimeError("Failed to update dataset due to a database error.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error updating dataset {dataset_id}: {e}")
            raise RuntimeError("An unexpected error occurred while updating the dataset.")


dataset_service = DatasetService()