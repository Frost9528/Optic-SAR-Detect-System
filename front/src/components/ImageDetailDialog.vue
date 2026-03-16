<template>
  <el-dialog
    :model-value="visible"
    width="800px"
    title="图像详情"
    @close="closeDialog"
  >
    <!-- 上半部分：图像展示 -->
    <div class="image-section">
      <div class="canvas-wrapper">
        <canvas ref="canvas" />
      </div>
    </div>

    <!-- 下半部分：标签列表 -->
    <div class="label-section">
      <div class="toolbar" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <div class="section-title">目标标签</div>

        <div>
          <el-button
            v-if="detail.labels?.length"
            @click="toggleBoxes"
            type="primary"
          >
            {{ showBoxes ? '隐藏标签框' : '显示标签框' }}
          </el-button>
          <el-button
            v-else
            disabled
            type="info"
          >
            无标签
          </el-button>
        </div>
      </div>

      <!-- 表格，仅在有标签时显示 -->
      <el-table
        v-if="detail.labels?.length"
        class="label-table"
        :data="detail.labels"
        style="width: 100%"
      >
        <el-table-column prop="class" label="类别" width="120" />
        <el-table-column
          prop="bbox"
          label="边界框"
          :formatter="formatBBox"
        />
      </el-table>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import axios from 'axios'

const props = defineProps({
  visible: Boolean,
  detail: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close'])

const showBoxes = ref(true)
const canvas = ref(null)
const img = new Image()

// 关闭弹窗
function closeDialog() {
  emit('close')
}

// 格式化 bbox
const formatBBox = (row, column, cellValue, index) => {
  if (!Array.isArray(cellValue) || cellValue.length !== 4) return ''
  const [x, y, w, h] = cellValue
  return `[ ${x}, ${y}, ${w}, ${h} ]`
}

// 切换目标框显示
function toggleBoxes() {
  showBoxes.value = !showBoxes.value
  drawImage()
}

// 绘制图像 + 可选目标框
function drawImage() {
  const ctx = canvas.value.getContext('2d')
  canvas.value.width = img.width
  canvas.value.height = img.height
  ctx.clearRect(0, 0, img.width, img.height)
  ctx.drawImage(img, 0, 0)

  if (showBoxes.value && props.detail.labels) {
    ctx.lineWidth = 2
    ctx.strokeStyle = 'rgb(199,78,78)'
    ctx.font = '20px sans-serif'
    ctx.fillStyle = 'rgb(197,77,77)'
    for (const label of props.detail.labels) {
      const [x, y, w, h] = label.bbox
      ctx.strokeRect(x, y, w, h)
      ctx.fillText(label.class, x+5, y-5)
    }
  }
}

function parseYoloLabel(text, imgWidth, imgHeight) {
  const lines = text.trim().split('\n')
  const labels = []

  for (const line of lines) {
    if (!line) continue
    const [clsId, x, y, w, h] = line.trim().split(/\s+/).map(Number)
    if ([clsId, x, y, w, h].some(val => isNaN(val))) continue

    const bbox = [
      (x - w / 2) * imgWidth,
      (y - h / 2) * imgHeight,
      w * imgWidth,
      h * imgHeight
    ]
    labels.push({
      class: `class_${clsId}`,
      bbox: bbox.map(n => Math.round(n))
    })
  }
  return labels
}

// 监听 detail 内容或 visible 状态变化
watch(() => props.detail, async () => {
  if (!props.detail?.url) return

  img.src = props.detail.url
  img.onload = async () => {
    const imgW = img.width
    const imgH = img.height
    console.log('图像尺寸', imgW, imgH)
    // 自动加载 label_path 标签
    if ((!props.detail.labels || props.detail.labels.length === 0) && props.detail.label_url) {
      try {
        const res = await axios.get('/api/'+ props.detail.label_url)
        props.detail.labels = parseYoloLabel(res.data, imgW, imgH)
      } catch (err) {
        console.warn('标签加载失败', err)
        props.detail.labels = []
      }
    }
    nextTick(() => drawImage())
  }

})

watch(() => props.visible, (v) => {
  if (v && props.detail?.url) {
    img.src = props.detail.url
  }
})
</script>

<style scoped>
.image-section {
  margin-bottom: 8px;
}
.toolbar {
  margin-bottom: 8px;
}
.section-title {
  font-weight: bold;
  font-size: 16px;
}
.canvas-wrapper {
  border: 1px solid #ddd;
  max-width: 100%;
  overflow: auto;
}
canvas {
  display: block;
  max-width: 100%;
}
.label-table {
  max-height: 300px;
  overflow-y: auto;
}
</style>
