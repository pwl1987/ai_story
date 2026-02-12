<!-- ChapterStudio.vue - 章节工作室主页面 -->
<template>
  <Layout>
    <div class="chapter-studio p-6">
      <!-- 页面头部 -->
      <div class="mb-6">
        <div class="text-sm breadcrumbs mb-2">
          <ul>
            <li><router-link to="/artworks">角色资产</router-link></li>
            <li><router-link :to="`/artworks/${chapter.artwork_id}`">作品详情</router-link></li>
            <li>{{ chapter?.title }} - 章节工作室</li>
          </ul>
        </div>
        <h1 class="text-3xl font-bold mb-2">{{ chapter?.title }}</h1>
        <p class="text-base-content/70" v-if="chapter">
          {{ chapter.description?.substring(0, 200) }}...
        </p>
      </div>

      <!-- 主内容 -->
      <template v-else>
        <!-- 错误边界包裹（P1-错误处理优化） -->
        <ErrorBoundary
          :can-retry="true"
          :can-dismiss="true"
          :dismiss-text="'关闭'"
          @retry="handleErrorRetry"
          @dismiss="handleErrorDismiss"
        >
          <!-- 工作流控制面板 -->
          <WorkflowControlPanel
            :status="workflowStatus"
            :progress="workflowProgress"
            :current-scene="currentSceneData"
            :total-scenes="chapter ? scenes.length : 0"
            :completed-scenes="completedScenesCount"
            :is-loading="isLoading"
            @start="handleStartWorkflow"
            @pause="handlePauseWorkflow"
            @resume="handleResumeWorkflow"
            @retry="handleRetryWorkflow"
            class="mb-6"
          />

        <!-- 场景网格 -->
        <div v-else class="mt-6">
          <div
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-xl font-semibold">场景列表</h2>
              <span v-if="chapter">({{ chapter.title }})</span>
              <span v-else>章节详情加载中...</span>
            </div>
            <button
              v-if="workflowStatus !== 'completed'"
              class="btn btn-sm btn-ghost"
              @click="goToStoryboard"
            >
              前往分镜编辑器
            </button>
          </div>

          <!-- 加载状态 -->
          <div v-if="isLoading" class="flex justify-center py-12">
            <span class="loading loading-spinner loading-lg"></span>
          </div>

          <!-- 空状态 -->
          <div
            v-else-if="chapter && scenes.length > 0"
            class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            <SceneProgressCard
              v-for="scene in scenes"
              :key="scene.id"
              :scene="scene"
              :is-active="currentSceneData?.id === scene.id"
              :show-extract-frames-button="showExtractFramesButton(scene)"
              @extract-frames="handleExtractFrames"
              @edit="handleEditScene"
            />
          </div>

          <!-- 无场景提示 -->
          <div
            v-else
            class="flex flex-col items-center justify-center py-20 bg-base-200 rounded-lg"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-20 w-20 text-base-content/20 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 19.197-2M7 19.4V3 19.197-2m7 19.4h.01M7 19.4V3 19.197-2m7 19.4h.01M7 19.4V3 19.197-2m7 19.4h.01M7 19.4V3 19.197-2z" />
            </svg>
            <h3 class="text-xl font-semibold mb-2">该章节还没有场景</h3>
            <p class="text-base-content/60 mb-4">请先添加场景，然后再启动工作流</p>
            <button class="btn btn-primary" @click="goToStoryboard">
              前往分镜编辑器
            </button>
          </div>
        </template>
      </div>

      <!-- 工作流事件日志 -->
      <WorkflowEventLog
        v-if="showEventLog"
        :events="workflowEvents"
        class="mt-6"
      />
        </ErrorBoundary>
      </div>
    </Layout>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex';
import Layout from '@/views/Layout.vue';
import WorkflowControlPanel from '@/components/artworks/WorkflowControlPanel.vue';
import SceneProgressCard from '@/components/artworks/SceneProgressCard.vue';
import WorkflowEventLog from '@/components/artworks/WorkflowEventLog.vue';
import ErrorBoundary from '@/components/common/ErrorBoundary.vue';
import chaptersApi from '@/services/api/chapters';
import WorkflowWebSocket from '@/utils/workflowWebSocket';

export default {
  name: 'ChapterStudio',
  components: {
    Layout,
    WorkflowControlPanel,
    SceneProgressCard,
    WorkflowEventLog,
    ErrorBoundary,
  },
  data() {
    return {
      chapterId: null,
      chapter: null,
      artworkId: null,
      artwork: null,
      // UI 状态
      showEventLog: false,
      // 错误边界状态（P1-错误处理优化）
      hasLoadError: false,
      loadError: null,
    };
  },
  computed: {
    ...mapState('workflow', [
      'currentWorkflow',
      'status',
      'progress',
      'currentScene',
      'chapter',
      'scenes',
      'events',
      'isConnected',
    ]),
    workflowStatus() {
      return this.status;
    },
    workflowProgress() {
      return this.progress;
    },
    currentSceneData() {
      return this.currentScene;
    },
    completedScenesCount() {
      return this.scenes.filter(scene => scene.is_completed).length;
    },
    isLoading() {
      return ['starting', 'stopping'].includes(this.status);
    },
    workflowEvents() {
      return this.events;
    },
  },
  methods: {
    ...mapActions('workflow', [
      'startWorkflow',
      'pauseWorkflow',
      'resumeWorkflow',
      'fetchWorkflowStatus',
      'addEvent',
      'updateProgress',
      'setConnected',
      'resetState',
    ]),

    async loadChapterData() {
      try {
        this.isLoading = true;
        this.hasLoadError = false;
        this.loadError = null;

        // 并行加载章节和场景数据
        const [chapterData, scenesData] = await Promise.all([
          chaptersApi.get(this.chapterId),
          chaptersApi.getScenes(this.chapterId),
        ]);

        this.chapter = chapterData;
        this.scenes = scenesData;

        // 如果工作流正在运行，获取工作流状态
        if (chapterData.workflow_status && chapterData.workflow_status !== 'idle') {
          await this.fetchWorkflowStatus(this.chapterId);
        }
      } catch (error) {
        console.error('加载章节数据失败:', error);

        // 记录错误状态供 ErrorBoundary 捕获
        this.hasLoadError = true;
        this.loadError = error;

        // 显示友好的错误提示
        const errorMessage = '加载章节数据失败: ' + (error.response?.data?.detail || error.message);
        this.$message.error(errorMessage, {
          duration: 5000,
          showClose: true,
        });
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * 处理错误边界的重试事件
     * @description 用户点击重试按钮时重新加载数据
     */
    handleErrorRetry() {
      this.hasLoadError = false;
      this.loadError = null;
      this.loadChapterData();
    },

    /**
     * 处理错误边界的关闭事件
     * @description 用户关闭错误提示时重置错误状态
     */
    handleErrorDismiss() {
      this.hasLoadError = false;
      this.loadError = null;
    },

    setupWebSocket() {
      this.wsClient = new WorkflowWebSocket(this.chapterId, {
        onConnected: () => console.log('WebSocket 已连接'),
        onEvent: (event) => this.handleWorkflowEvent(event),
        onDisconnected: () => {
          console.warn('WebSocket 断开，启用轮询模式');
          this.startPolling();
        },
        onError: (error) => {
          console.error('WebSocket 错误:', error);
          this.$message.warning('实时连接不稳定，已切换到轮询模式');
        },
      });

      this.wsClient.connect();
    },

    handleWorkflowEvent(event) {
      this.addEvent(event);

      switch (event.type) {
        case 'scene_started':
          this.currentScene = {
            id: event.scene_id,
            title: event.scene_title,
          };
          break;

        case 'scene_completed':
          this.updateProgress(event.progress);

          // 更新场景状态
          const sceneIndex = this.scenes.findIndex(s => s.id === event.scene_id);
          if (sceneIndex !== -1) {
            this.$set(this.scenes, sceneIndex, { is_completed: true });
          }
          break;

        case 'workflow_completed':
          this.updateProgress(100);
          this.$message.success('工作流已完成！');
          break;

        case 'workflow_failed':
          this.$message.error(`工作流失败: ${event.error_message}`);
          break;
      }
    },

    startPolling() {
      // 降级到轮询模式（P2-1: 轮询间隔可配置化）
      // 从环境变量读取轮询间隔，默认 5000ms（5秒）
      const pollingInterval = parseInt(process.env.VUE_APP_POLLING_INTERVAL) || 5000;
      this.pollInterval = setInterval(async () => {
        await this.fetchWorkflowStatus(this.chapterId);
      }, pollingInterval);
    },

    stopPolling() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval);
        this.pollInterval = null;
      }
    },

    handleStartWorkflow() {
      try {
        await this.startWorkflow(this.chapterId);
        this.$message.success('工作流已启动');
      } catch (error) {
        this.$message.error(`启动失败: ${error.response?.data?.detail || error.message}`);
      }
    },

    async handlePauseWorkflow() {
      try {
        await this.pauseWorkflow();
        this.$message.success('工作流已暂停');
      } catch (error) {
        this.$message.error(`暂停失败: ${error.message}`);
      }
    },

    async handleResumeWorkflow() {
      try {
        await this.resumeWorkflow();
        this.$message.success('工作流已继续');
      } catch (error) {
        this.$message.error(`继续失败: ${error.message}`);
      }
    },

    showExtractFramesButton(scene) {
      /**
       * 判断是否显示"提取首尾帧"按钮
       * 业务逻辑：只有当场景没有首尾帧，且工作流未运行时才显示
       * @param {Object} scene - 场景对象
       * @returns {boolean} 是否显示按钮
       */
      return !scene.head_frame && !scene.tail_frame && this.workflowStatus !== 'running';
    },

    async handleRetryWorkflow() {
      try {
        await this.startWorkflow(this.chapterId);
        this.$message.success('工作流已重新启动');
      } catch (error) {
        this.$message.error(`重试失败: ${error.response?.data?.detail || error.message}`);
      }
    },

    async handleExtractFrames(scene) {
      try {
        this.$message.info('正在提取场景首尾帧...');
        // 通过 Vuex action 触发首尾帧提取
        await this.$store.dispatch('artworks/extractSceneFrames', scene.id);

        // 刷新场景数据
        const updated = await chaptersApi.get(scene.id);
        const index = this.scenes.findIndex(s => s.id === scene.id);
        if (index !== -1) {
          this.$set(this.scenes, index, updated);
        }

        this.$message.success('首尾帧提取任务已创建');
      } catch (error) {
        this.$message.error(`提取失败: ${error.message}`);
      }
    },

    handleEditScene(scene) {
      this.$router.push({
        name: 'StoryboardEditor',
        params: {
          chapterId: this.chapterId,
          sceneId: scene.id,
        },
      });
    },

    goToStoryboard() {
      this.$router.push({
        name: 'StoryboardEditor',
        params: {
          chapterId: this.chapterId,
        },
      });
    },

    cleanup() {
      // 断开 WebSocket
      if (this.wsClient) {
        this.wsClient.disconnect();
        this.wsClient = null;
      }

      // 停止轮询
      this.stopPolling();

      // 重置状态
      this.$store.dispatch('workflow/resetState');
    },
  },
  beforeDestroy() {
    this.cleanup();
  },
};
</script>

<style scoped>
.chapter-studio {
  min-height: 100vh;
}
</style>
