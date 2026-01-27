<template>
  <div class="video-player">
    <!-- 视频列表 -->
    <div v-if="videos && videos.length > 0" class="space-y-4">
      <!-- 单个视频卡片 -->
      <div
        v-for="(video, index) in videos"
        :key="index"
        class="card bg-base-100 shadow-xl"
      >
        <div class="card-body p-4">
          <div class="flex justify-between items-center mb-3">
            <h3 class="card-title text-sm">
              <span class="badge badge-secondary">视频 {{ video.scene_number || (index + 1) }}</span>
            </h3>
            <div class="flex gap-2">
              <button
                class="btn btn-sm btn-outline"
                @click="downloadVideo(video)"
                :title="'下载视频'"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                下载
              </button>
              <button
                class="btn btn-sm btn-primary"
                @click="playFullscreen(video)"
                :title="'全屏播放'"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
                全屏
              </button>
            </div>
          </div>

          <!-- 视频播放器 -->
          <div class="relative aspect-video bg-black rounded-lg overflow-hidden">
            <video
              :ref="`video_${index}`"
              class="w-full h-full"
              controls
              preload="metadata"
              @error="handleVideoError(index, $event)"
            >
              <source :src="getVideoUrl(video)" type="video/mp4">
              您的浏览器不支持视频播放
            </video>

            <!-- 视频信息覆盖层 -->
            <div v-if="video.description" class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-3">
              <p class="text-white text-sm">{{ video.description }}</p>
            </div>
          </div>

          <!-- 视频元数据 -->
          <div v-if="video.duration_seconds" class="flex gap-4 mt-2 text-xs text-base-content/60">
            <span>时长: {{ formatDuration(video.duration_seconds) }}</span>
            <span v-if="video.aspect_ratio">比例: {{ video.aspect_ratio }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="alert">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>暂无视频</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VideoPlayer',
  props: {
    /**
     * 视频列表
     * 格式: [{ url: '...', scene_number: 1, duration_seconds: 8, description: '...' }]
     */
    videos: {
      type: Array,
      default: () => [],
    },
  },
  methods: {
    /**
     * 获取视频URL
     */
    getVideoUrl(video) {
      if (typeof video === 'string') {
        return video;
      }
      if (video.urls && Array.isArray(video.urls) && video.urls.length > 0) {
        return video.urls[0].url || video.urls[0];
      }
      return video.url || '';
    },

    /**
     * 下载视频
     */
    downloadVideo(video) {
      const url = this.getVideoUrl(video);
      if (!url) {
        this.$message?.error('无效的视频URL');
        return;
      }

      // 创建下载链接
      const link = document.createElement('a');
      link.href = url;
      link.download = `video_${video.scene_number || 'video'}.mp4`;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      this.$message?.success('开始下载视频');
    },

    /**
     * 全屏播放
     */
    playFullscreen(video) {
      const url = this.getVideoUrl(video);
      if (!url) {
        this.$message?.error('无效的视频URL');
        return;
      }

      // 在新窗口打开视频
      window.open(url, '_blank');
    },

    /**
     * 格式化时长
     */
    formatDuration(seconds) {
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    },

    /**
     * 处理视频加载错误
     */
    handleVideoError(index, event) {
      console.error('视频加载失败:', index, event);
      this.$message?.error(`视频 ${index + 1} 加载失败`);
    },
  },
};
</script>

<style scoped>
.video-player {
  width: 100%;
}

video {
  object-fit: contain;
}

/* 自定义视频控制栏样式 */
video::-webkit-media-controls-panel {
  background-color: rgba(0, 0, 0, 0.8);
}

video::-webkit-media-controls-current-time-display,
video::-webkit-media-controls-time-remaining-display {
  color: white;
}
</style>
