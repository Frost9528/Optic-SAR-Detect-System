<template>
  <el-dialog v-model="visible" title="导入数据集" width="800px" @close="resetDialog">
    <div class="folder-upload-container">
      <!-- 拖拽上传区域 -->
      <el-upload
        drag
        multiple
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFolderUpload"
        :before-upload="() => false"
        ref="uploadRef"
        class="folder-uploader"
      >
        <i class="el-icon-upload" />
        <div class="el-upload__text">点击此处上传</div>
        <div class="el-upload__tip">支持上传整个数据集文件夹</div>
      </el-upload>

      <!-- 上传后预览信息 -->
      <div v-if="fileList.length > 0" class="upload-preview">
        <el-descriptions column="1" border>
          <el-descriptions-item label="文件夹名称">{{ folderName }}</el-descriptions-item>
          <el-descriptions-item label="文件数量">{{ fileList.length }} 张</el-descriptions-item>
        </el-descriptions>
        <ul class="file-preview-list">
          <li v-for="(file, idx) in fileList.slice(0, 5)" :key="idx">{{ file.webkitRelativePath }}</li>
          <li v-if="fileList.length > 5">……</li>
        </ul>
      </div>
    </div>

    <!-- 操作按钮 -->
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :disabled="!fileList.length" @click="submitUpload">确定导入</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'

const props = defineProps({
  modelValue: Boolean,
})
const emit = defineEmits(['update:modelValue', 'upload-success'])

const visible = ref(props.modelValue)
const fileList = ref([])
const folderName = ref('')

watch(() => props.modelValue, (val) => {
  visible.value = val
})
watch(visible, (val) => {
  emit('update:modelValue', val)
})

// 设置 input 元素支持选择文件夹
onMounted(() => {
  nextTick(() => {
    const input = document.querySelector('.folder-uploader input[type="file"]')
    if (input) {
      input.setAttribute('webkitdirectory', '')
      input.setAttribute('directory', '')
    }
  })
})

// 选择文件夹后的处理
const handleFolderUpload = () => {
  const inputEl = document.querySelector('.folder-uploader input[type="file"]')
  const files = Array.from(inputEl?.files || [])
  if (files.length) {
    fileList.value = files
    folderName.value = files[0].webkitRelativePath.split('/')[0]
  }
}

// 上传成功，通知父组件
const submitUpload = () => {
  // 模拟上传过程，可替换为后端调用
  console.log('上传的文件：', fileList.value)
  emit('upload-success', { folderName: folderName.value, files: fileList.value })
  visible.value = false
}

// 重置状态
const resetDialog = () => {
  fileList.value = []
  folderName.value = ''
}
</script>

<style scoped>
.folder-upload-container {
  padding: 16px;
}

.folder-uploader {
  width: 100%;
  height: 200px;
  border: 2px dashed #c0ccda;
  border-radius: 6px;
  background-color: #f9f9f9;
  text-align: center;
  padding-top: 40px;
  margin-bottom: 20px;
  cursor: pointer;
}

.upload-preview {
  margin-top: 10px;
}

.file-preview-list {
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
  font-size: 13px;
  color: #666;
  max-height: 100px;
  overflow: auto;
}
</style>
