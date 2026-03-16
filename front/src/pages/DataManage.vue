<template>
  <div class="image-manage-page">
    <!-- 顶部功能区域 -->
    <div class="top-bar-container">
      <div class="left-section">
        <!-- 筛选框示例 -->
        <el-select v-model="filterValue" placeholder="选择影像类型" size="default">
          <el-option label="全部" value="all"></el-option>
          <el-option label="光学" value="optical"></el-option>
          <el-option label="SAR" value="sar"></el-option>
        </el-select>
      </div>
      <div class="center-section">
        <el-input
          v-model="searchText"
          placeholder="输入文件名筛选"
          class="filter-input"
          clearable
        />
      </div>
      <div class="right-section">
        <el-button type="primary" @click="toggleMultiSelect">
          {{ multiSelect ? '取消多选' : '多选' }}
        </el-button>
        <el-button
          v-if="multiSelect"
          type="danger"
          :disabled="selectedIds.length === 0"
          @click="deleteSelected"
        >
          删除选中图像
        </el-button>

        <el-button v-else type="primary" @click="importData" >
          导入数据
        </el-button>
        <UploadImage v-model="showUploadModal" @saved="onUploaded" @close="showUploadModal = false"/>
      </div>
    </div>
    <!-- 图像列表 -->
    <div class="func-container image-grid-container">
      <div class="image-grid">
        <ImageCard
          v-for="(img, index) in filteredImages"
          :key="index"
          :image-id="img.id"
          :image-url="img.url"
          :image-name="img.name"
          :is-selected="selectedIds.includes(img.id)"
          :selectable="multiSelect"
          @select="toggleSelect(img.id)"
          @open="() => goToDetail(img)"
        />
      </div>
      <ImageDetailDialog
        :visible="showDetail"
        :detail="image_detail"
        @close="showDetail = false"
      />
    </div>
  </div>
</template>


<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { inject, onMounted } from 'vue'
import axios from 'axios'
import UploadImage from '@/components/UploadImage.vue'
import ImageCard from "@/components/ImageCard.vue";
import ImageDetailDialog from "@/components/ImageDetailDialog.vue";

const setPageTitle = inject<(title: string) => void>('setPageTitle')
onMounted(() => {
  if (setPageTitle) {
    setPageTitle('数据管理')  // 修改为当前页面标题
  }
  fetchImages()
})
const pagination = ref({
  page: 1,
  per_page: 80,
  total: 0,
  pages: 1
})
const searchText = ref('')
const images = ref([])
const base64Prefix = "data:image/png;base64,"
const image_detail = ref()
const multiSelect = ref(false)
const selectedIds = ref([])
const showDetail = ref(false)

const fetchImages = async () => {
  try {
    const response = await axios.get('/api/files', {
      params: {
        page: pagination.value.page,
        per_page: pagination.value.per_page,
        filename_search: searchText.value
      }
    })
    images.value = response.data.data.images.map(image => ({
      id: image.id,
      name: image.image_name,
      url: image.base64_jpeg.startsWith(base64Prefix) ? image.base64_jpeg : base64Prefix + image.base64_jpeg
    }))
    pagination.value = {
      ...pagination.value,
      ...response.data.data.pagination
    }
  } catch (error) {
    console.error('获取文件列表失败:', error)
  }
}

const filteredImages = computed(() =>
  images.value.filter(img =>
    img.name.toLowerCase().includes(searchText.value.toLowerCase())
  )
)
const showUploadModal = ref(false)
function importData() {
  showUploadModal.value = true
}
function onUploaded() {
  showUploadModal.value = false
  fetchImages()
  console.log('图片上传成功，父组件收到 saved 事件')
}

function toggleSelect(id) {
  const index = selectedIds.value.indexOf(id)
  if (index > -1) {
    selectedIds.value.splice(index, 1)
  } else {
    selectedIds.value.push(id)
  }
}
function toggleMultiSelect() {
  multiSelect.value = !multiSelect.value
  if (!multiSelect.value) {
    selectedIds.value = []  // 取消多选时清除选中
  }
}
async function goToDetail(image) {
  showDetail.value = true
  image_detail.value = {
    ...image,
    labels: null,
    imageLoaded: false,
  }
  try {
    const response = await axios.get('/api/files/' + image.id)

    image_detail.value = {
      id: image.id,
      filename: image.filename,
      image_path: response.data.data.image_path,
      label_path: response.data.data.label_path,
      upload_time: response.data.data.upload_time,
      url: response.data.data.base64_jpeg.startsWith(base64Prefix) ? response.data.data.base64_jpeg : base64Prefix + response.data.data.base64_jpeg,
      label_url: response.data.data.label_url
    }

  } catch (error) {
      console.error('获取图像详情失败:', error)
      ElMessage.error('获取图像详情失败')
  }
}

async function deleteImage(id) {
  try {
    await ElMessageBox.confirm(
      '确定要删除这张图像吗？',
      '提示',
      { type: 'warning' }
    )
    const response = await axios.delete(`/api/files/${id}`)
    images.value = images.value.filter(img => img.id !== id)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败: ' + (error.response?.data?.message || error.message))
    }
  }
}

async function deleteSelected() {
  if (selectedIds.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 张图像吗？`,
      '提示',
      { type: 'warning' }
    )

    // 假设后端提供 POST /api/files/delete 接口，接收 JSON body
    const response = await axios.post('/api/files/delete', {
      ids: selectedIds.value
    })

    // 本地移除图像
    images.value = images.value.filter(img => !selectedIds.value.includes(img.id))
    selectedIds.value = []
    multiSelect.value = !multiSelect.value

    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('删除失败: ' + (error.response?.data?.message || error.message))
    }
  }
}
</script>


<style scoped>
.top-bar-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 16px;
  padding: 0 20px;
}
.left-section {
  width: 150px;
  display: flex;
  align-items: center;
}
.right-section {
  display: flex;
  width: 200px;
  margin-right: 16px;
}

.center-section {
  flex-grow: 1;

}
.filter-input {
  width: 500px;
}

.image-grid-container {
  margin-top: 12px;
}
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  padding: 12px 0;
}

.actions {
  display: flex;
  justify-content: space-between;
}
</style>