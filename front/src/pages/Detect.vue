<template>
  <div class="detect-page-container">
    <!-- 上半部分：图像导入 -->
    <div class="upload-box">
      <p class="section-title">选择识别图片：</p>
      <el-upload class="custom-upload-area"
        drag
        :auto-upload="false"
        :on-change="onImageUpload"
        :show-file-list="false"
        multiple
        accept="image/*"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">拖拽或点击上传图像文件</div>
        <div class="el-upload__text">支持 JPG、PNG 等图像格式</div>
      </el-upload>
    </div>

    <!-- 图像预览 -->
    <div v-if="imageList.length > 0" class="image-preview-grid">
      <div
        v-for="(img, index) in imageList"
        :key="index"
        class="image-card"
        @mouseenter="hoverIndex = index"
        @mouseleave="hoverIndex = -1"
      >
        <el-image :src="img.preview" fit="cover" class="preview-image" />
        <div class="image-footer">
          <span>{{ img.name }}</span>
          <el-icon v-if="hoverIndex === index" @click.stop="removeImage(index)" style="cursor: pointer">
            <Delete />
          </el-icon>
        </div>
      </div>
    </div>

    <!-- 下半部分：模型选择 + 参数区域 + 按钮 -->
    <div class="model-settings-section">
      <div class="section-title">模型选择与参数设置：</div>
      <div class="model-param-container">
        <!-- 左侧：模型选择 + 模型信息 -->
        <div class="model-selector">
          <el-select v-model="selectedModel" placeholder="选择模型" style="width: 100%;">
            <el-option
              v-for="item in modelInfo"
              :key="item.id"
              :label="item.name"
              :value="item.id">
            </el-option>
          </el-select>

          <div class="model-info-card" v-if="selectedModel">
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">适用图像类型：</span>
                <span class="info-value">{{ modelInfo[selectedModel].model_type }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">检测目标：</span>
                <span class="info-value">{{ modelInfo[selectedModel].targets }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">准确率：</span>
                <span class="info-value">{{ modelInfo[selectedModel].accuracy }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">虚警率：</span>
                <span class="info-value">{{ modelInfo[selectedModel].false_rate }}</span>
              </div>
            </div>
          </div>
        </div>
        <!-- 右侧：参数设置 -->
        <div class="param-settings">
          <div class="param-item">
            <span class="param-label">图像增强</span>
            <el-switch v-model="enableEnhancement" />
          </div>
          <div class="param-item">
            <span class="param-label">图像去噪</span>
            <el-switch v-model="enableDenoise" />
          </div>
        </div>
      </div>
    </div>
    <!-- 检测按钮 -->
    <div class="start-detect-btn">
        <el-button type="primary" @click="startDetection">开始检测</el-button>
    </div>
  </div>
</template>


<script lang="ts" setup>
import {computed, inject, onMounted, ref} from 'vue'
import { UploadFilled, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useRouter } from 'vue-router'

const imageList = ref<any[]>([])
const hoverIndex = ref(-1)
const selectedModel = ref('')

const setPageTitle = inject<(title: string) => void>('setPageTitle')
onMounted(() => {
  if (setPageTitle) {
    setPageTitle('目标识别')  // 修改为当前页面标题
    fetchModelInfo()
  }
})

function onImageUpload(fileObj) {
  const file = fileObj.raw
  const reader = new FileReader()
  reader.onload = () => {
    imageList.value.push({
      file: file,
      name: file.name,
      preview: reader.result
    })
  }
  reader.readAsDataURL(file)
}

function removeImage(index: number) {
  imageList.value.splice(index, 1)
}

const enableEnhancement = ref(false)
const enableDenoise = ref(false)

const modelInfo = ref([])
const fetchModelInfo = async () => {
  try {
    const response = await axios.get('/api/models')
    if (response.data.code === 0) {
      modelInfo.value = response.data.data.reduce((acc, model) => {
        acc[model.id] = model
        return acc
      }, {})
    } else {
      ElMessage.error(response.data.message || '获取模型信息失败')
    }
  } catch (err) {
    console.error('获取模型信息出错:', err)
    ElMessage.error('调用模型信息接口失败')
  }
}

const router = useRouter()
const startDetection = async () =>  {
  if (!selectedModel.value) {
    ElMessage.warning('请选择模型版本')
    return
  }
  if (imageList.value.length === 0) {
    ElMessage.warning('请上传图像')
    return
  }
  try {
    ElMessage.info('检测中，请稍候...')

    const formData = new FormData()
    imageList.value.forEach((file) => {
      formData.append('image', file.file)  // 假设 imageList 是上传图片列表
    })
    formData.append('model_id', selectedModel.value)
    formData.append('enhance', enableEnhancement.value? '1' : '0')
    formData.append('denoise', enableDenoise.value? '1' : '0')

    const response = await axios.post('/api/detect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    if (response.data.code !== 0) {
      ElMessage.error(response.data.message || '检测失败')
      return
    }
    // 只在成功时运行
    ElMessage.success('检测完成，正在跳转结果页面...')
    const taskId = response.data.data.task_id
    router.push(`/detect/result/${taskId}`)
    //localStorage.setItem('detect_result', JSON.stringify(response.data.data))
    // router.push('/detect/result')
  } catch (err) {
    console.error('检测出错:', err)
    ElMessage.error('调用检测接口失败')
  }
}
</script>


<style scoped>
.detect-page-container {
  background-color: #f9fafb;
}

.section-title {
  font-weight: bold;
  margin-bottom: 5px;
  text-align: left;
}

.upload-box {
  margin-bottom: 12px;
  min-height: 120px;
}
.custom-upload-area :deep(.el-upload-dragger) {
  height: 100px !important;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
:deep(.el-upload-dragger .el-icon--upload) {
  font-size: 36px;
  margin-bottom: 4px;
}
:deep(.el-upload-dragger .el-upload__text) {
  font-size: 12px;
  line-height: 1.5;
  text-align: center;
}

.image-preview-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.image-card {
  width: 150px;
  border: 1px solid #ddd;
  border-radius: 6px;
  overflow: hidden;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.preview-image {
  width: 100%;
  height: 100px;
  object-fit: cover;
}

.image-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 8px;
  font-size: 12px;
}

.model-settings-section {
  margin-top: 16px;
}

.model-param-container {
  display: flex;
  justify-content: space-between;
  gap: 32px;
  margin-top: 16px;
}

.model-selector, .param-settings {
  flex: 1;
  background-color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  box-sizing: border-box;
}

.model-info-card {
  margin-top: 16px;
  padding: 16px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  background-color: #f9fafb;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr; /* 两列 */
  row-gap: 12px;
  column-gap: 24px;
}

.info-item {
  display: flex;
  align-items: center;
}

.info-label {
  font-weight: 600;
  color: #333;
  margin-right: 4px;
  white-space: nowrap;
}

.info-value {
  color: #606266;
}

.param-settings {
  margin-left: 8px;
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.param-item {
  display: flex;
  align-items: center;
}

.param-label {
  width: 100px;
  font-weight: 500;
  color: #333;
  margin-right: 8px;
  text-align: left;
}

.start-detect-btn {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}
</style>