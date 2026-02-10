<template>
  <div class="shot-list">
    <!-- 镜头卡片网格（支持拖拽排序） -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="(shot, index) in shots"
        :key="shot.id"
        class="shot-card-wrapper"
        :class="{ 'dragging': draggingIndex === index }"
        draggable="true"
        @dragstart="handleDragStart(index, $event)"
        @dragover.prevent="handleDragOver(index, $event)"
        @dragend="handleDragEnd"
        @drop="handleDrop(index, $event)"
      >
        <div
          class="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow"
          :class="{
            'ring-2 ring-primary ring-offset-2': selectedShotId === shot.id,
            'ring-2 ring-error ring-offset-2': selectedShotIds.includes(shot.id)
          }"
        >
        <figure class="relative">
          <!-- 复选框（批量选择模式） -->
          <div class="absolute top-2 left-2 z-10">
            <input
              type="checkbox"
              class="checkbox checkbox-sm"
              :checked="selectedShotIds.includes(shot.id)"
              @change="toggleShotSelection(shot.id)"
              @click.stop
            />
          </div>

          <div class="aspect-video bg-base-200">
            <img
              v-if="shot.generated_image_url"
              :src="shot.generated_image_url"
              :alt="`镜头 ${shot.shot_number}`"
              class="w-full h-full object-cover"
            />
            <div v-else class="flex items-center justify-center h-full text-4xl">
              🎬
            </div>
          </div>

          <!-- 生成状态标记 -->
          <div class="absolute top-2 right-2 flex gap-1">
            <span
              v-if="shot.is_generated && shot.is_successfully_generated"
              class="badge badge-success badge-sm"
            >
              ✓ 已生成
            </span>
            <span
              v-else-if="shot.generation_error"
              class="badge badge-error badge-sm"
              :title="shot.generation_error"
            >
              ✗ 失败
            </span>
            <span
              v-else-if="shot.is_generated && !shot.is_successfully_generated"
              class="badge badge-warning badge-sm"
            >
              ⚠ 部分完成
            </span>
            <span v-else class="badge badge-ghost badge-sm">
              待生成
            </span>
          </div>

          <!-- 重试计数 -->
          <div v-if="shot.generation_retry_count > 0" class="absolute top-2 left-10">
            <span class="badge badge-outline badge-sm">
              重试 {{ shot.generation_retry_count }} 次
            </span>
          </div>

          <!-- 拖拽手柄 -->
          <div class="absolute top-2 right-2 cursor-move opacity-50 hover:opacity-100">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16" />
            </svg>
          </div>
        </figure>

        <div class="card-body p-4">
          <!-- 镜头头部 -->
          <div class="flex justify-between items-center mb-2">
            <h3 class="card-title text-sm">镜头 #{{ shot.shot_number }}</h3>
            <div class="badge badge-sm badge-outline">{{ shot.shot_type_display }}</div>
          </div>

          <!-- 镜头内容 -->
          <div class="space-y-2 text-sm mb-3">
            <div v-if="shot.content" class="line-clamp-2" :title="shot.content">
              <span class="font-semibold text-base-content/60">内容：</span>{{ shot.content }}
            </div>
            <div v-if="shot.narration" class="line-clamp-2" :title="shot.narration">
              <span class="font-semibold text-base-content/60">旁白：</span>{{ shot.narration }}
            </div>
            <div v-if="shot.speaker" class="text-xs text-base-content/50">
              说话人：{{ shot.speaker }}
            </div>
            <div v-if="shot.character_pose_name" class="flex items-center gap-2 text-xs">
              <span class="badge badge-info">{{ shot.character_pose_name }}</span>
              <span class="text-base-content/50">{{ shot.camera_angle || '默认角度' }}</span>
            </div>
          </div>

          <!-- 时长信息 -->
          <div v-if="shot.duration" class="text-xs text-base-content/50 mb-3">
            时长：{{ shot.duration }}秒
          </div>

          <!-- 操作按钮 -->
          <div class="card-actions justify-between mt-auto">
            <button
              class="btn btn-sm btn-ghost"
              @click="viewDetail(shot)"
            >
              详情
            </button>
            <button
              class="btn btn-sm btn-primary gap-1"
              @click="openRegenerateModal(shot)"
              :disabled="isProcessing"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              重新生成
            </button>
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!shots || shots.length === 0" class="text-center py-12">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-base-content/20 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
      </svg>
      <p class="text-base-content/60">暂无镜头数据</p>
    </div>

    <!-- 重新生成弹窗 -->
    <RegenerateModal
      v-if="showRegenerateModal && selectedShot"
      :shot="selectedShot"
      :available-poses="availablePoses"
      @close="closeRegenerateModal"
      @regenerate-started="handleRegenerateStarted"
      @regenerate-completed="handleRegenerateCompleted"
    />
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import RegenerateModal from './RegenerateModal.vue';
import { poseApi } from '@/services/artworkService';

export default {
  name: 'ShotList',
  components: {
    RegenerateModal,
  },
  props: {
    shots: {
      type: Array,
      default: () => [],
    },
    sceneId: {
      type: Number,
      default: null,
    },
    selectedShotIds: {
      type: Array,
      default: () => [],
    },
  },
  emits: ['shot-selected', 'shot-toggled', 'shots-reordered', 'regenerate-completed'],
  setup(props, { emit }) {
    const showRegenerateModal = ref(false);
    const selectedShot = ref(null);
    const selectedShotId = ref(null);
    const isProcessing = ref(false);
    const availablePoses = ref([]);

    // 拖拽状态
    const draggingIndex = ref(null);
    const dragOverIndex = ref(null);

    // 查看镜头详情
    const viewDetail = (shot) => {
      selectedShotId.value = shot.id;
      emit('shot-selected', shot);
    };

    // 切换镜头选中状态
    const toggleShotSelection = (shotId) => {
      emit('shot-toggled', shotId);
    };

    // 拖拽开始
    const handleDragStart = (index, event) => {
      draggingIndex.value = index;
      event.dataTransfer.effectAllowed = 'move';
      event.target.classList.add('dragging');
    };

    // 拖拽经过
    const handleDragOver = (index, event) => {
      event.preventDefault();
      if (draggingIndex.value !== index) {
        dragOverIndex.value = index;
      }
    };

    // 放置
    const handleDrop = (index, event) => {
      event.preventDefault();
      if (draggingIndex.value !== null && draggingIndex.value !== index) {
        // 重新排序数组
        const newShots = [...props.shots];
        const [removed] = newShots.splice(draggingIndex.value, 1);
        newShots.splice(index, 0, removed);
        emit('shots-reordered', newShots);
      }
    };

    // 拖拽结束
    const handleDragEnd = (event) => {
      draggingIndex.value = null;
      dragOverIndex.value = null;
      event.target.classList.remove('dragging');
    };

    // 打开重新生成弹窗
    const openRegenerateModal = async (shot) => {
      selectedShot.value = shot;
      showRegenerateModal.value = true;

      // 加载可用的角色造型
      try {
        // 如果镜头关联了角色，获取该角色的所有造型
        if (shot.character_pose?.character?.id) {
          const response = await poseApi.list({
            character: shot.character_pose.character.id,
          });
          availablePoses.value = response.data.results || response.data;
        }
      } catch (error) {
        console.error('加载角色造型失败:', error);
      }
    };

    // 关闭重新生成弹窗
    const closeRegenerateModal = () => {
      showRegenerateModal.value = false;
      selectedShot.value = null;
    };

    // 处理重新生成开始
    const handleRegenerateStarted = (data) => {
      console.log('[ShotList] 重新生成开始:', data);
      isProcessing.value = true;
    };

    // 处理重新生成完成
    const handleRegenerateCompleted = (data) => {
      console.log('[ShotList] 重新生成完成:', data);
      isProcessing.value = false;

      // 通知父组件刷新数据
      emit('regenerate-completed', {
        shotId: selectedShot.value?.id,
        data,
      });
    };

    return {
      showRegenerateModal,
      selectedShot,
      selectedShotId,
      isProcessing,
      availablePoses,
      draggingIndex,
      dragOverIndex,
      viewDetail,
      toggleShotSelection,
      handleDragStart,
      handleDragOver,
      handleDrop,
      handleDragEnd,
      openRegenerateModal,
      closeRegenerateModal,
      handleRegenerateStarted,
      handleRegenerateCompleted,
    };
  },
};
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.shot-card-wrapper {
  transition: transform 0.2s, box-shadow 0.2s;
}

.shot-card-wrapper.dragging {
  opacity: 0.5;
  transform: scale(0.95);
}

.shot-card-wrapper[draggable='true'] {
  cursor: move;
}

.shot-card-wrapper[draggable='true'] .card {
  cursor: move;
}
</style>
