<template>
  <div class="image-detail-page">
    <!-- 上半部分：图像展示区 -->
    <div class="image-preview">
      <div class="toolbar">
        <el-button @click="toggleBoxes">
          {{ showBoxes ? '隐藏标签框' : '显示标签框' }}
        </el-button>
      </div>
      <div class="image-container">
        <canvas ref="canvas" />
      </div>
    </div>

    <!-- 下半部分：标签列表 -->
    <div class="label-list">
      <h3>标签列表</h3>
      <el-table :data="labels" style="width: 100%">
        <el-table-column prop="class" label="类别" width="120" />
        <el-table-column prop="bbox" label="边界框 [x, y, w, h]" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'

const route = useRoute()
const imageId = route.params.id

const image = ref(null)       // 图像对象
const labels = ref([])        // 标签数组：{ class, bbox: [x, y, w, h] }
const showBoxes = ref(false)  // 是否显示目标框
const canvas = ref(null)      // canvas 引用

// 获取图像数据（base64）和标签
const fetchImageDetail = async () => {
  const response = await axios.get(`/api/image/${imageId}`)
  const data = response.data
  image.value = new Image()
  image.value.src = data.image_base64.startsWith('data:')
    ? data.image_base64
    : 'data:image/jpeg;base64,' + data.image_base64
  labels.value = data.labels || []
}

// 在 canvas 上绘制图像和（可选）框
const drawImage = () => {
  const ctx = canvas.value.getContext('2d')
  const img = image.value

  img.onload = () => {
    canvas.value.width = img.width
    canvas.value.height = img.height
    ctx.clearRect(0, 0, img.width, img.height)
    ctx.drawImage(img, 0, 0)

    if (showBoxes.value) {
      ctx.lineWidth = 2
      ctx.strokeStyle = '#409EFF'
      ctx.font = '14px sans-serif'
      ctx.fillStyle = '#409EFF'

      for (const item of labels.value) {
        const [x, y, w, h] = item.bbox
        ctx.strokeRect(x, y, w, h)
        ctx.fillText(item.class, x + 4, y + 16)
      }
    }
  }

  // 如果图片已加载，立即绘制（用于切换目标框状态）
  if (img.complete) img.onload()
}

// 切换目标框显示状态
const toggleBoxes = () => {
  showBoxes.value = !showBoxes.value
  drawImage()
}

// 初始化
onMounted(async () => {
  await fetchImageDetail()
  drawImage()
})

// 每当 showBoxes 切换时重绘
watch(showBoxes, () => {
  drawImage()
})
</script>

<style scoped>
.image-detail-page {
  padding: 20px;
}
.image-preview {
  margin-bottom: 24px;
}
.toolbar {
  margin-bottom: 8px;
}
.image-container {
  border: 1px solid #eee;
  display: inline-block;
  max-width: 100%;
  overflow: auto;
}
canvas {
  display: block;
  max-width: 100%;
}
.label-list {
  margin-top: 16px;
}
</style>