<template>
  <div class="shot-detail-sidebar drawer drawer-end">
    <input
      id="shot-detail-drawer"
      type="checkbox"
      class="drawer-toggle"
      checked
      @change="$emit('close')"
    />
    <div class="drawer-content">
      <div class="p-4 bg-base-200 h-full overflow-y-auto">
        <!-- 关闭按钮 -->
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-bold text-lg">镜头 #{{ shot?.shot_number }} 详情</h3>
          <button class="btn btn-sm btn-circle btn-ghost" @click="$emit('close')">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- 生成的图像预览 -->
        <div class="mb-6" v-if="shot?.generated_image_url">
          <h4 class="font-semibold mb-2">生成的画面</h4>
          <div class="relative">
            <img
              :src="shot.generated_image_url"
              :alt="`镜头 ${shot.shot_number}`"
              class="w-full rounded-lg shadow-lg"
            />
            <!-- 状态标记 -->
            <div class="absolute top-2 right-2">
              <span
                v-if="shot.is_successfully_generated"
                class="badge badge-success"
              >
                ✓ 已生成
              </span>
              <span
                v-else-if="shot.generation_error"
                class="badge badge-error"
                :title="shot.generation_error"
              >
                ✗ 失败
              </span>
            </div>
          </div>
        </div>

        <!-- 音频播放器 -->
        <div class="mb-6" v-if="shot?.generated_audio_url">
          <h4 class="font-semibold mb-2">语音</h4>
          <audio controls class="w-full" :src="shot.generated_audio_url">
            您的浏览器不支持音频播放
          </audio>
        </div>

        <!-- 镜头信息 -->
        <div class="space-y-4">
          <!-- 镜头内容 -->
          <div class="card bg-base-100 shadow">
            <div class="card-body p-4">
              <h4 class="card-title text-base mb-2">镜头内容</h4>
              <p class="text-sm">{{ shot?.content || '无内容' }}</p>
              <div v-if="shot?.speaker" class="text-xs text-base-content/60 mt-2">
                说话人: {{ shot.speaker }}
              </div>
            </div>
          </div>

          <!-- 旁白 -->
          <div class="card bg-base-100 shadow" v-if="shot?.narration">
            <div class="card-body p-4">
              <h4 class="font-semibold text-sm mb-2">旁白</h4>
              <p class="text-sm">{{ shot.narration }}</p>
            </div>
          </div>

          <!-- 角色造型 -->
          <div class="card bg-base-100 shadow" v-if="shot?.character_pose_name || shot?.character_pose">
            <div class="card-body p-4">
              <h4 class="font-semibold text-sm mb-2">角色造型</h4>
              <div class="flex items-center gap-3">
                <img
                  v-if="shot.character_pose?.pose_image"
                  :src="shot.character_pose.pose_image"
                  class="w-16 h-16 object-cover rounded"
                />
                <div>
                  <p class="text-sm font-medium">{{ shot.character_pose_name || shot.character_pose?.pose_name }}</p>
                  <p class="text-xs text-base-content/60">{{ shot.character_pose?.character_display_name }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- 运镜参数 -->
          <div class="card bg-base-100 shadow" v-if="hasCameraInfo">
            <div class="card-body p-4">
              <h4 class="font-semibold text-sm mb-2">运镜参数</h4>
              <div class="space-y-2 text-sm">
                <div v-if="shot?.camera_movement" class="flex justify-between">
                  <span class="text-base-content/60">类型:</span>
                  <span>{{ getCameraMovementLabel(shot.camera_movement) }}</span>
                </div>
                <div v-if="shot?.camera_angle" class="flex justify-between">
                  <span class="text-base-content/60">角度:</span>
                  <span>{{ getCameraAngleLabel(shot.camera_angle) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-base-content/60">时长:</span>
                  <span>{{ shot?.duration || 0 }}秒</span>
                </div>
                <div v-if="shot?.camera_movement_params && Object.keys(shot.camera_movement_params).length > 0" class="mt-3">
                  <span class="text-base-content/60">详细参数:</span>
                  <pre class="text-xs bg-base-200 p-2 rounded mt-1 overflow-x-auto">{{ JSON.stringify(shot.camera_movement_params, null, 2) }}</pre>
                </div>
              </div>
            </div>
          </div>

          <!-- 构图描述 -->
          <div class="card bg-base-100 shadow" v-if="shot?.shot_composition">
            <div class="card-body p-4">
              <h4 class="font-semibold text-sm mb-2">构图描述</h4>
              <p class="text-sm">{{ shot.shot_composition }}</p>
            </div>
          </div>

          <!-- 生成历史 -->
          <div class="card bg-base-100 shadow">
            <div class="card-body p-4">
              <h4 class="font-semibold text-sm mb-2">生成历史</h4>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-base-content/60">生成时间:</span>
                  <span>{{ shot?.generated_at ? formatDate(shot.generated_at) : '未生成' }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-base-content/60">重试次数:</span>
                  <span>{{ shot?.generation_retry_count || 0 }}次</span>
                </div>
                <div v-if="shot?.generation_error" class="mt-3">
                  <span class="text-base-content/60">错误信息:</span>
                  <p class="text-xs text-error mt-1">{{ shot.generation_error }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="mt-6 flex gap-2">
          <button
            class="btn btn-1/2 btn-primary"
            @click="$emit('regenerate', shot)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            重新生成
          </button>
          <button
            class="btn btn-1/2 btn-ghost"
            @click="$emit('close')"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'ShotDetailSidebar',
  props: {
    shot: {
      type: Object,
      required: true,
    },
    availablePoses: {
      type: Array,
      default: () => [],
    },
  },
  emits: ['close', 'shot-updated', 'regenerate'],
  setup(props) {
    // 是否有运镜信息
    const hasCameraInfo = computed(() => {
      return props.shot?.camera_movement ||
             props.shot?.camera_angle ||
             (props.shot?.camera_movement_params && Object.keys(props.shot.camera_movement_params).length > 0);
    });

    // 运镜类型标签映射
    const getCameraMovementLabel = (value) => {
      const labels = {
        zoom_in: '推近',
        zoom_out: '拉远',
        pan_left: '左摇',
        pan_right: '右摇',
        tilt_up: '上摇',
        tilt_down: '下摇',
        static: '固定',
      };
      return labels[value] || value;
    };

    // 镜头角度标签映射
    const getCameraAngleLabel = (value) => {
      const labels = {
        eye_level: '平视',
        high_angle: '俯视',
        low_angle: '仰视',
        bird_eye: '鸟瞰',
        worm_eye: '蚁视',
      };
      return labels[value] || value;
    };

    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    };

    return {
      hasCameraInfo,
      getCameraMovementLabel,
      getCameraAngleLabel,
      formatDate,
    };
  },
};
</script>

<style scoped>
.drawer-content {
  width: 100%;
}
</style>
