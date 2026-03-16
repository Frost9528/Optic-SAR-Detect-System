<template>
  <div class="result-page">
    <!-- 顶部统计信息 -->
    <div class="result-header">
      <div>识别时间：{{ summary.costTime }}</div>
      <div>总目标数：{{ summary.totalTargets }}</div>
    </div>

    <div class="result-body">
      <!-- 左侧：图片选择列表 -->
      <div class="image-selector">
        <el-radio-group v-model="selectedIndex" size="small" class="image-radio-group">
          <el-radio-button class="el-radio-button__inner"
            v-for="(img, idx) in detectionResults"
            :key="idx"
            :label="idx"
          >
            {{ img.name }}
          </el-radio-button>
        </el-radio-group>
      </div>

      <!-- 右侧：检测结果展示 -->
      <div class="result-display">
        <ZoomImageViewer :src="selectedImage.preview" :boxes="selectedImage.detections" />

        <!-- 表格展示检测框信息 -->
        <div class="objectbox_title">
          <div>目标信息：</div>
        </div>
        <el-table
          :data="selectedImage.detections"
          border
          style="margin-top: 20px"
          v-if="selectedImage.detections.length"
        >
          <el-table-column prop="class" label="类别" width="150" />
          <el-table-column label="坐标">
            <template #default="{ row }">
              ({{ row.box[0] }}, {{ row.box[1] }}, {{ row.box[2] }}, {{ row.box[3] }})
            </template>
          </el-table-column>
          <el-table-column prop="confidence" label="置信度">
            <template #default="{ row }">
              {{ (row.confidence * 100).toFixed(2) }}%
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject, ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import ZoomImageViewer from '@/components/ZoomImageViewer.vue'

const setPageTitle = inject<(title: string) => void>('setPageTitle')
onMounted(() => {
  if (setPageTitle) {
    setPageTitle('目标检测 / 检测结果')  // 修改为当前页面标题
  }
})

const route = useRoute()
const taskId = route.params.taskId
const resultList = ref([])

interface Detection {
  class: string
  confidence: number
  box: [number, number, number, number]
}
interface DetectionResult {
  name: string
  preview: string
  detections: Detection[]
}

const detectionResults = ref<DetectionResult[]>([])
const selectedIndex = ref(0)
const duration = ref(1.86)

interface DetectedResultTable {
  index: number
  filename: string
  class: string
  x1: number
  y1: number
  x2: number
  y2: number
  confidence: number
}

const selectedImage = computed(() => detectionResults.value[selectedIndex.value] || {
  preview: '',
  detections: [],
})

const summary = ref({
  costTime: '0',
  totalTargets: computed(() =>
                detectionResults.value.reduce((sum, item) => sum + item.detections.length, 0)
                )
})

const getBoxStyle = (box) => {
  const [x1, y1, x2, y2] = box.box;
  return {
    position: 'absolute',
    border: '2px solid red',
    left: `${x1}px`,
    top: `${y1}px`,
    width: `${x2 - x1}px`,
    height: `${y2 - y1}px`,
    boxSizing: 'border-box',
    pointerEvents: 'none',
  };
};

onMounted(async () => {
  try {
    const response = await axios.get(`/api/detect/result/${taskId}`)
    if (response.data.code === 0) {
      resultList.value = response.data.data.results
    } else {
      ElMessage.error(response.data.message)
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('加载检测结果失败')
  }
})

// 模拟加载数据
onMounted(() => {
  detectionResults.value = [
    {
      name: 'image1.jpg',
      preview: '/demo/bus.jpg',
      detections: [
        { class: 'car', confidence: 0.92, box: [50, 60, 200, 150] },
        { class: 'person', confidence: 0.88, box: [220, 70, 300, 180] }
      ]
    },
    {
      name: 'image2.jpg',
      preview: '/demo/test.jpg',
      detections: [
        { class: 'plane', confidence: 0.95, box: [30, 40, 250, 180] }
      ]
    },
    {
      name: 'image3.jpg',
      preview: '/demo/zidane.jpg',
      detections: []
    }
  ]

  const result = JSON.parse(localStorage.getItem('detect_result') || '[]')
  const base64Prefix = "data:image/png;base64,"
  detectionResults.value = result.map((item: any) => ({
    name: item.name,
    preview: item.preview.startsWith(base64Prefix) ? item.preview : base64Prefix + item.preview,
    detections: item.detections.map((det: any) => ({
      class: det.class,
      confidence: det.confidence,
      box: det.box
    }))
  }))
})


</script>

<style scoped>
.result-page {
  padding: 2px;
  display: flex;
  flex-direction: column;
}

.result-header {
  display: flex;
  gap: 40px;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 12px;
  padding-left: 4px;
  margin-top: -4px; /* 靠上 */
}

.result-body {
  display: flex;
  gap: 10px;
  height: calc(100vh - 150px);
}

.image-selector {
  flex-shrink: 0;
  width: 150px;
  overflow-y: auto;
  border-right: 1px solid #ccc;
  padding-right: 12px;
  box-sizing: border-box;
}

.image-radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.el-radio-button__inner {
  width: 100%;
  justify-content: center;
  padding: 12px 16px;
  text-align: center;
  font-size: 14px;
  box-sizing: border-box;
}

.image-item {
  width: 100%;
  margin-bottom: 12px;
  padding: 6px;
  cursor: pointer;
  text-align: center;
  border: 2px solid transparent;
  border-radius: 4px;
}

.result-display {
  flex-grow: 1;
  padding-left: 8px;
  overflow: auto;
  flex-direction: column;
  box-sizing: border-box;
}

.image-container {
  position: relative;
  width: 75%;
  max-width: 1000px;
  border: 1px solid #ccc;
  overflow: hidden;
  object-fit: contain;
  background-color: #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

.detected-image {
  width: 100%;
  height: auto;
  display: block;
}
.objectbox_title{
  max-width: 1000px;
  padding: 12px 8px 4px 8px;
  font-weight: 600;
  font-size: 16px;
  color: #333;
  margin-top: 16px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}
.el-table {
  width: 100% !important;
  max-width: 1000px;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.bounding-box {
  position: absolute;
  border: 2px solid red;
  color: red;
  font-size: 12px;
  padding: 2px 4px;
  pointer-events: none;
}

.box-label {
  background: red;
  color: white;
  font-size: 12px;
  padding: 1px 4px;
  position: absolute;
  top: -1.5em;
  left: 0;
}
</style>
