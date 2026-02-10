<!-- Progress Text - 百分比显示组件 -->
<template>
  <div class="progress-text flex items-center gap-2">
    <span class="text-2xl font-bold">{{ percentage }}%</span>
    <span class="text-sm text-gray-500">完成</span>
  </div>
</template>

<script>
export default {
  name: "ProgressText",
  props: {
    percentage: {
      type: Number,
      required: true,
      validator: (value) => value >= 0 && value <= 100,
    },
  },
};
</script>

<style scoped>
.progress-text {
  display: flex;
  align-items: center;
}
</style>
