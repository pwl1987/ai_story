<template>
  <div
    :class="[
      'card bg-base-100 shadow-xl hover:shadow-2xl transition-all duration-300',
      { 'ring-2 ring-primary': selected }
    ]"
    @click="$emit('select', character.id)"
  >
    <!-- 选择复选框 -->
    <div class="absolute top-2 left-2 z-10">
      <input
        type="checkbox"
        class="checkbox checkbox-sm"
        :checked="selected"
        @click.stop="$emit('select', character.id)"
      />
    </div>

    <!-- 立绘预览 -->
    <figure class="px-4 pt-4 relative">
      <portrait-preview
        :image="character.default_portrait"
        :name="character.display_name"
        :editable="false"
      />
      <!-- 角色类型标签 -->
      <div class="absolute top-2 right-2 flex flex-col gap-1">
        <div v-if="character.importance_rank <= 3" class="badge badge-primary badge-sm">
          主角
        </div>
        <div v-else class="badge badge-ghost badge-sm">
          配角
        </div>
      </div>
    </figure>

    <!-- 卡片内容 -->
    <div class="card-body p-4">
      <!-- 角色名称 -->
      <h2 class="card-title justify-center text-lg">
        {{ character.display_name }}
      </h2>

      <!-- 角色描述 -->
      <p v-if="character.description" class="text-sm text-base-content/70 line-clamp-2">
        {{ character.description }}
      </p>
      <p v-else class="text-sm text-base-content/50 italic">
        暂无描述
      </p>

      <!-- 统计信息 -->
      <div class="flex justify-center gap-2 my-2">
        <div class="badge badge-ghost">
          出场 {{ character.appearance_count }} 次
        </div>
        <div class="badge badge-ghost">
          造型 {{ character.poses?.length || 0 }} 套
        </div>
      </div>

      <!-- 造型预览 -->
      <div v-if="character.poses && character.poses.length > 0" class="mt-2">
        <div class="text-xs text-base-content/70 mb-1">造型预览</div>
        <div class="flex gap-1 overflow-x-auto pb-1">
          <img
            v-for="pose in character.poses.slice(0, 4)"
            :key="pose.id"
            :src="pose.pose_image"
            :alt="pose.pose_name"
            class="w-12 h-12 object-cover rounded cursor-pointer hover:ring-2 ring-primary"
            @click.stop="handlePoseClick(pose)"
          />
          <div
            v-if="character.poses.length > 4"
            class="w-12 h-12 bg-base-300 rounded flex items-center justify-center text-xs"
          >
            +{{ character.poses.length - 4 }}
          </div>
        </div>
      </div>

      <!-- 音色配置状态 -->
      <div v-if="character.voice_config" class="mt-2">
        <div class="text-xs text-base-content/70 mb-1">音色配置</div>
        <div class="badge badge-sm" :class="getVoiceBadgeClass(character.voice_config.tts_engine)">
          {{ character.voice_config.tts_engine_display || character.voice_config.tts_engine }}
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="card-actions justify-end mt-3">
        <button
          class="btn btn-sm btn-ghost"
          @click.stop="$emit('edit', character.id)"
        >
          编辑
        </button>
        <button
          class="btn btn-sm btn-ghost text-error"
          @click.stop="$emit('delete', character)"
        >
          删除
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import PortraitPreview from './PortraitPreview.vue';

export default {
  name: 'CharacterCard',

  components: {
    PortraitPreview,
  },

  props: {
    character: {
      type: Object,
      required: true,
    },
    selected: {
      type: Boolean,
      default: false,
    },
  },

  methods: {
    getVoiceBadgeClass(ttsEngine) {
      const classMap = {
        edge: 'badge-success',
        elevenlabs: 'badge-primary',
        baidu: 'badge-info',
        azure: 'badge-warning',
      };
      return classMap[ttsEngine] || 'badge-ghost';
    },

    handlePoseClick(pose) {
      // 可以添加造型预览或编辑逻辑
      console.log('Pose clicked:', pose);
    },
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
