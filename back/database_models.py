from extensions import db
from sqlalchemy import Enum as SqlEnum
from datetime import datetime
import json
import enum

class LabelStatusEnum(enum.Enum):
    UNLABELED = 'unlabeled'
    USER_UPLOADED = 'uploaded'
    AUTO_GENERATED = 'detected'
    HUMAN_VERIFIED = 'verified'
    IMAGE_LEVEL = 'image_level_tagged'

class Image(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(512), unique=True, nullable=False)
    label_path = db.Column(db.String(512), nullable=True)
    upload_time = db.Column(db.DateTime, default=datetime.now)

    label_status = db.Column(SqlEnum(LabelStatusEnum, values_callable=lambda x: [e.value for e in x]),
        default=LabelStatusEnum.UNLABELED.value, nullable=False)
    dataset_items = db.relationship('DatasetItem', back_populates='image', lazy=True, cascade='all, delete-orphan')
    def __repr__(self):
        return f"<Image {self.image_name}>"

    @property
    def has_label(self):
        return self.label_path is not None


class DetectionTask(db.Model):
    __tablename__ = 'detection_tasks'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(32), default='pending')  # pending, completed, failed

    model_id = db.Column(db.Integer, nullable=True)

    # 结果路径或统计结果（可选）
    result_dir = db.Column(db.String(512), nullable=True)
    total_images = db.Column(db.Integer, default=0)

    records = db.relationship('DetectionRecord', backref='task', lazy=True)


class DetectionRecord(db.Model):
    __tablename__ = 'detection_records'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('detection_tasks.id'), nullable=False)

    image_name = db.Column(db.String(256), nullable=False)
    image_path = db.Column(db.String(512), nullable=False)
    result_path = db.Column(db.String(512))
    detected_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(64), default='undetected') # undetected, detected,


class Dataset(db.Model):
    __tablename__ = 'datasets'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    type = db.Column(db.String(255), nullable=False)
    image_count = db.Column(db.Integer, default=0, nullable=False)
    dataset_path = db.Column(db.String(512), unique=True, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    last_modified_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 与 DatasetItem 一对多关系
    dataset_items = db.relationship('DatasetItem', back_populates='dataset', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Dataset {self.name}>'


class DatasetItem(db.Model):
    __tablename__ = 'dataset_items'
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)

    # 复合唯一约束，确保同一个图片不会被重复添加到同一个数据集中
    __table_args__ = (db.UniqueConstraint('dataset_id', 'image_id', name='_dataset_image_uc'),)

    # 与 Dataset 多对一关系
    dataset = db.relationship('Dataset', back_populates='dataset_items')
    # 与 Image 多对一关系
    image = db.relationship('Image', back_populates='dataset_items')

    def __repr__(self):
        return f'<DatasetItem Dataset ID: {self.dataset_id}, Image ID: {self.image_id}, Include Label: {self.include_label}>'


class Model(db.Model):
    __tablename__ = 'models'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    model_path = db.Column(db.String(512), unique=True, nullable=False)
    model_type = db.Column(db.String(255), nullable=False)
    targets = db.Column(db.String(255), nullable=False)
    accuracy = db.Column(db.Float, nullable=True)
    false_rate = db.Column(db.Float, nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<Model {self.name}>"


class TrainingRecord(db.Model):
    __tablename__ = 'training_records'

    id = db.Column(db.Integer, primary_key=True)

    task_name = db.Column(db.String(255), nullable=False, unique=True)
    model_id = db.Column(db.Integer, db.ForeignKey('models.id'), nullable=False)
    model = db.relationship('Model', backref='training_records', lazy=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False)
    dataset = db.relationship('Dataset', backref='training_records', lazy=True)

    training_params = db.Column(db.Text, nullable=True,
                                comment="JSON格式的训练参数，如 {'lr': 0.001, 'epochs': 100, 'batch_size': 32}")

    performance_metrics = db.Column(db.Text, nullable=True,
                                    comment="JSON格式的性能指标，如 {'val_loss': 0.05, 'mAP': 0.85, 'precision': 0.9}")

    output_path = db.Column(db.String(512), nullable=True,
                            comment="训练输出文件（模型、日志等）的存储路径")
    model_size = db.Column(db.Float, nullable=True,
                            comment="训练后模型的大小，单位为MB")

    create_time = db.Column(db.DateTime, default=datetime.now, nullable=False)
    def __repr__(self):
        return f"<TrainingRecord {self.job_name} ({self.status})>"

    def set_training_params(self, params: dict):
        self.training_params = json.dumps(params)

    def get_training_params(self) -> dict:
        return json.loads(self.training_params) if self.training_params else {}

    def set_performance_metrics(self, metrics: dict):
        self.performance_metrics = json.dumps(metrics)

    def get_performance_metrics(self) -> dict:
        return json.loads(self.performance_metrics) if self.performance_metrics else {}