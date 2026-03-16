<template>
  <el-config-provider :locale="locale">
    <router-view></router-view>
  </el-config-provider>
</template>

<script>
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { defineComponent } from 'vue'
import UploadImage from "@/components/UploadImage.vue";
import Detect from "@/pages/Detect.vue";
export default defineComponent({
  components: { Detect, Upload: UploadImage },
  setup() {
    return {
      locale: zhCn
  }
  }
})
</script>

<style lang="scss">

body {
  margin: 0;
}
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

.el-form {
  padding: 0 8px;
}
</style>
