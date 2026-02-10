<template>
  <div class="modal modal-open">
    <div class="modal-box max-w-2xl">
      <!-- 标题 -->
      <h3 class="font-bold text-lg mb-4">快速编辑镜头 #{{ shot?.shot_number }}</h3>

      <!-- 表单 -->
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <!-- 镜头内容 -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">镜头内容</span>
          </label>
          <textarea
            v-model="formData.content"
            class="textarea textarea-bordered h-24"
            placeholder="输入镜头内容..."
          ></textarea>
        </div>

        <!-- 说话人 -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">说话人</span>
          </label>
          <input
            v-model="formData.speaker"
            type="text"
            class="input input-bordered"
            placeholder="输入说话人名称（可选）"
          />
        </div>

        <!-- 旁白 -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">旁白</span>
          </label>
          <textarea
            v-model="formData.narration"
            class="textarea textarea-bordered h-20"
            placeholder="输入旁白内容（可选）"
          ></textarea>
        </div>

        <!-- 角色造型选择 -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">角色造型</span>
          </label>
          <select v-model="formData.character_pose" class="select select-bordered">
            <option :value="null">-- 无造型 --</option>
            <option
              v-for="pose in availablePoses"
              :key="pose.id"
              :value="pose.id"
            >
              {{ pose.character_display_name }} - {{ pose.pose_name }}
            </option>
          </select>
        </div>

        <!-- 运镜类型和角度 -->
        <div class="grid grid-cols-2 gap-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text">运镜类型</span>
            </label>
            <select v-model="formData.camera_movement" class="select select-bordered">
              <option value="">-- 默认 --</option>
              <option value="zoom_in">推近</option>
              <option value="zoom_out">拉远</option>
              <option value="pan_left">左摇</option>
              <option value="pan_right">右摇</option>
              <option value="tilt_up">上摇</option>
              <option value="tilt_down">下摇</option>
              <option value="static">固定</option>
            </select>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">镜头角度</span>
            </label>
            <select v-model="formData.camera_angle" class="select select-bordered">
              <option value="">-- 默认 --</option>
              <option value="eye_level">平视</option>
              <option value="high_angle">俯视</option>
              <option value="low_angle">仰视</option>
              <option value="bird_eye">鸟瞰</option>
              <option value="worm_eye">蚁视</option>
            </select>
          </div>
        </div>

        <!-- 运镜参数 JSON 编辑器 -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">运镜参数 (JSON)</span>
            <span class="label-text-alt text-base-content/50">可选</span>
          </label>
          <textarea
            v-model="cameraMovementParamsJson"
            class="textarea textarea-bordered h-20 font-mono text-sm"
            placeholder='{"zoom": "1.5x", "pan": "left", "speed": "medium"}'
            @input="validateJson"
          ></textarea>
          <label class="label" v-if="jsonError">
            <span class="label-text-alt text-error">{{ jsonError }}</span>
          </label>
        </div>

        <!-- 时长滑块 -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">时长: {{ formData.duration }}秒</span>
          </label>
          <input
            v-model.number="formData.duration"
            type="range"
            min="0.5"
            max="10"
            step="0.1"
            class="range range-primary"
          />
          <div class="flex justify-between text-xs text-base-content/50 mt-1">
            <span>0.5s</span>
            <span>5s</span>
            <span>10s</span>
          </div>
        </div>

        <!-- 构图描述 -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">构图描述</span>
            <span class="label-text-alt text-base-content/50">可选</span>
          </label>
          <textarea
            v-model="formData.shot_composition"
            class="textarea textarea-bordered h-20"
            placeholder="描述镜头构图和布局..."
          ></textarea>
        </div>

        <!-- 按钮组 -->
        <div class="modal-action">
          <button
            type="button"
            class="btn btn-ghost"
            @click="$emit('close')"
          >
            取消
          </button>
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="isSubmitting || !!jsonError"
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
</template>

<script>
import { ref, reactive, watch, onMounted } from 'vue';
import { shotApi } from '@/services/artworkService';

export default {
  name: 'QuickEditModal',
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
  emits: ['close', 'shot-updated'],
  setup(props, { emit }) {
    const isSubmitting = ref(false);
    const jsonError = ref('');

    // 表单数据
    const formData = reactive({
      content: '',
      speaker: '',
      narration: '',
      character_pose: null,
      camera_movement: '',
      camera_angle: '',
      camera_movement_params: {},
      duration: 3.0,
      shot_composition: '',
    });

    // 运镜参数 JSON 字符串
    const cameraMovementParamsJson = ref('{}');

    // 初始化表单数据
    const initFormData = () => {
      if (props.shot) {
        formData.content = props.shot.content || '';
        formData.speaker = props.shot.speaker || '';
        formData.narration = props.shot.narration || '';
        formData.character_pose = props.shot.character_pose || null;
        formData.camera_movement = props.shot.camera_movement || '';
        formData.camera_angle = props.shot.camera_angle || '';
        formData.camera_movement_params = props.shot.camera_movement_params || {};
        formData.duration = props.shot.duration || 3.0;
        formData.shot_composition = props.shot.shot_composition || '';

        // 转换为 JSON 字符串
        try {
          cameraMovementParamsJson.value = JSON.stringify(formData.camera_movement_params, null, 2);
        } catch {
          cameraMovementParamsJson.value = '{}';
        }
      }
    };

    // 验证 JSON 格式
    const validateJson = () => {
      try {
        if (cameraMovementParamsJson.value.trim()) {
          const parsed = JSON.parse(cameraMovementParamsJson.value);
          formData.camera_movement_params = parsed;
          jsonError.value = '';
        } else {
          formData.camera_movement_params = {};
          jsonError.value = '';
        }
      } catch (error) {
        jsonError.value = '无效的 JSON 格式';
      }
    };

    // 提交表单
    const handleSubmit = async () => {
      validateJson();
      if (jsonError.value) return;

      isSubmitting.value = true;
      try {
        const updateData = {
          content: formData.content,
          speaker: formData.speaker || null,
          narration: formData.narration || null,
          character_pose: formData.character_pose,
          camera_movement: formData.camera_movement || null,
          camera_angle: formData.camera_angle || null,
          camera_movement_params: formData.camera_movement_params,
          duration: formData.duration,
          shot_composition: formData.shot_composition || null,
        };

        const updatedShot = await shotApi.update(props.shot.id, updateData);
        emit('shot-updated', updatedShot);
        emit('close');
      } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败: ' + (error.message || '未知错误'));
      } finally {
        isSubmitting.value = false;
      }
    };

    // 监听 shot 变化
    watch(() => props.shot, initFormData, { immediate: true });

    onMounted(() => {
      initFormData();
    });

    return {
      formData,
      cameraMovementParamsJson,
      jsonError,
      isSubmitting,
      validateJson,
      handleSubmit,
    };
  },
};
</script>
