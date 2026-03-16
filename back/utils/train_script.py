import argparse
import json
import os
import sys
import pandas as pd
from ultralytics import YOLO


def get_metrics(model):
    metrics = {}

    results_csv = os.path.join(model.trainer.save_dir, 'results.csv')
    metrics_df = pd.read_csv(results_csv)
    metrics_df['F1'] = 2 * (metrics_df['metrics/precision(B)'] * metrics_df['metrics/recall(B)']) / \
                       (metrics_df['metrics/precision(B)'] + metrics_df['metrics/recall(B)'] + 1e-16)
    metrics['training_acc'] = metrics_df['metrics/precision(B)'].tolist()
    metrics['training_F1'] = metrics_df['F1'].tolist()

    val_results = model.val()
    metrics['final_precision'] = val_results.box.mp
    metrics['final_recall'] = val_results.box.mr
    metrics['final_mAP50'] = val_results.box.map50  # 替代AUC
    metrics['final_false_rate'] = 1 - val_results.box.mp
    metrics['final_F1'] = 2 * (val_results.box.mp * val_results.box.mr) / \
                        (val_results.box.mp + val_results.box.mr + 1e-16)
    metrics['training_time'] = metrics_df['time'].tolist()

    class_names = val_results.names
    num_classes = val_results.box.nc
    nt_per_class = val_results.nt_per_class  # 每个类别的真实样本数 (TP + FN)
    matrix = val_results.confusion_matrix.matrix
    class_metrics = []
    for i in range(num_classes):
        class_name = class_names.get(i, f"Class_{i}")
        TP = matrix[i, i].item()
        # FN: 真实类别 i 被漏检的数量 (矩阵的最后一列，对应真实类别 i 的行)
        FN = matrix[i, num_classes].item()
        # FP: 被错误预测为类别 i 的数量 (矩阵的最后一行，对应预测类别 i 的列)
        FP = matrix[num_classes, i].item()
        # 准确率 (Precision): TP / (TP + FP)
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
        # 识别率 (Recall): TP / (TP + FN)
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
        # 虚警率: FP / (TP + FP)
        false_rate = FP / (TP + FP) if (TP + FP) > 0 else 0.0
        # TP + FP = 0 (没有对该类别的任何预测)，虚警率和精确率都为0。
        # TP + FN = 0 (该类别没有真实样本)，召回率为0。

        metrics_entry = {
            "class_name": class_name,
            "sample_count": nt_per_class[i].item(),
            "precision": precision,
            "recall": recall,
            "false_rate": false_rate
        }
        class_metrics.append(metrics_entry)

    metrics['class_metrics'] = class_metrics

    return metrics


def train_model(task_name, model_path, data_config_path, epochs, batch_size, lr, conf_thres,  output_result_path):
    try:
        os.environ['OMP_NUM_THREADS'] = '1'
        os.environ['MKL_NUM_THREADS'] = '1'
        os.environ['NUMEXPR_NUM_THREADS'] = '1'
        os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

        model = YOLO(model_path, task='train')
        print(f"Subprocess for task {task_name}: Starting training with epochs={epochs}...")
        sys.stdout.flush()

        model.train(
            data=data_config_path,
            epochs=epochs,
            batch=batch_size,
            lr0=lr,
            conf=conf_thres,
            name=task_name,
            device='cuda'
        )
        performance_metrics = get_metrics(model)
        output_path = model.trainer.save_dir
        model_size = os.path.getsize(os.path.join(output_path, 'weights', 'best.pt')) / (1024 * 1024)

        print(f"Training task completed successfully. Status updated to COMPLETED.")

        final_output = {
            "task_name": task_name,
            "performance_metrics": performance_metrics,
            "output_path": str(output_path),
            "model_size": model_size,
            "training_params": {
                "epochs": epochs,
                "batch_size": batch_size,
                "learning_rate": lr,
                "confidence_threshold": conf_thres
            }
        }

        with open(output_result_path, 'w') as f:
            json.dump(final_output, f)

        print(f"Training subprocess: Training finished. Results saved to {output_result_path}")
        sys.stdout.flush()

    except Exception as e:
        error_output = {
            'status': 'FAILED',
            'task_name': task_name,
            'error_message': f"Training subprocess failed: {str(e)}",
            'traceback': str(e.__traceback__)
        }
        with open(output_result_path, 'w') as f:
            print(error_output)
            json.dump(error_output, f)
        print(f"Training subprocess: Failed: {e}", file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run YOLOv8 training in a subprocess.')
    parser.add_argument('--task_name', type=str, required=True, help='Name of the training task.')
    parser.add_argument('--model_path', type=str, required=True,
                        help='Path to YOLO model (e.g., yolov8n.pt or best.pt)')
    parser.add_argument('--data_config_path', type=str, required=True, help='Path to data.yaml configuration file.')
    parser.add_argument('--epochs', type=int, default=10, help='Number of training epochs.')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size for training.')
    parser.add_argument('--learning_rate', type=float, default=0.001, help='Learning rate for training.')
    parser.add_argument('--confidence_threshold', type=float, default=0.25, help='Confidence threshold for predictions.')
    parser.add_argument('--output_result_path', type=str, required=True, help='Path to save the final JSON result.')

    args = parser.parse_args()

    train_model(
        task_name=args.task_name,
        model_path=args.model_path,
        data_config_path=args.data_config_path,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.learning_rate,
        conf_thres=args.confidence_threshold,
        output_result_path=args.output_result_path
    )