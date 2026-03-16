<template>
  <div class="default-layout-container">
    <aside class="sidebar">
      <div class="logo">
        光学/SAR<br />卫星影像<br />目标识别系统
      </div>
      <nav class="sidebar-nav">
        <ul>
          <router-link to="/detect" class="nav-item" @click="toggleDetectMenu" :class="{ active: isActive('/detect') }">
            <i class="fas fa-bolt icon"></i> 目标识别
            <i :class="['fas', showDetectMenu ? 'fa-chevron-up' : 'fa-chevron-down']" style="margin-left:auto;"></i>
          </router-link>
          <transition name="fade">
            <ul v-show="showDetectMenu" class="submenu">
              <router-link to="/detect/result" class="nav-sub-item" :class="{ active: isActive('/detect/result') }">
                识别结果
              </router-link>
            </ul>
          </transition>

          <router-link to="/data" class="nav-item" :class="{ active: isActive('/data') }">
            <i class="fas fa-data icon"></i> 数据管理
          </router-link>

          <router-link to="/models" class="nav-item" @click="toggleModelMenu" :class="{ active: isActive('/models') }">
            <i class="fas fa-brain icon"></i> 识别模型
            <i :class="['fas', showModelMenu ? 'fa-chevron-up' : 'fa-chevron-down']" style="margin-left:auto;"></i>
          </router-link>
          <transition name="fade">
            <ul v-show="showModelMenu" class="submenu">
              <router-link to="/models/train" class="nav-sub-item" :class="{ active: isActive('/models/train') }">
                模型训练
              </router-link>
              <router-link to="/models/datasets" class="nav-sub-item" :class="{ active: isActive('/models/datasets') }">
                数据集管理
              </router-link>

            </ul>
          </transition>
        </ul>
      </nav>
    </aside>

    <main class="main-content-area">
      <header class="top-bar">
        <h1 class="page-title">{{ currentPageTitle }}</h1>
        <div class="user-info">
          <span>{{ username }}</span>
          </div>
      </header>
      <div class="page-content-wrapper">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script lang="ts" setup>
import { ref, provide } from 'vue';
import { useRoute } from 'vue-router'

const route = useRoute()
// 判断当前页面是否激活（用于菜单高亮）
const isActive = (path) => route.path.startsWith(path)

const currentPageTitle = ref('首页');
const username = ref('root');

const setPageTitle = (title: string) => {
  currentPageTitle.value = title;
};
provide('setPageTitle', setPageTitle);

const showModelMenu = ref(true);
const showDetectMenu = ref(false);
const toggleModelMenu = () => {
  showModelMenu.value = !showModelMenu.value;
};

const toggleDetectMenu = () => {
  showDetectMenu.value = !showDetectMenu.value;
};

</script>

<style scoped>
.default-layout-container {
  display: flex;
  height: 100vh;
  width: 100%;
  background-color: #f3f4f6;
  box-sizing: border-box;
}

.sidebar {
  width: 180px;
  flex-shrink: 0;
  background-color: #1f2937;
  color: white;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
}

.logo {
  padding: 16px;
  font-size: 20px;
  font-weight: bold;
  border-bottom: 1px solid #374151;
  text-align: left;
}

.sidebar-nav {
  flex-grow: 1;
  margin-top: 16px;
}

.sidebar-nav ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-item {
  padding: 8px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  color: #d1d5db;
  font-size: 16px;
  transition: background-color 0.2s ease;
}

.nav-item:hover,
.nav-item.active {
  background-color: #374151;
  color: #41b782;
}

.nav-sub-item {
  padding: 8px 32px; /* 缩进更明显 */
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 16px;
  color: #d1d5db;
  transition: background-color 0.2s ease;
}

.nav-sub-item:hover,
.nav-sub-item.active {
  background-color: #374151;
  color: #41b782;
}

.submenu {
  list-style: none;
  padding-left: 0;
  margin-left: 0;
}

.main-content-area {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  padding: 10px;
  background-color: #f3f4f6;
  box-sizing: border-box;
  min-width: 0;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid #d1d5db;
  flex-shrink: 0;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.username {
  color: #4b5563;
}

.user-icon {
  font-size: 24px;
  color: #4b5563;
}

.header-icon {
  font-size: 20px;
  color: #4b5563;
}

.page-content-wrapper {
  flex-grow: 1;
  margin-top: 12px;
  overflow-y: auto;
  box-sizing: border-box;
  min-height: 0;
}
</style>