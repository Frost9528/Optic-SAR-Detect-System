<template>
<div class="zoom-container" @wheel.prevent="handleWheel">
    <div
      class="zoom-inner"
      :style="{
        transform: `scale(${scale}) translate(${offset.x}px, ${offset.y}px)`
      }"
      @mousedown="startDrag"
      @mousemove="onDrag"
      @mouseup="endDrag"
      @mouseleave="endDrag"
    >
      <img :src="src" class="zoom-image" />
      <!-- 检测框 -->
      <div
        v-for="(box, index) in boxes"
        :key="index"
        class="bounding-box"
        :style="getBoxStyle(box)"
      >
        <span class="box-label">{{ box.class }} {{ (box.confidence * 100).toFixed(1) }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface Box {
  box: [number, number, number, number];
  class: string;
  confidence: number;
}

defineProps<{
  src: string;
  boxes: Box[];
}>();

const scale = ref(1);
const offset = ref({ x: 0, y: 0 });
let isDragging = false;
let start = { x: 0, y: 0 };

const handleWheel = (e: WheelEvent) => {
  const delta = e.deltaY > 0 ? -0.1 : 0.1;
  scale.value = Math.min(5, Math.max(0.1, scale.value + delta));
};

const startDrag = (e: MouseEvent) => {
  isDragging = true;
  start = { x: e.clientX, y: e.clientY };
};

const onDrag = (e: MouseEvent) => {
  if (isDragging) {
    offset.value.x += (e.clientX - start.x) / scale.value;
    offset.value.y += (e.clientY - start.y) / scale.value;
    start = { x: e.clientX, y: e.clientY };
  }
};

const endDrag = () => {
  isDragging = false;
};

const getBoxStyle = (box: Box) => {
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
</script>

<style scoped>
.zoom-container {
  width: 75%;
  height: 600px;
  overflow: hidden;
  border: 1px solid #ccc;
  position: relative;
  object-fit: contain;
  background-color: #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

.zoom-inner {
  width: fit-content;
  height: fit-content;
  transform-origin: top left;
  position: relative;
  user-select: none;
}

.zoom-image {
  display: block;
  max-width: none;
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