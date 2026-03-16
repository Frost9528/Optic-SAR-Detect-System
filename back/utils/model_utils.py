from typing import Union
from database_models import Model
from flask import current_app
from collections import OrderedDict
from utils.detect_utils import YOLODetector


class ModelManager:
    # LRU (Least Recently Used) 缓存策略
    # 限制同时加载到内存中的模型数量
    def __init__(self, max_cached_models: int = 1):
        # 使用 OrderedDict 实现 LRU 缓存
        # 键是模型ID，值是 YOLODetector 实例
        self.MAX_CACHED_MODELS = max_cached_models
        self._model_cache = OrderedDict()

    def get_model_by_id(self, model_id: int):
        model = Model.query.get(model_id)
        if not model:
            raise FileNotFoundError(f"Model with ID {model_id} not found in database.")
        return model

    def get_model_by_name(self, model_name: str):
        model = Model.query.filter_by(name=model_name).first()
        if not model:
            raise FileNotFoundError(f"Model with name '{model_name}' not found in database.")
        return model

    def get_detector(self, model_identifier: Union[int, str] = None) -> YOLODetector:
        if model_identifier is None:
            default_model = Model.query.first()
            if default_model:
                model_identifier = default_model.id
            else:
                raise ValueError("No model identifier provided and no default base model found.")

        model_id = None
        model_path = None

        if isinstance(model_identifier, int):
            model_id = model_identifier
            if model_id in self._model_cache:
                # 将最近使用的模型移到 OrderedDict 的末尾 (LRU 策略)
                self._model_cache.move_to_end(model_id)
                current_app.logger.info(f"Returning cached detector for Model ID: {model_id}")
                return self._model_cache[model_id]

            model_path = self.get_model_by_id(model_id).model_path

        elif isinstance(model_identifier, str):
            # 如果传入的是模型名称，先查询 ID
            model_obj = self.get_model_by_name(model_identifier)
            if not model_obj:
                raise FileNotFoundError(f"Model with name '{model_identifier}' not found in database.")

            model_id = model_obj.id
            if model_id in self._model_cache:
                self._model_cache.move_to_end(model_id)
                current_app.logger.info(
                    f"Returning cached detector for Model Name: {model_identifier} (ID: {model_id})")
                return self._model_cache[model_id]

            model_path = model_obj.model_path

        if not model_path:
            raise ValueError(f"Could not resolve model path for identifier: {model_identifier}")

        # 如果缓存已满，移除最久未使用的模型
        if len(self._model_cache) >= self.MAX_CACHED_MODELS:
            lru_model_id, lru_detector = self._model_cache.popitem(last=False) # last=False 移除第一个（最久未使用）
            current_app.logger.info(f"Cache full, unloading LRU model ID: {lru_model_id}")

        current_app.logger.info(f"Loading new detector for Model ID: {model_id} (Path: {model_path})")
        new_detector = YOLODetector(model_path=model_path, device='cuda')
        self._model_cache[model_id] = new_detector
        return new_detector

    def preload_model(self):
        first_model = Model.query.first()
        if first_model:
            self.get_detector(first_model.id)
            current_app.logger.info(f"Preloaded model ID: {first_model.id} (Name: {first_model.name})")
        else:
            current_app.logger.warning("No models found in the database to preload.")