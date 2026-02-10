<template>
  <div class="portrait-preview">
    <div
      class="relative w-full h-64 bg-base-200 rounded-lg overflow-hidden cursor-pointer"
      @click="handleClick"
    >
      <!-- 图片 -->
      <img
        v-if="imageUrl"
        :src="imageUrl"
        :alt="name"
        :style="imageStyle"
        class="w-full h-full object-contain transition-transform duration-200"
        @wheel.prevent="handleZoom"
        @error="handleImageError"
      />
      <!-- 占位符 -->
      <div
        v-else
        class="w-full h-full flex items-center justify-center bg-base-300"
      >
        <div class="text-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-16 w-16 mx-auto text-base-content/30"
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
          <p class="text-sm text-base-content/50 mt-2">{{ name }}</p>
        </div>
      </div>

      <!-- 编辑控制按钮 -->
      <div v-if="editable" class="absolute bottom-2 right-2 flex gap-1">
        <button
          class="btn btn-sm btn-circle btn-ghost bg-base-100/80"
          @click.stop="rotate(-90)"
          title="向左旋转"
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
              d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
            />
          </svg>
        </button>
        <button
          class="btn btn-sm btn-circle btn-ghost bg-base-100/80"
          @click.stop="rotate(90)"
          title="向右旋转"
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
              d="M21 10H11a8 8 0 00-8 8v2m18-10l-6 6m6-6l-6-6"
            />
          </svg>
        </button>
        <label
          class="btn btn-sm btn-circle btn-primary"
          title="上传图片"
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
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
            />
          </svg>
          <input
            type="file"
            class="hidden"
            accept="image/*"
            @change="handleUpload"
          />
        </label>
        <button
          v-if="imageUrl"
          class="btn btn-sm btn-circle btn-ghost bg-base-100/80 text-error"
          @click.stop="handleRemove"
          title="删除图片"
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
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <!-- 缩放指示器 -->
      <div v-if="scale !== 1" class="absolute top-2 right-2">
        <div class="badge badge-sm">{{ Math.round(scale * 100) }}%</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PortraitPreview',

  props: {
    image: {
      type: [String, File],
      default: null,
    },
    name: {
      type: String,
      default: '角色',
    },
    editable: {
      type: Boolean,
      default: true,
    },
  },

  data() {
    return {
      scale: 1,
      rotation: 0,
      localImage: null,
      imageError: false,
    };
  },

  computed: {
    imageUrl() {
      if (this.localImage instanceof File) {
        return URL.createObjectURL(this.localImage);
      }
      return this.localImage || this.image;
    },

    imageStyle() {
      return {
        transform: `scale(${this.scale}) rotate(${this.rotation}deg)`,
      };
    },
  },

  watch: {
    image(newVal) {
      if (newVal && typeof newVal === 'string') {
        this.localImage = newVal;
        this.imageError = false;
      }
    },
  },

  mounted() {
    if (this.image && typeof this.image === 'string') {
      this.localImage = this.image;
    }
  },

  methods: {
    handleClick() {
      this.$emit('click');
    },

    handleZoom(event) {
      const delta = event.deltaY > 0 ? -0.1 : 0.1;
      this.scale = Math.max(0.5, Math.min(3, this.scale + delta));
    },

    rotate(degrees) {
      this.rotation = (this.rotation + degrees) % 360;
    },

    handleUpload(event) {
      const file = event.target.files[0];
      if (file) {
        this.localImage = file;
        this.imageError = false;
        this.$emit('upload', file);
      }
    },

    handleRemove() {
      this.localImage = null;
      this.scale = 1;
      this.rotation = 0;
      this.$emit('remove');
    },

    handleImageError() {
      this.imageError = true;
      this.$emit('error');
    },

    reset() {
      this.scale = 1;
      this.rotation = 0;
    },
  },
};
</script>

<style scoped>
.portrait-preview img {
  transition: transform 0.2s ease-out;
}
</style>
