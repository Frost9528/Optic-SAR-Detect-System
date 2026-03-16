import { createRouter, createWebHistory } from "vue-router"
import DefaultLayout from "@/pages/DefaultLayout.vue";
import DataManage from "@/pages/DataManage.vue"
import ImageDetail from '@/pages/ImageDetail.vue'
import DetectPage from '@/pages/Detect.vue'
import ResultPage from '@/pages/Result.vue'
import Model   from "@/pages/Model.vue";
import ModelTrain from "@/pages/ModelTrain.vue";
import Datasets from "@/pages/Dataset.vue";
import CreateDataset from '../pages/CreateDataset.vue';
import DatasetDetail from "@/pages/DatasetDetail.vue";

const routes = [
  {
    path: '/',
    component: DefaultLayout,
    children: [
      {
        path: 'data',
        name: 'DataManage',
        component: DataManage
      },
      {
        path: 'image/:id',
        name: 'ImageDetail',
        component: ImageDetail
      },
      {
        path: 'detect',
        name: 'DetectPage',
        component: DetectPage
      },
      {
        path: 'detect/result/:taskId',
        name: 'ResultPage',
        component: ResultPage
      },
      {
        path: 'models',
        name: 'Model',
        component: Model
      },
      {
        path: 'models/train',
        name: 'ModelTrain',
        component: ModelTrain
      },
      {
        path: 'models/datasets',
        name: 'Datasets',
        component: Datasets
      },
        {
        path: 'models/datasets/:id',
        name: 'DatasetDetail',
        component: DatasetDetail
      },

      {
        path: 'models/datasets/createdataset',
        name: 'CreateDataset',
        component: CreateDataset
      },
    ],
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
