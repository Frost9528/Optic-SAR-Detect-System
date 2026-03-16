<template>
  <div class="detection-page-wrapper">
    <div class="breadcrumbs">
      首页 / 图像管理
    </div>

    <div class="alert-success">
      <span class="alert-text">模型刷新已完成</span>
      <span class="alert-close-btn">
        <i class="fas fa-times"></i>
      </span>
    </div>

    <div class="detection-controls">
      <div class="control-group">
        <span class="control-label">当前模型版本:</span>
        <el-select v-model="currentModelVersion" placeholder="选择版本" class="control-select">
          <el-option label="yolov5-7.0" value="yolov5-7.0"></el-option>
          <el-option label="yolov5-6.0" value="yolov5-6.0"></el-option>
        </el-select>
      </div>

      <div class="control-group">
        <span class="control-label">选择其他模型:</span>
        <el-select v-model="selectedOtherModel" placeholder="选择模型" class="control-select">
          <el-option label="yolov5-7.0 (COCO_yolo)" value="yolov5-7.0-coco"></el-option>
          <el-option label="yolov5-6.0 (VOC)" value="yolov5-6.0-voc"></el-option>
        </el-select>
      </div>

      <el-button type="success" class="switch-model-btn">切换模型</el-button>
    </div>

    <div class="upload-area">
      <i class="fas fa-cloud-upload-alt upload-icon"></i>
      <p class="upload-text">将需要检测的图片拖放此处或点击上传</p>
      <input type="file" multiple class="file-input" />
    </div>

    <div class="func-container">
      <UploadImage />
    </div>
    <div class="func-container">
      <Detect />
    </div>

    <div class="detection-results-grid">
      <div class="image-placeholder-box">
        <span class="placeholder-text">原始图片</span>
      </div>

      <div class="image-placeholder-box relative-box">
        <span class="placeholder-text">检测结果图片</span>
        <div class="bounding-box red-box" style="left: 60%; top: 20%; width: 30%; height: 50%;">
          <span class="box-label red-label">person 0.83</span>
        </div>
        <div class="bounding-box red-box" style="left: 10%; top: 40%; width: 40%; height: 50%;">
          <span class="box-label red-label">person 0.90</span>
        </div>
        <div class="bounding-box green-box" style="left: 45%; top: 60%; width: 15%; height: 20%;">
          <span class="box-label green-label">tie 0.42</span>
        </div>
      </div>

      <div class="detection-table-container">
        <h3 class="list-title">检测结果</h3>
        <el-table :data="detectionData" style="width: 100%" border>
          <el-table-column prop="category" label="检测类别"></el-table-column>
          <el-table-column prop="confidence" label="置信度"></el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, inject } from 'vue';
import Detect from "@/pages/Detect.vue";
import UploadImage from "@/components/UploadImage.vue";

const currentModelVersion = ref('yolov5-7.0');
const selectedOtherModel = ref('yolov5-7.0-coco');

const detectionData = ref([
  { category: 'person', confidence: '0.9' },
  { category: 'person', confidence: '0.83' },
  { category: 'tie', confidence: '0.42' },
]);

const setPageTitle = inject< (title: string) => void >('setPageTitle');
onMounted(() => {
  if (setPageTitle) {
    setPageTitle('图像管理');
  }
});

</script>

<style scoped>
.detection-page-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  padding-bottom: 20px;
  box-sizing: border-box;
  min-height: 0;
}

.breadcrumbs {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 16px;
}

.alert-success {
  background-color: #d1fae5;
  border: 1px solid #34d399;
  color: #065f46;
  padding: 12px 16px;
  border-radius: 8px;
  position: relative;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.alert-text {
  display: block;
}

.alert-close-btn {
  cursor: pointer;
  font-size: 1.2em;
  color: #10b981;
  padding: 0 10px;
}

.detection-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-label {
  color: #374151;
}

.control-select {
  min-width: 180px;
}

.func-container {
  margin-bottom: 24px;
  background-color: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 32px;
  text-align: center;
  background-color: white;
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  min-height: 150px;
  box-sizing: border-box;
  flex-shrink: 0;
}

.upload-icon {
  color: #9ca3af;
  font-size: 60px;
  margin-bottom: 16px;
}

.upload-text {
  color: #4b5563;
  margin: 0;
}

.file-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.list-title {
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}


.detection-results-grid {
  flex-grow: 1;
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
  min-height: 0;
}

@media (min-width: 768px) {
  .detection-results-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.image-placeholder-box {
  background-color: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  box-sizing: border-box;
}

.placeholder-text {
  color: #a0a0a0;
  font-style: italic;
}

.relative-box {
  position: relative;
}

.bounding-box {
  position: absolute;
  border-width: 2px;
  border-style: solid;
  box-sizing: border-box;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 0.8em;
}

.red-box {
  border-color: #ef4444;
}

.green-box {
  border-color: #22c55e;
}

.box-label {
  position: absolute;
  top: -20px;
  left: 0;
  padding: 2px 4px;
  color: white;
  white-space: nowrap;
  font-size: 0.75rem;
}

.red-label {
  background-color: #ef4444;
}

.green-label {
  background-color: #22c55e;
}

.detection-table-container {
  background-color: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  grid-column: span 1;
  box-sizing: border-box;
}

@media (min-width: 768px) {
  .detection-table-container {
    grid-column: span 2;
  }
}
</style>
<style>
.el-dialog {
  width: 80% !important;

  /* 完全居中
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  margin: 0 !important;
  */
}
</style>