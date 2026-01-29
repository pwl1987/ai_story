<template>
  <div class="field-help">
    <!-- 帮助图标 -->
    <span
      class="help-icon"
      @mouseenter="showTooltip"
      @mouseleave="hideTooltip"
      @click="toggleHelp"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    </span>

    <!-- Tooltip -->
    <div
      class="tooltip"
      :class="{ 'is-visible': tooltipVisible }"
      v-html="tooltipContent"
    ></div>

    <!-- 详细帮助面板 -->
    <div class="help-panel" v-if="helpVisible" v-click-outside="closeHelp">
      <div class="help-header">
        <strong>{{ title }}</strong>
        <button class="close-btn" @click="closeHelp">✕</button>
      </div>
      <div class="help-body" v-html="helpContent"></div>
      <div class="help-examples" v-if="examples.length > 0">
        <strong>示例：</strong>
        <div class="example-item" v-for="(example, index) in examples" :key="index">
          <code>{{ example.value }}</code>
          <span>{{ example.description }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FieldHelp',
  props: {
    title: {
      type: String,
      required: true
    },
    tooltip: {
      type: String,
      default: ''
    },
    content: {
      type: String,
      default: ''
    },
    examples: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      tooltipVisible: false,
      helpVisible: false
    };
  },
  computed: {
    tooltipContent() {
      return this.tooltip || this.content;
    },
    helpContent() {
      return this.content || this.tooltip;
    }
  },
  methods: {
    showTooltip() {
      if (!this.helpVisible) {
        this.tooltipVisible = true;
      }
    },
    hideTooltip() {
      this.tooltipVisible = false;
    },
    toggleHelp() {
      this.helpVisible = !this.helpVisible;
      this.tooltipVisible = false;
    },
    closeHelp() {
      this.helpVisible = false;
    }
  },
  directives: {
    'click-outside': {
      bind(el, binding, vnode) {
        el.clickOutsideEvent = function(event) {
          if (!(el == event.target || el.contains(event.target))) {
            vnode.context[binding.expression](event);
          }
        };
        document.body.addEventListener('click', el.clickOutsideEvent);
      },
      unbind(el) {
        document.body.removeEventListener('click', el.clickOutsideEvent);
      }
    }
  }
};
</script>

<style scoped>
.field-help {
  position: relative;
  display: inline-block;
  margin-left: 4px;
  vertical-align: middle;
}

.help-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  color: #9ca3af;
  cursor: help;
  transition: color 0.2s;
}

.help-icon:hover {
  color: #667eea;
}

.tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 8px;
  padding: 8px 12px;
  background: #333;
  color: white;
  font-size: 12px;
  border-radius: 6px;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s;
  z-index: 100;
  max-width: 300px;
  white-space: normal;
  line-height: 1.4;
}

.tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: #333;
}

.tooltip.is-visible {
  opacity: 1;
  visibility: visible;
}

.help-panel {
  position: absolute;
  bottom: 100%;
  left: 0;
  margin-bottom: 8px;
  width: 400px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
}

.help-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  border-radius: 8px 8px 0 0;
}

.help-header strong {
  color: #333;
  font-size: 14px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  color: #9ca3af;
  cursor: pointer;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e5e7eb;
  color: #333;
}

.help-body {
  padding: 16px;
  font-size: 13px;
  color: #666;
  line-height: 1.6;
}

.help-body >>> ul {
  margin: 8px 0;
  padding-left: 20px;
}

.help-body >>> li {
  margin-bottom: 4px;
}

.help-body >>> code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #e83e8c;
}

.help-examples {
  padding: 12px 16px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
  border-radius: 0 0 8px 8px;
}

.help-examples strong {
  display: block;
  margin-bottom: 12px;
  font-size: 12px;
  color: #333;
}

.example-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.example-item:last-child {
  margin-bottom: 0;
}

.example-item code {
  background: white;
  border: 1px solid #e5e7eb;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: #333;
  white-space: nowrap;
}

.example-item span {
  font-size: 12px;
  color: #666;
}
</style>
