<template>
  <div class="modal modal-open">
    <div class="modal-box max-w-2xl">
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-bold text-lg">重新生成镜头</h3>
        <button
          @click="$emit('close')"
          class="btn btn-sm btn-circle btn-ghost"
          :disabled="isProcessing"
        >
          ✕
        </button>
      </div>

      <!-- 镜头信息 -->
      <div class="bg-base-200 rounded-lg p-4 mb-4">
        <div class="flex items-start gap-3">
          <div class="avatar">
            <div class="w-16 h-16 rounded-lg overflow-hidden bg-base-300">
              <img
                v-if="shot.generated_image_url"
                :src="shot.generated_image_url"
                alt="镜头图像"
                class="w-full h-full object-cover"
              />
              <div v-else class="flex items-center justify-center h-full text-4xl">
                🎬
              </div>
            </div>
          </div>
          <div class="flex-1">
            <p class="font-semibold">镜头 #{{ shot.shot_number }}</p>
            <p class="text-sm opacity-70 line-clamp-2">{{ shot.content || shot.narration }}</p>
            <div class="flex gap-2 mt-2">
              <span class="badge badge-sm badge-outline">{{ shot.shot_type_display }}</span>
              <span v-if="shot.character_pose_name" class="badge badge-sm badge-info">
                {{ shot.character_pose_name }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 生成选项 -->
      <div class="space-y-4 mb-6">
        <h4 class="font-semibold text-sm">生成内容</h4>

        <div class="form-control">
          <label class="label cursor-pointer justify-start gap-3">
            <input
              type="checkbox"
              v-model="form.regenerate_image"
              class="checkbox checkbox-primary"
            />
            <span class="label-text">重新生成图像</span>
          </label>
        </div>

        <div class="form-control">
          <label class="label cursor-pointer justify-start gap-3">
            <input
              type="checkbox"
              v-model="form.regenerate_audio"
              class="checkbox checkbox-primary"
            />
            <span class="label-text">重新生成音频</span>
          </label>
        </div>

        <div class="alert alert-warning text-sm" v-if="!form.regenerate_image && !form.regenerate_audio">
          <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>至少需要选择重新生成图像或音频</span>
        </div>
      </div>

      <!-- 高级选项 (可折叠) -->
      <div class="collapse collapse-arrow bg-base-200 mb-6">
        <input type="checkbox" />
        <div class="collapse-title font-semibold text-sm px-4 py-3">
          高级选项
        </div>
        <div class="collapse-content px-4">
          <div class="space-y-4 mt-3">
            <!-- 自定义提示词 -->
            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">图像生成提示词</span>
                <span class="label-text-alt text-xs opacity-60">可选</span>
              </label>
              <textarea
                v-model="form.override_params.image_prompt"
                class="textarea textarea-bordered h-24 text-sm"
                placeholder="描述你想要的图像效果，例如：电影级光效、柔焦背景、暖色调..."
              ></textarea>
              <label class="label">
                <span class="label-text-alt text-xs opacity-60">
                  留空则使用镜头内容自动生成
                </span>
              </label>
            </div>

            <!-- 角色造型 -->
            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">角色造型</span>
                <span class="label-text-alt text-xs opacity-60">可选</span>
              </label>
              <select
                v-model="form.override_params.character_pose_id"
                class="select select-bordered select-sm"
              >
                <option value="">使用默认造型</option>
                <option
                  v-for="pose in availablePoses"
                  :key="pose.id"
                  :value="pose.id"
                >
                  {{ pose.pose_name }} ({{ pose.pose_type_display }})
                </option>
              </select>
            </div>

            <!-- 运镜参数 -->
            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">运镜参数</span>
                <span class="label-text-alt text-xs opacity-60">JSON格式</span>
              </label>
              <input
                type="text"
                v-model="cameraMovementInput"
                class="input input-bordered input-sm"
                placeholder='{"zoom": "1.5x", "pan": "left"}'
              />
              <label class="label" v-if="cameraMovementError">
                <span class="label-text-alt text-error">{{ cameraMovementError }}</span>
              </label>
            </div>

            <!-- 时长 -->
            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">镜头时长 (秒)</span>
              </label>
              <input
                type="number"
                v-model.number="form.override_params.duration"
                class="input input-bordered input-sm"
                min="1"
                max="60"
                step="0.1"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 进度显示 -->
      <div v-if="isProcessing || progress" class="mb-6">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-semibold">{{ progressMessage }}</span>
          <span class="text-sm opacity-70">{{ progress }}%</span>
        </div>
        <progress
          class="progress progress-primary w-full"
          :value="progress"
          max="100"
        ></progress>
      </div>

      <!-- 操作按钮 -->
      <div class="modal-action">
        <button
          @click="$emit('close')"
          class="btn"
          :disabled="isProcessing"
        >
          取消
        </button>
        <button
          @click="handleRegenerate"
          class="btn btn-primary"
          :class="{ 'loading': isProcessing }"
          :disabled="!canSubmit"
        >
          <span v-if="!isProcessing">开始重新生成</span>
          <span v-else>生成中...</span>
        </button>
      </div>
    </div>

    <!-- 背景遮罩 -->
    <div class="modal-backdrop" @click="$emit('close')"></div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import artworkService from '@/services/artworkService';

export default {
  name: 'RegenerateModal',
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
  emits: ['close', 'regenerate-started', 'regenerate-completed'],
  setup(props, { emit }) {
    const isProcessing = ref(false);
    const progress = ref(0);
    const progressMessage = ref('');
    const wsConnection = ref(null);

    const form = ref({
      regenerate_image: true,
      regenerate_audio: true,
      override_params: {
        image_prompt: '',
        character_pose_id: '',
        camera_movement_params: {},
        duration: props.shot.duration || 3,
      },
    });

    // 运镜参数输入（JSON字符串）
    const cameraMovementInput = ref('');
    const cameraMovementError = ref('');

    // 监听输入，尝试解析JSON
    watch(cameraMovementInput, (newValue) => {
      if (!newValue.trim()) {
        form.value.override_params.camera_movement_params = {};
        cameraMovementError.value = '';
        return;
      }

      try {
        const parsed = JSON.parse(newValue);
        form.value.override_params.camera_movement_params = parsed;
        cameraMovementError.value = '';
      } catch (e) {
        cameraMovementError.value = '无效的JSON格式';
      }
    });

    // 计算属性：是否可以提交
    const canSubmit = computed(() => {
      return (
        !isProcessing.value &&
        (form.value.regenerate_image || form.value.regenerate_audio) &&
        !cameraMovementError.value
      );
    });

    // WebSocket 进度订阅
    const connectWebSocket = () => {
      const wsUrl = `ws://localhost:8000/ws/artworks/shots/${props.shot.id}/regenerate/`;
      wsConnection.value = new WebSocket(wsUrl);

      wsConnection.value.onopen = () => {
        console.log('WebSocket 已连接');
      };

      wsConnection.value.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'connected':
            console.log('WebSocket 连接确认:', data.message);
            break;

          case 'stage_update':
          case 'progress':
            progress.value = data.progress || 0;
            progressMessage.value = data.message || '正在处理...';
            break;

          case 'completed':
            progress.value = 100;
            progressMessage.value = '生成完成！';
            emit('regenerate-completed', data);
            setTimeout(() => {
              emit('close');
            }, 1500);
            break;

          case 'error':
            progressMessage.value = `错误: ${data.error || '生成失败'}`;
            isProcessing.value = false;
            break;

          case 'pong':
            // 心跳响应
            break;

          default:
            console.log('未知消息类型:', data.type, data);
        }
      };

      wsConnection.value.onerror = (error) => {
        console.error('WebSocket 错误:', error);
      };

      wsConnection.value.onclose = () => {
        console.log('WebSocket 已断开');
      };
    };

    // 心跳检测
    let heartbeatInterval;
    const startHeartbeat = () => {
      heartbeatInterval = setInterval(() => {
        if (wsConnection.value && wsConnection.value.readyState === WebSocket.OPEN) {
          wsConnection.value.send(JSON.stringify({
            type: 'ping',
            timestamp: Date.now() / 1000,
          }));
        }
      }, 30000); // 每30秒发送一次心跳
    };

    // 处理重新生成
    const handleRegenerate = async () => {
      if (!canSubmit.value) return;

      isProcessing.value = true;
      progress.value = 0;
      progressMessage.value = '准备生成...';

      try {
        // 连接 WebSocket
        connectWebSocket();
        startHeartbeat();

        // 发起重新生成请求
        const response = await artworkService.shot.regenerate(
          props.shot.id,
          {
            regenerate_image: form.value.regenerate_image,
            regenerate_audio: form.value.regenerate_audio,
            override_params: form.value.override_params,
          }
        );

        console.log('重新生成任务已启动:', response.data);
        emit('regenerate-started', response.data);

        // 如果不需要 WebSocket（例如没有可用的参数），直接完成
        // 否则等待 WebSocket 消息
      } catch (error) {
        console.error('重新生成失败:', error);
        progressMessage.value = `错误: ${error.response?.data?.detail || error.message}`;
        isProcessing.value = false;

        // 关闭 WebSocket
        if (wsConnection.value) {
          wsConnection.value.close();
        }
      }
    };

    // 清理
    onUnmounted(() => {
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
      }
      if (wsConnection.value) {
        wsConnection.value.close();
      }
    });

    return {
      form,
      isProcessing,
      progress,
      progressMessage,
      cameraMovementInput,
      cameraMovementError,
      canSubmit,
      handleRegenerate,
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
</style>
