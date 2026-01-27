<template>
  <div class="project-detail">
    <loading-container :loading="loading">
      <!-- 项目头部信息 -->
      <div class="bg-base-100 rounded-lg shadow-sm p-6 mb-4">
        <div class="flex justify-between items-center">
          <div>
            <h1 class="text-2xl font-bold">{{ project?.name || '加载中...' }}</h1>
            <p class="text-sm text-base-content/60 mt-1">{{ project?.description || '暂无描述' }}</p>
          </div>
          <status-badge v-if="project" :status="project.status" type="project" />
        </div>
      </div>

      <!-- 横向Tab栏 -->
      <div class="bg-base-100 rounded-lg shadow-sm">
        <div role="tablist" class="tabs tabs-bordered tabs-lg flex-nowrap overflow-x-auto">
          <input
            type="radio"
            name="project_tabs"
            role="tab"
            class="tab"
            aria-label="项目信息"
            :checked="activeTab === 'info'"
            @change="activeTab = 'info'"
          />
          <div role="tabpanel" class="tab-content bg-base-100 border-base-300 rounded-box p-6">
            <!-- 项目信息内容 -->
            <div v-if="project" class="space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="form-control">
                  <label class="label"><span class="label-text font-semibold">项目名称</span></label>
                  <input
                    v-model="editForm.name"
                    type="text"
                    class="input input-bordered w-full"
                    placeholder="请输入项目名称"
                  />
                </div>
                <div class="form-control">
                  <label class="label"><span class="label-text font-semibold">状态</span></label>
                  <div><status-badge :status="project.status" type="project" /></div>
                </div>
                <div class="form-control">
                  <label class="label"><span class="label-text font-semibold">创建时间</span></label>
                  <div class="text-base-content">{{ formatDate(project.created_at) }}</div>
                </div>
                <div class="form-control">
                  <label class="label"><span class="label-text font-semibold">更新时间</span></label>
                  <div class="text-base-content">{{ formatDate(project.updated_at) }}</div>
                </div>
              </div>
              <div class="form-control">
                <label class="label"><span class="label-text font-semibold">项目描述</span></label>
                <textarea
                  v-model="editForm.description"
                  class="textarea textarea-bordered w-full"
                  rows="3"
                  placeholder="请输入项目描述"
                ></textarea>
              </div>
              <div class="form-control">
                <label class="label"><span class="label-text font-semibold">原始文案</span></label>
                <textarea
                  v-model="editForm.original_topic"
                  class="textarea textarea-bordered w-full min-h-[200px]"
                  placeholder="请输入原始文案"
                ></textarea>
              </div>
              <div class="flex justify-between items-start gap-4">
                <!-- 剪映草稿路径显示 -->
                <div v-if="project?.jianying_draft_path" class="alert alert-info flex-1">
                  <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <div class="font-bold">剪映草稿已生成</div>
                    <div class="text-sm">{{ project.jianying_draft_path }}</div>
                  </div>
                </div>

                <!-- 操作按钮组 -->
                <div class="flex gap-2 items-center">
                  <!-- 剪映草稿生成按钮 -->
                  <jianying-draft-button
                    v-if="project"
                    :project-id="project.id"
                    :project="project"
                    @generated="handleDraftGenerated"
                  />

                  <button
                    class="btn btn-primary btn-sm"
                    :disabled="saving"
                    @click="handleSaveProjectInfo"
                  >
                    <span v-if="saving" class="loading loading-spinner loading-sm"></span>
                    {{ saving ? '保存中...' : '保存' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <input
            type="radio"
            name="project_tabs"
            role="tab"
            class="tab"
            aria-label="文案改写"
            :checked="activeTab === 'rewrite'"
            @change="activeTab = 'rewrite'"
          />
          <div role="tabpanel" class="tab-content bg-base-100 border-base-300 rounded-box p-6">
            <stage-content
              stage-type="rewrite"
              :stage="getStage('rewrite')"
              :all-stages="stages"
              :project-id="project.id"
              :original-topic="project?.original_topic"
              @execute="handleExecuteStage"
              @save="handleSaveStage"
              @stage-updated="handleStageUpdated"
              @stage-completed="handleStageCompleted"
            />
          </div>

          <input
            type="radio"
            name="project_tabs"
            role="tab"
            class="tab"
            aria-label="分镜输出"
            :checked="activeTab === 'storyboard'"
            @change="activeTab = 'storyboard'"
          />
          <div role="tabpanel" class="tab-content bg-base-100 border-base-300 rounded-box p-6">
            <stage-content
              stage-type="storyboard"
              :stage="getStage('storyboard')"
              :all-stages="stages"
              :project-id="project.id"
              @execute="handleExecuteStage"
              @save="handleSaveStage"
              @stage-updated="handleStageUpdated"
              @stage-completed="handleStageCompleted"
            />
          </div>

          <input
            type="radio"
            name="project_tabs"
            role="tab"
            class="tab"
            aria-label="文生图"
            :checked="activeTab === 'image_generation'"
            @change="activeTab = 'image_generation'"
          />
          <div role="tabpanel" class="tab-content bg-base-100 border-base-300 rounded-box p-6">
            <stage-content
              stage-type="image_generation"
              :stage="getStage('image_generation')"
              :all-stages="stages"
              :project-id="project.id"
              @execute="handleExecuteStage"
              @save="handleSaveStage"
              @stage-updated="handleStageUpdated"
              @stage-completed="handleStageCompleted"
            />
          </div>

          <input
            type="radio"
            name="project_tabs"
            role="tab"
            class="tab"
            aria-label="运镜输出"
            :checked="activeTab === 'camera_movement'"
            @change="activeTab = 'camera_movement'"
          />
          <div role="tabpanel" class="tab-content bg-base-100 border-base-300 rounded-box p-6">
            <stage-content
              stage-type="camera_movement"
              :stage="getStage('camera_movement')"
              :all-stages="stages"
              :project-id="project.id"
              @execute="handleExecuteStage"
              @save="handleSaveStage"
              @stage-updated="handleStageUpdated"
              @stage-completed="handleStageCompleted"
            />
          </div>

          <input
            type="radio"
            name="project_tabs"
            role="tab"
            class="tab"
            aria-label="图生视频"
            :checked="activeTab === 'video_generation'"
            @change="activeTab = 'video_generation'"
          />
          <div role="tabpanel" class="tab-content bg-base-100 border-base-300 rounded-box p-6">
            <!-- 视频生成阶段内容 -->
            <stage-content
              stage-type="video_generation"
              :stage="getStage('video_generation')"
              :all-stages="stages"
              :project-id="project.id"
              @execute="handleExecuteStage"
              @save="handleSaveStage"
              @stage-updated="handleStageUpdated"
              @stage-completed="handleStageCompleted"
            />

            <!-- 视频播放器 - 当有视频生成结果时显示 -->
            <div v-if="getStage('video_generation')?.output_data?.human_text?.scenes" class="mt-6">
              <div class="divider">
                <h3 class="text-lg font-bold">生成的视频</h3>
              </div>
              <video-player
                :videos="getStage('video_generation').output_data.human_text.scenes.filter(scene => scene.video_urls && scene.video_urls.length > 0)"
              />
            </div>
          </div>
        </div>
      </div>
    </loading-container>
  </div>
</template>

<script>
import { mapActions } from 'vuex';
import StatusBadge from '@/components/common/StatusBadge.vue';
import LoadingContainer from '@/components/common/LoadingContainer.vue';
import StageContent from '@/components/projects/StageContent.vue';
import JianyingDraftButton from '@/components/projects/JianyingDraftButton.vue';
import VideoPlayer from '@/components/common/VideoPlayer.vue';
import { formatDate } from '@/utils/helpers';
import websocketClient from '@/services/websocketClient';

export default {
  name: 'ProjectDetail',
  components: {
    StatusBadge,
    LoadingContainer,
    StageContent,
    JianyingDraftButton,
    VideoPlayer,
  },
  data() {
    return {
      loading: false,
      saving: false,
      project: null,
      stages: [],
      activeTab: 'info',
      editForm: {
        name: '',
        description: '',
        original_topic: '',
      },
      savedScrollPosition: 0, // 保存滚动位置
    };
  },
  created() {
    this.fetchData();
    this.connectWebSocket();
  },
  beforeDestroy() {
    this.disconnectWebSocket();
  },
  methods: {
    ...mapActions('projects', ['fetchProject', 'fetchProjectStages', 'executeStage', 'updateProject', 'updateStageData']),
    formatDate,

    async fetchData(preserveScroll = false) {
      // 保存当前滚动位置
      if (preserveScroll) {
        this.savedScrollPosition = window.pageYOffset || document.documentElement.scrollTop;
      }

      this.loading = true;
      try {
        const projectId = this.$route.params.id;
        this.project = await this.fetchProject(projectId);
        this.stages = await this.fetchProjectStages(projectId);
        // 初始化编辑表单
        this.initEditForm();

        // 恢复滚动位置
        if (preserveScroll) {
          this.$nextTick(() => {
            window.scrollTo(0, this.savedScrollPosition);
          });
        }
      } catch (error) {
        console.error('Failed to fetch project:', error);
        this.$message.error('加载项目失败');
      } finally {
        this.loading = false;
      }
    },

    initEditForm() {
      if (this.project) {
        this.editForm = {
          name: this.project.name || '',
          description: this.project.description || '',
          original_topic: this.project.original_topic || '',
        };
      }
    },

    connectWebSocket() {
      const projectId = this.$route.params.id;
      websocketClient.connect(projectId);

      websocketClient.on('stage_update', (data) => {
        console.log('Stage update:', data);
        this.fetchData(true); // 保持滚动位置
      });

      websocketClient.on('project_update', (data) => {
        console.log('Project update:', data);
        this.project = data.project;
      });
    },

    disconnectWebSocket() {
      websocketClient.disconnect();
    },

    getStage(stageType) {
      return this.stages.find((s) => s.stage_type === stageType) || null;
    },

    async handleExecuteStage({ stageType, inputData }) {
      try {
        await this.executeStage({
          projectId: this.project.id,
          stageName: stageType,
          inputData: inputData
        });
        this.$message.success('阶段执行已开始');
      } catch (error) {
        console.error('Failed to execute stage:', error);
        this.$message.error('执行失败');
      }
    },

    async handleSaveStage({ stageType, inputData, outputData, skipRefresh = false }) {
      try {
        await this.updateStageData({
          projectId: this.project.id,
          stageName: stageType,
          data: { input_data: inputData, output_data: outputData },
        });
        this.$message.success('保存成功');
        // 只有在非流式生成期间才刷新数据，避免断开SSE连接
        if (!skipRefresh) {
          await this.fetchData(true); // 保持滚动位置
        }
      } catch (error) {
        console.error('Failed to save stage:', error);
        this.$message.error('保存失败');
      }
    },

    handleStageUpdated(stageData) {
      // 当阶段通过SSE更新时,刷新数据
      console.log('Stage updated:', stageData);
      this.fetchData(true); // 保持滚动位置
    },

    async handleStageCompleted(stageData) {
      // 当阶段完成时,刷新数据以获取最新的阶段状态
      console.log('[ProjectDetail] Stage completed:', stageData);
      console.log('[ProjectDetail] 开始刷新数据...');
      await this.fetchData(true); // 保持滚动位置
      console.log('[ProjectDetail] 数据刷新完成，新的 stages:', this.stages);
    },

    async handleSaveProjectInfo() {
      // 验证表单
      if (!this.editForm.name || !this.editForm.name.trim()) {
        this.$message.error('项目名称不能为空');
        return;
      }

      if (!this.editForm.original_topic || !this.editForm.original_topic.trim()) {
        this.$message.error('原始文案不能为空');
        return;
      }

      this.saving = true;
      try {
        await this.updateProject({
          id: this.project.id,
          data: {
            name: this.editForm.name.trim(),
            description: this.editForm.description?.trim() || '',
            original_topic: this.editForm.original_topic.trim(),
          },
        });
        this.$message.success('保存成功');
        // 重新加载项目数据
        await this.fetchData();
      } catch (error) {
        console.error('Failed to save project:', error);
        this.$message.error('保存失败');
      } finally {
        this.saving = false;
      }
    },

    async handleDraftGenerated(data) {
      console.log('剪映草稿生成成功:', data);
      this.$message.success(`剪映草稿生成成功！包含 ${data.videoCount} 个视频`);
      // 重新加载项目数据以更新草稿路径显示
      await this.fetchData(true); // 保持滚动位置
    },
  },
};
</script>

<style scoped>
.project-detail {
  width: 100%;
  max-width: 100%;
}

.tab-content {
  min-height: 400px;
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
}

/* 防止 tab 标签被挤压 */
.tab {
  flex-shrink: 0;
  white-space: nowrap;
}
</style>
