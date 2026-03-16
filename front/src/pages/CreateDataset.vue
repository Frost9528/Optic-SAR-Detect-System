<template>
  <div class="create-dataset-page">
    <!--上半部分：图像选择和导入 -->
    <div class="section">
      <div class="section-header">
        <el-button
        @click="goBack"
        link
        class="back-button"
        style="font-size: 16px;"
        >
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="section-title">从图像库中选择图片</div>
      </div>

      <div style="margin-left: 12px; text-align: left;">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索图片名"
          size="default"
          clearable
          style="width: 360px;"
        />
      </div>
      <!-- 图片列表 -->
      <div class="image-selection-container">
        <div class="image-grid">
          <ImageCard
            v-for="img in filteredImages"
            :key="img.id"
            :image-id="img.id"
            :image-url="img.path"
            :image-name="img.name"
            :is-selected="selectedImageIds.includes(img.id)"
            :selectable="true"
            @select="toggleSelect(img.id)"
            @open="() => {}"
          />
        </div>
      </div>
    </div>
    <!-- 下半部分：数据集信息设置 -->
    <div class="info-section">
      <div class="info-row">
        <!-- 已添加图像 -->
        <div class="info-item">
          <span class="info-label">已添加图像：</span>
          <span>{{ selectedImages.length }} 张</span>
        </div>

        <!-- 数据集名称 -->
        <div class="info-item">
          <span class="info-label">数据集名称：</span>
          <el-input
            v-model="datasetName"
            placeholder="请输入数据集名称"
            style="width: 240px"
            size="default"
          />
        </div>

        <!-- 数据集类型 -->
        <div class="info-item">
          <span class="info-label">数据集类型：</span>
          <el-select
            v-model="datasetType"
            placeholder="选择类型"
            style="width: 160px"
            size="default"
          >
            <el-option label="光学" value="光学" />
            <el-option label="SAR" value="SAR" />
            <el-option label="混合" value="混合" />
          </el-select>
        </div>
      </div>

      <!-- 居中按钮 -->
      <div class="center-button-row">
        <el-button type="success" @click="createDataset">创建完成</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, inject, onMounted} from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import UploadDataset from "@/components/UploadDataset.vue";
import axios from "axios";
import ImageCard from "@/components/ImageCard.vue";

const allImages = ref([])

const setPageTitle = inject<(title: string) => void>('setPageTitle')
onMounted(() => {
  if (setPageTitle) {
    setPageTitle('新建数据集')  // 修改为当前页面标题
  }
  fetchImages()
})

const searchKeyword = ref('')
const datasetName = ref('')
const datasetType = ref('')
const selectedImageIds = ref([])
const pagination = ref({
  page: 1,
  per_page: 80,
  total: 0,
  pages: 1
})
const base64Prefix = "data:image/png;base64,"

const fetchImages = async () => {
  try {
    const response = await axios.get('/api/files', {
      params: {
        page: pagination.value.page,
        per_page: pagination.value.per_page,
        filename_search: searchKeyword.value
      }
    })
    allImages.value = response.data.data.images.map(image => ({
      id: image.id,
      name: image.image_name,
      path: image.base64_jpeg.startsWith(base64Prefix) ? image.base64_jpeg : base64Prefix + image.base64_jpeg,
      selected: false
    }))
    pagination.value = {
      ...pagination.value,
      ...response.data.data.pagination
    }
  } catch (error) {
    console.error('获取文件列表失败:', error)
  }
}

// 过滤搜索结果
const filteredImages = computed(() =>
  allImages.value.filter(img =>
    img.name.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
)
const toggleSelect = (id) => {
  const index = selectedImageIds.value.indexOf(id)
  if (index === -1) {
    selectedImageIds.value.push(id)
  } else {
    selectedImageIds.value.splice(index, 1)
  }
}
// 获取被选中的图片
const selectedImages = computed(() =>
  filteredImages.value.filter(img => selectedImageIds.value.includes(img.id))
)

// // 构建图像完整路径（如果放在 public 下）
// const getImageUrl = (path: string) => `/${path}`

// 模拟导入整个文件夹
const showUploadDataset = ref(false)
function importDataset() {
  showUploadDataset.value = true
}
function onUploaded() {
  showUploadDataset.value = false
  fetchDataset() // TODO: 导入数据集文件夹
  console.log('数据集上传成功，父组件收到 saved 事件')
}
// 创建数据集
const createDataset = async () => {
  if (!datasetName.value || !datasetType.value || selectedImages.value.length === 0) {
    ElMessage.warning('请填写完整信息并添加图像')
    return
  }
  try {
    await axios.post('/api/datasets', {
      name: datasetName.value,
      type: datasetType.value,
      image_ids: selectedImages.value.map(img => img.id) // 仅发送选中图像的 ID
    })
  } catch (error) {
    console.error('创建数据集失败:', error)
    ElMessage.error('创建数据集失败，请稍后重试')
    return
  }
  ElMessage.success(`成功创建数据集 "${datasetName.value}"（${selectedImages.value.length} 张图像）`)
  datasetName.value = ''
  datasetType.value = ''
  selectedImageIds.value = []
  allImages.value.forEach(img => img.selected = false)
  goBack()
}

const router = useRouter()
const hasUnsavedChanges = computed(() =>
  datasetName.value || datasetType.value || selectedImages.value.length > 0
)
const goBack = () => {
  router.back()
}
onBeforeRouteLeave((to, from, next) => {
  if (hasUnsavedChanges.value) {
    ElMessageBox.confirm(
      '尚未完成创建，是否放弃创建数据集？',
      '提醒',
      {
        confirmButtonText: '放弃',
        cancelButtonText: '继续编辑',
        type: 'warning',
      }
    )
      .then(() => {
        next()  // 继续跳转
      })
      .catch(() => {
        next(false)  // 阻止跳转
      })
  } else {
    next()
  }
})
</script>

<style scoped>
.create-dataset-page {
}
.section-header {
  display: flex;
  align-items: center;
  position: relative;
  gap: 50px;
  margin-bottom: 8px;
}
.section-title {
  font-size: 16px;
  font-weight: bold;
}

.image-selection-container {
  height: 60vh; /* 占页面的大部分高度 */
  overflow-y: auto;
  padding-right: 24px;
  margin-bottom: 8px;
  margin-top: 8px;
}
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  padding-top: 10px;
}

.preview-col {
  margin-bottom: 8px;
}

.info-section {
  border-top: 1px solid #ddd;
  padding-left: 32px;
  padding-top: 16px;
}
.info-row {
  display: flex;
  align-items: center;
  gap: 64px; /* 每个信息块之间的间距 */
  margin-bottom: 16px;
}
.info-label {
  font-weight: 500;
}
.center-button-row {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>