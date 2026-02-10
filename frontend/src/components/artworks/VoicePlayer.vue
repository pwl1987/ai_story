<template>
  <div class="voice-player">
    <div class="bg-base-200 rounded-lg p-4">
      <!-- 标题 -->
      <div class="flex items-center justify-between mb-3">
        <label class="label">
          <span class="label-text font-medium">音色配置</span>
        </label>
        <button
          v-if="isConfigured"
          class="btn btn-xs btn-ghost"
          @click="testVoice"
          :disabled="isPlaying"
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
              d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
            />
          </svg>
          试听
        </button>
      </div>

      <!-- 未配置状态 -->
      <div v-if="!isConfigured" class="text-center py-4">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-8 w-8 mx-auto text-base-content/30"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
          />
        </svg>
        <p class="text-sm text-base-content/70 mt-2">未配置音色</p>
        <button class="btn btn-sm btn-primary mt-2" @click="$emit('configure')">
          配置音色
        </button>
      </div>

      <!-- 已配置状态 -->
      <div v-else class="space-y-4">
        <!-- TTS引擎显示 -->
        <div class="flex items-center gap-2">
          <div class="badge" :class="getEngineBadgeClass(config.tts_engine)">
            {{ config.tts_engine_display || config.tts_engine }}
          </div>
          <div v-if="config.voice_type" class="text-sm text-base-content/70">
            {{ config.voice_type }}
          </div>
        </div>

        <!-- 音色参数控制 -->
        <div class="space-y-3">
          <!-- 音调 -->
          <div class="form-control">
            <div class="label">
              <span class="label-text text-xs">音调</span>
              <span class="label-text-alt text-xs">{{ getPitchLabel(config.pitch) }}</span>
            </div>
            <input
              type="range"
              :value="pitchValues.indexOf(config.pitch)"
              min="0"
              :max="pitchValues.length - 1"
              class="range range-xs"
              @input="handlePitchChange"
            />
          </div>

          <!-- 语速 -->
          <div class="form-control">
            <div class="label">
              <span class="label-text text-xs">语速</span>
              <span class="label-text-alt text-xs">{{ getSpeedLabel(config.speed) }}</span>
            </div>
            <input
              type="range"
              :value="speedValues.indexOf(config.speed)"
              min="0"
              :max="speedValues.length - 1"
              class="range range-xs"
              @input="handleSpeedChange"
            />
          </div>

          <!-- 音量 -->
          <div class="form-control">
            <div class="label">
              <span class="label-text text-xs">音量</span>
              <span class="label-text-alt text-xs">{{ getVolumeLabel(config.volume) }}</span>
            </div>
            <input
              type="range"
              :value="volumeValues.indexOf(config.volume)"
              min="0"
              :max="volumeValues.length - 1"
              class="range range-xs"
              @input="handleVolumeChange"
            />
          </div>
        </div>

        <!-- 情感音色映射 -->
        <div v-if="config.emotion_voices && Object.keys(config.emotion_voices).length > 0" class="border-t border-base-300 pt-3">
          <div class="text-xs text-base-content/70 mb-2">情感音色</div>
          <div class="flex flex-wrap gap-1">
            <div
              v-for="(voiceId, emotion) in config.emotion_voices"
              :key="emotion"
              class="badge badge-ghost badge-sm cursor-pointer hover:badge-primary"
              @click="testEmotionVoice(emotion)"
            >
              {{ getEmotionLabel(emotion) }}
            </div>
          </div>
        </div>

        <!-- 音频播放器 -->
        <div v-if="audioUrl" class="border-t border-base-300 pt-3">
          <audio
            ref="audioPlayer"
            :src="audioUrl"
            @ended="handleAudioEnded"
            @timeupdate="handleTimeUpdate"
          />
          <div class="flex items-center gap-2">
            <button
              class="btn btn-sm btn-circle btn-primary"
              @click="togglePlay"
            >
              <svg
                v-if="!isPlaying"
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M8 5v14l11-7z" />
              </svg>
              <svg
                v-else
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
              </svg>
            </button>
            <button
              class="btn btn-sm btn-circle btn-ghost"
              @click="stop"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M6 6h12v12H6V6z" />
              </svg>
            </button>
            <div class="flex-1">
              <progress
                class="progress progress-primary w-full"
                :value="currentTime"
                :max="duration"
              ></progress>
            </div>
            <span class="text-xs">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VoicePlayer',

  props: {
    config: {
      type: Object,
      default: null,
    },
  },

  data() {
    return {
      pitchValues: ['very_low', 'low', 'normal', 'high', 'very_high'],
      speedValues: ['very_slow', 'slow', 'normal', 'fast', 'very_fast'],
      volumeValues: ['very_soft', 'soft', 'normal', 'loud', 'very_loud'],

      isPlaying: false,
      currentTime: 0,
      duration: 0,
      audioUrl: null,
    };
  },

  computed: {
    isConfigured() {
      return this.config && this.config.tts_engine;
    },
  },

  methods: {
    getEngineBadgeClass(engine) {
      const classMap = {
        edge: 'badge-success',
        elevenlabs: 'badge-primary',
        baidu: 'badge-info',
        azure: 'badge-warning',
      };
      return classMap[engine] || 'badge-ghost';
    },

    getPitchLabel(value) {
      const labels = {
        very_low: '极低',
        low: '低',
        normal: '正常',
        high: '高',
        very_high: '极高',
      };
      return labels[value] || value;
    },

    getSpeedLabel(value) {
      const labels = {
        very_slow: '极慢',
        slow: '慢',
        normal: '正常',
        fast: '快',
        very_fast: '极快',
      };
      return labels[value] || value;
    },

    getVolumeLabel(value) {
      const labels = {
        very_soft: '极小',
        soft: '小',
        normal: '正常',
        loud: '大',
        very_loud: '极大',
      };
      return labels[value] || value;
    },

    getEmotionLabel(emotion) {
      const labels = {
        neutral: '中性',
        happy: '开心',
        sad: '悲伤',
        angry: '愤怒',
        excited: '兴奋',
        calm: '平静',
      };
      return labels[emotion] || emotion;
    },

    handlePitchChange(event) {
      const index = parseInt(event.target.value);
      this.$emit('update:config', {
        ...this.config,
        pitch: this.pitchValues[index],
      });
    },

    handleSpeedChange(event) {
      const index = parseInt(event.target.value);
      this.$emit('update:config', {
        ...this.config,
        speed: this.speedValues[index],
      });
    },

    handleVolumeChange(event) {
      const index = parseInt(event.target.value);
      this.$emit('update:config', {
        ...this.config,
        volume: this.volumeValues[index],
      });
    },

    async testVoice() {
      this.$emit('test');
    },

    async testEmotionVoice(emotion) {
      this.$emit('test-emotion', emotion);
    },

    togglePlay() {
      const audio = this.$refs.audioPlayer;
      if (this.isPlaying) {
        audio.pause();
      } else {
        audio.play();
      }
      this.isPlaying = !this.isPlaying;
    },

    stop() {
      const audio = this.$refs.audioPlayer;
      audio.pause();
      audio.currentTime = 0;
      this.isPlaying = false;
      this.currentTime = 0;
    },

    handleAudioEnded() {
      this.isPlaying = false;
      this.currentTime = 0;
    },

    handleTimeUpdate(event) {
      this.currentTime = event.target.currentTime;
      if (!this.duration) {
        this.duration = event.target.duration;
      }
    },

    formatTime(seconds) {
      if (!seconds || isNaN(seconds)) return '0:00';
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    },

    setAudioUrl(url) {
      this.audioUrl = url;
    },
  },
};
</script>
