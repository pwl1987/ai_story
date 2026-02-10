<template>
  <div class="pose-selector">
    <div class="flex items-center justify-between mb-2">
      <label class="label">
        <span class="label-text font-medium">角色造型</span>
        <span v-if="poses.length > 0" class="label-text-alt text-base-content/70">
          {{ poses.length }} 套造型
        </span>
      </label>
      <button
        v-if="allowAdd"
        class="btn btn-xs btn-primary gap-1"
        @click="$emit('add')"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-3 w-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 4v16m8-8H4"
          />
        </svg>
        添加造型
      </button>
    </div>

    <!-- 空状态 -->
    <div
      v-if="poses.length === 0"
      class="bg-base-200 rounded-lg p-8 text-center"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-12 w-12 mx-auto text-base-content/30"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>
      <p class="text-sm text-base-content/70 mt-2">暂无造型</p>
      <button
        v-if="allowAdd"
        class="btn btn-sm btn-primary mt-4"
        @click="$emit('add')"
      >
        添加第一套造型
      </button>
    </div>

    <!-- 造型列表 - 网格模式 -->
    <div v-else-if="layout === 'grid'" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
      <div
        v-for="pose in poses"
        :key="pose.id"
        :class="[
          'relative group cursor-pointer rounded-lg overflow-hidden transition-all duration-200',
          { 'ring-2 ring-primary': selectedPose?.id === pose.id }
        ]"
        @click="$emit('select', pose)"
      >
        <!-- 造型图片 -->
        <div class="aspect-square bg-base-200">
          <img
            v-if="pose.pose_image"
            :src="pose.pose_image"
            :alt="pose.pose_name"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-8 w-8 text-base-content/30"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
        </div>

        <!-- 默认标签 -->
        <div v-if="pose.is_default" class="absolute top-1 left-1">
          <div class="badge badge-primary badge-xs">默认</div>
        </div>

        <!-- 悬停操作 -->
        <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1">
          <button
            v-if="allowEdit"
            class="btn btn-xs btn-circle btn-ghost text-white"
            @click.stop="$emit('edit', pose)"
            title="编辑"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
          </button>
          <button
            v-if="!pose.is_default && allowSetDefault"
            class="btn btn-xs btn-circle btn-ghost text-white"
            @click.stop="$emit('set-default', pose)"
            title="设为默认"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              />
            </svg>
          </button>
          <button
            v-if="allowDelete"
            class="btn btn-xs btn-circle btn-ghost text-error"
            @click.stop="$emit('delete', pose)"
            title="删除"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>

        <!-- 造型名称 -->
        <div class="absolute bottom-0 left-0 right-0 bg-black/70 p-2">
          <div class="text-white text-xs truncate">{{ pose.pose_name }}</div>
          <div class="text-white/70 text-xs">{{ pose.pose_type_display || pose.pose_type }}</div>
        </div>
      </div>
    </div>

    <!-- 造型列表 - 列表模式 -->
    <div v-else class="space-y-2">
      <div
        v-for="pose in poses"
        :key="pose.id"
        :class="[
          'card card-side bg-base-200 cursor-pointer transition-all duration-200',
          { 'ring-2 ring-primary': selectedPose?.id === pose.id }
        ]"
        @click="$emit('select', pose)"
      >
        <figure class="w-20 h-20 flex-shrink-0">
          <img
            v-if="pose.pose_image"
            :src="pose.pose_image"
            :alt="pose.pose_name"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center bg-base-300">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-8 w-8 text-base-content/30"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
        </figure>
        <div class="card-body py-3 px-4 flex-1">
          <div class="flex items-start justify-between">
            <div>
              <h3 class="card-title text-sm">
                {{ pose.pose_name }}
                <div v-if="pose.is_default" class="badge badge-primary badge-xs ml-1">默认</div>
              </h3>
              <p class="text-xs text-base-content/70">
                {{ pose.pose_type_display || pose.pose_type }} · 使用 {{ pose.usage_count }} 次
              </p>
            </div>
            <div class="flex gap-1">
              <button
                v-if="allowEdit"
                class="btn btn-ghost btn-xs"
                @click.stop="$emit('edit', pose)"
              >
                编辑
              </button>
              <button
                v-if="!pose.is_default && allowSetDefault"
                class="btn btn-ghost btn-xs"
                @click.stop="$emit('set-default', pose)"
              >
                设为默认
              </button>
              <button
                v-if="allowDelete"
                class="btn btn-ghost btn-xs text-error"
                @click.stop="$emit('delete', pose)"
              >
                删除
              </button>
            </div>
          </div>
          <!-- 适用场景标签 -->
          <div v-if="pose.suitable_for_scenes && pose.suitable_for_scenes.length > 0" class="flex gap-1 mt-1">
            <div
              v-for="scene in pose.suitable_for_scenes.slice(0, 3)"
              :key="scene"
              class="badge badge-ghost badge-xs"
            >
              {{ scene }}
            </div>
            <div v-if="pose.suitable_for_scenes.length > 3" class="badge badge-ghost badge-xs">
              +{{ pose.suitable_for_scenes.length - 3 }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PoseSelector',

  props: {
    poses: {
      type: Array,
      default: () => [],
    },
    selectedPose: {
      type: Object,
      default: null,
    },
    layout: {
      type: String,
      default: 'grid', // grid | list
      validator: (value) => ['grid', 'list'].includes(value),
    },
    allowAdd: {
      type: Boolean,
      default: true,
    },
    allowEdit: {
      type: Boolean,
      default: true,
    },
    allowDelete: {
      type: Boolean,
      default: true,
    },
    allowSetDefault: {
      type: Boolean,
      default: true,
    },
  },
};
</script>
