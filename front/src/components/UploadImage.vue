<template>
  <div class="app-container">

    <el-dialog
        v-model="dialogVisible"
        title="上传图像与标签" width="70%"
        :before-close="handleCancel">

    <div class="upload-area">
      <div v-if="imageList.length>0" class="image-preview-wrapper">
        <div class="image-grid">
          <div
            v-for="(img, index) in imageList"
            :key="index"
            class="image-item"
            @mouseenter="hoverIndex = index"
            @mouseleave="hoverIndex = -1"
          >
            <el-image :src="img.preview" fit="fill" class="full-image" />
          <div
            class="delete-mask"
            v-show="hoverIndex === index"
            @click.stop="onImageRemove(index)"
          >
            <el-icon :size="24" color="#fff"><Delete /></el-icon>
          </div>
          </div>
        </div>
      </div>

      <div class="upload-box">
        <p>上传图像：</p>
        <el-upload
          drag
          :auto-upload="false"
          :on-change="onImageUpload"
          :show-file-list="false"
          multiple
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">拖拽或点击上传图像文件</div>
        </el-upload>
      </div>
    </div>

    <div class="upload-area">
      <div v-if="labelFileList.length>0" class="label-preview-wrapper">
        <el-table :data="labelFileList" border style="width: 100%">
          <el-table-column prop="name" label="标签文件名"/>
          <el-table-column label="匹配状态" width="300" >
            <template #default="{ row }">
              <el-tag :type="getMatchStatus(row).type">
                {{ getMatchStatus(row).text }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ $index }">
              <el-button
                size="small"
                type="danger"
                @click="removeLabelFile($index)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="upload-box">
        <p>上传标签：</p>
        <el-upload
          drag
          :auto-upload="false"
          :show-file-list="false"
          :on-change="onLabelUpload"
          multiple
          accept=".json,.txt,.csv"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">拖拽或点击上传标签文件</div>
          <div class="el-upload__text">支持JSON、TXT、CSV格式</div>
        </el-upload>
      </div>
    </div>
    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleSave">完成并保存</el-button>
    </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import axios from "axios"
import { defineEmits, defineProps, watch, ref, computed } from 'vue'
import { ElDialog, ElButton, ElImage, ElUpload, ElMessage, ElMessageBox, ElLoading } from "element-plus"

const props = defineProps({
  modelValue: Boolean
})
const emit = defineEmits(['update:modelValue', 'close', 'saved'])

const dialogVisible = ref(props.modelValue)

watch(() => props.modelValue, (val) => {
  dialogVisible.value = val
})

watch(dialogVisible, (val) => {
  emit('update:modelValue', val)
  if (!val) emit('close')
})

const hoverIndex = ref(-1)

interface ImageFile {
  file: File
  preview: string
  name: string
}
interface LabelFile {
  file: File
  name: string
  matched: boolean
  key?: number
}

const imageList = ref<ImageFile[]>([])
const labelFileList = ref<LabelFile[]>([])
let keyCounter = 0

const imageBaseNames = computed(() =>
  imageList.value.map(img =>
    img.name.replace(/\.[^/.]+$/, "") ?? ""
  )
)
const onImageUpload = async (file: any) => {
  try {
    const formData = new FormData()
    formData.append('file', file.raw)

    const res = await axios.post('/api/files/preview', formData)
    for (const item of res.data.data) {
      if (!item.preview) {
        ElMessage.error(`文件 ${file.name} 预览链接获取失败`)
        return
      }
      const base64Prefix = "data:image/jpeg;base64,"
      const raw = item.preview.startsWith(base64Prefix)? item.preview : base64Prefix + item.preview
      imageList.value.push({
        file: file.raw,
        preview: raw,
        name: file.raw.name,
      })
    }
    updateLabelMatches()
  } catch (error) {
    ElMessage.error(`文件 ${file.name} 获取预览失败`)
  }
}
const onImageRemove = (index: number) => {
  imageList.value.splice(index, 1)
  updateLabelMatches()
}

const updateLabelMatches = () => {
  labelFileList.value.forEach(label => {
    const labelBaseName = label.name.replace(/\.[^/.]+$/, "")
    label.matched = imageBaseNames.value.includes(labelBaseName)
  })
  labelFileList.value = [...labelFileList.value]
}
const getMatchStatus = (row: LabelFile) => {
  const labelBaseName = row.name.replace(/\.[^/.]+$/, "")
  const isMatched = imageBaseNames.value.includes(labelBaseName)
  return isMatched
    ? { type: 'success', text: '已匹配' }
    : { type: 'danger', text: '未匹配' }
}
const onLabelUpload = (uploadFile: any) => {
  const file = uploadFile.raw
  const labelBaseName = file.name.replace(/\.[^/.]+$/, "")
  const matched = imageList.value.some(img =>
    img.name?.replace(/\.[^/.]+$/, "") === labelBaseName
  )
  labelFileList.value.push({
    file: file,
    name: file.name,
    matched: matched,
    key: keyCounter++
  })
}
const removeLabelFile = (index: number) => {
  labelFileList.value.splice(index, 1)
}

async function handleCancel () {
  if (imageList.value.length === 0 && labelFileList.value.length === 0) {
    dialogVisible.value = false
    return
  }

  ElMessageBox.confirm('确定要取消上传吗？所有未保存的内容将会丢失。', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    dialogVisible.value = false
    imageList.value = []
    labelFileList.value = []
    ElMessage.info('已取消上传')
  }).catch(() => {
    ElMessage.info('操作已取消')
  })
}
async function handleSave () {
  if (imageList.value.length === 0) {
    ElMessage.warning('请至少上传一张图片');
    return;
  }
  if (labelFileList.value.length > 0) {
    const allMatched = labelFileList.value.every(label => label.matched);
    if (!allMatched) {
      ElMessage.warning('请确保所有标签文件都已匹配到图像');
      return;
    }
  }
  const loading = ElLoading.service({
    lock: true,
    text: '正在保存数据...',
    spinner: 'el-icon-loading',
    background: 'rgba(0, 0, 0, 0.7)'
  });

  try {
    const formData = new FormData();
    imageList.value.forEach(img => {
      formData.append('images', img.file);
    });
    labelFileList.value.forEach(label => {
      formData.append('labels', label.file);
    });
    formData.append('label_status', 'uploaded');
    await axios.post('/api/files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    ElMessage.success('数据上传成功');
    dialogVisible.value = false;
    imageList.value = [];
    labelFileList.value = [];
    emit('saved')
  } catch(error) {
    console.error('上传失败:', error);
    ElMessage.error('数据上传失败，请稍后重试');
  } finally {
    loading.close();
  }
}

</script>

<style scoped>
.upload-area {
  border: 1px dashed var(--el-border-color);
  border-radius: 8px;
  background-color: var(--el-fill-color-light);
  min-height: 150px;
  margin-bottom: 10px;
}

.upload-box {
  width: 100%;
  min-height: 100px;
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-sizing: border-box;
  position: relative;
  align-items: center;
}
:deep(.el-upload-dragger) {
  width: 300px !important;
  height: 100px !important;
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
.image-preview-wrapper {
  position: relative;
  border: 1px dashed var(--el-border-color);
  border-radius: 8px;
  padding: 8px;
  background-color: var(--el-fill-color-light);
  margin-bottom: 10px;
}
.image-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.image-item {
  width: 150px;
  height: 100px;
  aspect-ratio: 1 / 1;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}
.full-image {
  width: 100%;
  height: 100%;
  object-fit: fill;
}
.delete-mask {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
  cursor: pointer;
}
.image-item:hover .delete-mask {
  opacity: 1;
}
</style>
