<template>
  <div class="train-model-page">
    <!-- 左侧配置栏 -->
    <div class="train-config-panel">
      <div class="section-title">训练配置</div>
      <el-form :model="form" label-width="100px" label-position="top" class="form-section">
        <el-form-item label="模型类型">
          <el-select v-model="form.model" placeholder="选择模型">
            <el-option
              v-for="item in modelInfo"
              :key="item.id"
              :label="item.name"
              :value="item.id">
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="数据集">
          <el-select v-model="form.dataset" placeholder="选择数据集">
            <el-option
              v-for="item in datasetInfo"
              :key="item.id"
              :label="item.name"
              :value="item.id">
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="训练轮数">
          <el-input-number v-model="form.epochs" :min="1" :max="500" />
        </el-form-item>
        <el-form-item label="学习率">
          <el-input-number v-model="form.learningRate" :min="0.0001" :max="1" :step="0.0001" />
        </el-form-item>
        <el-form-item label="批大小">
          <el-input-number v-model="form.batchSize" :min="1" :max="128" />
        </el-form-item>

        <el-form-item>
          <div style="display: flex; gap: 8px;">
            <el-button type="primary" @click="startTraining" :loading="isTraining">开始训练</el-button>
            <el-button @click="stopTraining" :disabled="!isTraining">终止训练</el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <!-- 右侧日志和结果 -->
    <div class="train-right-panel">
      <!-- 日志显示 -->
      <div class="log-section">
        <div class="section-title">训练日志</div>
        <el-card shadow="never" class="log-box">
          <el-scrollbar class="log-content" ref="logScrollbar" >
            <div v-for="(line, idx) in logs" :key="idx" class="log-line">
              {{ line }}
            </div>
            <div ref="bottomAnchor"></div>
          </el-scrollbar>
        </el-card>
      </div>

      <!-- 模型训练结果 -->
      <div class="result-section" v-if="!isTraining && trainingCompleted">
        <div class="section-title">训练结果</div>

        <!-- 上半部分并排布局 -->
        <div class="upper-result-summary">
          <!-- 左侧：基本指标 + 命名 -->
          <div class="left-summary">
            <div class="metrics-list">
              <div class="metric-row">
                <span class="metric-label">模型名称：</span>
                <el-input class="name-input" v-model="result.modelName" :placeholder="defaultModelName" />
              </div>
              <div class="metric-row">
                <span class="metric-label">总样本数：</span>
                <span class="metric-value">{{ result.overallMetrics.totalSamples }}</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">平均mAP：</span>
                <span class="metric-value">{{ (result.overallMetrics.averageMAP * 100).toFixed(1) }}%</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">准确率：</span>
                <span class="metric-value">{{ (result.overallMetrics.accuracy * 100).toFixed(1) }}%</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">虚警率：</span>
                <span class="metric-value">{{ (result.overallMetrics.falsePositiveRate * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>

          <!-- 右侧：曲线图 -->
          <div class="right-chart">
            <!--img :src="result.curveImage" class="chart-image" alt="训练曲线" -->
            <img src="/demo/PR_curve.png" class="chart-image" alt="训练曲线" />
            <!-- 你也可以用 ECharts 或其他图表组件代替占位图 -->
          </div>
        </div>

        <!-- 下半部分：每个目标类别的指标 -->
        <div class="lower-metric-table">
          <div class="sub-title">各目标类别指标</div>
          <el-table :data="result.classMetrics" border style="width: 65%">
            <el-table-column prop="className" label="目标" width="150" />
            <el-table-column prop="count" label="样本数量" width="150" />
            <el-table-column prop="accuracy" label="准确率" width="200">
              <template #default="{ row }">
                {{ (row.accuracy * 100).toFixed(1) }}%
              </template>
            </el-table-column>
            <el-table-column prop="falseAlarm" label="虚警率" >
              <template #default="{ row }">
                {{ (row.falsePositiveRate * 100).toFixed(1) }}%
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="button-group">
          <el-button type="success" @click="saveModel">保存模型</el-button>
          <el-button type="info" @click="discardModel">不保存</el-button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { inject, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from "axios";
import { io, Socket } from 'socket.io-client';

const setPageTitle = inject<(title: string) => void>('setPageTitle')
onMounted(() => {
  if (setPageTitle) {
    setPageTitle('模型训练')  // 修改为当前页面标题
    fetchModelInfo()
    fetchDatasetInfo()
  }
})
onUnmounted(() => {
  if (task_id.value) {
    teardownSocketListener(task_id.value);
  }
});
const form = ref({
  model: '',
  dataset: '',
  epochs: 50,
  learningRate: 0.001,
  batchSize: 16
})

const logs = ref<string[]>([])
const isTraining = ref(false)
const trainingCompleted = ref(false)

const task_id = ref('')

const modelInfo = ref([])
const fetchModelInfo = async () => {
  try {
    const response = await axios.get('/api/models')
    if (response.data.code === 0) {
      modelInfo.value = response.data.data.reduce((acc, model) => {
        acc[model.id] = model
        return acc
      }, {})
    } else {
      ElMessage.error(response.data.message || '获取模型信息失败')
    }
  } catch (err) {
    console.error('获取模型信息出错:', err)
    ElMessage.error('调用模型信息接口失败')
  }
}
const datasetInfo = ref([])
const fetchDatasetInfo = async () => {
  try {
    const response = await axios.get('/api/datasets', {
      params: {
        per_page: 1000 // 极大值，无视分页
      }
    })
    if (response.data.code === 0) {
      datasetInfo.value = response.data.data.datasets.reduce((acc, dataset) => {
        acc[dataset.id] = dataset
        return acc
      }, {})
    } else {
      ElMessage.error(response.data.message || '获取数据集信息失败')
    }
  } catch (err) {
    console.error('获取数据集信息出错:', err)
    ElMessage.error('调用数据集信息接口失败')
  }
}

const result = ref({
  modelName: '',
  overallMetrics: {
    totalSamples: 0,
    averageMAP: 0,
    accuracy: 0,
    falsePositiveRate: 0,
  },
  curveImage: '',
  classMetrics: [
    {
      className: 'ship',
      count: 10,
      accuracy: 0.94,
      falsePositiveRate: 0.03
    }
  ]
})

let trainingInterval: ReturnType<typeof setInterval> | null = null

const startTraining = async () => {
  if (!form.value.model || !form.value.dataset) {
    ElMessage.warning('请填写完整训练配置')
    return
  }

  trainingCompleted.value = false
  try {
    const response = await axios.post('/api/training/tasks', form.value)
    if (response.data.code === 0) {
      ElMessage.success('训练请求已发送，正在等待结果...')
      logs.value = [`[开始训练] 模型: ${form.value.model}, 数据集: ${form.value.dataset}`]
      logs.value.push(`[任务ID: ${response.data.data}]`)
      isTraining.value = true
      task_id.value = response.data.data
      setupSocketListener(task_id.value);
    } else {
      ElMessage.error(response.data.message || '训练请求失败')
      isTraining.value = false
    }
  } catch (err) {
    console.error('训练请求出错:', err)
    ElMessage.error('调用训练接口失败')
    isTraining.value = false
    return
  }
}

const stopTraining = async () => {
  try {
    if (!task_id.value) {
      ElMessage.warning('没有正在进行的训练任务')
      return
    }
    const response = await axios.post(`/api/training/tasks/${task_id.value}/cancel`)
    if (response.data.code === 0) {
      ElMessage.success('训练已终止')
      isTraining.value = false
      logs.value.push('[训练已终止]')
      teardownSocketListener(task_id.value);
      if (trainingInterval) {
        clearInterval(trainingInterval)
        trainingInterval = null
      }
    } else {
      ElMessage.error(response.data.message || '终止训练失败')
    }
  } catch (err) {
    console.error('终止训练出错:', err)
    ElMessage.error('终止训练时发生错误')
    return
  }

}

const saveModel = async () => {
  // TODO: 多次点击的处理
  try {
    const response = await axios.post(`/api/training/tasks/${task_id.value}/save`, {
      model_name: result.value.modelName
    })
    if (response.data.code === 0) {
      ElMessage.success(`模型 ${result.value.modelName || '未命名模型'} 保存成功`)
    } else {
      ElMessage.error(response.data.message || '模型保存失败')
    }
  } catch (err) {
    console.error('保存模型出错:', err)
    ElMessage.error('保存模型时发生错误')
    return
  }
}
const discardModel = async () => {
  // 可添加返回主页或清空逻辑
  try {
    const response = await axios.delete(`/api/training/tasks/${task_id.value}`)
    if (response.data.code === 0) {
      ElMessage.info('模型未保存')
    } else {
      ElMessage.error(response.data.message || '取消保存模型失败')
    }
  } catch (err) {
    console.error('取消保存模型出错:', err)
    ElMessage.error('取消保存模型时发生错误')
  }
}

const logScrollbar = ref<any>(null);
const bottomAnchor = ref<HTMLElement>()
const scrollToBottom = () => {
  nextTick(() => {
    bottomAnchor.value.scrollIntoView({ behavior: 'smooth' });
  });
};
let socket: Socket;
const setupSocketListener = (currentTaskId: string) => {
  socket = io('http://localhost:5050'); // TODO: 替换为实际的 WebSocket URL
  socket.on('training_log_update', (data: { task_id: string; log: string }) => {
    logs.value.push(`${data.log}`);
    scrollToBottom();

  });

  socket.on('task_status_update',
      (data: { task_id: string; status: string; results?: any; error_message?: string }) => {
    logs.value.push(`[Task Status Update] Task ${data.task_id} is ${data.status}`);
    if (data.status === 'COMPLETED' || data.status === 'FAILED' || data.status === 'CANCELLED') {
      isTraining.value = false;
      teardownSocketListener(currentTaskId);
      if (data.status === 'FAILED') {
        console.error('Training failed:', data.error_message);
        logs.value.push(`[训练失败] 错误信息: ${data.error_message || '未知错误'}`);
        ElMessage.error(`训练失败: ${data.error_message || '未知错误'}`);
        return ;
      }
      trainingCompleted.value = true;
      result.value = {
        modelName: '',
        overallMetrics: {
          totalSamples: data.results.total_samples || 0,
          averageMAP: data.results.performance_metrics.final_mAP50 || 0,
          accuracy: data.results.performance_metrics.final_precision,
          falsePositiveRate: data.results.performance_metrics.final_false_rate,
        },
        curveImage: '',
        classMetrics: data.results.performance_metrics.class_metrics.map(class_metrics => ({
            className: class_metrics.class_name,
            count: class_metrics.sample_count,
            accuracy: class_metrics.precision,
            falsePositiveRate: class_metrics.false_rate
          }))
      };
      generateDefaultModelName()
    }
  });
};
const teardownSocketListener = (currentTaskId: string) => {
  if (socket) {
    logs.value.push(`[Leaving log room: task_${currentTaskId}]`);
    socket.emit('leave_task_room', { room: currentTaskId });
    socket.disconnect();
    socket = null;
    logs.value.push('[WebSocket Listener Stopped]');
  }
};

const defaultModelName = ref('')
const trainingStartTime = new Date()

  // 在训练完成后自动生成默认名称
const generateDefaultModelName = () => {
  const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')
  const modelType = form.value.model || 'unknown'
  defaultModelName.value = `model-${modelType}-${timestamp}`

  // 如果用户没有手动输入，则使用默认值
  if (!result.value.modelName) {
    result.value.modelName = defaultModelName.value
  }
}

</script>

<style scoped>
.train-model-page {
  display: flex;
  height: 100%;
  gap: 8px;
}
.train-config-panel {
  width: 250px;
  background: white;

}
.form-section {
  display: flex;
  flex-direction: column;
  padding: 8px;
}

.train-config-panel .el-form-item,
.train-config-panel .el-select,
.train-config-panel .el-input-number,
.train-config-panel .el-button {
  width: 90%;
}

.train-right-panel {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-right: 24px;
}
.log-section,
.result-section {
  background: white;
  padding: 16px;

}
.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #111827;
}
.log-box {
  background: #1e1e1e;
  color: #d1d5db;
  height: 240px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 13px;
}
.log-content {
  text-align: left;
  white-space: pre-wrap;
  flex-direction: column;
  overflow-y: auto;
}

.upper-result-summary {
  display: flex;
  gap: 16px;
  justify-content: space-between;
  align-items: flex-start;
}

.left-summary {
  display: flex;
  flex-direction: column;
  width: 400px;
  gap: 24px;
  padding-left: 16px;
}
.name-input {
  max-width: 250px; /* 控制输入框最大宽度 */
  width: 100%;
}
.metrics-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-row {
  display: flex;
  gap: 16px;
  font-size: 14px;
}

.metric-label {
  font-weight: bold;
  color: #333;
}

.metric-value {
  color: #1f2937; /* 深灰 */
}

.right-chart {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.chart-image {
  max-width: 100%;
  max-height: 300px;
  border: 1px solid #ccc;
  padding: 8px;
  background-color: #fff;
}

.lower-metric-table {
  margin-top: 24px;
}

.sub-title {
  font-weight: bold;
  margin-bottom: 8px;
  text-align: left;
}
.button-group {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}
</style>
