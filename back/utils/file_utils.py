import os
from flask import current_app


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def get_safe_full_path(relative_path, is_dir=False):
    base_upload_folder = os.path.abspath(current_app.config['CURRENT_FOLDER'])
    normalized_path = os.path.normpath(relative_path)

    if normalized_path.startswith('/') or normalized_path.startswith('\\'):
        normalized_path = normalized_path.lstrip('/\\')

    full_path = os.path.join(base_upload_folder, normalized_path)
    full_path = os.path.abspath(full_path)

    if not full_path.startswith(base_upload_folder):
        current_app.logger.error(f"Attempted path traversal detected: {relative_path} resulted in {full_path}")
        raise ValueError("Invalid target path specified: Cannot access outside upload folder.")

    if is_dir:
        if not os.path.isdir(full_path):
            raise FileNotFoundError(f"Target directory does not exist: {full_path}")

    return full_path



