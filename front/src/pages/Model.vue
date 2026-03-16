<template>
  <div class="model-manage-page">
    <!-- 左侧模型列表栏 -->
    <div class="model-sidebar">
      <div class="sidebar-title">模型列表</div>
      <el-input
        v-model="searchText"
        placeholder="搜索模型名称"
        size="default"
        clearable
        class="search-input"
      />
      <el-scrollbar class="model-list-scroll">
        <div class="model-card-list">
          <div
            v-for="model in filteredModels"
            :key="model.id"
            class="model-card"
            :class="{ selected: model.id === selectedModelId }"
            @click="selectModel(model.id)"
          >
            <div class="model-name">{{ model.name }}</div>
            <div class="model-time">{{ model.createdAt }}</div>
          </div>
        </div>
      </el-scrollbar>
    </div>
    <!-- 右侧模型详情展示 -->
    <div class="main-content" v-if="selectedModel">
      <div class="model-details-area">
        <div class="details-top">
          <!-- 左侧指标 -->
          <div class="left-summary">
            <div class="metrics-list">
              <div class="metric-row">
                <span class="metric-label">模型名称：</span>
                <span class="metric-value">{{ selectedModel.name }}</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">平均 mAP：</span>
                <span class="metric-value">{{ (selectedModel.map * 100).toFixed(1) }}%</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">准确率：</span>
                <span class="metric-value">{{ (selectedModel.accuracy * 100).toFixed(1) }}%</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">召回率：</span>
                <span class="metric-value">{{ (selectedModel.recall * 100).toFixed(1) }}%</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">虚警率：</span>
                <span class="metric-value">{{ (selectedModel.falsePositiveRate * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
          <!-- 右侧曲线图 -->
          <div class="right-chart">
            <img :src="selectedModel.curveImage" class="chart-image" alt="训练曲线图" />
          </div>
        </div>

        <!-- 下方类别指标表 -->
        <div class="details-bottom">
          <div class="section-title">各目标类指标</div>
          <el-table :data="selectedModel.classMetrics" border style="width: 100%">
            <el-table-column prop="className" label="目标类别" width="150" />
            <el-table-column prop="count" label="数量" width="150" />
            <el-table-column prop="accuracy" label="准确率" width="200">
              <template #default="{ row }">{{ (row.accuracy * 100).toFixed(1) }}%</template>
            </el-table-column>
            <el-table-column prop="falsePositiveRate" label="虚警率" >
              <template #default="{ row }">{{ (row.falsePositiveRate * 100).toFixed(1) }}%</template>
            </el-table-column>
          </el-table>
          <!-- 操作按钮 -->
          <div class="action-buttons">
            <el-button type="danger" @click="deleteModel">删除模型和记录</el-button>
          </div>
        </div>
      </div>

      <div class="side-panel">
        <!-- 模型信息 -->
        <div class="info-block">
          <div class="info-title">模型信息</div>
          <div class="information-list">
            <div class="metric-row">
              <span class="metric-label">模型类型：</span>
              <span class="metric-value">{{ selectedModel.type }}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">模型大小：</span>
              <span class="metric-value">{{ selectedModel.size.toFixed(2) }} MB</span>
            </div>
          </div>
        </div>

        <!-- 数据集信息 -->
        <div class="info-block">
          <div class="info-title">数据集信息</div>
          <div class="information-list">
            <div class="metric-row">
              <span class="metric-label">数据集：</span>
              <span class="metric-value">{{ selectedModel.dataset }}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">图像数：</span>
              <span class="metric-value">{{ selectedModel.datacount }}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">模型大小：</span>
              <span class="metric-value">{{ selectedModel.size.toFixed(2) }} MB</span>
            </div>
          </div>
        </div>

        <!-- 训练参数 -->
        <div class="info-block">
          <div class="info-title">训练参数</div>
          <div class="information-list">
            <div class="metric-row">
              <span class="metric-label">轮数：</span>
              <span class="metric-value">{{ selectedModel.epoch }}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">学习率：</span>
              <span class="metric-value">{{ selectedModel.lr }}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">批次大小：</span>
              <span class="metric-value">{{ selectedModel.bachsize }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 未选择模型提示 -->
    <div v-else class="empty-placeholder">
        <el-empty description="请选择一个模型查看详情" />
      </div>
  </div>
</template>


<script lang="ts" setup>
import {ref, computed, watch, onMounted, inject} from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from "axios";

const setPageTitle = inject<(title: string) => void>('setPageTitle')
onMounted(() => {
  if (setPageTitle) {
    setPageTitle('数据集管理')  // 修改为当前页面标题
  }
  fetchModels()
})

const searchText = ref('')
const selectedModelId = ref<number | null>(null)

const modelList = ref([])

const fetchModels = async () => {
  try {
    const response = await axios.get('/api/training/tasks')
    modelList.value = response.data.data.tasks.map(task => ({
      id: task.id,
      name: task.task_name,
      model_id: task.model_id,
      dataset_id: task.dataset_id,
      createdAt: task.create_time,
      accuracy: task.performance_metrics.final_precision,
      recall: task.performance_metrics.final_recall,
      map: task.performance_metrics.final_mAP50,
      falsePositiveRate: task.performance_metrics.final_false_rate,
      curveImage: '/demo/PR_curve1.png', // TODO: 替换为实际曲线图
      classMetrics: task.performance_metrics.class_metrics.map(class_metrics => ({
        className: class_metrics.class_name,
        count: class_metrics.sample_count,
        accuracy: class_metrics.precision,
        falsePositiveRate: class_metrics.false_rate
      })),
      epoch: task.training_params.epochs,
      lr: task.training_params.learning_rate,
      bachsize: task.training_params.batch_size,
      size: task.model_size,
    }))
  } catch (error) {
    console.error('获取模型列表失败:', error)
    ElMessage.error('获取模型列表失败，请稍后重试')
  }
}
const filteredModels = computed(() =>
  modelList.value.filter(model =>
    model.name.toLowerCase().includes(searchText.value.toLowerCase())
  )
)
const selectModel = (id: number) => {
  selectedModelId.value = id
}
const selectedModel = computed(() =>
  modelList.value.find(m => m.id === selectedModelId.value) || null
)
watch(selectedModel, async (newModel) => {
  if (!newModel) {
    return
  }

  if (!newModel.dataset || !newModel.datacount) {
    try {
      const dataset_response = await axios.get(`/api/datasets/${newModel.dataset_id}`)
      newModel.dataset = dataset_response.data.data.name
      newModel.datacount = dataset_response.data.data.image_count
    } catch (error) {
      console.error(`获取模型 ${newModel.name} 的数据集图像数失败:`, error)
      ElMessage.error(`获取模型 ${newModel.name} 的数据集图像数失败。`)
    }
  }
  if (!newModel.type) {
    try {
      const model_response = await axios.get(`/api/models/${newModel.model_id}`)
      newModel.type = model_response.data.data.model_type
    } catch (error) {
      console.error(`获取模型 ${newModel.name} 的类型失败:`, error)
      ElMessage.error(`获取模型 ${newModel.name} 的类型失败。`)
    }
  }
}, { immediate: true })
const downloadModel = () => {
  if (!selectedModel.value) return
  ElMessage.success(`下载模型：${selectedModel.value.name}`)
}

const deleteModel = () => {
  if (!selectedModel.value) return
  ElMessageBox.confirm(`确定删除模型 ${selectedModel.value.name}？`, '确认删除', {
    type: 'warning'
  }).then(() => {
    try {
      axios.delete(`/api/training/tasks/${selectedModelId.value}`)
    } catch (error) {
      console.error('删除模型失败:', error)
      ElMessage.error('删除模型失败，请稍后重试')
      return
    }
    modelList.value = modelList.value.filter(m => m.id !== selectedModelId.value)
    selectedModelId.value = null
    ElMessage.success('模型已删除')
  })
}

</script>

<style scoped>
.model-manage-page {
  display: flex;
  height: 100%;
}

.model-sidebar {
  width: 280px;
  padding: 8px;
  border-right: 1px solid #ddd;
  background: #f9f9f9;
}

.sidebar-title {
  font-weight: bold;
  margin-bottom: 8px;
}

.search-input {
  width: 100%;
  margin-bottom: 12px;
  padding-right: 16px;
}

.model-list-scroll {
  max-height: calc(100vh - 200px);
  padding-right: 16px;
}
.model-card-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  overflow-y: auto;
  max-height: 100%;
}

.model-card {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 12px;
  background-color: white;
  cursor: pointer;
  transition: border 0.3s, background-color 0.3s;
}

.model-card:hover {
  background-color: #f3f4f6;
  border-color: #409eff;
}

.model-card.selected {
  border-color: #409eff;
  background-color: #e6f7ff;
}

.model-name {
  font-weight: 600;
  margin-bottom: 4px;
  font-size: 15px;
}

.model-time {
  font-size: 12px;
  color: #666;
}
.main-content{
  display: flex;
  width: 100%;
  gap: 8px;
  box-sizing: border-box;
}
.model-details-area {
  width: 75%;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.details-top {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.left-summary {
  width: 50%;
  padding-right: 24px;
  background: white;
}

.metrics-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-left: 24px;
}
.information-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.metric-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
}

.metric-label {
  font-weight: 450;
  width: 100px;
  text-align: left;
}

.metric-value {
  flex: 1;
  text-align: left;
}

.right-chart {
  width: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.chart-image {
  max-width: 100%;
  max-height: 300px;
  border: 1px solid #ccc;
}

.details-bottom {
  margin-top: 24px;
}

.section-title {
  font-weight: bold;
  margin-bottom: 8px;
  text-align: left;
}
.side-panel {

  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  border: 1px solid #ddd;
  background: white;
}

.info-block {
  padding: 24px;
  border-bottom: 1px solid #ddd;
}

.info-title {
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 8px;
}
.action-buttons {
  margin-top: 16px;
  display: flex;
  gap: 16px;
}

</style>