<!-- Stage Progress - 阶段进度条组件 -->
<template>
  <div class="stage-progress">
    <!-- 阶段进度条容器 -->
    <div class="flex items-center justify-between mb-2">
      <h3 class="text-lg font-bold">{{ title }}</h3>
      <div class="text-sm text-gray-500">
        {{ completedStages.length }}/{{ stages.length }} 已完成
      </div>
    </div>

    <!-- 进度条 -->
    <div class="progress w-full h-4 bg-base-200 rounded-full overflow-hidden">
      <div
        class="progress-bar h-full transition-all duration-300 ease-in-out"
        :class="progressBarClass"
        :style="{ width: overallProgress + '%' }"
      ></div>
    </div>

    <!-- 阶段指示器 -->
    <div class="stage-indicators flex justify-between mt-4 relative">
      <!-- 连接线 -->
      <div class="absolute top-1/2 left-0 right-0 h-0.5 bg-base-300 -z-10"></div>

      <!-- 单个阶段指示器 -->
      <div
        v-for="(stage, index) in stages"
        :key="stage.key"
        class="stage-indicator relative z-0 flex flex-col items-center"
        :class="getStageClass(stage)"
      >
        <!-- 阶段图标 -->
        <div
          class="stage-icon w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all duration-300"
          :class="getStageIconClass(stage)"
        >
          <span v-if="isStageCompleted(stage)">✓</span>
          <span v-else-if="isStageActive(stage)">{{ index + 1 }}</span>
          <span v-else>{{ index + 1 }}</span>
        </div>

        <!-- 阶段名称 -->
        <div class="stage-name mt-2 text-xs text-center">{{ stage.name }}</div>

        <!-- 阶段状态（hover显示） -->
        <div class="stage-status mt-1 text-xs" :class="getStageStatusClass(stage)">
          {{ getStageStatusText(stage) }}
        </div>
      </div>
    </div>

    <!-- 当前阶段详情 -->
    <div v-if="currentStage" class="mt-6 p-4 bg-base-200 rounded-lg">
      <div class="flex justify-between items-center mb-2">
        <span class="font-medium">{{ currentStage.name }}</span>
        <span class="badge" :class="getStageBadgeClass(currentStage)">
          {{ getStageProgressText(currentStage) }}
        </span>
      </div>

      <!-- 进度条 -->
      <div class="progress w-full h-2 bg-base-300 rounded-full overflow-hidden">
        <div
          class="progress-bar h-full transition-all duration-300 ease-in-out"
          :class="getStageProgressBarClass(currentStage)"
          :style="{ width: getStageProgress(currentStage) + '%' }"
        ></div>
      </div>

      <!-- 步骤信息 -->
      <div v-if="currentStep" class="mt-2 text-sm text-gray-600">
        <StepInfo
          :current-step="currentStep"
          :total-steps="totalSteps"
          :step-name="stepName"
        />
      </div>

      <!-- 剩余时间 -->
      <div v-if="showTimeRemaining" class="mt-2">
        <TimeRemaining
          :percentage="getStageProgress(currentStage)"
          :stage-key="currentStage.key"
        />
      </div>
    </div>
  </div>
</template>

<script>
import StepInfo from "./StepInfo.vue";
import TimeRemaining from "./TimeRemaining.vue";

export default {
  name: "StageProgress",
  components: {
    StepInfo,
    TimeRemaining,
  },
  props: {
    title: {
      type: String,
      default: "生产进度",
    },
    stages: {
      type: Array,
      required: true,
      // 格式: [{ key: "llm", name: "文案改写", progress: 100, status: "completed" }]
    },
    currentStageKey: {
      type: String,
      default: null,
    },
    currentStep: {
      type: Number,
      default: null,
    },
    totalSteps: {
      type: Number,
      default: null,
    },
    stepName: {
      type: String,
      default: "",
    },
    showTimeRemaining: {
      type: Boolean,
      default: true,
    },
  },
  computed: {
    completedStages() {
      return this.stages.filter((s) => s.status === "completed");
    },
    activeStages() {
      return this.stages.filter((s) => s.status === "active");
    },
    currentStage() {
      if (!this.currentStageKey) return null;
      return this.stages.find((s) => s.key === this.currentStageKey);
    },
    overallProgress() {
      if (!this.stages.length) return 0;
      const totalProgress = this.stages.reduce((sum, s) => sum + (s.progress || 0), 0);
      return Math.round(totalProgress / this.stages.length);
    },
    progressBarClass() {
      const progress = this.overallProgress;
      if (progress >= 100) return "bg-success";
      if (progress >= 50) return "bg-warning";
      return "bg-primary";
    },
  },
  methods: {
    getStageClass(stage) {
      if (stage.status === "completed") return "stage-completed";
      if (stage.status === "active") return "stage-active";
      return "stage-pending";
    },
    getStageIconClass(stage) {
      if (stage.status === "completed") return "border-success bg-success text-success-content";
      if (stage.status === "active") return "border-primary bg-primary text-primary-content animate-pulse";
      return "border-base-300 bg-base-100 text-base-content";
    },
    getStageStatusClass(stage) {
      if (stage.status === "completed") return "text-success";
      if (stage.status === "active") return "text-primary";
      return "text-gray-400";
    },
    getStageStatusText(stage) {
      if (stage.status === "completed") return "已完成";
      if (stage.status === "active") return "进行中";
      return "未开始";
    },
    getStageBadgeClass(stage) {
      if (stage.status === "completed") return "badge-success";
      if (stage.status === "active") return "badge-primary";
      return "badge-ghost";
    },
    getStageProgressText(stage) {
      const progress = this.getStageProgress(stage);
      return `${progress}%`;
    },
    getStageProgress(stage) {
      return stage.progress || 0;
    },
    getStageProgressBarClass(stage) {
      const progress = this.getStageProgress(stage);
      if (progress >= 100) return "bg-success";
      if (progress >= 50) return "bg-info";
      return "bg-primary";
    },
    isStageCompleted(stage) {
      return stage.status === "completed";
    },
    isStageActive(stage) {
      return stage.status === "active";
    },
  },
};
</script>

<style scoped>
.stage-progress {
  position: relative;
}

.progress-bar {
  background-image: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #22c55e 100%);
}

.stage-icon {
  font-weight: 600;
  font-size: 0.875rem;
}

.stage-name {
  min-width: 60px;
  text-align: center;
}

.stage-completed .stage-icon {
  animation: checkmark 0.3s ease-in-out;
}

@keyframes checkmark {
  0% {
    transform: scale(0.8);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

.stage-active .stage-icon {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

.stage-pending .stage-icon {
  color: #9ca3af;
}
</style>
