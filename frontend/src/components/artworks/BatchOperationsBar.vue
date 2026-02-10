<template>
  <div class="batch-operations-bar bg-base-200 rounded-lg p-4 shadow">
    <div class="flex items-center justify-between">
      <!-- 左侧：选中数量和清除按钮 -->
      <div class="flex items-center gap-3">
        <span class="badge badge-primary badge-lg">已选 {{ selectedCount }} 个</span>
        <button
          class="btn btn-sm btn-ghost"
          @click="$emit('clear-selection')"
        >
          清除选择
        </button>
      </div>

      <!-- 右侧：批量操作按钮 -->
      <div class="flex gap-2">
        <!-- 批量重新生成 -->
        <div class="dropdown dropdown-end">
          <label tabindex="0" class="btn btn-sm btn-primary gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            批量重新生成
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </label>
          <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
            <li><a @click="handleBatchRegenerate('image')">仅重新生成图像</a></li>
            <li><a @click="handleBatchRegenerate('audio')">仅重新生成音频</a></li>
            <li><a @click="handleBatchRegenerate('both')">重新生成图像和音频</a></li>
          </ul>
        </div>

        <!-- 批量设置造型 -->
        <div class="dropdown dropdown-end">
          <label tabindex="0" class="btn btn-sm btn-outline gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            设置造型
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </label>
          <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52 max-h-64 overflow-y-auto">
            <li><a @click="handleBatchSetPose(null)">清除造型</a></li>
            <li><a @click="handleBatchSetPose(null)">-- 无 --</a></li>
            <div class="divider my-0"></div>
            <li v-for="pose in availablePoses" :key="pose.id">
              <a @click="handleBatchSetPose(pose.id)">
                {{ pose.character_display_name }} - {{ pose.pose_name }}
              </a>
            </li>
          </ul>
        </div>

        <!-- 批量修改时长 -->
        <div class="dropdown dropdown-end">
          <label tabindex="0" class="btn btn-sm btn-outline gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            修改时长
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </label>
          <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-40">
            <li><a @click="handleBatchUpdateDuration(2)">2 秒</a></li>
            <li><a @click="handleBatchUpdateDuration(3)">3 秒</a></li>
            <li><a @click="handleBatchUpdateDuration(5)">5 秒</a></li>
            <li><a @click="handleBatchUpdateDuration(7)">7 秒</a></li>
            <li><a @click="handleBatchUpdateDuration(10)">10 秒</a></li>
          </ul>
        </div>

        <!-- 批量删除 -->
        <button
          class="btn btn-sm btn-error gap-1"
          @click="handleBatchDelete"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          删除
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BatchOperationsBar',
  props: {
    selectedCount: {
      type: Number,
      required: true,
    },
    availablePoses: {
      type: Array,
      default: () => [],
    },
  },
  emits: [
    'clear-selection',
    'batch-regenerate',
    'batch-delete',
    'batch-update-duration',
    'batch-set-pose',
  ],
  setup(props, { emit }) {
    // 批量重新生成
    const handleBatchRegenerate = (regenerateType) => {
      emit('batch-regenerate', regenerateType);
    };

    // 批量删除
    const handleBatchDelete = () => {
      if (confirm(`确定要删除选中的 ${props.selectedCount} 个镜头吗？此操作不可撤销。`)) {
        emit('batch-delete');
      }
    };

    // 批量修改时长
    const handleBatchUpdateDuration = (duration) => {
      emit('batch-update-duration', duration);
    };

    // 批量设置造型
    const handleBatchSetPose = (poseId) => {
      const poseName = poseId
        ? props.availablePoses.find((p) => p.id === poseId)?.pose_name || '该造型'
        : '无';
      if (confirm(`确定要将选中的 ${props.selectedCount} 个镜头的造型设置为${poseName}吗？`)) {
        emit('batch-set-pose', poseId);
      }
    };

    return {
      handleBatchRegenerate,
      handleBatchDelete,
      handleBatchUpdateDuration,
      handleBatchSetPose,
    };
  },
};
</script>

<style scoped>
.batch-operations-bar {
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
