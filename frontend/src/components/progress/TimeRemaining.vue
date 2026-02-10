<!-- Time Remaining - 剩余时间组件 -->
<template>
  <div class="time-remaining flex items-center gap-2 text-sm">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="h-4 w-4 text-gray-400"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
    <span class="text-gray-500">预计剩余:</span>
    <span class="font-medium" :class="{ 'text-warning': isLongTime }">
      {{ formattedTime }}
    </span>
  </div>
</template>

<script>
export default {
  name: "TimeRemaining",
  props: {
    percentage: {
      type: Number,
      required: true,
    },
    stageKey: {
      type: String,
      default: "",
    },
  },
  data() {
    return {
      // 历史平均耗时（秒）- 可从后端配置获取
      stageDurations: {
        llm: 60, // 文案改写：60秒
        storyboard: 120, // 分镜生成：2分钟
        image: 300, // 文生图：5分钟
        camera: 180, // 运镜生成：3分钟
        video: 600, // 图生视频：10分钟
      },
    };
  },
  computed: {
    stageDuration() {
      return this.stageDurations[this.stageKey] || 120;
    },
    remainingSeconds() {
      if (this.percentage >= 100) return 0;
      return Math.round(this.stageDuration * (1 - this.percentage / 100));
    },
    formattedTime() {
      const seconds = this.remainingSeconds;
      if (seconds < 60) {
        return `${seconds}秒`;
      } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        return `${minutes}分${seconds % 60}秒`;
      } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}小时${minutes}分`;
      }
    },
    isLongTime() {
      return this.remainingSeconds > 300; // 超过5分钟显示警告色
    },
  },
};
</script>

<style scoped>
.time-remaining {
  display: flex;
  align-items: center;
}
</style>
