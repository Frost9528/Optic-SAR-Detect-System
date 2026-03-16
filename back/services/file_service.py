import os
import shutil
from flask import current_app, url_for
from extensions import db
from database_models import Image, Dataset, DatasetItem
from werkzeug.utils import secure_filename
from utils.file_utils import get_safe_full_path, allowed_file
from utils.preview_utils import convert_image_to_jpeg_base64
from sqlalchemy import update


class FileService:
    def __init__(self):
        pass

    def get_image_by_id(self, image_id):
        return Image.query.get(image_id)

    def upload_file(self, image_obj, target_subdir="", label_obj=None, label_status='uploaded'):
        if not image_obj or not image_obj.filename:
            raise ValueError("No Image provided.")
        if not allowed_file(image_obj.filename):
            raise ValueError(f"Image type not allowed: {image_obj.filename}")

        target_subdir = os.path.join('uploads', target_subdir.strip('/'))
        original_filename_secure = os.path.basename(image_obj.filename)
        file_relative_path = os.path.normpath(os.path.join(target_subdir, original_filename_secure))

        try:
            filepath_on_disk = get_safe_full_path(file_relative_path)
            target_dir_on_disk = os.path.dirname(filepath_on_disk)
            if not os.path.exists(target_dir_on_disk):
                os.makedirs(target_dir_on_disk, exist_ok=True)

            image_obj.save(filepath_on_disk)

            if label_obj:
                label_filename_secure = secure_filename(label_obj.filename)
                label_relative_path = os.path.normpath(os.path.join(target_subdir, label_filename_secure))
                label_filepath_on_disk = get_safe_full_path(label_relative_path)
                label_obj.save(label_filepath_on_disk)

                new_file_instance = Image(
                    image_name=image_obj.filename,
                    image_path=file_relative_path,
                    label_path=label_relative_path,
                    label_status=label_status
                )
            else:
                new_file_instance = Image(
                    image_name=original_filename_secure,
                    image_path=file_relative_path,
                    label_status = 'unlabeled'
                )

            db.session.add(new_file_instance)
            db.session.commit()

            return {
                "id": new_file_instance.id,
                "image_name": new_file_instance.image_name,
                "image_path": new_file_instance.image_path,
                "label_path": new_file_instance.label_path if new_file_instance.has_label else None
            }
        except (ValueError, FileNotFoundError) as e:
            raise RuntimeError(f"Image path error: {str(e)}")
        except Exception as e:
            current_app.logger.error(f"Error saving Image {original_filename_secure}: {e}")
            raise RuntimeError(f"Failed to save or process Image: {str(e)}")

    def upload_files_batch(self, image_objs, label_dict, label_status, target_subdir=""):
        results = []
        errors = []

        base_upload_dir = get_safe_full_path(target_subdir)
        if not os.path.exists(base_upload_dir):
            os.makedirs(base_upload_dir, exist_ok=True)

        for img_obj in image_objs:
            try:
                if not allowed_file(img_obj.filename):
                    raise ValueError(f"Image type not allowed: {img_obj.filename}")
                label_key = os.path.splitext(img_obj.filename)[0]
                matched_label = label_dict.get(label_key)
                result = self.upload_file(img_obj, target_subdir, matched_label, label_status)
                results.append(result)
            except Exception as e:
                current_app.logger.error(f"Error uploading file {img_obj.filename}: {e}")
                errors.append({
                    'filename': img_obj.filename,
                    'error': str(e)
                })

        return results, errors

    def get_all_images(self, page=1, per_page=10, imagename_search=None):
        query = Image.query

        if imagename_search:
            query = query.filter(Image.image_name.ilike(f"%{imagename_search}%"))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        images_list = []
        for image_record in pagination.items:
            try:
                filepath_on_disk = get_safe_full_path(image_record.image_path)
                image_preview = convert_image_to_jpeg_base64(filepath_on_disk)
            except (ValueError, FileNotFoundError) as e:
                current_app.logger.error(f"Error getting Image path for {image_record.image_path}: {e}")
                raise RuntimeError(f"Failed to get image preview for {image_record.image_name}: {str(e)}")

            images_list.append({
                'id': image_record.id,
                'image_name': image_record.image_name,
                'image_path': image_record.image_path,
                'label_path': image_record.label_path if image_record.has_label else None,
                'upload_time': image_record.upload_time.isoformat(),

                'base64_jpeg': image_preview,
            })

        return {
            'images': images_list,
            'pagination': {
                'total': pagination.total,
                'pages': pagination.pages,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        }

    def get_image_details(self, image_id):
        image_record = self.get_image_by_id(image_id)
        if not image_record:
            return None

        try:
            filepath_on_disk = get_safe_full_path(image_record.image_path)
        except (ValueError, FileNotFoundError) as e:
            current_app.logger.error(f"Error getting Image path for {image_record.image_path}: {e}")
            raise RuntimeError(f"Failed to get image details for {image_record.image_name}: {str(e)}")

        details = {
            'id': image_record.id,
            'image_name': image_record.image_name,
            'image_path': image_record.image_path,
            'label_path': image_record.label_path if image_record.has_label else None,
            'upload_time': image_record.upload_time.isoformat(),
        }

        if image_record.has_label and image_record.label_path:
            filename = os.path.basename(image_record.label_path)
            details['label_url'] = url_for('file.get_label_file', filename=filename, _external=False)
        else:
            details['label_url'] = None

        try:
            details['base64_jpeg'] = convert_image_to_jpeg_base64(filepath_on_disk, size=None)
        except (FileNotFoundError, IOError, ValueError) as e:
            current_app.logger.error(f"Failed to encode image {image_record.image_name} to Base64: {e}")
            details['base64_jpeg'] = None
        except Exception as e:
            current_app.logger.error(
                f"An unexpected error occurred while encoding image {image_record.image_name} to Base64: {e}")
            details['base64_jpeg'] = None

        return details

    def copy_file(self, file_id, target_subdir):
        original_file = self.get_image_by_id(file_id)
        if not original_file:
            raise FileNotFoundError("Original Image not found in database.")

        original_filename_secure = secure_filename(original_file.image_name)
        dest_file_relative_path = os.path.normpath(os.path.join(target_subdir, original_filename_secure))

        src_filepath_on_disk = get_safe_full_path(original_file.image_path)
        dest_filepath_on_disk = get_safe_full_path(dest_file_relative_path)
        target_dir_on_disk = os.path.dirname(dest_filepath_on_disk)

        if not os.path.exists(src_filepath_on_disk):
            raise FileNotFoundError("Original Image not found on server disk.")
        if os.path.exists(dest_filepath_on_disk):
            raise FileExistsError("Target Image already exists in destination folder.")

        if not os.path.exists(target_dir_on_disk):
            os.makedirs(target_dir_on_disk, exist_ok=True)

        shutil.copy2(src_filepath_on_disk, dest_filepath_on_disk)
        if original_file.has_label:
            label_filename_secure = secure_filename(os.path.basename(original_file.label_path))
            dest_file_relative_path_label = os.path.normpath(os.path.join(target_subdir, label_filename_secure))
            src_label_filepath_on_disk = get_safe_full_path(original_file.label_path)
            shutil.copy2(src_label_filepath_on_disk, get_safe_full_path(dest_file_relative_path_label))
            new_db_file = Image(
                image_name=original_file.image_name,
                image_path=dest_file_relative_path,
                label_path=dest_file_relative_path_label
            )
        else:
            new_db_file = Image(image_name=original_file.image_name, image_path=dest_file_relative_path)

        db.session.add(new_db_file)
        db.session.commit()

        return {
            'original_id': original_file.id,
            'new_id': new_db_file.id,
            'new_filepath': new_db_file.image_path,
            'new_label_path': new_db_file.label_path if new_db_file.has_label else None
        }

    def move_file(self, file_id, target_subdir):
        original_file = self.get_image_by_id(file_id)
        if not original_file:
            raise FileNotFoundError("Original Image not found in database.")

        original_filename_secure = secure_filename(os.path.basename(original_file.image_name))
        dest_file_relative_path = os.path.normpath(os.path.join(target_subdir, original_filename_secure))

        src_filepath_on_disk = get_safe_full_path(original_file.image_path)
        dest_filepath_on_disk = get_safe_full_path(dest_file_relative_path)
        target_dir_on_disk = os.path.dirname(dest_filepath_on_disk)

        if not os.path.exists(src_filepath_on_disk):
            raise FileNotFoundError("Original Image not found on server disk.")
        if os.path.exists(dest_filepath_on_disk) and src_filepath_on_disk != dest_filepath_on_disk:
            raise FileExistsError("Target Image already exists in destination folder.")

        if not os.path.exists(target_dir_on_disk):
            os.makedirs(target_dir_on_disk, exist_ok=True)

        shutil.move(src_filepath_on_disk, dest_filepath_on_disk)
        if original_file.has_label:
            label_filename_secure = secure_filename(os.path.basename(original_file.label_path))
            dest_file_relative_path_label = os.path.normpath(os.path.join(target_subdir, label_filename_secure))
            src_label_filepath_on_disk = get_safe_full_path(original_file.label_path)
            shutil.move(src_label_filepath_on_disk, get_safe_full_path(dest_file_relative_path_label))
            original_file.label_path = dest_file_relative_path_label

        original_file.image_path = dest_file_relative_path
        db.session.commit()

        return {
            'file_id': original_file.id,
            'new_filepath': original_file.image_path,
            'new_label_path': original_file.label_path if original_file.has_label else None
        }

    def delete_file(self, file_id):
        file_to_delete = self.get_image_by_id(file_id)
        if not file_to_delete:
            raise FileNotFoundError("Image not found in database.")

        filepath_on_disk = get_safe_full_path(file_to_delete.image_path)

        if os.path.exists(filepath_on_disk):
            os.remove(filepath_on_disk)
            if file_to_delete.has_label:
                label_filepath_on_disk = get_safe_full_path(file_to_delete.label_path)
                os.remove(label_filepath_on_disk)
        else:
            current_app.logger.warning(f"Image {filepath_on_disk} not found on disk, but found in DB. Proceeding with DB removal.")

        try:
            dataset_ids_to_update = db.session.query(DatasetItem.dataset_id). \
                filter(DatasetItem.image_id == file_to_delete.id). \
                distinct(). \
                all()

            dataset_ids_to_update = [ds_id for (ds_id,) in dataset_ids_to_update]
            db.session.delete(file_to_delete)
            stmt = (
                update(Dataset)
                .where(Dataset.id.in_(dataset_ids_to_update))
                .values(image_count=Dataset.image_count - 1)
            )
            db.session.execute(stmt)
            db.session.commit()

            return {
                'id': file_id,
                'image_name': file_to_delete.image_name,
                'filepath': file_to_delete.image_path,
                'label_path': file_to_delete.label_path
            }

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred while deleting the image: {e}")
            raise RuntimeError("An unexpected error occurred while deleting the image.")


file_service = FileService()