<!-- Step Info - 步骤信息组件 -->
<template>
  <div class="step-info">
    <span class="text-gray-500">步骤</span>
    <span class="font-medium mx-1">{{ currentStep }}</span>
    <span class="text-gray-500">/ {{ totalSteps }}</span>
    <span v-if="stepName" class="ml-2 text-gray-600">: {{ stepName }}</span>
  </div>
</template>

<script>
export default {
  name: "StepInfo",
  props: {
    currentStep: {
      type: Number,
      required: true,
    },
    totalSteps: {
      type: Number,
      required: true,
    },
    stepName: {
      type: String,
      default: "",
    },
  },
};
</script>

<style scoped>
.step-info {
  display: flex;
  align-items: center;
}
</style>
