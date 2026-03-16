<template>
  <el-card
    :body-style="{ padding: '4px' }"
    class="image-card"
    :class="{ 'selected-card': isSelected }"
    shadow="hover"
    @click="handleClick"
    @dblclick="handleDblClick"
  >
    <el-image
      :src="imageUrl"
      fit="cover"
      style="width: 100%; height: 100px;"
      lazy
    />
    <div class="file-name">{{ imageName }}</div>
  </el-card>
</template>

<script setup>
const props = defineProps({
  imageUrl: String,
  imageName: String,
  imageId: [String, Number],
  isSelected: Boolean,           // 控制样式
  selectable: Boolean,           // 是否启用选择（点击）
})
const emit = defineEmits(['select', 'open'])

function handleClick() {
  if (props.selectable) {
    emit('select', props.imageId)
  }
}

function handleDblClick() {
  console.log('双击事件触发，图像ID:', props.imageId)
  emit('open', props.imageId)
}

</script>

<style scoped>
.image-card:hover {
  box-shadow: 4px 4px 8px rgba(64, 158, 255, 0.3);
}
.selected-card {
  border: 1px solid #409EFF;
  background-color: #e6f7ff;
  box-shadow: 0 0 2px rgba(64, 158, 255, 0.5);
}
.file-name {
  font-size: 12px;
  text-align: center;
  word-break: break-word;
}
</style>