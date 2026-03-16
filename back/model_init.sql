USE sar;

INSERT INTO models (name, model_path, model_type, targets, accuracy, false_rate, create_time) VALUES
('yolov8n', 'models/yolov8n.pt', '光学图像', '车辆、舰船、飞机', 0.923, 0.031, NOW());
INSERT INTO models (name, model_path, model_type, targets, accuracy, false_rate, create_time) VALUES
('3RS', 'models/3RS.pt', '光学图像', '车辆、舰船', 0.91, 0.035, NOW());
INSERT INTO models (name, model_path, model_type, targets, accuracy, false_rate, create_time) VALUES
('SAR', 'models/SAR.pt', 'SAR图像', '舰船、小艇', 0.897, 0.048, NOW());
