<template>
  <div class="detect-page-container">
    <div class="upload-area">
      <div v-if="detectionResults.length > 0" class="image-result-wrapper">
        <div class="image-result-grid">
          <div
              v-for="(result, index) in detectionResults"
              :key="index"
              class="image-result-item"
              @mouseenter="hoverIndex = index"
              @mouseleave="hoverIndex = -1"
          >
            <el-image :src="result.preview" fit="contain" class="full-image" />
            <div class="result-info">
              <p>文件名: {{ result.name }}</p>
              <p>检测状态:
                <el-tag :type="result.status === 'success' ? 'success' : 'warning'">
                    {{ result.status === 'success' ? '成功' : '待处理' }}
                </el-tag>
              </p>
              <p v-if="result.detections && result.detections.length > 0">
                检测到物体: {{ result.detections.length }} 个
              </p>
              <p v-else>检测到物体: 无</p>
            </div>
            <div class="action-mask" v-show="hoverIndex === index">
              <el-icon :size="48" color="#fff" @click.stop="onViewLargeImage(result.preview)"><ZoomIn /></el-icon>
              <el-icon :size="48" color="#fff" @click.stop="onRemoveResult(index)"><Delete /></el-icon>
            </div>
          </div>
        </div>
      </div>

      <div class="upload-box">
        <p style="font-weight: bold">上传图像文件：</p>
        <el-upload
            drag
            :auto-upload="false"
            :on-change="onImageUpload"
            :show-file-list="false"
            multiple
            accept="image/*"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">拖拽或点击上传图像文件</div>
          <div class="el-upload__tip">支持JPG、PNG等常见图像格式</div>
        </el-upload>
      </div>
    </div>


    <div class="result-display-area">
      <p>检测结果：</p>
      <div v-if="detectionResults.length > 0">
        <el-table :data="processedResults" border>
          <el-table-column prop="index" label="序号" width="60" align="center" />
          <el-table-column prop="filename" label="文件名" width="240" />
          <el-table-column prop="class" label="类别" width="160" />
          <el-table-column prop="point" label="坐标" >
            <template #default="{row}">
              ({{ row.x1 }}, {{ row.y1 }}, {{ row.x2 }}, {{ row.y2 }})
            </template>
          </el-table-column>
          <el-table-column prop="confidence" label="置信度" width="120">
            <template #default="{row}">
              {{ (row.confidence * 100).toFixed(2) }}%
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else class="no-results-placeholder">
        <el-empty description="暂无检测结果" />
      </div>
    </div>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleSubmit">提交检测</el-button>
    </template>
    <el-image-viewer
        v-if="showImageViewer"
        :url-list="imageViewerSrcList"
        :initial-index="imageViewerInitialIndex"
        @close="showImageViewer = false"
    />
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import {inject, onMounted, ref} from "vue";
import { ElDialog, ElButton, ElImage, ElUpload, ElMessage, ElMessageBox, ElLoading, ElTag, ElEmpty } from "element-plus";
import { UploadFilled, Delete } from '@element-plus/icons-vue';

const setPageTitle = inject<(title: string) => void>('setPageTitle')
onMounted(() => {
  if (setPageTitle) {
    setPageTitle('目标检测')  // 修改为当前页面标题
  }
})

const dialogVisible = ref(false);
const hoverIndex = ref(-1);

interface Detection{
  class: string;
  confidence: number;
  box: [number, number, number, number];
}
interface DetectionResult {
  file: File;
  preview: string;
  name: string;
  status?: 'success' | 'warning';
  detections: Detection[];
}

interface DetectedResultTable {
  index: number;
  filename: string;
  class: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  confidence: number;
}

const detectionResults = ref<DetectionResult[]>([]);
const processedResults = ref<DetectedResultTable[]>([]);
const showImageViewer = ref(false);
const imageViewerSrcList = ref<string[]>([]);
const imageViewerInitialIndex = ref(0);
const onViewLargeImage = (src: string) => {
  imageViewerSrcList.value = [src];
  imageViewerInitialIndex.value = 0;
  showImageViewer.value = true;
};

const onImageUpload = async (file: any) => {
  try {
    const formData = new FormData()
    formData.append('file', file.raw)

    const res = await axios.post('/api/upload/preview', formData)
    for (const item of res.data.data) {
      if (!item.preview) {
        ElMessage.error(`文件 ${file.name} 预览链接获取失败`)
        return
      }
      const base64Prefix = "data:image/jpeg;base64,"
      const raw = item.preview.startsWith(base64Prefix)? item.preview : base64Prefix + item.preview
      detectionResults.value.push({
        file: file.raw,
        preview: raw,
        name: file.raw.name,
        status: 'warning',
        detections: [],
      })
    }
  } catch (error) {
    ElMessage.error(`文件 ${file.name} 获取预览失败`)
  }
}

const onRemoveResult = (index: number) => {
  detectionResults.value.splice(index, 1);
};

const handleCancel = () => {
  if (detectionResults.value.length === 0) {
    dialogVisible.value = false;
    return;
  }

  ElMessageBox.confirm('确定要取消上传吗？所有未提交的内容将会丢失。', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    dialogVisible.value = false;
    detectionResults.value = [];
    ElMessage.info('已取消操作');
  }).catch(() => {
    ElMessage.info('操作已取消');
  });
};

const handleSubmit = async () => {
  if (detectionResults.value.length === 0) {
    ElMessage.warning('请至少上传一张图片进行检测');
    return;
  }

  processedResults.value = [];

  const loading = ElLoading.service({
    lock: true,
    text: '正在提交检测结果...',
    spinner: 'el-icon-loading',
    background: 'rgba(0, 0, 0, 0.7)'
  });
  const formData = new FormData();
  detectionResults.value.forEach(img => {
    formData.append(`image`, img.file);
  });

  try {
    await axios.post('/api/detect', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }).then(response => {
      if (response.data.code === 1) {
        ElMessage.error('检测结果提交失败，请稍后重试');
        return;
      }
      detectionResults.value.forEach((result, index) => {
        result.detections = response.data.data.detections[index] || [];
        result.preview = response.data.data.rendered_images[index] || result.preview;
        const base64Prefix = "data:image/jpeg;base64,"
        result.preview = result.preview.startsWith(base64Prefix) ? result.preview : base64Prefix + result.preview;
        result.status = 'success';

        // 更新 processedResults
        result.detections.forEach(det => {
          processedResults.value.push({
            index: processedResults.value.length + 1,
            filename: result.name,
            class: det.class,
            x1: det.box[0],
            y1: det.box[1],
            x2: det.box[2],
            y2: det.box[3],
            confidence: det.confidence,
          });
        });
      });
    });

    ElMessage.success('检测结果提交成功');
  } catch (error) {
    console.error('提交失败:', error);
    ElMessage.error('检测结果提交失败，请稍后重试');
  } finally {
    loading.close();
  }
};


</script>

<style scoped>
.app-container {
  padding: 20px;
}

:deep(.el-upload-dragger) {
  width: 200px !important;
  height: 180px !important;
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.upload-area {
  border: 1px dashed var(--el-border-color);
  padding: 16px;
  border-radius: 8px;
  background-color: var(--el-fill-color-light);
  min-height: 150px;
  margin-bottom: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.image-result-wrapper {
  width: 100%;
  margin-bottom: 20px;
}
.image-result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}
.image-result-item {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.full-image {
  width: 100%;
  height: 220px;
  object-fit: contain;
  border-bottom: 1px solid var(--el-border-color);
}
.action-mask {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  opacity: 0;
  transition: opacity 0.2s;
  cursor: pointer;
}
.image-result-item:hover .action-mask {
  opacity: 1;
}

.result-display-area {
  border: 1px dashed var(--el-border-color);
  padding: 16px;
  border-radius: 8px;
  background-color: var(--el-fill-color-light);
  min-height: 300px;
  margin-top: 20px;
}
.result-display-area p {
  margin-bottom: 15px;
  font-weight: bold;
}

.result-info {
  padding: 10px;
  width: 100%;
  box-sizing: border-box;
  text-align: left;
}
.result-info p {
  margin: 5px 0;
  font-weight: normal;
  font-size: 0.9em;
}

.no-results-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}
</style>