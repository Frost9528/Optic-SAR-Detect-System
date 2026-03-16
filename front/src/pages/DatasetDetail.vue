<template>
  <div class="dataset-detail">
    <!-- 顶部信息 -->
    <div class="top-info">
      <el-button
      @click="goBack"
      link
      class="back-button"
      >
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <div class="section-title">数据集详情：</div>
    </div>
    <div v-if="dataset">
      <!-- 基本信息卡片 -->
      <div class="section">
        <el-table :data="[dataset]" border style="width: 1120px">
          <el-table-column prop="name" label="数据集名称" width="320"/>
          <el-table-column prop="type" label="类型" width="250" />
          <el-table-column prop="size" label="大小" width="250">
          <template #default="{ row }">{{ row.size }} 张</template>
          </el-table-column>
          <el-table-column prop="createdAt" label="创建时间" width="300"/>
        </el-table>
      </div>

      <!-- 示例图像 -->
      <div class="section">
        <div class="section-title">图像预览</div>
        <div class="image-grid">
          <ImageCard
            v-for="(img, index) in dataset.images"
            :key="index"
            :image-id="img.id"
            :image-url="img.image_preview"
            :image-name="img.name"
            :is-selected="false"
            :selectable="false"
            @open="() => goToDetail(img)"
          />
          <ImageDetailDialog
            :visible="showDetail"
            :detail="image_detail"
            @close="showDetail = false"
          />
        </div>
      </div>
    </div>
    <div v-else>
      <el-empty description="未找到该数据集" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from "axios";
import {ElMessage} from "element-plus";
import ImageCard from "@/components/ImageCard.vue";
import ImageDetailDialog from "@/components/ImageDetailDialog.vue";

// 模拟数据加载
const route = useRoute()
const router = useRouter()
const dataset = ref(null)
const base64Prefix = "data:image/png;base64,"
const image_detail = ref()
const showDetail = ref(false)

onMounted(() => {
  const id = route.params.id
  fetchDatasetDetail(id)
})
const fetchDatasetDetail = async (id) => {
  try {
    const response = await axios.get(`/api/datasets/${id}/images`)
    dataset.value = {
      id: response.data.data.dataset_id,
      name: response.data.data.dataset_name,
      type: response.data.data.dataset_type,
      size: response.data.data.dataset_image_count,
      createdAt: response.data.data.dataset_create_time,
      images: response.data.data.items.map(item => ({
        id: item.image_id,
        name: item.image_name,
        image_preview: item.image_preview.startsWith(base64Prefix) ? item.image_preview : base64Prefix + item.image_preview
      })),
    }
  } catch (error) {
    console.error('获取数据集详情失败:', error)
    dataset.value = null
  }
}
const goBack = () => {
  router.back()
}
async function goToDetail(image) {
  try {
    const response = await axios.get('/api/files/' + image.id)

    image_detail.value = {
      id: image.id,
      filename: image.filename,
      image_path: response.data.data.image_path,
      label_path: response.data.data.label_path,
      upload_time: response.data.data.upload_time,
      url: response.data.data.base64_jpeg.startsWith(base64Prefix) ? response.data.data.base64_jpeg : base64Prefix + response.data.data.base64_jpeg
    }
    // TODO 显示详情页
    showDetail.value = true
  } catch (error) {
      console.error('获取图像详情失败:', error)
      ElMessage.error('获取图像详情失败')
  }
}

</script>

<style scoped>
.dataset-detail {
}
.top-info {
  display: flex;
  align-items: center;
  justify-content: center; /* 居中标题 */
  position: relative;
  gap: 20px;
}
.back-button {
  position: absolute;
  left: 0;
  font-size: 16px;
  display: flex;
}
.section {
  margin-top: 24px;
  padding-left: 20px;
  padding-right: 20px;
}
.section-title {
  font-size: 16px;
  font-weight: bold;
}
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.preview-row {
  margin-top: 10px;
}
.preview-col {
  display: flex;
  justify-content: center;
}
</style>