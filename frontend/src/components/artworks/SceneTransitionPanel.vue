<template>
  <div class="scene-transition-panel drawer drawer-end">
    <input
      id="transition-panel-drawer"
      type="checkbox"
      class="drawer-toggle"
      :checked="true"
      @change="$emit('close')"
    />
    <div class="drawer-content">
      <div class="p-4 bg-base-200 h-full overflow-y-auto">
        <!-- 关闭按钮 -->
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-bold text-lg">场景转场配置</h3>
          <button class="btn btn-sm btn-circle btn-ghost" @click="$emit('close')">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- 场景信息 -->
        <div class="mb-6">
          <div class="alert alert-info">
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>场景 #{{ scene?.scene_number }}: {{ scene?.scene_name }}</span>
          </div>
        </div>

        <!-- 转场配置表单 -->
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- 转场类型 -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-semibold">转场类型</span>
              <span class="label-text-alt text-base-content/50">可选</span>
            </label>
            <select v-model="formData.transition_type" class="select select-bordered">
              <option value="">-- 无转场 --</option>
              <option value="fade">淡入淡出</option>
              <option value="dissolve">溶解</option>
              <option value="wipe">擦除</option>
              <option value="cut">切镜</option>
            </select>
            <label class="label" v-if="transitionTypeError">
              <span class="label-text-alt text-error">{{ transitionTypeError }}</span>
            </label>
          </div>

          <!-- 转场目标场景 -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-semibold">转场目标场景</span>
              <span class="label-text-alt text-base-content/50">下一个场景</span>
            </label>
            <select v-model="formData.transition_to_next" class="select select-bordered" :disabled="!formData.transition_type">
              <option value="">-- 无 --</option>
              <option
                v-for="targetScene in availableTargetScenes"
                :key="targetScene.id"
                :value="targetScene.id"
              >
                场景 {{ targetScene.scene_number }}: {{ targetScene.scene_name }}
              </option>
            </select>
            <label class="label">
              <span class="label-text-alt text-base-content/50">
                {{ formData.transition_type && !formData.transition_to_next ? '⚠️ 设置转场类型时必须指定目标场景' : '' }}
              </span>
            </label>
          </div>

          <!-- 转场时长 -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-semibold">转场时长</span>
              <span class="label-text-alt">{{ formData.transition_duration }}秒</span>
            </label>
            <input
              v-model.number="formData.transition_duration"
              type="range"
              min="0"
              max="10"
              step="0.1"
              class="range range-primary"
              :disabled="!formData.transition_type"
            />
            <div class="flex justify-between text-xs text-base-content/50 mt-1">
              <span>0s</span>
              <span>5s</span>
              <span>10s</span>
            </div>
            <label class="label" v-if="durationError">
              <span class="label-text-alt text-error">{{ durationError }}</span>
            </label>
          </div>

          <!-- 转场预览 -->
          <div v-if="formData.transition_type" class="bg-base-100 rounded-lg p-4">
            <h4 class="font-semibold text-sm mb-3">转场预览</h4>
            <div class="relative h-32 bg-base-200 rounded overflow-hidden">
              <!-- 简单的转场预览动画 -->
              <div
                class="absolute inset-0 flex items-center justify-center transition-opacity duration-150"
                :style="{ opacity: previewOpacity }"
              >
                <span class="text-sm text-base-content/60">当前场景</span>
              </div>
              <div class="absolute bottom-2 left-2 text-xs text-base-content/50">
                {{ getTransitionTypeLabel(formData.transition_type) }}
              </div>
            </div>
            <button
              type="button"
              class="btn btn-sm btn-ghost w-full mt-3"
              @click="playPreview"
              :disabled="isPlayingPreview"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" v-if="!isPlayingPreview">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" v-else>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {{ isPlayingPreview ? '播放中...' : '播放预览' }}
            </button>
          </div>

          <!-- 首尾帧上传 -->
          <div class="space-y-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">场景首帧</span>
                <span class="label-text-alt text-base-content/50">用于淡入效果</span>
              </label>
              <input
                type="file"
                accept="image/png,image/jpeg,image/jpg"
                class="file-input file-input-bordered"
                @change="handleHeadFrameUpload"
              />
              <div v-if="scene?.head_frame" class="mt-2">
                <img
                  :src="scene.head_frame"
                  alt="首帧预览"
                  class="h-24 w-auto rounded"
                />
              </div>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-semibold">场景尾帧</span>
                <span class="label-text-alt text-base-content/50">用于淡出效果</span>
              </label>
              <input
                type="file"
                accept="image/png,image/jpeg,image/jpg"
                class="file-input file-input-bordered"
                @change="handleTailFrameUpload"
              />
              <div v-if="scene?.tail_frame" class="mt-2">
                <img
                  :src="scene.tail_frame"
                  alt="尾帧预览"
                  class="h-24 w-auto rounded"
                />
              </div>
            </div>
          </div>

          <!-- 按钮组 -->
          <div class="flex gap-2 pt-4 border-t border-base-300">
            <button
              type="button"
              class="btn btn-ghost flex-1"
              @click="$emit('close')"
            >
              取消
            </button>
            <button
              type="submit"
              class="btn btn-primary flex-1"
              :disabled="isSubmitting || hasErrors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" v-if="!isSubmitting">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" v-else>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {{ isSubmitting ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, onMounted } from 'vue';
import { sceneApi } from '@/services/artworkService';

export default {
  name: 'SceneTransitionPanel',
  props: {
    scene: {
      type: Object,
      required: true,
    },
    allScenes: {
      type: Array,
      default: () => [],
    },
  },
  emits: ['close', 'scene-updated'],
  setup(props, { emit }) {
    const isSubmitting = ref(false);
    const transitionTypeError = ref('');
    const durationError = ref('');
    const isPlayingPreview = ref(false);
    const previewOpacity = ref(1);

    // 表单数据
    const formData = reactive({
      transition_type: '',
      transition_to_next: null,
      transition_duration: 1.5,
    });

    // 可用的目标场景（当前场景之后的场景）
    const availableTargetScenes = computed(() => {
      if (!props.scene) return [];
      return props.allScenes.filter((s) => {
        // 只显示当前场景之后的场景
        return s.chapter === props.scene.chapter && s.scene_number > props.scene.scene_number;
      });
    });

    // 是否有错误
    const hasErrors = computed(() => {
      return !!transitionTypeError.value || !!durationError.value;
    });

    // 初始化表单数据
    const initFormData = () => {
      if (props.scene) {
        formData.transition_type = props.scene.transition_type || '';
        formData.transition_to_next = props.scene.transition_to_next || null;
        formData.transition_duration = props.scene.transition_duration || 1.5;
      }
    };

    // 验证表单
    const validateForm = () => {
      transitionTypeError.value = '';
      durationError.value = '';

      // 验证转场类型和目标
      if (formData.transition_type && !formData.transition_to_next) {
        transitionTypeError.value = '设置转场类型时必须指定转场目标场景';
        return false;
      }

      // 验证转场时长
      if (formData.transition_duration < 0 || formData.transition_duration > 10) {
        durationError.value = '转场时长必须在0-10秒之间';
        return false;
      }

      return true;
    };

    // 处理首帧上传
    const handleHeadFrameUpload = async (event) => {
      const file = event.target.files?.[0];
      if (!file) return;

      // TODO: 实现文件上传
      console.log('上传首帧:', file.name);
    };

    // 处理尾帧上传
    const handleTailFrameUpload = async (event) => {
      const file = event.target.files?.[0];
      if (!file) return;

      // TODO: 实现文件上传
      console.log('上传尾帧:', file.name);
    };

    // 播放预览动画
    const playPreview = () => {
      if (isPlayingPreview.value) return;

      isPlayingPreview.value = true;
      let opacity = 1;
      const duration = (formData.transition_duration || 1.5) * 1000;
      const steps = 60;
      const interval = duration / steps;

      const animate = setInterval(() => {
        opacity -= 1 / steps;
        previewOpacity.value = Math.max(0, opacity);

        if (opacity <= 0) {
          clearInterval(animate);
          setTimeout(() => {
            // 重置并反向动画
            let reverseOpacity = 0;
            const reverseAnimate = setInterval(() => {
              reverseOpacity += 1 / steps;
              previewOpacity.value = Math.min(1, reverseOpacity);

              if (reverseOpacity >= 1) {
                clearInterval(reverseAnimate);
                isPlayingPreview.value = false;
              }
            }, interval);
          }, 500);
        }
      }, interval);
    };

    // 获取转场类型标签
    const getTransitionTypeLabel = (type) => {
      const labels = {
        fade: '淡入淡出',
        dissolve: '溶解',
        wipe: '擦除',
        cut: '切镜',
      };
      return labels[type] || type;
    };

    // 提交表单
    const handleSubmit = async () => {
      if (!validateForm()) return;

      isSubmitting.value = true;
      try {
        const updateData = {
          transition_type: formData.transition_type || null,
          transition_to_next: formData.transition_to_next || null,
          transition_duration: formData.transition_duration,
        };

        const updatedScene = await sceneApi.update(props.scene.id, updateData);
        emit('scene-updated', updatedScene);
        emit('close');
      } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败: ' + (error.message || '未知错误'));
      } finally {
        isSubmitting.value = false;
      }
    };

    // 监听 scene 变化
    watch(() => props.scene, initFormData, { immediate: true });

    onMounted(() => {
      initFormData();
    });

    return {
      formData,
      availableTargetScenes,
      transitionTypeError,
      durationError,
      isSubmitting,
      hasErrors,
      isPlayingPreview,
      previewOpacity,
      handleHeadFrameUpload,
      handleTailFrameUpload,
      playPreview,
      getTransitionTypeLabel,
      handleSubmit,
    };
  },
};
</script>

<style scoped>
.drawer-content {
  width: 100%;
}
</style>
