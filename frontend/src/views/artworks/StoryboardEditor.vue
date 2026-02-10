<template>
  <Layout>
    <div class="storyboard-editor p-6">
      <!-- 页面头部 -->
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold">分镜编辑器</h1>
          <p class="text-base-content/60 mt-1" v-if="chapter">
            {{ artwork?.title }} - {{ chapter?.title }}
          </p>
        </div>
        <div class="flex gap-2">
          <button
            class="btn btn-ghost btn-sm"
            @click="showTransitionPanel = !showTransitionPanel"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
            转场配置
          </button>
          <button
            class="btn btn-primary btn-sm"
            @click="saveAllChanges"
            :disabled="!hasChanges || isSaving"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" v-if="!isSaving">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" v-else>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {{ isSaving ? '保存中...' : '保存更改' }}
          </button>
        </div>
      </div>

      <!-- 场景选择器 -->
      <div class="mb-6">
        <div class="flex items-center gap-4">
          <label class="label">选择场景:</label>
          <select
            v-model="selectedSceneId"
            class="select select-bordered select-sm w-64"
            @change="loadSceneShots"
          >
            <option value="">-- 请选择场景 --</option>
            <option
              v-for="scene in scenes"
              :key="scene.id"
              :value="scene.id"
            >
              场景 {{ scene.scene_number }}: {{ scene.scene_name }}
            </option>
          </select>
        </div>
      </div>

      <!-- 批量操作工具栏 -->
      <BatchOperationsBar
        v-if="selectedShotIds.length > 0"
        :selected-count="selectedShotIds.length"
        :available-poses="availablePoses"
        @batch-regenerate="handleBatchRegenerate"
        @batch-delete="handleBatchDelete"
        @batch-update-duration="handleBatchUpdateDuration"
        @batch-set-pose="handleBatchSetPose"
        @clear-selection="clearSelection"
        class="mb-6"
      />

      <!-- 主内容区域 -->
      <div class="flex gap-6">
        <!-- 故事板区域 -->
        <div class="flex-1">
          <ShotList
            v-if="currentScene"
            :shots="shots"
            :scene-id="currentScene?.id"
            :selected-shot-ids="selectedShotIds"
            @shot-selected="handleShotSelected"
            @shot-toggled="handleShotToggled"
            @shots-reordered="handleShotsReordered"
            @regenerate-completed="handleRegenerateCompleted"
          />

          <!-- 空状态 -->
          <div
            v-else
            class="flex flex-col items-center justify-center py-20 bg-base-200 rounded-lg"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-20 w-20 text-base-content/20 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
            </svg>
            <p class="text-lg text-base-content/60">请选择一个场景开始编辑</p>
          </div>
        </div>

        <!-- 镜头详情侧边栏 -->
        <ShotDetailSidebar
          v-if="selectedShot && showDetailSidebar"
          :shot="selectedShot"
          :available-poses="availablePoses"
          @close="closeDetailSidebar"
          @shot-updated="handleShotUpdated"
          @regenerate="handleRegenerate"
          class="w-96"
        />

        <!-- 场景转场配置面板 -->
        <SceneTransitionPanel
          v-if="showTransitionPanel && currentScene"
          :scene="currentScene"
          :all-scenes="scenes"
          @close="showTransitionPanel = false"
          @scene-updated="handleSceneUpdated"
          class="w-96"
        />
      </div>

      <!-- 快速编辑弹窗 -->
      <QuickEditModal
        v-if="showQuickEdit && editingShot"
        :shot="editingShot"
        :available-poses="availablePoses"
        @close="closeQuickEdit"
        @shot-updated="handleShotUpdated"
      />
    </div>
  </Layout>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import Layout from '@/views/Layout.vue';
import { artworkApi, sceneApi, shotApi, poseApi } from '@/services/artworkService';
import ShotList from '@/components/artworks/ShotList.vue';
import ShotDetailSidebar from '@/components/artworks/ShotDetailSidebar.vue';
import QuickEditModal from '@/components/artworks/QuickEditModal.vue';
import BatchOperationsBar from '@/components/artworks/BatchOperationsBar.vue';
import SceneTransitionPanel from '@/components/artworks/SceneTransitionPanel.vue';

export default {
  name: 'StoryboardEditor',
  components: {
    Layout,
    ShotList,
    ShotDetailSidebar,
    QuickEditModal,
    BatchOperationsBar,
    SceneTransitionPanel,
  },
  setup() {
    const route = useRoute();

    // 数据状态
    const artwork = ref(null);
    const chapter = ref(null);
    const scenes = ref([]);
    const shots = ref([]);
    const availablePoses = ref([]);

    // UI 状态
    const selectedSceneId = ref(null);
    const selectedShot = ref(null);
    const selectedShotIds = ref([]);
    const showDetailSidebar = ref(false);
    const showQuickEdit = ref(false);
    const showTransitionPanel = ref(false);
    const editingShot = ref(null);
    const isSaving = ref(false);
    const hasChanges = ref(false);

    // 计算属性
    const currentScene = computed(() => {
      return scenes.value.find((s) => s.id === selectedSceneId.value);
    });

    // 加载作品数据
    const loadArtworkData = async () => {
      try {
        const artworkId = route.params.artworkId;
        const chapterId = route.params.chapterId;

        if (artworkId) {
          const [artworkRes, chapterRes] = await Promise.all([
            artworkApi.get(artworkId),
            chapterId ? artworkApi.chapter.get(chapterId) : null,
          ]);
          artwork.value = artworkRes;
          chapter.value = chapterRes;

          // 加载场景列表
          await loadScenes();
        }
      } catch (error) {
        console.error('加载作品数据失败:', error);
      }
    };

    // 加载场景列表
    const loadScenes = async () => {
      try {
        const params = {};
        if (chapter.value) {
          params.chapter = chapter.value.id;
        }

        const response = await sceneApi.list(params);
        scenes.value = response.results || response;

        // 自动选择第一个场景
        if (scenes.value.length > 0 && !selectedSceneId.value) {
          selectedSceneId.value = scenes.value[0].id;
          await loadSceneShots();
        }
      } catch (error) {
        console.error('加载场景列表失败:', error);
      }
    };

    // 加载场景的镜头列表
    const loadSceneShots = async () => {
      if (!selectedSceneId.value) return;

      try {
        const response = await shotApi.list({
          scene: selectedSceneId.value,
          ordering: 'sort_order,shot_number',
        });
        shots.value = response.results || response;

        // 加载可用的角色造型
        await loadAvailablePoses();
      } catch (error) {
        console.error('加载镜头列表失败:', error);
      }
    };

    // 加载可用的角色造型
    const loadAvailablePoses = async () => {
      try {
        const response = await poseApi.list({
          artwork: artwork.value?.id,
        });
        availablePoses.value = response.results || response;
      } catch (error) {
        console.error('加载角色造型失败:', error);
      }
    };

    // 处理镜头选择
    const handleShotSelected = (shot) => {
      selectedShot.value = shot;
      showDetailSidebar.value = true;
    };

    // 处理镜头选中切换（复选框）
    const handleShotToggled = (shotId) => {
      const index = selectedShotIds.value.indexOf(shotId);
      if (index === -1) {
        selectedShotIds.value.push(shotId);
      } else {
        selectedShotIds.value.splice(index, 1);
      }
    };

    // 处理镜头排序变更
    const handleShotsReordered = async (reorderedShots) => {
      try {
        // 批量更新 sort_order
        const updates = reorderedShots.map((shot, index) => {
          return shotApi.update(shot.id, { sort_order: index });
        });

        await Promise.all(updates);
        shots.value = reorderedShots;
        hasChanges.value = true;
      } catch (error) {
        console.error('更新排序失败:', error);
      }
    };

    // 处理镜头更新
    const handleShotUpdated = (updatedShot) => {
      const index = shots.value.findIndex((s) => s.id === updatedShot.id);
      if (index !== -1) {
        shots.value.splice(index, 1, updatedShot);
      }
      hasChanges.value = true;
    };

    // 处理场景更新
    const handleSceneUpdated = (updatedScene) => {
      const index = scenes.value.findIndex((s) => s.id === updatedScene.id);
      if (index !== -1) {
        scenes.value.splice(index, 1, updatedScene);
      }
      if (currentScene.value?.id === updatedScene.id) {
        selectedSceneId.value = updatedScene.id;
      }
      hasChanges.value = true;
    };

    // 处理重新生成完成
    const handleRegenerateCompleted = ({ shotId, data }) => {
      const index = shots.value.findIndex((s) => s.id === shotId);
      if (index !== -1 && data.shot) {
        shots.value.splice(index, 1, data.shot);
      }
    };

    // 处理重新生成
    const handleRegenerate = (shot) => {
      editingShot.value = shot;
      showQuickEdit.value = true;
    };

    // 批量操作处理函数
    const handleBatchRegenerate = async () => {
      // TODO: 实现批量重新生成
      console.log('批量重新生成:', selectedShotIds.value);
    };

    const handleBatchDelete = async () => {
      // TODO: 实现批量删除（需要确认）
      console.log('批量删除:', selectedShotIds.value);
    };

    const handleBatchUpdateDuration = async (duration) => {
      try {
        const updates = selectedShotIds.value.map((shotId) => {
          return shotApi.update(shotId, { duration });
        });
        await Promise.all(updates);
        await loadSceneShots();
        clearSelection();
      } catch (error) {
        console.error('批量更新时长失败:', error);
      }
    };

    const handleBatchSetPose = async (poseId) => {
      try {
        const updates = selectedShotIds.value.map((shotId) => {
          return shotApi.update(shotId, { character_pose: poseId });
        });
        await Promise.all(updates);
        await loadSceneShots();
        clearSelection();
      } catch (error) {
        console.error('批量设置造型失败:', error);
      }
    };

    // 清除选择
    const clearSelection = () => {
      selectedShotIds.value = [];
    };

    // 关闭详情侧边栏
    const closeDetailSidebar = () => {
      showDetailSidebar.value = false;
      selectedShot.value = null;
    };

    // 关闭快速编辑
    const closeQuickEdit = () => {
      showQuickEdit.value = false;
      editingShot.value = null;
    };

    // 保存所有更改
    const saveAllChanges = async () => {
      isSaving.value = true;
      try {
        // 这里可以添加额外的保存逻辑
        hasChanges.value = false;
      } catch (error) {
        console.error('保存失败:', error);
      } finally {
        isSaving.value = false;
      }
    };

    // 组件挂载时加载数据
    onMounted(() => {
      loadArtworkData();
    });

    return {
      // 数据
      artwork,
      chapter,
      scenes,
      shots,
      availablePoses,

      // 计算属性
      currentScene,

      // UI 状态
      selectedSceneId,
      selectedShot,
      selectedShotIds,
      showDetailSidebar,
      showQuickEdit,
      showTransitionPanel,
      editingShot,
      isSaving,
      hasChanges,

      // 方法
      loadSceneShots,
      handleShotSelected,
      handleShotToggled,
      handleShotsReordered,
      handleShotUpdated,
      handleSceneUpdated,
      handleRegenerateCompleted,
      handleRegenerate,
      handleBatchRegenerate,
      handleBatchDelete,
      handleBatchUpdateDuration,
      handleBatchSetPose,
      clearSelection,
      closeDetailSidebar,
      closeQuickEdit,
      saveAllChanges,
    };
  },
};
</script>

<style scoped>
.storyboard-editor {
  min-height: calc(100vh - 4rem);
}
</style>
