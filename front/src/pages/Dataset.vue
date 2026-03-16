<template>
  <div class="dataset-page">
     <!-- 顶部标题和按钮栏 -->
    <div class="dataset-header">
      <div class="header-left">
        <span class="dataset-title">数据集列表</span>
        <el-input v-model="searchText" placeholder="输入数据集名称" clearable style="width: 300px;" />
      </div>
      <el-button type="primary" @click="createNewDataset" class="header-right">新建数据集</el-button>
    </div>

    <!-- 数据集表格 -->
      <el-table
          :data="filteredDatasets"
          border style="width: 100%"
          height="700"
      >
        <el-table-column prop="name" label="数据集名称" width="320" fixed/>
        <el-table-column prop="type" label="类型" width="250" />
        <el-table-column prop="size" label="大小" width="250">
          <template #default="{ row }">{{ row.size }} 张</template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="300"/>
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetails(row)">查看</el-button>
            <el-button size="small" type="danger" @click="deleteDataset(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    <!-- 数据集详细信息展示 -->
    <div v-if="selectedDataset" class="dataset-detail">
      <div class="section-title">数据集详情 - {{ selectedDataset.name }}</div>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="数据集名称">{{ selectedDataset.name }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ selectedDataset.type }}</el-descriptions-item>
        <el-descriptions-item label="图像数量">{{ selectedDataset.size }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ selectedDataset.createdAt }}</el-descriptions-item>
      </el-descriptions>

      <div class="section-title" style="margin-top: 24px;">类别分布</div>
      <el-table :data="selectedDataset.classes" border style="width: 60%">
        <el-table-column prop="className" label="类别名称" />
        <el-table-column prop="count" label="数量" />
      </el-table>

      <div class="section-title" style="margin-top: 24px;">样例图像</div>
      <div class="image-preview-box">
        <el-image
          v-for="(img, idx) in selectedDataset.samples"
          :key="idx"
          :src="img"
          class="sample-image"
          fit="cover"
        />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import {computed, inject, onMounted, ref} from 'vue'
import {ElMessage, ElMessageBox} from "element-plus";
import {useRouter} from "vue-router";
import axios from "axios";

const setPageTitle = inject<(title: string) => void>('setPageTitle')
onMounted(() => {
  if (setPageTitle) {
    setPageTitle('数据集管理')  // 修改为当前页面标题
  }
  fetchDatasets()
})

const searchText = ref('')
const router = useRouter()
const datasets = ref([])
const pagination = ref({
  page: 1,
  per_page: 80,
  total: 0,
  pages: 1
})

const selectedDataset = ref(null)

const filteredDatasets = computed(() =>
  datasets.value.filter(d =>
    d.name.toLowerCase().includes(searchText.value.toLowerCase())
  )
)
const fetchDatasets = async () => {
  try {
    const response = await axios.get('/api/datasets', {
      params: {
        page: pagination.value.page,
        per_page: pagination.value.per_page,
        dataset_name_search: searchText.value
      }
    })
    datasets.value = response.data.data.datasets.map(dataset => ({
      id: dataset.id,
      name: dataset.name,
      type: dataset.type,
      size: dataset.image_count,
      createdAt: dataset.create_time,
    }))
    pagination.value = {
      ...pagination.value,
      ...response.data.data.pagination
    }
  } catch (error) {
    console.error('获取数据集列表失败:', error)
  }
}

const createNewDataset = () => {
  router.push('/models/datasets/createdataset')  // 跳转到新建数据集页面
}

const viewDetails = (dataset) => {
  router.push(`/models/datasets/${dataset.id}`)
}

const deleteDataset = (dataset) => {
  ElMessageBox.confirm(`确定删除数据集 ${dataset.name}？`, '确认删除', {
    type: 'warning'
  }).then(() => {
    try {
      axios.delete(`/api/datasets/${dataset.id}`)
    } catch (error) {
      console.error('删除数据集失败:', error)
      ElMessage.error('删除数据集失败，请稍后重试')
      return
    }
    datasets.value = datasets.value.filter(d => d.name !== dataset.name) // 直接根据名称删除
    if (selectedDataset.value?.name === dataset.name) {
      selectedDataset.value = null
    }
    ElMessage.success('数据集已删除')
  })
}

</script>

<style scoped>
.dataset-page {
  padding-left: 16px;
  padding-right: 16px;
}
.dataset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 24px;
}

.header-left {
  display: flex;
  gap: 20px;
}

.dataset-title {
  font-size: 18px;
  font-weight: bold;
}

.header-right {
  margin-left: auto;
}
.section-title {
  font-weight: bold;
  font-size: 16px;
  margin-bottom: 8px;
  text-align: left;
}

.dataset-list{

}
.dataset-detail {
  margin-top: 32px;
}

.image-preview-box {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.sample-image {
  width: 150px;
  height: 120px;
  object-fit: cover;
  border: 1px solid #ddd;
}
</style>
